import customtkinter as ctk
import time
from ui import theme as T
from config import COMPANY_NAME, COMPANY_TAG


class Header(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=T.CARD, corner_radius=12)
        self.pack(fill="x", padx=12, pady=(12, 6))

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", padx=14, pady=10)
        ctk.CTkLabel(left, text=COMPANY_NAME, font=("Hind Siliguri", 22, "bold"),
                     text_color=T.TEXT).pack(anchor="w")
        ctk.CTkLabel(left, text=COMPANY_TAG + "  |  ট্রাক স্কেল বিক্রয় সংস্করণ",
                     font=("Hind Siliguri", 12), text_color=T.MUTED).pack(anchor="w")

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=14, pady=10)
        self.badge = ctk.CTkLabel(right, text="TEST MODE", font=("Hind Siliguri", 12, "bold"),
                                  fg_color=T.YELLOW, text_color="black",
                                  corner_radius=8, padx=10, pady=4)
        self.badge.pack(anchor="e")
        self.clock = ctk.CTkLabel(right, text="", font=("Arial", 12), text_color=T.MUTED)
        self.clock.pack(anchor="e", pady=(4, 0))
        self._tick()

    def set_live(self, live=True):
        if live:
            self.badge.configure(text="LIVE", fg_color=T.GREEN)
        else:
            self.badge.configure(text="TEST MODE", fg_color=T.YELLOW)

    def _tick(self):
        try:
            self.clock.configure(text=time.strftime("%Y-%m-%d  %H:%M:%S"))
        except Exception:
            pass
        self.after(1000, self._tick)
