"""PIN screen branding, data isolation and backup PIN input regression tests."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class BrandedEntryTests(unittest.TestCase):
    def test_both_entry_screens_use_original_wallpaper_and_branding(self):
        source=(ROOT/"login_ui_v0816.py").read_text("utf-8")
        desktop=(ROOT/"desktop_v04.py").read_text("utf-8")
        self.assertIn('VERSION = "0.8.18"',desktop)
        self.assertIn("from windows.wallpaper_shell_v06 import WallpaperShell",source)
        self.assertGreaterEqual(source.count("WallpaperShell(self,light="),2)
        self.assertIn('ctk.CTkLabel(brand,image=self.logo,text=""',source)
        self.assertIn('"SaúdePrática",29,True',source)
        self.assertIn('"Primeira utilização no Windows",21,True',source)
        self.assertIn('"Introduz o PIN para entrar",21,True',source)
        self.assertNotIn('p["id"][:8]',source)
        self.assertIn("self._login_unlocked=bool(",desktop)
        self.assertIn('if not self._login_unlocked:',desktop)

    def test_new_portable_backups_use_pin_not_password(self):
        source=(ROOT/"backup_ui_v072.py").read_text("utf-8")
        self.assertIn("PIN para criar ou restaurar backup (4 números)",source)
        self.assertIn("Repetir PIN (apenas ao criar o backup)",source)
        self.assertIn("len(pwd)!=4",source)
        self.assertIn('if kind=="password":',source)
        self.assertIn("Este é um backup antigo.",source)
        self.assertNotIn("len(pwd)<10",source)


if __name__=="__main__":
    unittest.main()
