"""v0.2 regression checks using synthetic data only."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from windows.secure_store import SecureStore, LocalStoreError
from shared.python.saude_backup import read_backup

@unittest.skipUnless(sys.platform=="win32","Windows DPAPI is required.")
class MedicationEditorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{"LOCALAPPDATA":self.tmp.name})
        self.env.start()
        self.store=SecureStore()
        self.profile=self.store.create_profile("Perfil fictício")["id"]

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_edit_keeps_id_and_unknown_existing_metadata(self):
        old=self.store.add_medication(self.profile,"Medicamento fictício","20 mg","07:00","oral")
        old["prescription_id"]="FICTICIOUS-123"
        self.store.save()
        changed=self.store.save_medication(self.profile,{
            "name":"Medicamento fictício", "dose":"25 mg","time":"08:30",
            "administration_route":"parenteral","injection_type":"sc",
            "dose_pattern":"Jejum","indication":"Prescrição fictícia",
            "notes":"Nota de teste","no_alarm":False,"suspended":False,
        },medication_id=old["id"])
        self.assertEqual(changed["id"],old["id"])
        self.assertEqual(changed["prescription_id"],"FICTICIOUS-123")
        self.assertEqual(changed["injection_type"],"sc")
        self.assertEqual(len(SecureStore().profiles()[0]["medications"]),1)
        backup=self.store.export_backup("Frase de teste secreta 2026")
        decoded=read_backup(backup,"Frase de teste secreta 2026")
        self.assertIn(b'"injection_type": "sc"',list(decoded.values())[1])

    def test_invalid_time_does_not_change_store(self):
        old=self.store.add_medication(self.profile,"Medicamento fictício","20 mg","07:00","oral")
        with self.assertRaises(LocalStoreError):
            self.store.save_medication(self.profile,{
                "name":"Medicação errada","time":"27:75",
                "dose":"25 mg","administration_route":"oral"
            },medication_id=old["id"])
        self.assertEqual(self.store.get_profile(self.profile)["medications"][0]["name"],
                         "Medicamento fictício")

    def test_sos_has_no_alarm_and_old_data_persists(self):
        old=self.store.add_medication(self.profile,"SOS fictício","1 dose","","")
        changed=self.store.save_medication(self.profile,{
            "name":"SOS fictício","dose":"1 dose","time":"",
            "dose_pattern":"SOS","administration_route":"oral",
            "no_alarm":True,"suspended":True,
        },medication_id=old["id"])
        self.assertTrue(changed["no_alarm"])
        self.assertTrue(changed["suspended"])

    def test_injection_does_not_survive_route_change(self):
        m=self.store.save_medication(self.profile,{
            "name":"Exemplo","dose":"10 mg","time":"09:00",
            "administration_route":"oral","injection_type":"iv",
        })
        self.assertEqual(m["injection_type"],"")

if __name__ == "__main__":
    unittest.main()
