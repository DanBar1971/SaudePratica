"""0.6.8 catalogue tests use only synthetic data."""
import unittest
from pathlib import Path
from windows.medication_gallery_v068 import medication_filter_matches, medication_status

class MedicationGalleryTests(unittest.TestCase):
    def test_status_colors(self):
        self.assertEqual(medication_status({"no_alarm":True}),("Sem alarme","#f3bf43","#25200b"))
        self.assertEqual(medication_status({"suspended":True})[0],"Suspensa")
        self.assertEqual(medication_status({})[0],"Ativa")
        self.assertEqual(medication_status({"no_alarm":True,"suspended":True})[0],"Suspensa")
    def test_filters_are_distinct(self):
        self.assertTrue(medication_filter_matches({"no_alarm":True,"time":""},"no_alarm"))
        self.assertFalse(medication_filter_matches({"no_alarm":True,"time":""},"undefined"))
        self.assertTrue(medication_filter_matches({"time":""},"undefined"))
        self.assertFalse(medication_filter_matches({"time":""},"no_alarm"))
        self.assertFalse(medication_filter_matches({"android_original":{"reminder_time":"09:00","repeat_mode":"daily"}},"undefined"))
        self.assertTrue(medication_filter_matches({"suspended":True,"time":""},"undefined"))
    def test_cards_are_opaque_and_auto_height(self):
        text=(Path(__file__).resolve().parents[2]/"windows/desktop_v04.py").read_text(encoding="utf-8")
        part=text[text.index("    def _medication(self):"):text.index("    def _new_med(self):")]
        self.assertIn("self.wallpaper_shell.glass_enabled=False",part)
        self.assertNotIn("tile.grid_propagate(False)",part)
        self.assertNotIn("tile.configure(height=",part)
        self.assertIn('("undefined","Sem definição")',part)
if __name__=="__main__":unittest.main()
