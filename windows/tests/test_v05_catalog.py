"""v0.5 UI, safe photo persistence and theme regression tests."""
import base64
from io import BytesIO
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from windows.ui_catalog_v05 import MODULE_CARDS, filter_cards, accessible_contrast
from windows.secure_store import SecureStore, LocalStoreError

class CatalogTests(unittest.TestCase):
    def test_android_module_catalog_is_comprehensive_not_falsely_implemented(self):
        self.assertGreaterEqual(len(MODULE_CARDS),24)
        keys=[card[0] for card in MODULE_CARDS]
        self.assertEqual(len(keys),len(set(keys)))
        for key in ("medication","profiles","agenda","calendar","doses","documents",
                    "water","nutrition","clinical","expenses","symptoms","vaccines",
                    "emergency","sns24","ipo","options"):
            self.assertIn(key,keys)
        for key,_,_,_,enabled in MODULE_CARDS:
            if key in ("sync","emergency","doses","calendar"):
                self.assertFalse(enabled,key)
    def test_viewers_enabled_but_no_android_alarm_claim(self):
        statuses={row[0]:row[4] for row in MODULE_CARDS}
        self.assertTrue(statuses["agenda"])  # read-only viewer
        self.assertTrue(statuses["documents"]) # secure file import/export
        self.assertFalse(statuses["doses"])

    def test_search_matches_portuguese_accents(self):
        self.assertEqual(filter_cards("MEDICACAO")[0][0],"medication")
        self.assertEqual(filter_cards("Saude Visual")[0][0],"vision")
    def test_light_and_dark_palettes_are_readable(self):
        # These are the actual palette values declared in desktop_v04.py.
        for foreground,background in [
            ("#172b36","#ffffff"),("#52616e","#ffffff"),
            ("#172b36","#f8fbfd"),("#f1f7fa","#16232e"),
            ("#b6c4cd","#16232e"),("#f1f7fa","#101d27")]:
            self.assertGreaterEqual(accessible_contrast(foreground,background),4.5)
    def test_source_uses_real_photo_and_compact_controls(self):
        source=(ROOT/"windows/desktop_v04.py").read_text(encoding="utf-8")
        for token in ("_populate_med_gallery","Dashboard(self.body,self",
                      "med_gallery_state","_choose_med_photo","_authentic_thumb",
                      "text_color=self.p[\"text\"]", "height=33",
                      "def _settings_page(self):"):
            self.assertIn(token,source)
        self.assertNotIn("def _options(self):",source)
        smoke=(ROOT/"windows/tools/smoke_windows.py").read_text(encoding="utf-8")
        self.assertIn("SAUDEPRATICA_SMOKE_REPORT",smoke)
        self.assertIn("--exe",smoke)
        self.assertIn('app._edit_med(med["id"])',source)
        self.assertIn('("light","dark","system")',source)


@unittest.skipUnless(sys.platform=="win32","Windows DPAPI required.")
class PhotoTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{"LOCALAPPDATA":self.tmp.name})
        self.env.start()
        self.store=SecureStore()
        self.pid=self.store.create_profile("Test only")["id"]
    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def photo(self):
        out=BytesIO()
        Image.new("RGB",(64,80),(10,155,120)).save(out,format="JPEG")
        return base64.b64encode(out.getvalue()).decode("ascii")

    def test_med_photo_save_edit_and_restore(self):
        pic=self.photo()
        m=self.store.save_medication(self.pid,{
            "name":"Sample","dose":"10 mg","time":"07:00",
            "administration_route":"oral","photo_b64":pic})
        self.assertEqual(SecureStore().get_profile(self.pid)["medications"][0]["photo_b64"],pic)
        edited=self.store.save_medication(self.pid,{
            "name":"Sample","dose":"20 mg","time":"08:00",
            "administration_route":"oral","photo_b64":pic},m["id"])
        self.assertEqual(edited["id"],m["id"])
        self.assertEqual(edited["photo_b64"],pic)
        archive=self.store.export_backup("sample secure phrase 2026")
        people,files=self.store.inspect_backup(archive,"sample secure phrase 2026")
        with tempfile.TemporaryDirectory() as temp2:
            with patch.dict(os.environ,{"LOCALAPPDATA":temp2}):
                clean=SecureStore()
                clean.restore_backup(files)
                self.assertEqual(clean.profiles()[0]["medications"][0]["photo_b64"],pic)

    def test_rejects_non_jpeg_photos(self):
        bad=base64.b64encode(b"not-a-jpeg").decode("ascii")
        with self.assertRaises(LocalStoreError):
            self.store.save_medication(self.pid,{
                "name":"Sample","dose":"1","time":"09:00",
                "administration_route":"oral","photo_b64":bad})
        self.assertFalse(self.store.get_profile(self.pid)["medications"])

if __name__=="__main__":
    unittest.main()
