"""Windows v0.7.8 regression: medication details and photos stay in their profiles.

Uses generated, non-clinical images and profiles; no private user backups.
"""
import base64
import unittest
from io import BytesIO
from types import SimpleNamespace
from PIL import Image
from windows.desktop_v04 import Desktop
from windows.medication_details_v078 import additional_medication_fields

def jpeg():
    out=BytesIO()
    Image.new("RGB",(40,35),"#628ea4").save(out,format="JPEG")
    return out.getvalue()

class FakeStore:
    def __init__(self):
        self.requests=[]
        self.data=jpeg()
    def imported_assets(self,profile):
        self.requests.append(("list",profile))
        return [{"filename":"box.jpg","category":"fotografia de medicamento",
                 "sha256":"synthetic", "profile_id":profile}]
    def read_imported_asset(self,entry):
        self.requests.append(("read",entry["profile_id"]))
        return self.data

class MedicationImageRegression(unittest.TestCase):
    def test_recovers_photo_only_from_current_profile_and_caches(self):
        store=FakeStore()
        model=SimpleNamespace(active_id="profileA",store=store)
        med={"id":"med1","name":"Medicação exemplo",
             "android_original":{"images":["content://example/box.jpg"]}}
        first=Desktop._med_photo_b64(model,med)
        self.assertTrue(base64.b64decode(first).startswith(b"\xff\xd8\xff"))
        self.assertEqual(first,Desktop._med_photo_b64(model,med))
        self.assertEqual(store.requests,[("list","profileA"),("read","profileA")])
        model.active_id="profileB"
        second=Desktop._med_photo_b64(model,med)
        self.assertEqual(first,second)
        self.assertEqual(store.requests[-2:],[("list","profileB"),("read","profileB")])

    def test_does_not_guess_photo_when_unavailable(self):
        store=FakeStore()
        model=SimpleNamespace(active_id="one",store=store)
        self.assertEqual(Desktop._med_photo_b64(model,{"android_original":{"images":[]}}),"")
        self.assertFalse(store.requests)

    def test_maintains_raw_clinical_fields_and_excludes_foreign_data(self):
        med={"name":"Teste","notes":"só medicação",
             "android_original":{"suspended_from":"2026-10-28",
                                 "prescriber":"Dr. Exemplo",
                                 "repeat_interval":12,
                                 "appointment":"NAO MOSTRAR",
                                 "profile_phone":"NAO MOSTRAR"}}
        detail=dict(additional_medication_fields(med))
        self.assertEqual(detail["Suspensa desde"],"2026-10-28")
        self.assertEqual(detail["Prescritor"],"Dr. Exemplo")
        self.assertEqual(detail["Intervalo de repetição"],"12")
        self.assertNotIn("appointment",str(detail))
        self.assertNotIn("NAO MOSTRAR",str(detail))

    def test_busy_cursor_and_selector_visible(self):
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text(encoding="utf-8")
        self.assertIn('self.configure(cursor="wait")',source)
        self.assertIn('text=label+"   ▼"',source)
        self.assertIn('VERSION = "0.7.9"',source)

if __name__=="__main__":
    unittest.main()
