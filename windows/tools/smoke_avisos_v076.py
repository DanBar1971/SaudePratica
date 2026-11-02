"""Smoke real packaged Avisos tray: no splash, graceful exit, original ICO.

Runs in CI with disposable LOCALAPPDATA and no patient information.
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

def main():
    if sys.platform!="win32":
        raise SystemExit("Windows-only smoke test")
    import win32event,win32con,win32api,win32gui
    from windows.reminder_agent_v071 import STOP_EVENT_NAME
    target=ROOT/"dist"/"SaudePraticaAvisos"/"SaudePraticaAvisos.exe"
    assert target.is_file(), "Background exe missing"
    desktop=ROOT/"dist"/"SaudePraticaDesktop"/"SaudePraticaDesktop.exe"
    assert desktop.is_file()
    with tempfile.TemporaryDirectory(prefix="saude-avisos-smoke-") as tmp:
        env=os.environ.copy()
        env["LOCALAPPDATA"]=tmp
        proc=subprocess.Popen([str(target)],env=env,cwd=target.parent)
        handle=None
        try:
            for _ in range(40):
                if proc.poll() is not None:
                    raise RuntimeError("Avisos agent exited unexpectedly: "+str(proc.returncode))
                try:
                    handle=win32event.OpenEvent(win32event.EVENT_MODIFY_STATE,False,STOP_EVENT_NAME)
                    break
                except Exception:
                    time.sleep(0.25)
            if handle is None:
                raise RuntimeError("Avisos agent never created its stop event")
            time.sleep(1)
            if proc.poll() is not None:
                raise RuntimeError("Avisos agent exited during startup")
            # The exact action selected in the tray's right-click Exit menu.
            window=win32gui.FindWindow("SaudePraticaReminderTrayWindow",None)
            if not window:
                raise RuntimeError("Native Avisos tray window never appeared")
            win32gui.PostMessage(window,win32con.WM_COMMAND,1001,0)
            proc.wait(timeout=10)
            if proc.returncode != 0:
                raise RuntimeError("Avisos Exit command failed: "+str(proc.returncode))
            print("PASS: right-click menu Exit command closes Avisos process")
            # Start again and ensure Inno Setup's safe-stop signal still works.
            proc=subprocess.Popen([str(target)],env=env,cwd=target.parent)
            for _ in range(40):
                if proc.poll() is not None:
                    raise RuntimeError("Avisos restart unexpectedly exited")
                if win32gui.FindWindow("SaudePraticaReminderTrayWindow",None):
                    break
                time.sleep(0.25)
            else:
                raise RuntimeError("Avisos did not restart after manual Exit")
            win32event.SetEvent(handle)
            proc.wait(timeout=15)
            if proc.returncode != 0:
                raise RuntimeError("Avisos installer shutdown failed: "+str(proc.returncode))
            print("PASS: standalone no-splash Avisos and safe installer shutdown")
        finally:
            if handle is not None:
                win32api.CloseHandle(handle)
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=10)

if __name__=="__main__":
    main()
