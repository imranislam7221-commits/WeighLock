import threading
import time
import random
import re
import os
import json

from config import SCALE_COM_PORT, SCALE_BAUDRATE, SCALE_TIMEOUT, USE_TEST_SIMULATOR
from database import get_local_directory

BAUDS = [9600, 4800, 2400, 1200, 19200, 38400, 57600, 115200]


def parse_weight(raw):
    # Hijibiji bad: serial/date/overload reject, 0-60000kg valid
    # ex: "ST,GS,+  1234kg" "WN007500kg" "= 12.34T" ok
    # "CH-20261015" / "2026-10-15" / "99999999" -> None
    if not raw:
        return None
    s = raw.strip().upper()
    if not s:
        return None
    # date/time line bad (2026-10-15, 12:30:45) - scale data te thake na
    if re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', s) or s.count(":") >= 2:
        return None
    if re.search(r'\bOL\b', s) or "OVER" in s or "ERROR" in s or "FAIL" in s:
        return None
    is_ton = ("TON" in s or re.search(r'(?<![A-Z0-9])T(?![A-Z])', s) is not None)
    nums = re.findall(r'-?\d+(?:\.\d+)?', s.replace(",", ""))
    if not nums:
        return None
    cands = []
    for n in nums:
        try:
            f = float(n)
        except Exception:
            continue
        digits = len(n.replace("-", "").replace(".", ""))
        # 8+ digit serial/date bad (20261015)
        if digits >= 8:
            continue
        v = f
        if is_ton and abs(v) < 300:
            v = v * 1000
        elif not is_ton and 0 < abs(f) < 300 and "." in n:
            # 12.5 (dot, choto) -> ton, kintu 7500.0 -> kg thakbe
            intpart = n.split(".")[0].replace("-", "")
            if len(intpart) <= 3:
                v = f * 1000
        v = int(v)
        if 0 <= v <= 150000:
            cands.append(v)
    if not cands:
        return None
    # sabcheye boro valid tai weight
    return max(cands)


def read_scale_settings():
    port, baud, sim = SCALE_COM_PORT, SCALE_BAUDRATE, USE_TEST_SIMULATOR
    try:
        p = os.path.join(get_local_directory(), "settings.json")
        if os.path.exists(p):
            with open(p, "r") as f:
                js = json.load(f)
            port = js.get("scale_port", port) or port
            baud = js.get("scale_baud", baud) or baud
            if "use_simulator" in js:
                sim = bool(js["use_simulator"])
    except Exception:
        pass
    return port, baud, sim


def list_com_ports():
    try:
        from serial.tools import list_ports
        return [p.device for p in list_ports.comports()]
    except Exception:
        return []


class ScaleReader:
    """Universal RS232 / RS485-USB / USB-VirtualCOM reader + simulator.
    Note: beshir vag USB scale virtual-COM hoye ase, tai COM scan ei pabe.
    Pure HID scale hole driver + hidapi lagbe (code ready, optional)."""

    def __init__(self, on_weight=None, on_status=None, on_raw=None):
        self.current_weight = 0
        self.connected = False
        self.is_sim = False
        self.port = None
        self.baud = None
        self.stop_flag = False
        self.on_weight = on_weight
        self.on_status = on_status
        self.on_raw = on_raw
        self.thread = None
        self._sim_base = 12250

    def start(self):
        self.stop_flag = False
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_flag = True
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)

    def _set_status(self, msg):
        if self.on_status:
            self.on_status(msg)

    def _open(self, port, baud):
        import serial
        return serial.Serial(port=port, baudrate=int(baud), bytesize=8,
                             parity='N', stopbits=1, timeout=SCALE_TIMEOUT)

    def _candidates(self):
        want_port, want_baud, _sim = read_scale_settings()
        ports = []
        if want_port and str(want_port).upper() != "AUTO":
            ports = [want_port]
        else:
            ports = list_com_ports()
            if not ports:
                ports = [f"COM{i}" for i in range(1, 9)]
        if want_baud and str(want_baud).upper() != "AUTO":
            try:
                bauds = [int(want_baud)]
            except Exception:
                bauds = [9600]
        else:
            # fast: 9600 age, tarpor baki
            bauds = [9600, 4800, 2400, 19200, 38400, 1200, 57600, 115200]
        return ports, bauds

    def _stable_filter(self, val):
        # hijibiji spike bad: hothat +-1000 jump 1 bar asle ignore,
        # 2 bar same range e asle accept. median of last 3.
        try:
            if not hasattr(self, "_fbuf"):
                self._fbuf = []
                self._last = None
            if self._last is not None and abs(val - self._last) > 1000:
                # spike check: buf e same spike ache?
                same = [x for x in self._fbuf if abs(x - val) <= 100]
                if len(same) < 1:
                    self._fbuf.append(val)
                    if len(self._fbuf) > 3:
                        self._fbuf.pop(0)
                    return None
            self._fbuf.append(val)
            if len(self._fbuf) > 3:
                self._fbuf.pop(0)
            s = sorted(self._fbuf)
            med = s[len(s)//2]
            self._last = med
            return med
        except Exception:
            return val

    def _loop(self):
        ser = None
        ports, bauds = self._candidates()
        _, _, use_sim = read_scale_settings()
        # fast scan: proti combo 0.4s
        found = None
        if use_sim or ports:
            for pt in ports:
                if self.stop_flag:
                    return
                for bd in bauds:
                    if self.stop_flag:
                        return
                    try:
                        t = self._open(pt, bd)
                    except Exception:
                        continue
                    t0 = time.time()
                    buf = ""
                    while time.time() - t0 < 0.4 and not self.stop_flag:
                        try:
                            if t.in_waiting > 0:
                                chunk = t.read(t.in_waiting).decode('utf-8', errors='ignore')
                                buf += chunk
                                if self.on_raw:
                                    self.on_raw(f"{pt}@{bd}: {chunk.strip()[:60]}")
                                if parse_weight(buf) is not None:
                                    found = (pt, bd, t)
                                    break
                            else:
                                time.sleep(0.03)
                        except Exception:
                            break
                    if found:
                        break
                    try:
                        t.close()
                    except Exception:
                        pass
                if found:
                    break

        if found:
            pt, bd, ser = found
            self.port, self.baud = pt, bd
            self.connected = True
            self.is_sim = False
            self._set_status(f"Scale connected: {pt} @ {bd} (RS/USB auto)")
        else:
            if use_sim:
                self.connected = True
                self.is_sim = True
                n = len(list_com_ports())
                self._set_status(f"TEST MODE - Simulator ON (COM pai nai, scan {n} port)")
            else:
                self.connected = False
                self._set_status(f"Scale pai nai (scan {len(ports)} port). USB/RS cable + driver check korun.")
                return

        while not self.stop_flag:
            if self.is_sim:
                self._sim_base += random.randint(-8, 8)
                self._sim_base = max(1000, min(100000, self._sim_base))
                self.current_weight = self._sim_base
                if self.on_weight:
                    self.on_weight(self.current_weight)
                time.sleep(0.5)
                continue
            try:
                if ser and ser.in_waiting > 0:
                    raw = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    for line in raw.replace("\r", "\n").split("\n"):
                        val = parse_weight(line)
                        if val is not None:
                            fval = self._stable_filter(val)
                            if fval is None:
                                continue
                            self.current_weight = fval
                            if self.on_weight:
                                self.on_weight(self.current_weight)
                            break
                else:
                    time.sleep(0.05)
            except Exception as e:
                # disconnect hole reconnect try
                try:
                    self._set_status(f"Read error, reconnect... {e}")
                    try:
                        ser.close()
                    except Exception:
                        pass
                    time.sleep(1.5)
                    ser = self._open(self.port, self.baud)
                except Exception:
                    time.sleep(1.5)
        try:
            if ser and ser.is_open:
                ser.close()
        except Exception:
            pass
