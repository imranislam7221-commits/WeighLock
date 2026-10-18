import os
import shutil
import sqlite3
import logging

from logger import get_logger

log = get_logger("database")

APP_DIR = os.path.dirname(os.path.abspath(__file__))


def get_local_directory():
    # LOCAL SAVE: app folder er ভেতরে data/
    d = os.path.join(APP_DIR, "data")
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "Receipts"), exist_ok=True)
    return d


def get_working_directory():
    return get_local_directory()


def get_backup_directory():
    # D: থাকলে auto backup ওখানেও যাবে
    if os.path.exists("D:\\"):
        b = os.path.join("D:\\", "TruckScale_SafeBackup")
        try:
            os.makedirs(b, exist_ok=True)
            os.makedirs(os.path.join(b, "Receipts"), exist_ok=True)
            return b
        except Exception as e:
            log.warning("backup dir create failed: %s", e)
            return None
    return None


def backup_file(local_path):
    # local -> D: backup copy
    try:
        bdir = get_backup_directory()
        if not bdir:
            return
        rel = os.path.relpath(local_path, get_local_directory())
        dest = os.path.join(bdir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(local_path, dest)
    except Exception as e:
        log.debug("backup_file failed: %s", e)


def find_history_from_drives():
    # Windows notun dile D:/E:/F: theke history khuje local e restore
    # Returns: (found_path, restored_bool, msg)
    local_db = os.path.join(get_local_directory(), "truck_scale.db")
    local_empty = True
    if os.path.exists(local_db) and os.path.getsize(local_db) > 12288:
        try:
            c = sqlite3.connect(local_db, timeout=5)
            n = c.execute("SELECT COUNT(*) FROM records").fetchone()[0]
            c.close()
            if n > 0:
                local_empty = False
        except Exception as e:
            log.warning("local db check failed: %s", e)
            pass
    if not local_empty:
        return (local_db, False, "Local e history ache")
    for drv in ["D:\\", "E:\\", "F:\\", "G:\\"]:
        cand = os.path.join(drv, "TruckScale_SafeBackup", "truck_scale.db")
        try:
            if os.path.exists(cand) and os.path.getsize(cand) > 0:
                shutil.copy2(cand, local_db)
                # receipts folder o restore
                r_src = os.path.join(drv, "TruckScale_SafeBackup", "Receipts")
                r_dst = os.path.join(get_local_directory(), "Receipts")
                if os.path.exists(r_src):
                    for fn in os.listdir(r_src):
                        s = os.path.join(r_src, fn)
                        d = os.path.join(r_dst, fn)
                        if os.path.isfile(s) and not os.path.exists(d):
                            try:
                                shutil.copy2(s, d)
                            except Exception as e:
                                log.debug("receipt restore skip %s: %s", fn, e)
                return (cand, True, f"{drv} theke history restore hoise")
        except Exception as e:
            log.warning("drive %s scan failed: %s", drv, e)
            continue
    return (None, False, "Kothao backup pai nai")


def get_db_connection():
    db_path = os.path.join(get_local_directory(), "truck_scale.db")
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            truck_no TEXT, material TEXT, gross REAL, tare REAL, net REAL, time_stamp TEXT,
            driver TEXT DEFAULT '', supplier TEXT DEFAULT '', mobile TEXT DEFAULT '',
            slip_no TEXT DEFAULT '', challan_no TEXT DEFAULT '', product TEXT DEFAULT '',
            owner TEXT DEFAULT '', address TEXT DEFAULT '',
            amount REAL DEFAULT 0, paid REAL DEFAULT 0, due REAL DEFAULT 0,
            operator TEXT DEFAULT ''
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS truck_tare (
            truck_no TEXT PRIMARY KEY, tare REAL, updated TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS operators (
            name TEXT PRIMARY KEY, pin TEXT
        )
    ''')
    try:
        cur = conn.execute("SELECT COUNT(*) FROM operators")
        if cur.fetchone()[0] == 0:
            conn.execute("INSERT INTO operators (name, pin) VALUES (?, ?)", ("admin", "1234"))
            conn.commit()
    except Exception as e:
        log.warning("operator init failed: %s", e)
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(records)").fetchall()]
        for c in ["driver", "supplier", "mobile", "slip_no", "challan_no", "product", "owner", "address"]:
            if c not in cols:
                conn.execute(f"ALTER TABLE records ADD COLUMN {c} TEXT DEFAULT ''")
        for c in ["amount", "paid", "due"]:
            if c not in cols:
                conn.execute(f"ALTER TABLE records ADD COLUMN {c} REAL DEFAULT 0")
        if "operator" not in cols:
            conn.execute("ALTER TABLE records ADD COLUMN operator TEXT DEFAULT ''")
    except Exception as e:
        log.warning("schema migration failed: %s", e)
    conn.execute('CREATE INDEX IF NOT EXISTS idx_time ON records(time_stamp)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_truck ON records(truck_no)')
    return conn


def save_tare_memory(truck_no, tare):
    try:
        import time as _t
        conn = get_db_connection()
        conn.execute("INSERT OR REPLACE INTO truck_tare (truck_no, tare, updated) VALUES (?,?,?)",
                     (truck_no.strip(), float(tare), _t.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_tare_memory(truck_no):
    try:
        conn = get_db_connection()
        cur = conn.execute("SELECT tare FROM truck_tare WHERE LOWER(TRIM(truck_no))=LOWER(TRIM(?))", (truck_no.strip(),))
        r = cur.fetchone()
        conn.close()
        return r[0] if r else None
    except Exception:
        return None


def check_operator(name, pin):
    try:
        conn = get_db_connection()
        cur = conn.execute("SELECT pin FROM operators WHERE LOWER(TRIM(name))=LOWER(TRIM(?))", (name.strip(),))
        r = cur.fetchone()
        conn.close()
        return bool(r and r[0] == pin)
    except Exception:
        return False


def fetch_recent(limit=30):
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "SELECT id, truck_no, driver, material, gross, tare, net, time_stamp, challan_no, slip_no "
            "FROM records ORDER BY id DESC LIMIT ?", (limit,)
        )
        return cur.fetchall()
    finally:
        conn.close()


def search_history(q, limit=50):
    # reprint: gari/challan/slip/date diye khujo, same gari multi-trip serial+date onujayi
    q = (q or "").strip()
    conn = get_db_connection()
    try:
        if not q:
            cur = conn.execute(
                "SELECT id, truck_no, challan_no, slip_no, material, gross, tare, net, time_stamp "
                "FROM records ORDER BY id DESC LIMIT ?", (limit,)
            )
            return cur.fetchall()
        like = "%" + q + "%"
        cur = conn.execute(
            "SELECT id, truck_no, challan_no, slip_no, material, gross, tare, net, time_stamp "
            "FROM records WHERE truck_no LIKE ? OR challan_no LIKE ? OR slip_no LIKE ? "
            "OR driver LIKE ? OR time_stamp LIKE ? "
            "ORDER BY id DESC LIMIT ?",
            (like, like, like, like, like, limit)
        )
        return cur.fetchall()
    finally:
        conn.close()


def report_range(d_from, d_to, truck_q="", limit=500):
    # date range + truck filter: d_from/d_to 'YYYY-MM-DD'
    conn = get_db_connection()
    try:
        if d_from == d_to:
            if truck_q:
                cur = conn.execute(
                    "SELECT id, truck_no, challan_no, material, gross, tare, net, time_stamp, amount, paid, due "
                    "FROM records WHERE date(time_stamp)=date(?) AND truck_no LIKE ? "
                    "ORDER BY id", (d_from, "%" + truck_q + "%"))
            else:
                cur = conn.execute(
                    "SELECT id, truck_no, challan_no, material, gross, tare, net, time_stamp, amount, paid, due "
                    "FROM records WHERE date(time_stamp)=date(?) ORDER BY id", (d_from,))
        else:
            if truck_q:
                cur = conn.execute(
                    "SELECT id, truck_no, challan_no, material, gross, tare, net, time_stamp, amount, paid, due "
                    "FROM records WHERE date(time_stamp) BETWEEN date(?) AND date(?) AND truck_no LIKE ? "
                    "ORDER BY id LIMIT ?", (d_from, d_to, "%" + truck_q + "%", limit))
            else:
                cur = conn.execute(
                    "SELECT id, truck_no, challan_no, material, gross, tare, net, time_stamp, amount, paid, due "
                    "FROM records WHERE date(time_stamp) BETWEEN date(?) AND date(?) "
                    "ORDER BY id LIMIT ?", (d_from, d_to, limit))
        rows = cur.fetchall()
        trips = len(rows)
        total_net = sum((r[6] or 0) for r in rows)
        total_due = sum((r[10] or 0) for r in rows)
        return rows, trips, total_net, total_due
    finally:
        conn.close()


def get_record_by_id(rid):
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "SELECT id, truck_no, material, gross, tare, net, time_stamp, driver, supplier, mobile, slip_no, challan_no, product, owner, address "
            "FROM records WHERE id=?", (rid,)
        )
        r = cur.fetchone()
        if not r:
            return None
        keys = ["id","truck_no","material","gross","tare","net","time_stamp","driver","supplier","mobile","slip_no","challan_no","product","owner","address"]
        return dict(zip(keys, r))
    finally:
        conn.close()


def today_total():
    import time
    conn = get_db_connection()
    try:
        d = time.strftime('%Y-%m-%d')
        cur = conn.execute(
            "SELECT COUNT(*), IFNULL(SUM(net),0) FROM records WHERE time_stamp LIKE ?",
            (d + "%",)
        )
        return cur.fetchone()
    finally:
        conn.close()


def find_last_by_truck(truck_no):
    # গাড়ি নম্বর দিলে আগের শেষ তথ্য auto আনবে
    truck_no = (truck_no or "").strip()
    if not truck_no:
        return None
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "SELECT truck_no, driver, supplier, mobile, material, challan_no, product, owner, address "
            "FROM records WHERE LOWER(TRIM(truck_no))=LOWER(TRIM(?)) "
            "ORDER BY id DESC LIMIT 1", (truck_no,)
        )
        row = cur.fetchone()
        if not row:
            # partial match
            cur = conn.execute(
                "SELECT truck_no, driver, supplier, mobile, material, challan_no, product, owner, address FROM records "
                "WHERE truck_no LIKE ? ORDER BY id DESC LIMIT 1", ("%" + truck_no + "%",)
            )
            r2 = cur.fetchone()
            if r2:
                return {"truck_no": r2[0], "driver": r2[1], "supplier": r2[2],
                        "mobile": r2[3], "material": r2[4], "challan": r2[5],
                        "product": r2[6], "owner": r2[7], "address": r2[8],
                        "trips": 1, "exact": False}
            return None
        # total trips
        cur2 = conn.execute("SELECT COUNT(*) FROM records WHERE LOWER(TRIM(truck_no))=LOWER(TRIM(?))",
                            (truck_no,))
        trips = cur2.fetchone()[0]
        return {"truck_no": row[0], "driver": row[1], "supplier": row[2],
                "mobile": row[3], "material": row[4], "challan": row[5],
                "product": row[6], "owner": row[7], "address": row[8],
                "trips": trips, "exact": True}
    finally:
        conn.close()


def search_trucks(prefix, limit=8):
    prefix = (prefix or "").strip()
    if len(prefix) < 1:
        return []
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "SELECT DISTINCT truck_no FROM records WHERE truck_no LIKE ? "
            "ORDER BY id DESC LIMIT ?", ("%" + prefix + "%", limit)
        )
        return [r[0] for r in cur.fetchall()]
    finally:
        conn.close()


def get_next_challan():
    # proti challan e auto number: CH-YYYYMMDD-001
    import time as _t
    d = _t.strftime('%Y%m%d')
    conn = get_db_connection()
    try:
        cur = conn.execute("SELECT COUNT(*) FROM records WHERE time_stamp LIKE ?",
                           (_t.strftime('%Y-%m-%d') + "%",))
        n = (cur.fetchone()[0] or 0) + 1
        return f"CH-{d}-{n:03d}"
    finally:
        conn.close()


def find_by_truck_or_challan(q):
    # gari number BA challan number likhle history theke auto fill
    q = (q or "").strip()
    if len(q) < 2:
        return None
    conn = get_db_connection()
    try:
        cur = conn.execute(
            "SELECT truck_no, driver, supplier, mobile, material, challan_no, product, owner, address "
            "FROM records WHERE LOWER(TRIM(truck_no))=LOWER(TRIM(?)) "
            "OR LOWER(TRIM(challan_no))=LOWER(TRIM(?)) "
            "OR LOWER(TRIM(slip_no))=LOWER(TRIM(?)) "
            "ORDER BY id DESC LIMIT 1", (q, q, q)
        )
        r = cur.fetchone()
        if r:
            cur2 = conn.execute("SELECT COUNT(*) FROM records WHERE LOWER(TRIM(truck_no))=LOWER(TRIM(?))", (r[0],))
            trips = cur2.fetchone()[0]
            return {"truck_no": r[0], "driver": r[1], "supplier": r[2], "mobile": r[3],
                    "material": r[4], "challan": r[5], "product": r[6],
                    "owner": r[7], "address": r[8], "trips": trips, "exact": True}
        cur = conn.execute(
            "SELECT truck_no, driver, supplier, mobile, material, challan_no, product, owner, address "
            "FROM records WHERE truck_no LIKE ? OR challan_no LIKE ? OR slip_no LIKE ? "
            "ORDER BY id DESC LIMIT 1", ("%" + q + "%", "%" + q + "%", "%" + q + "%")
        )
        r2 = cur.fetchone()
        if r2:
            return {"truck_no": r2[0], "driver": r2[1], "supplier": r2[2], "mobile": r2[3],
                    "material": r2[4], "challan": r2[5], "product": r2[6],
                    "owner": r2[7], "address": r2[8], "trips": 1, "exact": False}
        return None
    finally:
        conn.close()
