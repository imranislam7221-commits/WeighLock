import customtkinter as ctk
from ui import theme as T


class HistoryTable(ctk.CTkFrame):
    def __init__(self, master, on_backup=None, on_restore=None):
        super().__init__(master, fg_color=T.CARD, corner_radius=12)
        self.pack(fill="both", expand=True, padx=6, pady=6)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(top, text="আজকের হিসাব + শেষ স্লিপ",
                     font=("Hind Siliguri", 15, "bold"), text_color=T.TEXT).pack(side="left")
        self.total = ctk.CTkLabel(top, text="0 গাড়ি | 0 KG",
                                  font=("Hind Siliguri", 12, "bold"),
                                  text_color=T.GREEN)
        self.total.pack(side="right")

        self.box = ctk.CTkScrollableFrame(self, fg_color=T.BG, corner_radius=8, height=220)
        self.box.pack(fill="both", expand=True, padx=12, pady=6)

        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkButton(bot, text="💾 ব্যাকআপ (D:)", font=("Hind Siliguri", 12, "bold"),
                      fg_color=T.BLUE_DARK, height=36, command=on_backup).pack(
                          side="left", expand=True, fill="x", padx=(0, 4))
        ctk.CTkButton(bot, text="📥 হিস্ট্রি ফেরত আনুন", font=("Hind Siliguri", 12, "bold"),
                      fg_color=T.CARD2, height=36, command=on_restore).pack(
                          side="left", expand=True, fill="x", padx=(4, 0))

    def set_total(self, count, kg):
        self.total.configure(text=f"{count} গাড়ি | {kg} KG")

    def set_rows(self, rows):
        for w in self.box.winfo_children():
            w.destroy()
        if not rows:
            ctk.CTkLabel(self.box, text="এখনো স্লিপ হয়নি",
                         font=("Hind Siliguri", 13), text_color=T.MUTED).pack(pady=20)
            return
        for r in rows:
            # backward compatible: 8 col (puran) ba 10 col (challan+slip soho)
            if len(r) >= 10:
                _id, truck, driver, mat, g, t, n, ts, challan, slip = r[:10]
                txt = f"#{_id} {truck} | {challan or slip} | {mat} | Net {n}kg | {ts}"
            elif len(r) == 9:
                _id, truck, challan, slip, mat, g, t, n, ts = r
                txt = f"#{_id} {truck} | {challan or slip} | {mat} | Net {n}kg | {ts}"
            else:
                _id, truck, driver, mat, g, t, n, ts = r[:8]
                txt = f"#{_id} {truck} | {mat} | Net {n}kg | {ts}"
            ctk.CTkLabel(self.box, text=txt, font=("Hind Siliguri", 12),
                         text_color=T.TEXT, anchor="w").pack(anchor="w", padx=8, pady=2)
