"""Clinical-medication editor regressions using synthetic profiles only."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from windows import secure_store
from windows.medication_editor_v080 import (
    GROUPS,ALL_FIELDS,source_value,apply_extras,medication_document_assets,
)

class MedicationV080(unittest.TestCase):
    def test_all_sections_have_editable_fields(self):
        self.assertEqual([name for name,_ in GROUPS],
                         ["Prescrição","Repetições e posologia","Informação clínica","Bula"])
        source=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text(encoding="utf-8")
        method=source.split("    def _med_form(self,frame,med):",1)[1].split(
            "    def _update_med_preview(self):",1)[0]
        self.assertIn("for heading,entries in GROUPS",method)
        self.assertIn('self._attach_med_document(k,m)',method)
        self.assertNotIn('self.t("coming")',method)
        self.assertIn('VERSION = "0.8.11"',source)

    def test_native_android_values_read_and_complex_fields_preserved(self):
        old={"id":"m1","name":"Fictício","android_original":{
            "prescriptionDate":"2026-10-15","frequencyHours":6,
            "prescription":{"document":"keep","series":[1,2]},
            "suspended_from":"2026-10-27"}}
        self.assertEqual(source_value(old,"frequency_hours"),"6")
        self.assertEqual(source_value(old,"prescription_date"),"2026-10-15")
        self.assertEqual(source_value(old,"prescription"),"")
        self.assertEqual(apply_extras(old,{"prescription":"",
             "frequency_hours":"6","suspended_from":"2026-10-27"}),{})
        self.assertEqual(old["android_original"]["prescription"]["series"],[1,2])

    def test_edit_and_backup_preserve_original_and_profile_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/"data.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=dest),patch.object(
                secure_store,"_encrypt",side_effect=lambda raw:raw),patch.object(
                secure_store,"_decrypt",side_effect=lambda raw:raw):
                store=secure_store.SecureStore()
                a=store.create_profile("Pessoa A Fictícia")
                b=store.create_profile("Pessoa B Fictícia")
                old=store.save_medication(a["id"],{
                    "name":"Medicamento A","dose":"20 mg","time":"Jejum",
                    "reminder_time":"07:00","no_alarm":False,"suspended":True})
                old["android_original"]={
                    "prescriptionDate":"2026-10-15","frequencyHours":12,
                    "prescription":{"native":"keep"},"suspended_from":"2026-10-27"}
                store.save()
                fake=Path(directory)/"bula.pdf"
                fake.write_bytes(b"%PDF-1.4\nsynthetic fake")
                self.assertTrue(store.import_local_document(a["id"],fake))
                own=medication_document_assets(store.imported_assets(a["id"]))
                self.assertEqual(len(own),1)
                self.assertFalse(medication_document_assets(store.imported_assets(b["id"])))
                digest=own[0]["sha256"]
                edited=store.save_medication(a["id"],{
                    "name":"Medicamento A","dose":"20 mg","time":"Jejum",
                    "reminder_time":"07:00","no_alarm":False,"suspended":True,
                    "prescription_date":"2026-10-15","frequency_hours":"12",
                    "prescription":"","posology":"Após pequeno-almoço",
                    "leaflet":"Ler o folheto oficial","leaflet_asset_sha256":digest,
                },old["id"])
                self.assertTrue(edited["suspended"])
                self.assertEqual(edited["reminder_time"],"07:00")
                self.assertEqual(edited["posology"],"Após pequeno-almoço")
                self.assertEqual(edited["android_original"]["prescription"],{"native":"keep"})
                self.assertIsInstance(edited["android_original"]["frequencyHours"],int)
                self.assertEqual(edited["leaflet_asset_sha256"],digest)
                self.assertEqual(len(store.get_profile(b["id"])["medications"]),0)
                with self.assertRaises(secure_store.LocalStoreError):
                    store.save_medication(b["id"],{
                        "name":"Falso","dose":"2 mg","time":"", 
                        "leaflet_asset_sha256":digest,
                    })
                self.assertEqual(len(store.get_profile(b["id"])["medications"]),0)
                self.assertEqual(store.read_imported_asset(own[0]),fake.read_bytes())

    def test_invalid_fields_are_rejected_without_clinical_edit(self):
        with self.assertRaises(ValueError):
            apply_extras({},{"profile_address":"DEVE SER BLOQUEADO"})
        with self.assertRaises(ValueError):
            apply_extras({},{"posology":"x"*3000})
        self.assertIn("suspended_from",ALL_FIELDS)

    def test_avisos_cannot_fallback_to_splashed_desktop(self):
        root=Path(__file__).resolve().parents[1]
        agent=(root/"reminder_agent_v071.py").read_text(encoding="utf-8")
        installer=(root/"installer"/"SaudePratica.iss").read_text(encoding="utf-8")
        self.assertNotIn('return [str(here),"--reminder-agent"]',agent)
        self.assertIn("SaudePraticaAvisos.exe",agent)
        self.assertIn('end;\n  begin\n    { For installations',installer)

if __name__=="__main__":
    unittest.main()
