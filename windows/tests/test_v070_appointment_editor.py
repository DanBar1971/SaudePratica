"""Windows 0.7.0 appointment editor tests: synthetic data only."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
from windows import secure_store
from windows.agenda_filter_v069 import appointment_status,filtered_appointments
from windows.appointment_editor_v070 import (
    MAIN_FIELDS,STATUS_OPTIONS,extra_fields,parse_extra,clean_appointment_fields
)

class AppointmentEditorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"profile_data.dpapi"
        self.path_patch=patch.object(secure_store,"_user_data_path",return_value=self.path)
        self.encrypt=patch.object(secure_store,"_encrypt",side_effect=lambda b:b)
        self.decrypt=patch.object(secure_store,"_decrypt",side_effect=lambda b:b)
        self.path_patch.start();self.encrypt.start();self.decrypt.start()
        self.store=secure_store.SecureStore()
        self.profile=self.store.create_profile("Utilizador de teste")["id"]
        self.other=self.store.create_profile("Outro teste")["id"]
    def tearDown(self):
        self.decrypt.stop();self.encrypt.stop();self.path_patch.stop()
        self.temp.cleanup()
    def sample(self):
        original={"id":"android-123","date":"2026-11-10",
                  "status":"Cancelada","extra":{"booking":"example"}}
        rec=self.store.save_appointment(self.profile,{
            "title":"Consulta fictícia","date":"2026-11-10","time":"09:30",
            "location":"Hospital fictício","department":"Serviço fictício",
            "notes":"Nota inicial","desktop_status":"cancelled"
        })
        stored=self.store.get_profile(self.profile)["appointments"][0]
        stored.update({"android_original":original,
                       "android_source_key":"source-id",
                       "external_ref":"ABC-123","number":2,
                       "extra":{"room":"A"},"confirmed":True})
        self.store.save()
        return rec["id"]

    def test_every_common_field_can_change_and_persists_after_reload(self):
        ident=self.sample()
        changes={k:f"Exemplo {k}" for k,_ in MAIN_FIELDS
                 if k not in ("date","time")}
        changes.update(date="2026-12-14",time="14:25",
                       desktop_status="pending",external_ref="DEF-456",
                       number=4,extra={"room":"B"},confirmed=False)
        result=self.store.save_appointment(self.profile,changes,ident)
        self.assertEqual(result["id"],ident)
        self.assertEqual(result["android_source_key"],"source-id")
        self.assertEqual(result["android_original"]["status"],"Cancelada")
        saved=secure_store.SecureStore().get_profile(self.profile)["appointments"][0]
        for key,val in changes.items():self.assertEqual(saved[key],val)
        self.assertEqual(appointment_status(saved,datetime(2026,10,31)),"pending")
        self.assertEqual(self.store.get_profile(self.other)["appointments"],[])

    def test_cancel_and_reopen_without_mutating_original_android(self):
        ident=self.sample()
        self.store.save_appointment(self.profile,{"desktop_status":"done"},ident)
        self.assertEqual(appointment_status(
            self.store.get_profile(self.profile)["appointments"][0]),"done")
        self.store.save_appointment(self.profile,{"desktop_status":"cancelled"},ident)
        self.assertEqual(appointment_status(
            self.store.get_profile(self.profile)["appointments"][0]),"cancelled")
        self.store.save_appointment(self.profile,{"desktop_status":"pending"},ident)
        item=self.store.get_profile(self.profile)["appointments"][0]
        self.assertEqual(appointment_status(item),"pending")
        self.assertEqual(item["android_original"]["status"],"Cancelada")
        self.assertEqual([x["id"] for x in filtered_appointments([item],"pending")],[ident])

    def test_rollback_on_storage_error(self):
        ident=self.sample()
        original=dict(self.store.get_profile(self.profile)["appointments"][0])
        with patch.object(self.store,"save",side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.store.save_appointment(self.profile,
                    {"title":"Mudança","desktop_status":"done"},ident)
        self.assertEqual(self.store.get_profile(self.profile)["appointments"][0],original)

    def test_invalid_date_and_status_do_not_alter_store(self):
        ident=self.sample()
        original=dict(self.store.get_profile(self.profile)["appointments"][0])
        for fields in ({"date":"2026-02-30"},{"time":"40:99"},
                       {"desktop_status":"unknown"},{"id":"changed"},
                       {"android_original":{}},{"number":"texto"}):
            with self.subTest(fields=fields):
                with self.assertRaises(secure_store.LocalStoreError):
                    self.store.save_appointment(self.profile,fields,ident)
                self.assertEqual(self.store.get_profile(self.profile)["appointments"][0],original)

    def test_draft_create_and_original_metadata_hidden(self):
        ident=self.sample()
        item=self.store.get_profile(self.profile)["appointments"][0]
        extras=dict(extra_fields(item))
        self.assertEqual(extras["external_ref"],"ABC-123")
        self.assertNotIn("android_original",extras)
        self.assertNotIn("android_source_key",extras)
        self.assertNotIn("id",extras)
        self.assertEqual(parse_extra("number","3",2),3)
        self.assertEqual(parse_extra("extra",'{"room":"C"}',{"room":"A"}),{"room":"C"})
        with self.assertRaises(ValueError):parse_extra("id","bad","old")
        new=self.store.save_appointment(self.profile,{
            "title":"Nova marcação fictícia","date":"2027-01-10",
            "time":"12:00","desktop_status":"pending"})
        self.assertNotEqual(new["id"],ident)
        self.assertEqual(len(self.store.get_profile(self.profile)["appointments"]),2)

    def test_ui_editor_is_available_from_cards(self):
        text=(Path(__file__).resolve().parents[2]/"windows/desktop_v04.py").read_text(encoding="utf-8")
        for phrase in ("def _appointment_form(self,person):",
                       "def _save_appointment(self):",
                       "def _open_appointment(self,appointment_id):",
                       "self.store.save_appointment(",
                       '"Abrir ficha"',
                       'self.agenda_mode=="editor"'):
            self.assertIn(phrase,text)

if __name__=="__main__":unittest.main()
