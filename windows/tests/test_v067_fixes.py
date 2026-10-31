"""Windows 0.6.7 regressions: no private patient data."""
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from windows import secure_store
from windows.android_profile_v067 import read_profile_extras
from windows.tests.test_v063_archive import make_zip, _archive_files

class MedicationsCanBeEditedWithoutSchedule(unittest.TestCase):
    def test_change_suspended_without_creating_hour_or_type(self):
        with tempfile.TemporaryDirectory() as folder:
            storage=Path(folder)/"profile_data.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=storage),\
                 patch.object(secure_store,"_encrypt",side_effect=lambda x:x),\
                 patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                store=secure_store.SecureStore()
                person=store.create_profile("Fictício")
                source={"id":"med","name":"Medicamento exemplo","time":"Jejum",
                        "dose_pattern":"Android type old","dose":"",
                        "android_original":{"custom":37},"images":["untouched.jpg"],
                        "suspended":False}
                person["medications"].append(source)
                store.save()
                out=store.save_medication(person["id"],{
                    "name":"Medicamento exemplo","time":"Jejum",
                    "dose_pattern":"Android type old","suspended":True,
                    "no_alarm":False},medication_id="med")
                self.assertTrue(out["suspended"])
                self.assertEqual(out["time"],"Jejum")
                self.assertEqual(out["images"],["untouched.jpg"])
                self.assertEqual(out["android_original"],{"custom":37})
                self.assertTrue(store.get_profile(person["id"])["medications"][0]["suspended"])

    def test_new_medication_optional_time_and_dose(self):
        with tempfile.TemporaryDirectory() as folder:
            storage=Path(folder)/"profile_data.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=storage),\
                 patch.object(secure_store,"_encrypt",side_effect=lambda x:x),\
                 patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                store=secure_store.SecureStore()
                person=store.create_profile("Fictício")
                out=store.save_medication(person["id"],{"name":"Novo medicamento fictício",
                     "time":"","dose":"","no_alarm":False})
                self.assertEqual(out["time"],"")
                self.assertEqual(out["dose"],"")

class ProfileRecoveryTests(unittest.TestCase):
    def test_identity_metadata_recovered_and_other_profile_excluded(self):
        files=_archive_files()
        files["saudepratica_identity/legacy/records.json"]=json.dumps({
            "personal":{"birthDate":"1988-04-18","healthUnit":"Unidade fictícia",
                        "postalCode":"0000-111"},"citizenCard":"EXAMPLE-ONLY"
        }).encode()
        files["saudepratica_identity/legacy/cc_front.jpg"]=files[
            "saudepratica_identity/legacy/avatar.jpg"]
        files["saudepratica_identity/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/records.json"]=json.dumps({
            "private":"OTHER PERSON SHOULD NOT APPEAR"}).encode()
        fields,rows=read_profile_extras(make_zip(files),"legacy")
        self.assertEqual(fields["birth_date"],"1988-04-18")
        self.assertEqual(fields["health_unit"],"Unidade fictícia")
        self.assertTrue(any("citizenCard" in k for k,_ in rows))
        self.assertFalse(any("OTHER PERSON" in v for _,v in rows))

    def test_agenda_uses_stable_cards_without_glass_overlay(self):
        root=Path(__file__).resolve().parents[2]
        view=(root/"windows/desktop_v04.py").read_text(encoding="utf-8")
        shell=(root/"windows/wallpaper_shell_v06.py").read_text(encoding="utf-8")
        self.assertIn("self.wallpaper_shell.glass_enabled=False",view)
        self.assertIn("not self.glass_enabled",shell)
        self.assertNotIn('row.pack_propagate(False)',view[view.index("    def _agenda("):view.index("    def _documents(")])
        self.assertIn("Documentos de identificação do Android",view)

if __name__=="__main__":unittest.main()
