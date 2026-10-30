"""Guard against the previous Python desktop icon and no startup splash."""
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]


class OfficialBrandingTests(unittest.TestCase):
    def test_official_three_images_are_present(self):
        for name in ("saude_icon.png","saude_splash.png","saude_background.png"):
            p=ROOT/"assets"/name
            self.assertTrue(p.is_file(),str(p))
            with Image.open(p) as img:
                self.assertGreater(img.width,300)
                self.assertGreater(img.height,300)

    def test_windows_package_embeds_real_icon_and_splash(self):
        workflow=(ROOT/".github/workflows/windows-build.yml").read_text(encoding="utf-8")
        self.assertIn("--icon dist/saude_icon.ico",workflow)
        self.assertIn("--splash dist/saude_splash_windows.png",workflow)
        self.assertIn("--onedir",workflow)
        installer=(ROOT/"windows/installer/SaudePratica.iss").read_text(encoding="utf-8")
        self.assertIn('IconFilename: "{app}\\SaudePratica.ico"',installer)
        self.assertIn('Source: "..\\..\\dist\\SaudePraticaDesktop\\*"',installer)
        source=(ROOT/"windows/desktop_v04.py").read_text(encoding="utf-8")
        self.assertIn("pyi_splash.close()",source)
        self.assertIn("SAUDEPRATICA_SMOKE_REPORT",source)
        self.assertIn("startup_error.log",source)
        self.assertIn("smoke_windows.py --exe",workflow)
        self.assertIn('self.iconbitmap(str(icon_file))',source)

    def test_original_splash_is_actually_rendered(self):
        s=(ROOT/"windows/tools/build_brand_assets.py").read_text(encoding="utf-8")
        self.assertIn('saude_splash.png',s)
        self.assertIn("ImageOps.contain(original_splash",s)
        self.assertNotIn(".crop(",s)
        self.assertNotIn("draw.text(",s)
        self.assertNotIn("rounded_rectangle(",s)
        self.assertIn("(430, 720)",s)


if __name__=="__main__":
    unittest.main()
