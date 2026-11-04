"""Windows 0.8.14 — synthetic Android SOS/Lares recovery and pharmacy portal.

No patient data, real address, or real medical contact is used in fixtures.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZIP_DEFLATED,ZipFile

from windows import secure_store
from windows.android_sos_lares_v0811 import extract_sos_care


def typed(values):
    return {key:{"t":"s","v":value} for key,value in values.items()}


def android_zip(a,b):
    """Authentic FamilyBackupStore-shaped manifest with two disjoint profiles."""
    prefs={
        "saudepratica_emergency_"+a:typed({
            "contact_name":"Contacto A fictício",
            "contact_phone":"+351 210 000 001",
            "allergies":"Dado exclusivamente sintético",
            "chronic_conditions":"Nenhuma informação real",
            "blood_group":""
        }),
        "saudepratica_emergency_"+b:typed({
            "contact_name":"Contacto B fictício",
            "contact_phone":"+351 210 000 002",
            "allergies":"Não mostrar no perfil A",
        }),
        "saudepratica_care_home_v1_"+a:typed({
            "institution":"Residência A de teste",
            "valence":"ERPI","address":"Rua Fictícia, 1",
            "phone":"+351 210 000 003",
            "email":"teste@example.org",
            "website":"https://example.org/",
            "notes":"Nota sintética de cuidados",
            "months":json.dumps({
                "2026-10":{
                    "state":"RECEBIDA",
                    "total":"1200,50","paid":"1200,50","refunded":"0,00",
                    "adse_reference":"TESTE-01",
                    "document_name":"recibo-de-teste.pdf",
                    "document_id":"file-fake"},
                "2026-11":{
                    "state":"SUBMETIDA","total":"1300,00",
                    "paid":"1300,00","refunded":"0"},
            })
        }),
        "saudepratica_care_home_v1_"+b:typed({
            "institution":"Residência B de teste",
            "valence":"SAD",
            "months":json.dumps({"2026-10":{"state":"REEMBOLSADA",
                "total":"850,00","paid":"850,00","refunded":"200,00"}})
        }),
    }
    files={f"saudepratica_profiles/{a}/medicacao.json":b'{"medications":[]}',
           f"saudepratica_profiles/{b}/medicacao.json":b'{"medications":[]}'}
    manifest=[{"path":k,"size":len(v),"sha256":sha256(v).hexdigest()}
              for k,v in files.items()]
    head={"kind":"saudepratica-complete-backup","format":1,
          "prefs":prefs,"files":manifest}
    buff=BytesIO()
    with ZipFile(buff,"w",ZIP_DEFLATED) as z:
        z.writestr("backup.json",json.dumps(head).encode())
        for path,raw in files.items():
            z.writestr("data/"+path,raw)
    return buff.getvalue()


class ExtractionTests(unittest.TestCase):
    def test_extraction_filters_strictly_by_uuid(self):
        a,b=str(uuid4()),str(uuid4())
        archive=android_zip(a,b)
        own=extract_sos_care(archive,a)
        self.assertEqual(own["sos"]["contact_name"],"Contacto A fictício")
        self.assertEqual(len(own["residences"]),1)
        self.assertEqual(len(own["residence_invoices"]),2)
        self.assertEqual(own["residence_invoices"][0]["date"],"2026-11-01")
        self.assertEqual(own["residence_invoices"][1]["amount_cents"],120050)
        self.assertEqual(own["residences"][0]["type"],"ERPI")
        self.assertNotIn("Residência B",str(own))
        self.assertNotIn("Contacto B",str(own))
        other=extract_sos_care(archive,b)
        self.assertEqual(other["sos"]["contact_name"],"Contacto B fictício")
        self.assertEqual(other["residences"][0]["type"],"Serviço de Apoio Domiciliário")
        with self.assertRaises(ValueError):
            extract_sos_care(archive,"../../other")

    def test_missing_pref_group_is_not_invented(self):
        a,b=str(uuid4()),str(uuid4())
        data=extract_sos_care(android_zip(a,b),str(uuid4()))
        self.assertFalse(any(data["sos"].values()))
        self.assertEqual(data["residences"],[])
        self.assertEqual(data["residence_invoices"],[])


class ImportStoreTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        for mock in (
            patch.object(secure_store,"_user_data_path",
                         return_value=Path(self.t.name)/"family.dpapi"),
            patch.object(secure_store,"_encrypt",side_effect=lambda data:data),
            patch.object(secure_store,"_decrypt",side_effect=lambda data:data),
        ):
            mock.start()
            self.addCleanup(mock.stop)
        self.store=secure_store.SecureStore()
        self.a=self.store.create_profile("Pessoa A fictícia")["id"]
        self.b=self.store.create_profile("Pessoa B fictícia")["id"]
        self.source_a=str(uuid4())
        self.source_b=str(uuid4())
        original=android_zip(self.source_a,self.source_b)
        digest=sha256(original).hexdigest()
        self.store._write_assets([(digest,original)])
        self.store.get_profile(self.a)["android_zip_source_id"]=self.source_a
        self.store.get_profile(self.b)["android_zip_source_id"]=self.source_b
        self.store.data["android_family_archives"]=[
            {"sha256":digest,"bytes":len(original),
             "source_ids":[self.source_a,self.source_b],
             "profile_ids":[self.a,self.b]}]
        self.store.save()

    def test_import_sos_preserves_windows_edits(self):
        self.store.save_emergency_data(self.a,{
            "contact_name":"Contacto que escrevi no Windows"})
        r=self.store.import_android_sos_lares(self.a,"sos")
        self.assertGreaterEqual(r["available_sos"],3)
        self.assertEqual(self.store.emergency_data(self.a)["contact_name"],
                         "Contacto que escrevi no Windows")
        self.assertEqual(self.store.emergency_data(self.a)["contact_phone"],
                         "+351 210 000 001")
        self.assertEqual(self.store.emergency_data(self.b)["contact_name"],"")
        self.assertEqual(self.store.import_android_sos_lares(self.a,"sos")["sos_fields"],0)

    def test_import_care_add_only_idempotent_private(self):
        first=self.store.import_android_sos_lares(self.a,"care")
        self.assertEqual(first["residences"],1)
        self.assertEqual(first["invoices"],2)
        self.assertEqual(self.store.remaining_records(self.b,"residences"),[])
        self.assertEqual(self.store.remaining_records(self.b,"residence_invoices"),[])
        self.assertEqual(self.store.import_android_sos_lares(self.a,"care")["invoices"],0)
        original=self.store.remaining_records(self.a,"residence_invoices")[0]
        self.store.save_remaining_record(self.a,"residence_invoices",{
            "title":"Fatura editada manualmente",
            "date":original["date"],"status":"Em análise",
            "amount":"1400,00","paid":"1400,00","reimbursed":"0,00"},
            original["id"])
        self.assertEqual(self.store.import_android_sos_lares(self.a,"care")["invoices"],0)
        updated=next(x for x in self.store.remaining_records(self.a,"residence_invoices")
                     if x["id"]==original["id"])
        self.assertEqual(updated["status"],"Em análise")
        self.assertEqual(updated["amount_cents"],140000)
        self.store.import_android_sos_lares(self.b,"care")
        self.assertEqual(self.store.remaining_records(self.b,"residences")[0]["title"],
                         "Residência B de teste")

    def test_family_backup_preserves_imports(self):
        self.store.import_android_sos_lares(self.a,"sos")
        self.store.import_android_sos_lares(self.a,"care")
        from shared.python.saude_backup import read_backup
        backup=self.store.export_backup("senha-puramente-de-teste")
        files=read_backup(backup,"senha-puramente-de-teste")
        profile=json.loads(files[f"profiles/{self.a}/profile.json"])
        self.assertEqual(profile["emergency_contact_data"]["contact_name"],
                         "Contacto A fictício")
        self.assertEqual(len(profile["residence_invoices"]),2)
        self.assertNotIn("emergency_contact_data",
                         json.loads(files[f"profiles/{self.b}/profile.json"]))

    def test_missing_identity_fails_closed(self):
        other=self.store.create_profile("Sem ligação")["id"]
        with self.assertRaises(secure_store.LocalStoreError):
            self.store.import_android_sos_lares(other,"care")
        with self.assertRaises(secure_store.LocalStoreError):
            self.store.import_android_sos_lares(other,"sos")

    def test_rollback_on_disk_write_failure(self):
        before=self.store.emergency_data(self.a)
        with patch.object(self.store,"save",side_effect=OSError("failing disk")):
            with self.assertRaises(OSError):
                self.store.import_android_sos_lares(self.a,"sos")
        self.assertEqual(self.store.emergency_data(self.a),before)


class GuiContracts(unittest.TestCase):
    def test_both_backup_import_controls_and_pharmacy_portal(self):
        src=(Path(__file__).resolve().parents[1]/
             "remaining_ui_v0810.py").read_text("utf-8")
        self.assertIn("care_home_residents",src)
        self.assertNotIn("Recuperar instituição e faturas do Android",src)
        self.assertNotIn("Recuperar SOS do backup Android",src)
        self.assertIn("https://www.farmaciasdeservico.info/",src)
        self.assertIn("https://www.farmaciasdeservico.net/",src)
        self.assertIn("📍 Encontrar perto de mim",src)
        desktop=(Path(__file__).resolve().parents[1]/
                 "desktop_v04.py").read_text("utf-8")
        self.assertIn('VERSION = "0.8.18"',desktop)


if __name__=="__main__":
    unittest.main()
