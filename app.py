import time
import customtkinter as ctk
from tkinter import messagebox
from config import APP_TITLE, APP_SIZE, USE_TEST_SIMULATOR, STABLE_RANGE, STABLE_COUNT, SCALE_COM_PORT, WEIGHT_UNIT
from database import get_db_connection, fetch_recent, today_total, find_history_from_drives, get_local_directory, get_backup_directory, backup_file, find_last_by_truck, find_by_truck_or_challan, get_next_challan, save_tare_memory, get_tare_memory
from receipt import generate_pdf_receipt
from scale_reader import ScaleReader
from license_manager import get_hwid, check_license, save_license
from ui import theme as T
from ui.header import Header
from ui.weight_panel import WeightPanel
from ui.entry_form import EntryForm
from ui.history_table import HistoryTable
from ui.settings_window import SettingsWindow
import os
import shutil


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(APP_SIZE)
        ctk.set_appearance_mode("dark")

        self.current_weight = 0
        self.locked_weight = None
        self.saved_gross = 0
        self._hist = []
        self._stable_buf = []

        # Windows reinstall restore check
        try:
            _, restored, msg = find_history_from_drives()
            if restored:
                print(msg)
        except Exception:
            pass

        self.header = Header(self)
        self.header.set_live(not USE_TEST_SIMULATOR)

        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="both", expand=True)

        left = ctk.CTkFrame(mid, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)
        self.unit = self.load_unit()
        self.settings = self.load_settings()
        self.panel = WeightPanel(left, on_lock=self.toggle_lock,
                                 on_gross=self.save_gross, on_tare=self.save_tare_and_print,
                                 on_unit=self.save_unit, unit=self.unit)

        right = ctk.CTkScrollableFrame(mid, fg_color="transparent", width=360)
        right.pack(side="right", fill="both")
        # settings + reprint button
        ctk.CTkButton(right, text="⚙ সেটিংস (ফিল্ড অন/অফ)", font=("Hind Siliguri", 12, "bold"),
                      fg_color=T.CARD2, height=34, command=self.open_settings).pack(fill="x", padx=6, pady=(6, 0))
        ctk.CTkButton(right, text="🖨 Reprint - হারানো চালান", font=("Hind Siliguri", 12, "bold"),
                      fg_color=T.BLUE_DARK, height=34, command=self.open_reprint).pack(fill="x", padx=6, pady=(4, 0))
        ctk.CTkButton(right, text="📊 রিপোর্ট + ভাড়া", font=("Hind Siliguri", 12, "bold"),
                      fg_color=T.GREEN_DARK, height=34, command=self.open_report).pack(fill="x", padx=6, pady=(4, 0))
        from ui.entry_form import DEFAULT_MATS
        self.form = EntryForm(right, material_list=self.settings.get("material_list") or DEFAULT_MATS)
        self.form.apply_settings(show_challan=self.settings.get("show_challan", True),
                                 show_product=self.settings.get("show_product", True),
                                 allow_manual=self.settings.get("allow_manual", True),
                                 show_owner=self.settings.get("show_owner", True),
                                 show_address=self.settings.get("show_address", True))
        self.history = HistoryTable(right, on_backup=self.do_backup, on_restore=self.do_restore)

        self.status = ctk.CTkLabel(self, text="স্কেল চেক হচ্ছে...",
                                   font=("Hind Siliguri", 12), text_color=T.MUTED)
        self.status.pack(pady=(0, 6))

        # license check + HWID show
        self.hwid = get_hwid()
        if not check_license():
            self.after(500, lambda: self.ask_activation(f"ভুল কী! HWID: {self.hwid}"))
        else:
            # license.key না থাকলে seller কে HWID দেখাও
            import os as _os
            from license_manager import license_path as _lp
            if not _os.path.exists(_lp()):
                self.status.configure(text=f"HWID: {self.hwid} - বিক্রির সময় এই HWID দিয়ে কী বানান")

        self.reader = ScaleReader(on_weight=self._w_cb, on_status=self._s_cb)
        self.reader.start()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh_history()
        # operator login
        self.operator = "admin"
        try:
            from ui.login_window import LoginWindow
            def _set_op(n):
                self.operator = n
                try:
                    self.status.configure(text=f"Operator: {n} | {self.status.cget('text')}")
                except Exception:
                    pass
            self.after(600, lambda: LoginWindow(self, _set_op))
        except Exception:
            pass
        # truck / challan দিলে পুরান data auto
        self._truck_after = None
        try:
            self.form.truck.bind("<KeyRelease>", self._truck_typing)
            self.form.truck.bind("<FocusOut>", lambda e: self.auto_fill_truck())
            self.form.truck.bind("<Return>", lambda e: self.auto_fill_truck())
            self.form.challan.bind("<KeyRelease>", self._challan_typing)
            self.form.challan.bind("<FocusOut>", lambda e: self.auto_fill_challan())
            self.form.challan.bind("<Return>", lambda e: self.auto_fill_challan())
        except Exception:
            pass

    # thread-safe callbacks
    def _w_cb(self, v):
        self.after(0, lambda: self._on_weight(v))

    def _s_cb(self, m):
        self.after(0, lambda: self.status.configure(text=m))

    def _on_weight(self, v):
        # lock থাকলে update বন্ধ
        if self.locked_weight is not None:
            return
        self.current_weight = v
        self.panel.set_weight(v)
        # stable check
        self._stable_buf.append(v)
        if len(self._stable_buf) > STABLE_COUNT:
            self._stable_buf.pop(0)
        if len(self._stable_buf) == STABLE_COUNT:
            if max(self._stable_buf) - min(self._stable_buf) <= STABLE_RANGE:
                self.panel.stable.configure(text="স্থির ✔ LOCK চাপুন", fg_color=T.GREEN, text_color="black")
                # auto-lock ON থাকলে নিজে লক হবে, default manual
                try:
                    if getattr(self, "settings", {}).get("auto_lock", False):
                        self.toggle_lock()
                        try:
                            self.status.configure(text="অটো LOCK হয়েছে (setting ON)")
                        except Exception:
                            pass
                except Exception:
                    pass

    def toggle_lock(self):
        if self.locked_weight is None:
            self.locked_weight = self.current_weight
            self.panel.set_locked(True, self.locked_weight)
            self.panel.set_weight(self.locked_weight)
        else:
            self.locked_weight = None
            self._stable_buf.clear()
            self.panel.set_locked(False)

    def eff_weight(self):
        return self.locked_weight if self.locked_weight is not None else self.current_weight

    def save_gross(self):
        d0 = self.form.get_data()
        if not d0["truck"]:
            messagebox.showwarning("আটকে গেছে", "ধাপ ১: আগে গাড়ি নম্বর লিখুন।\nগাড়ি নম্বর ছাড়া ১ম ওজন হবে না।")
            try:
                self.form.truck.focus()
            except Exception:
                pass
            return
        if self.locked_weight is None:
            messagebox.showwarning("আটকে গেছে", "ওজন LOCK না করে ১ম সেভ হবে না।\nআগে ⚖ LOCK চাপুন।")
            return
        if not d0["material"]:
            messagebox.showwarning("আটকে গেছে", "মাল / Item dropdown থেকে বাছুন।")
            return
        w = self.eff_weight()
        if w <= 0:
            messagebox.showwarning("সতর্ক", "ওজন ০! গাড়ি তুলুন, LOCK করে আবার চাপুন।")
            return
        if w < 1 or w > 150000:
            messagebox.showwarning("আটকে গেছে", "ওজন ১ KG - ১৫০ টন (1-150000 KG) এর মধ্যে হতে হবে।")
            return
        self.saved_gross = w
        self.panel.set_values(self.saved_gross, 0, 0)
        self.form.set_step(f"✔ ১ম সেভ OK: {w} KG | গাড়ি: {d0['truck']}\nএবার খালি গাড়ি তুলে LOCK + ২য় স্লিপ চাপুন।")
        messagebox.showinfo("সেভ", f"১ম ওজন সেভ: {w} KG\nগাড়ি: {d0['truck']}\nএবার খালি গাড়ি তুলুন।")

    def save_tare_and_print(self):
        # mandatory: truck + gross + tare + net, skip করে print হবে না
        if self.saved_gross <= 0:
            messagebox.showwarning("আটকে গেছে", "আগে LOCK করে ১ম ওজন (Gross) সেভ করুন।\nস্কিপ করে স্লিপ হবে না।")
            return
        d = self.form.get_data()
        if not d["truck"]:
            messagebox.showwarning("আটকে গেছে", "ট্রাক নম্বর ছাড়া স্লিপ হবে না।")
            return
        if not d["material"]:
            messagebox.showwarning("আটকে গেছে", "মাল / Item বাছুন। না থাকলে অন্যান্য / Others দিন।")
            return
        # manual tare / single weight: হাতে লেখা tare use
        if d.get("use_manual"):
            try:
                tare = float(d["manual_tare"])
            except Exception:
                messagebox.showwarning("সতর্ক", "হাতে tare সংখ্যায় লিখুন।")
                return
        else:
            if self.locked_weight is None:
                messagebox.showwarning("আটকে গেছে", "২য় ওজনের জন্য LOCK চাপুন।\nঅথবা 'খালি ওজন জানা আছে' টিক দিন।")
                return
            tare = self.eff_weight()
            if tare <= 0:
                messagebox.showwarning("সতর্ক", "২য় ওজন ০! গাড়ি তুলুন বা হাতে tare লিখুন।")
                return
        if tare <= 0:
            messagebox.showwarning("আটকে গেছে", "Tare ওজন ০ হতে পারবে না।")
            return
        net = self.saved_gross - tare
        if net < 0:
            # উল্টা হলে swap (খালি আগে, ভরা পরে)
            net = -net
            gross, tare = tare, self.saved_gross
        else:
            gross = self.saved_gross
        if gross <= 0 or tare <= 0 or net <= 0:
            messagebox.showwarning("আটকে গেছে", "Gross/Tare/Net তিনটাই লাগবে। ০ দিয়ে স্লিপ হবে না।")
            return
        if gross == tare:
            messagebox.showwarning("আটকে গেছে", "১ম ও ২য় ওজন একই! ভুল স্কিপ হচ্ছে।")
            return
        # overload alarm: capacity (default 100 ton)
        try:
            cap = float(self.settings.get("capacity_ton", 100) or 100) * 1000
        except Exception:
            cap = 100000
        if gross > cap:
            if not messagebox.askyesno("OVERLOAD!", f"ওজন {gross} KG capacity {cap:.0f} KG এর বেশি!\nতবুও স্লিপ করবেন?"):
                return
        # vara auto + due/baki
        try:
            fps = float(self.settings.get("fee_per_slip", 0) or 0)
        except Exception:
            fps = 0
        try:
            fpt = float(self.settings.get("fee_per_ton", 0) or 0)
        except Exception:
            fpt = 0
        amount = fps + (net/1000.0) * fpt
        try:
            paid = float(d.get("paid", 0) or 0)
        except Exception:
            paid = 0
        due = max(0, amount - paid)
        slip = str(int(time.time()))[-8:]
        import time as _t
        ts = _t.strftime('%Y-%m-%d %H:%M:%S')
        # proti challan e auto number, khali thakle banai dao
        challan_auto = (d.get("challan") or "").strip()
        if not challan_auto:
            try:
                challan_auto = get_next_challan()
                try:
                    self.form.challan.delete(0, "end")
                    self.form.challan.insert(0, challan_auto)
                except Exception:
                    pass
            except Exception:
                challan_auto = f"CH-{slip}"
        try:
            conn = get_db_connection()
            conn.execute("INSERT INTO records (truck_no, material, gross, tare, net, time_stamp, driver, supplier, mobile, slip_no, challan_no, product, owner, address, amount, paid, due, operator) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (d["truck"], d["material"], gross, tare, net, ts, d["driver"], d["supplier"], d["mobile"], slip, challan_auto, d.get("product",""), d.get("owner",""), d.get("address",""), amount, paid, due, getattr(self, "operator", "")))
            conn.commit()
            conn.close()
            # tare memory save (porer bar auto)
            try:
                # khali gari = choto weight tai tare
                save_tare_memory(d["truck"], tare)
            except Exception:
                pass
            # local DB backup to D:
            try:
                backup_file(os.path.join(get_local_directory(), "truck_scale.db"))
            except Exception:
                pass
            pdf = generate_pdf_receipt(d["truck"], d["material"], gross, tare, net,
                                       driver=d["driver"], supplier=d["supplier"],
                                       slip_no=slip, mobile=d["mobile"],
                                       challan_no=challan_auto, product=d.get("product",""),
                                       owner=d.get("owner",""), address=d.get("address",""),
                                       amount=amount, paid=paid, due=due,
                                       operator=getattr(self, "operator", ""))
            try:
                backup_file(pdf)
            except Exception:
                pass
            self.panel.set_values(gross, tare, net)
            self.saved_gross = 0
            self.locked_weight = None
            self.panel.set_locked(False)
            self.form.set_step("✔ স্লিপ OK। পরের গাড়ির নম্বর লিখুন।")
            self.refresh_history()
            messagebox.showinfo("সফল", f"নিট: {net} KG\nভাড়া: {amount:.0f} জমা: {paid:.0f} বাকি: {due:.0f}\nস্লিপ: {slip}\nPDF রেডি।")
        except Exception as e:
            messagebox.showerror("এরর", str(e))

    def refresh_history(self):
        try:
            rows = fetch_recent(30)
            self.history.set_rows(rows)
            c, kg = today_total()
            self.history.set_total(c or 0, kg or 0)
        except Exception:
            pass

    def _truck_typing(self, event=None):
        try:
            if self._truck_after:
                self.after_cancel(self._truck_after)
            self._truck_after = self.after(600, self.auto_fill_truck)
        except Exception:
            pass

    def auto_fill_truck(self):
        self._auto_fill(self.form.truck.get().strip())

    def _challan_typing(self, event=None):
        try:
            if self._truck_after:
                self.after_cancel(self._truck_after)
            self._truck_after = self.after(600, self.auto_fill_challan)
        except Exception:
            pass

    def auto_fill_challan(self):
        q = ""
        try:
            q = self.form.challan.get().strip()
        except Exception:
            pass
        if len(q) >= 2:
            self._auto_fill(q, from_challan=True)

    def _auto_fill(self, q, from_challan=False):
        try:
            if len((q or "").strip()) < 2:
                return
            rec = find_by_truck_or_challan(q)
            if not rec:
                if not from_challan:
                    self.form.set_data(info="নতুন গাড়ি - তথ্য লিখুন")
                return
            # truck khali thakle truck o bosao, challan khali thakle challan bosao
            try:
                if not self.form.truck.get().strip() and rec.get("truck_no"):
                    self.form.truck.delete(0, "end")
                    self.form.truck.insert(0, rec["truck_no"])
                if not self.form.challan.get().strip() and rec.get("challan"):
                    self.form.challan.delete(0, "end")
                    self.form.challan.insert(0, rec["challan"])
            except Exception:
                pass
            self.form.set_data(driver=rec.get("driver", ""),
                               supplier=rec.get("supplier", ""),
                               mobile=rec.get("mobile", ""),
                               material=rec.get("material", ""),
                               challan=rec.get("challan", ""),
                               product=rec.get("product", ""),
                               owner=rec.get("owner", ""),
                               address=rec.get("address", ""),
                               info=f"✔ হিস্ট্রি পাওয়া গেছে: {rec['trips']} বার | {rec['truck_no']}")
            # tare memory: khali wajan mone thakle manual e bosao
            try:
                mem = get_tare_memory(rec["truck_no"])
                if mem and not self.form.tare_manual.get().strip():
                    self.form.manual_var.set(True)
                    try:
                        self.form._toggle_manual()
                    except Exception:
                        pass
                    self.form.tare_manual.delete(0, "end")
                    self.form.tare_manual.insert(0, str(int(mem)))
                    self.form.set_step(f"মনে রাখা tare: {int(mem)} KG বসানো হয়েছে।")
            except Exception:
                pass
        except Exception:
            pass

    def do_backup(self):
        try:
            b = get_backup_directory()
            if not b:
                messagebox.showwarning("ব্যাকআপ", "D: drive পাইনি।")
                return
            src = os.path.join(get_local_directory(), "truck_scale.db")
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(b, "truck_scale.db"))
            messagebox.showinfo("ব্যাকআপ", f"ব্যাকআপ OK: {b}")
        except Exception as e:
            messagebox.showerror("এরর", str(e))

    def do_restore(self):
        _, ok, msg = find_history_from_drives()
        messagebox.showinfo("Restore", msg)
        self.refresh_history()

    def open_reprint(self):
        from ui.reprint_window import ReprintWindow
        try:
            ReprintWindow(self)
        except Exception as e:
            messagebox.showerror("এরর", str(e))

    def open_report(self):
        from ui.report_window import ReportWindow
        def on_fee(fps, fpt):
            try:
                self.settings["fee_per_slip"] = fps
                self.settings["fee_per_ton"] = fpt
                self.save_settings()
            except Exception:
                pass
        try:
            ReportWindow(self, self.settings, on_fee_save=on_fee)
        except Exception as e:
            messagebox.showerror("এরর", str(e))

    def ask_activation(self, msg):
        import customtkinter as _ctk
        win = _ctk.CTkToplevel(self)
        win.title("Lifetime Activation")
        win.geometry("420x260")
        _ctk.CTkLabel(win, text="Lifetime Register", font=("Hind Siliguri", 16, "bold")).pack(pady=10)
        _ctk.CTkLabel(win, text=f"HWID: {self.hwid}\n{msg}\nবিক্রেতার দেওয়া কী দিন:",
                      font=("Hind Siliguri", 12)).pack(pady=6)
        ent = _ctk.CTkEntry(win, width=300, height=40)
        ent.pack(pady=8)
        def ok():
            if save_license(ent.get()):
                messagebox.showinfo("OK", "Lifetime active!")
                win.destroy()
            else:
                messagebox.showerror("ভুল", "কী মিলেনি। HWID বিক্রেতাকে দিন।")
        _ctk.CTkButton(win, text="Active করুন", command=ok).pack(pady=8)

    def load_unit(self):
        import json
        try:
            p = os.path.join(get_local_directory(), "settings.json")
            if os.path.exists(p):
                with open(p, "r") as f:
                    u = json.load(f).get("unit", WEIGHT_UNIT)
                    return u if u in ("KG", "TON_KG") else "KG"
        except Exception:
            pass
        return WEIGHT_UNIT

    def load_settings(self):
        import json
        from ui.entry_form import DEFAULT_MATS
        base = {"unit": self.unit if hasattr(self, "unit") else WEIGHT_UNIT,
                "show_challan": True, "show_product": True,
                "show_owner": True, "show_address": True,
                "allow_manual": True, "require_truck": True,
                "auto_lock": False, "use_simulator": True,
                "strict_license": False, "fee_per_slip": 0, "fee_per_ton": 0,
                "capacity_ton": 100,
                "scale_port": "AUTO", "scale_baud": "AUTO",
                "material_list": DEFAULT_MATS[:]}
        try:
            p = os.path.join(get_local_directory(), "settings.json")
            if os.path.exists(p):
                with open(p, "r") as f:
                    base.update(json.load(f))
        except Exception:
            pass
        return base

    def open_settings(self):
        def on_save(out):
            old_port = self.settings.get("scale_port", "AUTO")
            old_baud = self.settings.get("scale_baud", "AUTO")
            old_sim = self.settings.get("use_simulator", True)
            mats = out.pop("material_list", None)
            self.settings.update(out)
            if mats:
                self.settings["material_list"] = mats
                try:
                    self.form.set_material_list(mats)
                except Exception:
                    pass
            self.save_settings()
            self.form.apply_settings(show_challan=self.settings.get("show_challan", True),
                                     show_product=self.settings.get("show_product", True),
                                     allow_manual=self.settings.get("allow_manual", True),
                                     show_owner=self.settings.get("show_owner", True),
                                     show_address=self.settings.get("show_address", True))
            # port/baud/sim bodlale reader restart
            try:
                if (self.settings.get("scale_port") != old_port or
                        self.settings.get("scale_baud") != old_baud or
                        self.settings.get("use_simulator") != old_sim):
                    try:
                        self.reader.stop()
                    except Exception:
                        pass
                    self.reader = ScaleReader(on_weight=self._w_cb, on_status=self._s_cb)
                    self.reader.start()
                    self.status.configure(text="Scale restart: port/baud change")
            except Exception:
                pass
        SettingsWindow(self, self.settings, on_save)

    def save_settings(self):
        import json
        try:
            self.settings["unit"] = getattr(self, "unit", WEIGHT_UNIT)
            p = os.path.join(get_local_directory(), "settings.json")
            with open(p, "w") as f:
                json.dump(self.settings, f)
            try:
                backup_file(p)
            except Exception:
                pass
        except Exception:
            pass

    def save_unit(self, unit):
        self.unit = unit
        try:
            if hasattr(self, "settings"):
                self.settings["unit"] = unit
                self.save_settings()
                return
        except Exception:
            pass
        import json
        try:
            p = os.path.join(get_local_directory(), "settings.json")
            cur = {}
            if os.path.exists(p):
                with open(p, "r") as f:
                    cur = json.load(f)
            cur["unit"] = unit
            with open(p, "w") as f:
                json.dump(cur, f)
        except Exception:
            pass

    def on_close(self):
        try:
            self.reader.stop()
        except Exception:
            pass
        self.destroy()
