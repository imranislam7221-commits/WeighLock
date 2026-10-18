import customtkinter as ctk
import time
from ui import theme as T
from database import report_range
from ui.report_pdf import generate_report_pdf
from tkinter import messagebox


class ReportWindow(ctk.CTkToplevel):
    # date-range hisab + vara/fee
    def __init__(self, master, settings, on_fee_save=None):
        super().__init__(master)
        self.title("Report - Hisab + Vara")
        self.geometry("620x540")
        self.settings = settings
        self.on_fee_save = on_fee_save

        ctk.CTkLabel(self, text="রিপোর্ট - তারিখ + ভাড়া হিসাব",
                     font=("Hind Siliguri", 15, "bold")).pack(pady=8)

        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="x", padx=16)
        self.d1 = ctk.CTkEntry(f, width=130, font=("Arial", 12))
        self.d1.pack(side="left", padx=(0, 6))
        self.d1.insert(0, time.strftime('%Y-%m-%d'))
        self.d2 = ctk.CTkEntry(f, width=130, font=("Arial", 12))
        self.d2.pack(side="left", padx=(0, 6))
        self.d2.insert(0, time.strftime('%Y-%m-%d'))
        self.tq = ctk.CTkEntry(f, font=("Hind Siliguri", 12))
        self.tq.pack(side="left", expand=True, fill="x", padx=(0, 6))
        try:
            self.tq.configure(placeholder_text="গাড়ি filter (khali = sob)")
        except Exception:
            pass
        ctk.CTkButton(f, text="দেখুন", width=80, command=self.do_view).pack(side="left")

        ff = ctk.CTkFrame(self, fg_color="transparent")
        ff.pack(fill="x", padx=16, pady=(8, 0))
        ctk.CTkLabel(ff, text="Vara/slip Tk:", font=("Hind Siliguri", 12)).pack(side="left")
        self.fee_s = ctk.CTkEntry(ff, width=90, font=("Arial", 12))
        self.fee_s.pack(side="left", padx=6)
        self.fee_s.insert(0, str(settings.get("fee_per_slip", 0)))
        ctk.CTkLabel(ff, text="Vara/ton Tk:", font=("Hind Siliguri", 12)).pack(side="left")
        self.fee_t = ctk.CTkEntry(ff, width=90, font=("Arial", 12))
        self.fee_t.pack(side="left", padx=6)
        self.fee_t.insert(0, str(settings.get("fee_per_ton", 0)))

        self.total = ctk.CTkLabel(self, text="", font=("Hind Siliguri", 13, "bold"), text_color=T.GREEN)
        self.total.pack(pady=6)
        self.box = ctk.CTkScrollableFrame(self, height=240)
        self.box.pack(fill="both", expand=True, padx=16, pady=4)
        ctk.CTkButton(self, text="🖨 Report PDF + Vara", font=("Hind Siliguri", 14, "bold"),
                      fg_color=T.GREEN_DARK, height=42, command=self.do_pdf).pack(fill="x", padx=16, pady=(4, 4))
        ctk.CTkButton(self, text="📗 Excel Ledger Export", font=("Hind Siliguri", 13, "bold"),
                      height=38, command=self.do_excel).pack(fill="x", padx=16, pady=(0, 10))
        self.do_view()

    def _fees(self):
        try:
            fps = float(self.fee_s.get().strip() or 0)
        except Exception:
            fps = 0
        try:
            fpt = float(self.fee_t.get().strip() or 0)
        except Exception:
            fpt = 0
        return fps, fpt

    def do_view(self):
        d1 = self.d1.get().strip() or time.strftime('%Y-%m-%d')
        d2 = self.d2.get().strip() or d1
        tq = self.tq.get().strip()
        try:
            rows, trips, net, due = report_range(d1, d2, tq)
        except Exception as e:
            messagebox.showerror("এরর", str(e))
            return
        fps, fpt = self._fees()
        fee = trips * fps + (net/1000) * fpt
        self.total.configure(text=f"{trips} trip | {net} KG | Vara {fee:.0f} Tk | Due {due:.0f} Tk")
        for w in self.box.winfo_children():
            w.destroy()
        for r in rows[:100]:
            _id, truck, challan, mat, g, t, n, ts = r[:8]
            due1 = r[10] if len(r) > 10 else 0
            ctk.CTkLabel(self.box, text=f"#{_id} {str(ts)[:16]} {truck} {challan} Net {n}kg Due {due1}",
                         font=("Hind Siliguri", 12), anchor="w").pack(anchor="w", padx=8, pady=1)
        self._last = (d1, d2, tq)

    def do_excel(self):
        try:
            from ui.excel_export import export_ledger_excel
            d1, d2, tq = getattr(self, "_last", (self.d1.get().strip(), self.d2.get().strip(), self.tq.get().strip()))
            rows, trips, net, due = report_range(d1, d2, tq)
            path = export_ledger_excel(rows, d1, d2)
            messagebox.showinfo("Excel OK", f"{trips} trip\n{path}")
        except Exception as e:
            messagebox.showerror("এরর", str(e))

    def do_pdf(self):
        d1 = self.d1.get().strip() or time.strftime('%Y-%m-%d')
        d2 = self.d2.get().strip() or d1
        tq = self.tq.get().strip()
        fps, fpt = self._fees()
        try:
            if self.on_fee_save:
                self.on_fee_save(fps, fpt)
        except Exception:
            pass
        try:
            path, trips, net, fee = generate_report_pdf(d1, d2, tq, fps, fpt)
            messagebox.showinfo("Report OK", f"{trips} trip, {net} KG, Vara {fee:.0f} Tk\n{path}")
        except Exception as e:
            messagebox.showerror("এরর", str(e))
