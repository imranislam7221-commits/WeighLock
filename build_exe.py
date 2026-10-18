import PyInstaller.__main__ as m
import os
here = os.path.dirname(os.path.abspath(__file__))
m.run([os.path.join(here, "main.py"), "--name", "WeighLock", "--onefile",
       "--windowed", "--noconfirm", "--clean",
       "--add-data", f"{os.path.join(here, 'ui')}{os.pathsep}ui",
       "--hidden-import", "customtkinter",
       "--collect-all", "customtkinter"])
print("BUILD DONE: dist/WeighLock.exe")
