"""Regression for the actual right-click path, not just WM_COMMAND spoofing.

No Windows required for this unit test; the real popup is exercised by the
Windows executable smoke test in CI.
"""
import unittest
from types import SimpleNamespace
from windows.reminder_agent_v071 import TrayNotifier

class StubGUI:
    def __init__(self,selected):
        self.selected=selected
        self.items=[]
        self.destroyed=False
        self.foreground=False
        self.posted=[]
        self.tracked=False
    def CreatePopupMenu(self):return 42
    def AppendMenu(self,handle,flag,action,label):
        assert handle==42
        assert isinstance(label,str), "separator None breaks some pywin32 builds"
        self.items.append((flag,action,label))
    def SetForegroundWindow(self,hwnd):
        assert hwnd==100
        self.foreground=True
    def GetCursorPos(self):return (300,220)
    def TrackPopupMenu(self,menu,flags,x,y,reserved,hwnd,rect):
        assert menu==42 and hwnd==100
        assert flags & 0x0100, "TPM_RETURNCMD must be used to avoid lost WM_COMMAND"
        self.tracked=True
        return self.selected
    def PostMessage(self,*args):self.posted.append(args)
    def DestroyMenu(self,menu):
        assert menu==42
        self.destroyed=True
    def DefWindowProc(self,*args):return 0

class TrayPopupTests(unittest.TestCase):
    def fake(self,selected):
        menu=TrayNotifier.__new__(TrayNotifier)
        menu.EXIT_MENU=1001
        menu.OPEN_MENU=1002
        menu.window=100
        menu.ident=1
        menu.exit_requested=False
        menu.callback=0x414
        menu.con=SimpleNamespace(
            MF_STRING=0,MF_SEPARATOR=0x800,TPM_LEFTALIGN=0,
            TPM_RIGHTBUTTON=2,TPM_RETURNCMD=0x100,
            WM_NULL=0,WM_COMMAND=0x111,WM_RBUTTONUP=0x205,
            WM_CONTEXTMENU=0x7b,WM_LBUTTONDBLCLK=0x203,
            WM_DESTROY=2)
        menu.gui=StubGUI(selected)
        menu._open_desktop=lambda:None
        return menu
    def test_right_click_shows_actual_menu_and_exits(self):
        tray=self.fake(1001)
        self.assertEqual(tray._wnd_proc(100,tray.callback,1,0x205),0)
        self.assertTrue(tray.gui.tracked)
        self.assertTrue(tray.gui.foreground)
        self.assertTrue(tray.gui.destroyed)
        self.assertTrue(tray.exit_requested)
        self.assertEqual([x[2] for x in tray.gui.items],
                         ["Abrir SaúdePrática","","Sair dos avisos"])
    def test_menu_is_cancelable_and_open_action_works(self):
        tray=self.fake(0)
        tray._wnd_proc(100,tray.callback,1,0x205)
        self.assertFalse(tray.exit_requested)
        tray=self.fake(1002)
        called=[]
        tray._open_desktop=lambda:called.append(True)
        tray._wnd_proc(100,tray.callback,1,0x7b)
        self.assertTrue(called)
        self.assertFalse(tray.exit_requested)
    def test_contextmenu_low_word_for_version4_shell(self):
        tray=self.fake(1001)
        tray._wnd_proc(100,tray.callback,1,0x10000+0x7b)
        self.assertTrue(tray.exit_requested)
if __name__=="__main__":
    unittest.main()
