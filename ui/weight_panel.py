import customtkinter as ctk
from ui import theme as T
from ui.units import format_weight


class WeightPanel(ctk.CTkFrame):
    # Live weight + LOCK + Gross/Tare/Net card + KG/Ton switch
    def __init__(self, master, on_lock=None, on_gross=None, on_tare=None, on_reset=None, on_unit=None, unit="KG"):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="x", padx=12, pady=6)
        self.on_lock = on_lock
        self.on_unit = on_unit
        self.unit = unit
        self._last = 0
        self._gv = self._tv = self._nv = 0

        box = ctk.CTkFrame(self, fg_color="#0a0f1e", corner_radius=14,
                           border_width=2, border_color=T.CARD2)
        box.pack(fill="x")

        top = ctk.CTkFrame(box, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkLabel(top, text="লাইভ ওজন (Live Weight)",
                     font=("Hind Siliguri", 14), text_color=T.MUTED).pack(side="left")
        self.stable = ctk.CTkLabel(top, text="স্থির হলে LOCK চাপুন",
                                   font=("Hind Siliguri", 12, "bold"),
                                   fg_color=T.CARD2, text_color=T.YELLOW,
                                   corner_radius=8, padx=10, pady=4)
        self.stable.pack(side="right")

        self.lbl = ctk.CTkLabel(box, text="0 KG", font=("Arial", 62, "bold"),
                                text_color=T.GREEN)
        self.lbl.pack(pady=(4, 2))

        self.lock_lbl = ctk.CTkLabel(box, text="🔓 আনলক - ওজন উঠানামা করছে",
                                     font=("Hind Siliguri", 13), text_color=T.MUTED)
        self.lock_lbl.pack(pady=(0, 8))

        btns = ctk.CTkFrame(box, fg_color="transparent")
        btns.pack(pady=(0, 12))
        self.btn_lock = ctk.CTkButton(btns, text="⚖ ওজন LOCK করুন",
                                      font=("Hind Siliguri", 14, "bold"),
                                      fg_color=T.YELLOW, text_color="black",
                                      width=180, height=42, command=self.on_lock)
        self.btn_lock.pack(side="left", padx=6)
        self.btn_unit = ctk.CTkButton(btns, text="KG | টন-কেজি",
                                      font=("Hind Siliguri", 12, "bold"),
                                      fg_color=T.CARD2, text_color=T.TEXT,
                                      width=140, height=42, command=self._unit_click)
        self.btn_unit.pack(side="left", padx=6)
        self._unit_text()

        # Gross / Tare / Net 3 card
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", pady=(8, 0))
        self.gross_v = self._card(cards, "১ম ওজন (Gross)", "0 KG", T.BLUE)
        self.tare_v = self._card(cards, "২য় ওজন (Tare)", "0 KG", T.BLUE_DARK)
        self.net_v = self._card(cards, "নিট মাল (Net)", "0 KG", T.GREEN_DARK)

        act = ctk.CTkFrame(self, fg_color="transparent")
        act.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(act, text="১ম ওজন সেভ (Gross)",
                      font=("Hind Siliguri", 13, "bold"),
                      fg_color=T.BLUE, height=44, command=on_gross).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(act, text="২য় ওজন + স্লিপ (Net)",
                      font=("Hind Siliguri", 13, "bold"),
                      fg_color=T.GREEN_DARK, height=44, command=on_tare).pack(side="left", expand=True, fill="x", padx=(5, 0))

    def _card(self, parent, title, val, color):
        f = ctk.CTkFrame(parent, fg_color=T.CARD, corner_radius=10)
        f.pack(side="left", expand=True, fill="x", padx=4)
        ctk.CTkLabel(f, text=title, font=("Hind Siliguri", 12),
                     text_color=T.MUTED).pack(pady=(8, 0))
        v = ctk.CTkLabel(f, text=val, font=("Arial", 18, "bold"), text_color=T.TEXT)
        v.pack(pady=(0, 8))
        return v

    def set_weight(self, kg):
        self._last = kg
        self.lbl.configure(text=format_weight(kg, self.unit))

    def set_locked(self, locked, kg=0):
        if locked:
            self.lock_lbl.configure(text=f"🔒 লকড: {format_weight(kg, self.unit)} - এবার সেভ চাপুন", text_color=T.GREEN)
            self.stable.configure(text="LOCKED", fg_color=T.GREEN, text_color="black")
        else:
            self.lock_lbl.configure(text="🔓 আনলক - ওজন উঠানামা করছে", text_color=T.MUTED)
            self.stable.configure(text="স্থির হলে LOCK চাপুন", fg_color=T.CARD2, text_color=T.YELLOW)

    def set_values(self, gross, tare, net):
        self._gv, self._tv, self._nv = gross, tare, net
        self.gross_v.configure(text=format_weight(gross, self.unit))
        self.tare_v.configure(text=format_weight(tare, self.unit))
        self.net_v.configure(text=format_weight(net, self.unit))

    def _unit_click(self):
        self.unit = "TON_KG" if self.unit == "KG" else "KG"
        self._unit_text()
        self.set_weight(self._last)
        self.set_values(self._gv, self._tv, self._nv)
        if self.on_unit:
            self.on_unit(self.unit)

    def _unit_text(self):
        try:
            self.btn_unit.configure(text="মোড: টন-কেজি" if self.unit == "TON_KG" else "মোড: কেজি (KG)")
        except Exception:
            pass

    def set_unit(self, unit):
        self.unit = unit if unit in ("KG", "TON_KG") else "KG"
        self._unit_text()
