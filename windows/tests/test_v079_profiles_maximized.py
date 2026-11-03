"""Regression guards for the actual Windows 0.7.9 profile actions and startup.

Only source UI contracts and synthetic records; no patient profiles in CI.
"""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"desktop_v04.py").read_text(encoding="utf-8")

class V079ProfileStartup(unittest.TestCase):
    def test_explicit_profile_open_button_is_not_tiny_chevron(self):
        pane=SOURCE.split("    def _profiles(self):",1)[1].split("    def _delete_profile",1)[0]
        self.assertIn('left,listing,right=self._two_pane(self.t("registered_profiles"),365)',pane)
        self.assertIn('self._button(row,"ABRIR  ❯"',pane)
        self.assertIn("width=92,height=34",pane)
        self.assertNotIn('self._button(row,"›"',pane)

    def test_async_worker_really_controls_loading_indicator(self):
        start=SOURCE.split("    def _edit_profile(self,pid):",1)[1].split("    def _show_cc_photo",1)[0]
        self.assertIn("self._busy_profile=pid if pid not in self._profile_view_cache else None",start)
        self.assertIn('CTkProgressBar(progress,mode="indeterminate"',SOURCE)
        self.assertIn("bar.start()",SOURCE)
        self.assertIn("self._busy_profile=None",start)
        self.assertIn("bar.stop()",start)
        self.assertIn("self._profile_view_cache[pid]=(fields,photos)",start)
        self.assertIn('self.configure(cursor="watch")',SOURCE)
        self.assertIn("self.after(150,self._finish_busy_cursor)",SOURCE)

    def test_only_one_startup_screen_until_maximized_main_window(self):
        self.assertIn('self.withdraw()',SOURCE)
        boot=SOURCE.split('def main():',1)[1].split('if smoke_report:',1)[0]
        self.assertIn("_close_boot_splash()",boot)
        self.assertIn("app.deiconify()",boot)
        self.assertIn('app.state("zoomed")',boot)
        self.assertLess(boot.index("_close_boot_splash()"),boot.index("app.deiconify()"))
        self.assertIn('VERSION = "0.8.3"',SOURCE)

if __name__=="__main__":
    unittest.main()
