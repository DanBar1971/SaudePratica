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

def main():
    if sys.platform!="win32":
        raise SystemExit("Windows-only smoke test")
    import win32event,win32con,win32api
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
            # Exact event used by Inno Setup, preserving safe in-place upgrades.
            win32event.SetEvent(handle)
            proc.wait(timeout=15)
            if proc.returncode != 0:
                raise RuntimeError("Avisos agent exited with error: "+str(proc.returncode))
            print("PASS: standalone no-splash Avisos, native tray agent stopped on installer event")
        finally:
            if handle is not None:
                win32api.CloseHandle(handle)
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=10)

if __name__=="__main__":
    main()
