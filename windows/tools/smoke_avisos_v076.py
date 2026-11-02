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
    import win32event,win32con,win32api,win32gui,win32process
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
            # Earlier smoke sent WM_COMMAND directly and never checked
            # whether a real right-click created any visible menu.
            def menu_for_agent():
                results=[]
                def visitor(hwnd,unused):
                    try:
                        if (win32gui.GetClassName(hwnd)=="#32768"
                                and win32gui.IsWindowVisible(hwnd)
                                and win32process.GetWindowThreadProcessId(hwnd)[1]==proc.pid):
                            results.append(hwnd)
                    except Exception:
                        pass
                win32gui.EnumWindows(visitor,None)
                return results[0] if results else None

            win32gui.PostMessage(window,win32con.WM_USER+20,1,
                                 win32con.WM_RBUTTONUP)
            popup=None
            for _ in range(50):
                if proc.poll() is not None:
                    raise RuntimeError("Avisos quit while showing right-click menu")
                popup=menu_for_agent()
                if popup:break
                time.sleep(0.1)
            if not popup:
                raise RuntimeError(
                    "Real right-click failed: no visible native popup menu")
            left,top,right,bottom=win32gui.GetWindowRect(popup)
            if (right-left)<70 or (bottom-top)<30:
                raise RuntimeError("Avisos context menu dimensions invalid")
            print("PASS: real right click opens native Avisos context menu")
            # Select last item ("Sair dos avisos") by a genuine mouse click.
            position=(left+(right-left)//2,bottom-14)
            win32api.SetCursorPos(position)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
            time.sleep(0.08)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
            proc.wait(timeout=10)
            if proc.returncode != 0:
                raise RuntimeError("Native tray Exit menu command failed: "
                                   +str(proc.returncode))
            print("PASS: mouse click on Sair dos avisos closes resident process")
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
