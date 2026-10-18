import customtkinter as ctk


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, settings, on_save):
        super().__init__(master)
        self.title("সেটিংস")
        self.geometry("430x700")
        self.on_save = on_save
        self.vars = {}
        items = [
            ("show_challan", "চালান নম্বর দেখাও", True),
            ("show_product", "প্রোডাক্ট নাম দেখাও", True),
            ("show_owner", "মালিকের নাম দেখাও", True),
            ("show_address", "ঠিকানা দেখাও", True),
            ("allow_manual", "হাতে tare / single weight allow", True),
            ("require_truck", "ট্রাক নম্বর বাধ্যতামূলক (ON রাখুন)", True),
            ("auto_lock", "অটো LOCK - default OFF manual", False),
            ("use_simulator", "টেস্ট simulator ON (scale না থাকলে)", True),
            ("strict_license", "কড়া লাইসেন্স (key ছাড়া চলবে না)", False),
        ]
        ctk.CTkLabel(self, text="সেটিংস", font=("Hind Siliguri", 16, "bold")).pack(pady=8)
        box = ctk.CTkScrollableFrame(self, height=560)
        box.pack(fill="both", expand=True, padx=10, pady=4)
        for key, label, default in items:
            v = ctk.BooleanVar(value=bool(settings.get(key, default)))
            self.vars[key] = v
            ctk.CTkCheckBox(box, text=label, font=("Hind Siliguri", 13),
                            variable=v).pack(anchor="w", padx=16, pady=4)
        ctk.CTkLabel(box, text="মালের dropdown (কমা দিয়ে):",
                     font=("Hind Siliguri", 13)).pack(anchor="w", padx=16, pady=(8, 2))
        self.mat_box = ctk.CTkTextbox(box, height=60, font=("Hind Siliguri", 12))
        self.mat_box.pack(fill="x", padx=16, pady=4)
        try:
            self.mat_box.insert("1.0", ", ".join(settings.get("material_list", [])))
        except Exception:
            pass
        ctk.CTkLabel(box, text="Scale Port / Baud (AUTO = sob USB/RS scan):",
                     font=("Hind Siliguri", 13)).pack(anchor="w", padx=16, pady=(8, 2))
        prow = ctk.CTkFrame(box, fg_color="transparent")
        prow.pack(fill="x", padx=16, pady=2)
        self.ent_port = ctk.CTkEntry(prow, width=140, font=("Hind Siliguri", 12))
        self.ent_port.pack(side="left", padx=(0, 6))
        try:
            self.ent_port.insert(0, str(settings.get("scale_port", "AUTO")))
        except Exception:
            pass
        self.ent_baud = ctk.CTkEntry(prow, width=140, font=("Hind Siliguri", 12))
        self.ent_baud.pack(side="left")
        try:
            self.ent_baud.insert(0, str(settings.get("scale_baud", "AUTO")))
        except Exception:
            pass
        ctk.CTkLabel(box, text="ex: AUTO বা COM3 / 9600. বদলালে reader restart হবে।",
                     font=("Hind Siliguri", 11)).pack(anchor="w", padx=16)
        ctk.CTkButton(box, text="সেভ করুন", font=("Hind Siliguri", 13, "bold"),
                      command=self._save).pack(pady=12)

    def _save(self):
        out = {k: bool(v.get()) for k, v in self.vars.items()}
        try:
            txt = self.mat_box.get("1.0", "end").strip()
            mats = [m.strip() for m in txt.split(",") if m.strip()]
            if "অন্যান্য / Others" not in mats and "Others" not in mats:
                mats.append("অন্যান্য / Others")
            out["material_list"] = mats if mats else None
        except Exception:
            out["material_list"] = None
        try:
            out["scale_port"] = self.ent_port.get().strip() or "AUTO"
            out["scale_baud"] = self.ent_baud.get().strip() or "AUTO"
        except Exception:
            pass
        self.on_save(out)
        self.destroy()
