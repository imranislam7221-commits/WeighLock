from license_manager import check_license
from app import MainApp
from tkinter import messagebox

if __name__ == "__main__":
    try:
        if check_license():
            app = MainApp()
            app.mainloop()
        else:
            # activation window app er ভেতরে আসবে, তবুও block না করে খোলো
            app = MainApp()
            app.mainloop()
    except Exception as e:
        try:
            messagebox.showerror("Error", str(e))
        except Exception:
            print(e)
