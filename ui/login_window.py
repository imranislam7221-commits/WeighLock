import customtkinter as ctk
from database import check_operator
from tkinter import messagebox


class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master, on_login):
        super().__init__(master)
        self.title("Operator Login")
        self.geometry("340x260")
        self.on_login = on_login
        self.grab_set()
        ctk.CTkLabel(self, text="অপারেটর লগইন", font=("Hind Siliguri", 16, "bold")).pack(pady=12)
        self.name = ctk.CTkEntry(self, placeholder_text="নাম (admin)", height=40)
        self.name.pack(fill="x", padx=30, pady=5)
        self.pin = ctk.CTkEntry(self, placeholder_text="PIN (1234)", show="*", height=40)
        self.pin.pack(fill="x", padx=30, pady=5)
        self.pin.bind("<Return>", lambda e: self.go())
        ctk.CTkButton(self, text="Login", command=self.go).pack(pady=12)
        try:
            self.name.insert(0, "admin")
            self.pin.insert(0, "1234")
        except Exception:
            pass

    def go(self):
        n = self.name.get().strip() or "admin"
        p = self.pin.get().strip()
        if check_operator(n, p):
            self.on_login(n)
            self.destroy()
        else:
            messagebox.showerror("ভুল", "নাম/PIN ভুল।")
