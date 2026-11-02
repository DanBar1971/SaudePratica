"""SaúdePrática Windows per-user background reminder agent.

The resident helper runs with the current user's DPAPI key, from a separate
splash-free EXE alongside the installed desktop application. It does not contact the network,
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
STOP_EVENT_NAME=r"Local\SaudePraticaAgendaReminderAgentStop"

def _agent_command():
    """Prefer the separately packaged, no-splash agent over the UI executable."""
    if getattr(sys,"frozen",False):
        here=Path(sys.executable).resolve()
        if here.stem.lower()=="saudepraticaavisos":
            return [str(here)]
        helper=here.parent/"Avisos"/"SaudePraticaAvisos.exe"
        if helper.is_file():
            return [str(helper)]
        # Legacy deployments before the standalone Avisos binary.
        return [str(here),"--reminder-agent"]
    return [sys.executable,str(Path(__file__).with_name("desktop_v04.py")),"--reminder-agent"]

def _icon_path():
    """The original app ICO, beside the main EXE, not a generated placeholder."""
    if getattr(sys,"frozen",False):
        where=Path(sys.executable).resolve().parent
        for path in (where/"SaudePratica.ico",where.parent/"SaudePratica.ico"):
            if path.is_file():
                return path
    return None


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
    """Native Win32 tray with official ICO and a working close command."""
    EXIT_MENU=1001
    OPEN_MENU=1002

    def __init__(self):
        import win32gui,win32api,win32con
        self.gui=win32gui
        self.con=win32con
        self.ident=1
        self.exit_requested=False
        module=win32api.GetModuleHandle(None)
        self.callback=win32con.WM_USER+20
        wc=win32gui.WNDCLASS()
        wc.hInstance=module
        wc.lpszClassName="SaudePraticaReminderTrayWindow"
        wc.lpfnWndProc=self._wnd_proc
        try:
            win32gui.RegisterClass(wc)
        except Exception:
            pass
        self.window=win32gui.CreateWindow(
            wc.lpszClassName,"SaúdePrática · Avisos",0,
            0,0,0,0,0,0,module,None)
        self.icon=None
        self.owned_icon=False
        official=_icon_path()
        if official is not None:
            try:
                self.icon=win32gui.LoadImage(
                    0,str(official),win32con.IMAGE_ICON,0,0,
                    win32con.LR_LOADFROMFILE|win32con.LR_DEFAULTSIZE)
                self.owned_icon=True
            except Exception:
                pass
        if self.icon is None:
            self.icon=win32gui.LoadIcon(0,win32con.IDI_APPLICATION)
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD,(
            self.window,self.ident,
            win32gui.NIF_MESSAGE|win32gui.NIF_ICON|win32gui.NIF_TIP,
            self.callback,self.icon,"SaúdePrática · Avisos"))

    def _wnd_proc(self,hwnd,msg,wparam,lparam):
        if msg==self.callback:
            if lparam in (self.con.WM_RBUTTONUP,self.con.WM_CONTEXTMENU):
                self._show_menu()
            elif lparam==self.con.WM_LBUTTONDBLCLK:
                self._open_desktop()
            return 0
        if msg==self.con.WM_COMMAND:
            action=wparam & 0xffff
            if action==self.EXIT_MENU:
                self.exit_requested=True
                return 0
            if action==self.OPEN_MENU:
                self._open_desktop()
                return 0
        if msg==self.con.WM_DESTROY:
            return 0
        return self.gui.DefWindowProc(hwnd,msg,wparam,lparam)

    def _show_menu(self):
        menu=self.gui.CreatePopupMenu()
        try:
            self.gui.AppendMenu(menu,self.con.MF_STRING,
                                self.OPEN_MENU,"Abrir SaúdePrática")
            self.gui.AppendMenu(menu,self.con.MF_SEPARATOR,0,None)
            self.gui.AppendMenu(menu,self.con.MF_STRING,
                                self.EXIT_MENU,"Sair dos avisos")
            try:
                self.gui.SetForegroundWindow(self.window)
            except Exception:
                pass
            x,y=self.gui.GetCursorPos()
            self.gui.TrackPopupMenu(
                menu,self.con.TPM_LEFTALIGN|self.con.TPM_RIGHTBUTTON,
                x,y,0,self.window,None)
            self.gui.PostMessage(self.window,self.con.WM_NULL,0,0)
        finally:
            self.gui.DestroyMenu(menu)

    def _open_desktop(self):
        if not getattr(sys,"frozen",False):
            return
        here=Path(sys.executable).resolve()
        desktop=here.parent/"SaudePraticaDesktop.exe"
        if here.stem.lower()=="saudepraticaavisos":
            desktop=here.parent.parent/"SaudePraticaDesktop.exe"
        if desktop.is_file():
            subprocess.Popen([str(desktop)],close_fds=True)

    def notify(self,planned,minutes):
        title="SaúdePrática · Lembrete da Agenda"
        # Do not display patient name, diagnosis, location or profile on lock screen.
        body=reminder_message(planned,minutes)
        self.gui.Shell_NotifyIcon(self.gui.NIM_MODIFY,(
            self.window,self.ident,
            self.gui.NIF_MESSAGE|self.gui.NIF_ICON|self.gui.NIF_TIP|self.gui.NIF_INFO,
            self.callback,self.icon,"SaúdePrática · Avisos",
            body,15000,title,self.gui.NIIF_INFO))

    def pump(self):
        self.gui.PumpWaitingMessages()

    def close(self):
        try:
            self.gui.Shell_NotifyIcon(self.gui.NIM_DELETE,(self.window,self.ident))
        except Exception:
            pass
        try:
            self.gui.DestroyWindow(self.window)
        except Exception:
            pass
        if self.owned_icon:
            try:self.gui.DestroyIcon(self.icon)
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
    stop=win32event.CreateEvent(None,True,False,STOP_EVENT_NAME)
    # An updater uses this same-session named event to stop this helper
    # safely before replacing any of its installed EXE/DLL files.
    notifier=None
    try:
        if win32event.WaitForSingleObject(stop,0)==win32event.WAIT_OBJECT_0:
            return
        notifier=TrayNotifier()
        path=_sent_path()
        sent=_read_sent(path)
        next_scan=0.0
        while True:
            notifier.pump()
            if notifier.exit_requested:
                break
            if win32event.WaitForSingleObject(stop,0)==win32event.WAIT_OBJECT_0:
                break
            if time.monotonic()>=next_scan:
                next_scan=time.monotonic()+20
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
            # Process right clicks every second, not just after a 20s scan.
            if win32event.WaitForSingleObject(stop,1_000)==win32event.WAIT_OBJECT_0:
                break
    finally:
        if notifier:notifier.close()
        # Reset the manual-reset updater event for the next logon/startup.
        # The mutex is still owned here, so another agent cannot race it.
        win32event.ResetEvent(stop)
        win32api.CloseHandle(stop)
        win32api.CloseHandle(mutex)
