"""SaúdePrática Windows per-user background reminder agent.

The resident helper runs with the current user's DPAPI key, from the same
installed EXE as the desktop application. It does not contact the network,
upload medical data, register machine-wide services or require admin rights.
"""
from __future__ import annotations
from datetime import datetime,timedelta
import json,os,sys,time,tempfile,subprocess
from pathlib import Path
from .appointment_reminders_v071 import due_events,reminder_message

RUN_KEY=r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE="SaudePraticaAgendaReminders"
MUTEX_NAME=r"Local\SaudePraticaAgendaReminderAgent"

def _agent_command():
    if getattr(sys,"frozen",False):
        return [sys.executable,"--reminder-agent"]
    return [sys.executable,str(Path(__file__).with_name("desktop_v04.py")),"--reminder-agent"]

def register_user_startup(enabled=True):
    """HKCU logon start, never HKLM or UAC (current user only)."""
    if sys.platform!="win32":return False
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER,RUN_KEY) as key:
        if enabled:
            from subprocess import list2cmdline
            winreg.SetValueEx(key,RUN_VALUE,0,winreg.REG_SZ,
                             list2cmdline(_agent_command()))
        else:
            try:winreg.DeleteValue(key,RUN_VALUE)
            except FileNotFoundError:pass
    return True

def spawn_agent():
    """Run independently of the main app, once per user session."""
    if sys.platform!="win32":return
    flags=(getattr(subprocess,"DETACHED_PROCESS",0) |
           getattr(subprocess,"CREATE_NEW_PROCESS_GROUP",0) |
           getattr(subprocess,"CREATE_NO_WINDOW",0))
    subprocess.Popen(_agent_command(),creationflags=flags,
                     stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL,close_fds=True)

def enable_background_reminders():
    """Enable user-logon startup and start agent after normal app launch."""
    if sys.platform!="win32":return
    register_user_startup(True)
    spawn_agent()

def _sent_path():
    local=Path(os.getenv("LOCALAPPDATA") or str(Path.home()))
    path=local/"SaudePraticaDesktop"
    path.mkdir(parents=True,exist_ok=True)
    return path/"appointment_notification_keys.json"

def _read_sent(path):
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data,dict):return data
    except (FileNotFoundError,OSError,ValueError):
        pass
    return {}

def _save_sent(path,entries):
    cutoff=(datetime.now()-timedelta(days=90)).isoformat()
    entries={key:ts for key,ts in entries.items()
             if isinstance(key,str) and isinstance(ts,str) and ts>=cutoff}
    fd,name=tempfile.mkstemp(prefix=".reminders_",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            json.dump(entries,stream,ensure_ascii=False)
            stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

class TrayNotifier:
    """Native Windows notification balloon, tray icon held while agent runs."""
    def __init__(self):
        import win32gui,win32api,win32con
        self.gui=win32gui
        self.con=win32con
        self.ident=1
        module=win32api.GetModuleHandle(None)
        wc=win32gui.WNDCLASS()
        wc.hInstance=module
        wc.lpszClassName="SaudePraticaReminderTrayWindow"
        wc.lpfnWndProc={
            win32con.WM_DESTROY:lambda hwnd,msg,wparam,lparam:0
        }
        try:win32gui.RegisterClass(wc)
        except Exception:pass
        self.window=win32gui.CreateWindow(wc.lpszClassName,
                       "SaúdePrática - Agenda",0,0,0,0,0,0,0,module,None)
        self.icon=win32gui.LoadIcon(0,win32con.IDI_APPLICATION)
        self.callback=win32con.WM_USER+20
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD,(
            self.window,self.ident,
            win32gui.NIF_MESSAGE|win32gui.NIF_ICON|win32gui.NIF_TIP,
            self.callback,self.icon,"SaúdePrática · Avisos"))
    def notify(self,planned,minutes):
        import win32gui
        title="SaúdePrática · Lembrete da Agenda"
        # Do not display patient name, diagnosis, location or profile on lock screen.
        body=reminder_message(planned,minutes)
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY,(
            self.window,self.ident,
            win32gui.NIF_MESSAGE|win32gui.NIF_ICON|win32gui.NIF_TIP|win32gui.NIF_INFO,
            self.callback,self.icon,"SaúdePrática · Avisos",
            body,15000,title,win32gui.NIIF_INFO))
    def pump(self):
        self.gui.PumpWaitingMessages()
    def close(self):
        try:self.gui.Shell_NotifyIcon(self.gui.NIM_DELETE,(self.window,self.ident))
        except Exception:pass
        try:self.gui.DestroyWindow(self.window)
        except Exception:pass

def run_reminder_agent():
    """Non-GUI daemon-like session agent; session ends on Windows logout.

    Repeat at logon via HKCU Run. Poll new DPAPI data so saves in the desktop
    immediately affect future reminders without restarting the process.
    """
    if sys.platform!="win32":return
    import win32api,win32event,winerror
    mutex=win32event.CreateMutex(None,False,MUTEX_NAME)
    if win32api.GetLastError()==winerror.ERROR_ALREADY_EXISTS:
        return
    notifier=None
    try:
        notifier=TrayNotifier()
        path=_sent_path()
        sent=_read_sent(path)
        while True:
            try:
                from .secure_store import SecureStore
                store=SecureStore()
                for token,planned,offset in due_events(store.profiles()):
                    if token in sent:continue
                    notifier.notify(planned,offset)
                    sent[token]=datetime.now().isoformat()
                    _save_sent(path,sent)
            except Exception:
                # Patient data must never appear in public diagnostic logs.
                pass
            notifier.pump()
            time.sleep(20)
    finally:
        if notifier:notifier.close()
        win32api.CloseHandle(mutex)
