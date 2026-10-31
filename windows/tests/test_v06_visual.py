"""Regression tests for the Windows 0.6 approved visual direction."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from windows.visual_v07 import wallpaper_image, icon_image, circular_photo, _source, _widescreen
from windows.ui_catalog_v05 import MODULE_CARDS

class VisualV06Tests(unittest.TestCase):
    def test_approved_wallpaper_is_real_16_9_and_contains_colour(self):
        im=wallpaper_image(1600,900,False)
        self.assertEqual(im.size,(1600,900))
        self.assertNotEqual(im.getpixel((50,50)),im.getpixel((800,450)))
        self.assertNotEqual(im.getpixel((1490,760)),im.getpixel((800,450)))
        self.assertEqual(wallpaper_image(1600,900,True).size,(1600,900))
        self.assertNotEqual(wallpaper_image(1600,900,True).getpixel((300,100)),
                            wallpaper_image(1600,900,False).getpixel((300,100)))

    def test_every_android_module_has_a_colored_nonempty_icon(self):
        for i,(key,emoji,*rest) in enumerate(MODULE_CARDS):
            image=icon_image(emoji,i,50)
            self.assertEqual(image.size,(50,50))
            center=image.getpixel((25,25))
            self.assertLess(image.getpixel((0,0))[3],32,key)  # transparent corner, antialiasing permitted
            self.assertIsNotNone(image.getbbox(),key)

    def test_wallpaper_uses_full_resolution_original_and_preserves_ratio(self):
        source=_source()
        self.assertGreaterEqual(source.width,900)
        self.assertGreaterEqual(source.height,900)
        master=_widescreen()
        self.assertEqual(master.size,(1672,941))
        self.assertEqual(wallpaper_image(1920,1080).size,(1920,1080))
        visual=(Path(__file__).resolve().parents[2]/"windows/visual_v07.py").read_text(encoding="utf-8")
        self.assertNotIn("_BG_WEBP",visual)
        self.assertIn("saude_background.png",visual)
        self.assertIn("source.width*h/source.height",visual)
        self.assertIn("ImageOps.fit",visual)

    def test_missing_photo_is_not_invented(self):
        self.assertIsNone(circular_photo("",42))
        self.assertIsNone(circular_photo("invalid-photo",42))

    def test_dashboard_uses_canvas_not_opaque_hero_banner(self):
        root=Path(__file__).resolve().parents[2]
        main=(root/"windows/desktop_v04.py").read_text(encoding="utf-8")
        dashboard=(root/"windows/dashboard_v06.py").read_text(encoding="utf-8")
        self.assertIn('VERSION = "0.6.4"',main)
        self.assertIn('self.dashboard=Dashboard(self.body,self,full=False)',main)
        self.assertIn('def _toggle_profile_menu(self)',main)
        self.assertIn('circular_photo(person.get("photo_b64",""),42)',main)
        self.assertIn('class Dashboard(tk.Canvas):',dashboard)
        self.assertIn('self.create_image(0,0,image=self._background_photo',dashboard)
        self.assertIn('self._icon_cache.append(ico)',dashboard)
        self.assertIn("icon_image(icon,i,64)",dashboard)
        self.assertIn('self.tag_bind(tag,"<Button-1>"',dashboard)

if __name__=="__main__":unittest.main()
