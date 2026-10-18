import customtkinter as ctk
from ui import theme as T

DEFAULT_MATS = ["পাথর", "ধান", "বালু", "সিমেন্ট", "রড", "কয়লা", "অন্যান্য / Others"]


class EntryForm(ctk.CTkFrame):
    # ধাপ: ১.গাড়ি নম্বর ২.LOCK+Gross ৩.info ৪.Tare+slip
    # mandatory: truck, gross, tare, net | optional: baki sob
    def __init__(self, master, material_list=None):
        super().__init__(master, fg_color=T.CARD, corner_radius=12)
        self.pack(fill="both", expand=True, padx=6, pady=6)
        self._mats = material_list or DEFAULT_MATS[:]

        ctk.CTkLabel(self, text="ধাপ ১: গাড়ি নম্বর লিখুন *",
                     font=("Hind Siliguri", 15, "bold"), text_color=T.YELLOW).pack(
                         anchor="w", padx=14, pady=(12, 2))
        self.truck = ctk.CTkEntry(self, placeholder_text="ট্রাক নম্বর * (যেমন: ঢাকা-মেট্রো-ট ১২৩৪)",
                                  font=("Hind Siliguri", 14, "bold"), height=44)
        self.truck.pack(fill="x", padx=14, pady=5)
        self.info = ctk.CTkLabel(self, text="", font=("Hind Siliguri", 12),
                                 text_color=T.GREEN)
        self.info.pack(anchor="w", padx=14, pady=(0, 2))

        ctk.CTkLabel(self, text="ধাপ ২: তথ্য দিন (ড্রাইভার/মালিক optional)",
                     font=("Hind Siliguri", 13, "bold"), text_color=T.TEXT).pack(
                         anchor="w", padx=14, pady=(6, 2))

        self.driver = self._field("ড্রাইভারের নাম (optional)")
        self.owner = self._field("গাড়ির মালিকের নাম (optional)")
        self.mobile = self._field("মোবাইল নম্বর (optional)")
        self.address = self._field("ঠিকানা (optional)")
        self.supplier = self._field("পার্টি / সাপ্লায়ার (optional)")

        ctk.CTkLabel(self, text="মাল / Item * (dropdown থেকে বাছুন)",
                     font=("Hind Siliguri", 13), text_color=T.TEXT).pack(
                         anchor="w", padx=14, pady=(6, 0))
        self.material = ctk.CTkComboBox(self, values=self._mats,
                                        font=("Hind Siliguri", 13), height=40)
        self.material.pack(fill="x", padx=14, pady=5)
        try:
            self.material.set(self._mats[0])
        except Exception:
            pass

        self.challan = self._field("চালান নম্বর (খালি রাখলে auto হবে / পুরান লিখলে auto fill)")
        self.product = self._field("প্রোডাক্ট নাম (optional)")
        self.paid = self._field("জমা / Paid Tk (optional, khali = baki)")

        self.manual_var = ctk.BooleanVar(value=False)
        self.chk_manual = ctk.CTkCheckBox(self, text="খালি ওজন জানা আছে (হাতে লিখব)",
                                          font=("Hind Siliguri", 12),
                                          variable=self.manual_var,
                                          command=self._toggle_manual)
        self.chk_manual.pack(anchor="w", padx=14, pady=(6, 2))
        self.tare_manual = ctk.CTkEntry(self, placeholder_text="খালি গাড়ির ওজন KG লিখুন",
                                        font=("Hind Siliguri", 13), height=40)

        self.step = ctk.CTkLabel(self, text="➡ আগে গাড়ি নম্বর + LOCK + ১ম সেভ করুন",
                                 font=("Hind Siliguri", 12), text_color=T.MUTED,
                                 justify="left", wraplength=300)
        self.step.pack(anchor="w", padx=14, pady=8)

    def _field(self, placeholder):
        e = ctk.CTkEntry(self, placeholder_text=placeholder,
                         font=("Hind Siliguri", 13), height=40)
        e.pack(fill="x", padx=14, pady=4)
        return e

    def _toggle_manual(self):
        try:
            if self.manual_var.get():
                self.tare_manual.pack(fill="x", padx=14, pady=5)
            else:
                self.tare_manual.pack_forget()
        except Exception:
            pass

    def set_material_list(self, mats):
        if mats:
            self._mats = mats
            try:
                cur = self.material.get()
                self.material.configure(values=mats)
                if cur not in mats:
                    self.material.set(mats[0])
            except Exception:
                pass

    def apply_settings(self, show_challan=True, show_product=True, allow_manual=True,
                       show_owner=True, show_address=True, material_list=None):
        if material_list:
            self.set_material_list(material_list)
        for w, show in [(self.challan, show_challan), (self.product, show_product),
                        (self.owner, show_owner), (self.address, show_address)]:
            try:
                if show:
                    w.pack(fill="x", padx=14, pady=4)
                else:
                    w.pack_forget()
            except Exception:
                pass
        try:
            if allow_manual:
                self.chk_manual.pack(anchor="w", padx=14, pady=(6, 2))
            else:
                self.chk_manual.pack_forget()
                self.tare_manual.pack_forget()
        except Exception:
            pass

    def set_step(self, txt):
        try:
            self.step.configure(text=txt)
        except Exception:
            pass

    def get_data(self):
        mt = ""
        try:
            mt = self.tare_manual.get().strip() if self.manual_var.get() else ""
        except Exception:
            pass
        try:
            mat = self.material.get().strip()
        except Exception:
            mat = ""
        try:
            paid = float(self.paid.get().strip() or 0)
        except Exception:
            paid = 0
        return {
            "truck": self.truck.get().strip(),
            "driver": self.driver.get().strip(),
            "owner": self.owner.get().strip(),
            "mobile": self.mobile.get().strip(),
            "address": self.address.get().strip(),
            "supplier": self.supplier.get().strip(),
            "material": mat,
            "challan": self.challan.get().strip(),
            "product": self.product.get().strip(),
            "paid": paid,
            "manual_tare": mt,
            "use_manual": bool(self.manual_var.get() and mt),
        }

    def set_data(self, driver="", supplier="", mobile="", material="", challan="",
                 product="", owner="", address="", info=""):
        for widget, val in [(self.driver, driver), (self.supplier, supplier),
                            (self.mobile, mobile), (self.challan, challan),
                            (self.product, product), (self.owner, owner),
                            (self.address, address)]:
            if val:
                try:
                    widget.delete(0, "end")
                    widget.insert(0, val)
                except Exception:
                    pass
        if material:
            try:
                if material not in self._mats:
                    self._mats = self._mats + [material]
                    self.material.configure(values=self._mats)
                self.material.set(material)
            except Exception:
                pass
        self.info.configure(text=info or "")
