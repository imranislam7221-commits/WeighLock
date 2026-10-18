import customtkinter as ctk
from ui import theme as T
from database import search_history, get_record_by_id
from receipt import generate_pdf_receipt
from tkinter import messagebox


class ReprintWindow(ctk.CTkToplevel):
    # হারানো challan reprint: gari/challan/slip/date দিয়ে খুঁজে same PDF আবার
    # same gari multi-trip serial+date অনুযায়ী আলাদা save থাকে
    def __init__(self, master):
        super().__init__(master)
        self.title("Reprint - হারানো চালান আবার প্রিন্ট")
        self.geometry("640x520")
        self._rows = []

        ctk.CTkLabel(self, text="Reprint - গাড়ি / চালান / স্লিপ / তারিখ লিখে খুঁজুন",
                     font=("Hind Siliguri", 15, "bold")).pack(pady=10)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16)
        self.ent = ctk.CTkEntry(top, placeholder_text="যেমন: TRUCK-123 বা CH-20261015-001 বা 2026-10-15",
                                font=("Hind Siliguri", 13), height=40)
        self.ent.pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(top, text="🔍 খুঁজুন", font=("Hind Siliguri", 13, "bold"),
                      width=110, command=self.do_search).pack(side="left")
        self.ent.bind("<Return>", lambda e: self.do_search())

        self.list = ctk.CTkScrollableFrame(self, height=300)
        self.list.pack(fill="both", expand=True, padx=16, pady=10)

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkLabel(bot, text="লিস্ট থেকে একটা বেছে Reprint চাপুন। Same গাড়ির প্রতিটা ট্রিপ আলাদা serial+date এ save থাকে।",
                     font=("Hind Siliguri", 12), text_color=T.MUTED).pack(anchor="w")
        self.btn = ctk.CTkButton(bot, text="🖨 Reprint PDF", font=("Hind Siliguri", 14, "bold"),
                                 fg_color=T.GREEN_DARK, height=44, command=self.do_reprint)
        self.btn.pack(fill="x", pady=(8, 0))
        self._sel = None
        self.do_search()

    def do_search(self):
        q = self.ent.get().strip() if hasattr(self, "ent") else ""
        try:
            rows = search_history(q, limit=50)
        except Exception as e:
            messagebox.showerror("এরর", str(e))
            return
        self._rows = rows
        for w in self.list.winfo_children():
            w.destroy()
        self._sel = None
        if not rows:
            ctk.CTkLabel(self.list, text="কিছু পাওয়া যায়নি। local drive + D: backup দুটোতেই খোঁজা হয়।",
                         font=("Hind Siliguri", 13)).pack(pady=20)
            return
        self.var = ctk.StringVar(value="")
        for r in rows:
            _id, truck, challan, slip, mat, g, t, n, ts = r
            txt = f"#{_id} | {ts} | {truck} | {challan} | {mat} | Net {n}kg"
            ctk.CTkRadioButton(self.list, text=txt, value=str(_id),
                               variable=self.var, font=("Hind Siliguri", 12)).pack(anchor="w", padx=8, pady=3)

    def do_reprint(self):
        try:
            rid = self.var.get().strip()
        except Exception:
            rid = ""
        if not rid:
            messagebox.showwarning("বাছুন", "আগে লিস্ট থেকে একটা রেকর্ড বাছুন।")
            return
        try:
            rec = get_record_by_id(int(rid))
        except Exception:
            rec = None
        if not rec:
            messagebox.showerror("এরর", "রেকর্ড পাওয়া যায়নি।")
            return
        try:
            path = generate_pdf_receipt(rec["truck_no"], rec["material"], rec["gross"],
                                        rec["tare"], rec["net"], driver=rec.get("driver",""),
                                        supplier=rec.get("supplier",""), slip_no=rec.get("slip_no",""),
                                        mobile=rec.get("mobile",""), challan_no=rec.get("challan_no",""),
                                        product=rec.get("product",""), owner=rec.get("owner",""),
                                        address=rec.get("address",""), reprint=True)
            messagebox.showinfo("Reprint OK", f"আবার প্রিন্ট রেডি:\n{path}\nChallan: {rec.get('challan_no')}")
        except Exception as e:
            messagebox.showerror("এরর", str(e))
