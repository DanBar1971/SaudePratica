"""No patient examples: synthetic regression tests for Windows 0.6.6."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
from windows.profile_fields_v066 import mapped_fields, missing_profile_fields
from windows.medication_schedule_v066 import next_medication_label
from windows import secure_store

class ProfilesMappingTests(unittest.TestCase):
    def test_realistic_android_aliases_fill_missing_fields_only(self):
        original={"birthDate":"1984-05-03","mobile":"900000000",
                  "healthUnit":"USF fictícia","morada":"Rua Exemplo",
                  "codigoPostal":"1000-001","NISS":"00000000000"}
        mapped=mapped_fields(original)
        self.assertEqual(mapped["health_unit"],"USF fictícia")
        self.assertEqual(mapped["birth_date"],"1984-05-03")
        self.assertNotIn("email",mapped)
        current={"phone":"999999999","address":""}
        missing=missing_profile_fields(current,original)
        self.assertNotIn("phone",missing)
        self.assertEqual(missing["address"],"Rua Exemplo")
    def test_invalid_birthday_not_written(self):
        self.assertNotIn("birth_date",mapped_fields({"birthDate":"03/05/1984"}))
        self.assertEqual(mapped_fields({}),{})

class MedicationScheduleTests(unittest.TestCase):
    def test_daily_recurrence_after_hour_today(self):
        item={"name":"Fictício","android_original":{
            "reminder_time":"09:30","repeat_mode":"daily"}}
        self.assertEqual(next_medication_label(item,datetime(2026,11,1,10,0)),
            "Próxima toma prevista: 2026-11-02 · 09:30")
    def test_weekly_sunday_is_js_zero(self):
        item={"android_original":{"reminder_time":"09:30","repeat_mode":"weekly",
                                 "repeat_weekdays":[0]}}
        self.assertEqual(next_medication_label(item,datetime(2026,10,31,10,0)),
            "Próxima toma prevista: 2026-11-01 · 09:30")
    def test_unknown_frequency_shows_no_invented_date(self):
        self.assertEqual(next_medication_label({"time":"08:30"},
             datetime(2026,10,31,7,0)),"Data da próxima toma por definir · 08:30")
    def test_suspended_has_no_next_reminder(self):
        self.assertEqual(next_medication_label({"suspended":True,"time":"07:00"},
            datetime(2026,10,31,6,0)),"Medicação suspensa")
    def test_dated_schedule(self):
        item={"android_original":{"reminder_time":"08:00",
              "schedule":{"2026-11":[2,5]}}}
        self.assertEqual(next_medication_label(item,datetime(2026,10,31,12,0)),
            "Próxima toma prevista: 2026-11-02 · 08:00")

class DeletionTests(unittest.TestCase):
    def test_delete_profile_preserves_other_members_shared_encrypted_assets(self):
        with tempfile.TemporaryDirectory() as d:
            store_path=Path(d)/"user"/"profile_data.dpapi"
            store_path.parent.mkdir()
            with patch.object(secure_store,"_user_data_path",return_value=store_path),\
                 patch.object(secure_store,"_encrypt",side_effect=lambda x:x),\
                 patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                store=secure_store.SecureStore()
                first=store.save_profile({"name":"Pessoa A"})
                second=store.save_profile({"name":"Pessoa B"})
                store.update_settings(active_profile=first["id"])
                file=Path(d)/"synthetic.pdf"
                file.write_bytes(b"%PDF-1.4 fake clinical-free data")
                self.assertTrue(store.import_local_document(first["id"],file))
                self.assertTrue(store.import_local_document(second["id"],file))
                item=store.imported_assets(first["id"])[0]
                path=store._asset_path(item["sha256"])
                self.assertTrue(path.exists())
                result=store.delete_profile(first["id"])
                self.assertEqual(result["next_active"],second["id"])
                self.assertIsNone(store.get_profile(first["id"]))
                self.assertEqual(len(store.imported_assets(second["id"])),1)
                self.assertEqual(store.read_imported_asset(
                    store.imported_assets(second["id"])[0]),file.read_bytes())
                self.assertTrue(path.exists())
                store.delete_profile(second["id"])
                self.assertFalse(path.exists())
                self.assertEqual(store.profiles(),[])

    def test_save_failure_rolls_back_deletion(self):
        with tempfile.TemporaryDirectory() as d:
            data_path=Path(d)/"profile_data.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=data_path),\
                 patch.object(secure_store,"_encrypt",side_effect=lambda x:x),\
                 patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                store=secure_store.SecureStore()
                person=store.save_profile({"name":"Pessoa fictícia"})
                with patch.object(store,"save",side_effect=OSError("fail")):
                    with self.assertRaises(OSError):store.delete_profile(person["id"])
                self.assertIsNotNone(store.get_profile(person["id"]))

    def test_modules_hide_import_buttons(self):
        root=Path(__file__).resolve().parents[2]
        text=(root/"windows/desktop_v04.py").read_text(encoding="utf-8")
        self.assertNotIn('self._button(bar,"Importar JSON"',text)
        self.assertNotIn('self._button(bar,"Importar agenda JSON"',text)
        self.assertIn('section("Próximos compromissos",future,True)',text)

if __name__=="__main__":unittest.main()
