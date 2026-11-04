"""Real Tkinter check of both PIN wallpaper screens with synthetic empty store.

Runs on Windows CI in a disposable LOCALAPPDATA profile. No private or
real clinical data is loaded, submitted or exported.
"""
from pathlib import Path
import os
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))


def walk(widget):
    for child in widget.winfo_children():
        yield child
        yield from walk(child)


def main():
    import customtkinter as ctk
    from windows.desktop_v04 import Desktop
    from windows.wallpaper_shell_v06 import WallpaperShell

    with tempfile.TemporaryDirectory(prefix="sp-login-0817-") as tmp:
        os.environ["LOCALAPPDATA"]=str(Path(tmp))
        os.environ["SAUDEPRATICA_SMOKE_REPORT"]=str(Path(tmp)/"synthetic.marker")
        app=Desktop()
        try:
            app.deiconify()
            app.geometry("1280x770")
            app._login_unlocked=False
            app._display_login()
            app.update_idletasks()
            app.update()
            shells=[x for x in app.winfo_children() if isinstance(x,WallpaperShell)]
            assert len(shells)==1,"Primeira entrada sem fundo oficial."
            assert shells[0]._wallpaper_photo is not None,"Fundo não foi desenhado."
            assert isinstance(app._login_first_pin,ctk.CTkEntry)
            assert isinstance(app._login_confirm_pin,ctk.CTkEntry)
            app._login_first_pin.insert(0,"4821")
            app._login_confirm_pin.insert(0,"4821")
            app._configure_login_pin()
            app.update()
            assert app._login_unlocked,"PIN inicial não desbloqueou."
            app._login_unlocked=False
            app._display_login()
            app.update_idletasks()
            app.update()
            shells=[x for x in app.winfo_children() if isinstance(x,WallpaperShell)]
            assert len(shells)==1,"Login habitual sem fundo oficial."
            assert shells[0]._wallpaper_photo is not None
            fields=[x for x in walk(shells[0]) if isinstance(x,ctk.CTkEntry)]
            assert len(fields)==1,"O login deve mostrar apenas um campo PIN."
            fields[0].insert(0,"4821")
            app._check_login_pin(fields[0])
            app.update()
            assert app._login_unlocked,"O PIN correto não desbloqueou."
            print("PASS: original wallpaper, logo and both 4-digit PIN screens.")
        finally:
            app.destroy()


if __name__=="__main__":
    main()
