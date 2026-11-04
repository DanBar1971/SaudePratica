"""Windows 0.8.14: clinical and expense modules synthetic end-to-end tests."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shared.python.saude_backup import read_backup
from windows import secure_store
from windows.clinical_expenses_v088 import (
    CLINICAL_TYPES, CLINICAL_STATES, EXPENSE_TYPES, TAX_STATES,
    date_iso, cents_from_pt, euro_text, annual_summary,
)


CLINICAL = {
    "title": "Exame fictício de medicina do trabalho",
    "date": "04/11/2026",
    "category": "Medicina do Trabalho",
    "status": "Em acompanhamento",
    "unit": "Unidade de demonstração",
    "professional": "Profissional fictício",
    "description": "Observação apenas de teste.",
    "next_date": "2026-12-04",
    "document_sha256": "",
}
EXPENSE = {
    "date": "03/11/2026",
    "category": "Consulta",
    "merchant": "Prestador fictício",
    "description": "Despesa sintética",
    "receiptNumber": "FT2026-01",
    "supplierNif": "123456789",
    "amountCents": 3333,
    "reimbursedCents": 1000,
    "taxStatus": "Por verificar",
    "notes": "Não é uma fatura real.",
    "document_sha256": "",
}


class NumericTests(unittest.TestCase):
    def test_currency_in_cents_no_float(self):
        self.assertEqual(cents_from_pt("1.234,50 €"),123450)
        self.assertEqual(cents_from_pt("1234.50"),123450)
        self.assertEqual(cents_from_pt("0,01"),1)
        self.assertEqual(euro_text(123450),"1.234,50 €")
        self.assertEqual(euro_text(1),"0,01 €")
        for val in ("-1", "0,001", "NaN", "Infinity", "10e100", "100000001"):
            with self.subTest(val=val),self.assertRaises(ValueError):
                cents_from_pt(val)

    def test_dates_validated_and_android_expense_categories_retained(self):
        self.assertEqual(date_iso("04/11/2026"),"2026-11-04")
        self.assertEqual(date_iso("2026-11-04"),"2026-11-04")
        with self.assertRaises(ValueError):
            date_iso("31/02/2026")
        self.assertIn("Medicina do Trabalho",CLINICAL_TYPES)
        self.assertIn("Por avaliar",CLINICAL_STATES)
        self.assertIn("Óculos / Lentes",EXPENSE_TYPES)
        self.assertIn("Pendente no e-Fatura",TAX_STATES)

    def test_annual_totals(self):
        entries=[dict(EXPENSE,date="2026-11-03"),
                 dict(EXPENSE,date="2025-11-03"),
                 dict(EXPENSE,date="2026-12-01",amountCents=100, reimbursedCents=0)]
        a=annual_summary(entries,2026)
        self.assertEqual(a["count"],2)
        self.assertEqual(a["amountCents"],3433)
        self.assertEqual(a["reimbursedCents"],1000)
        self.assertEqual(a["remainingCents"],2433)


class ProfileRecordsTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        mocks=[
            patch.object(secure_store,"_user_data_path",
                         return_value=Path(self.dir.name)/"store.dpapi"),
            patch.object(secure_store,"_encrypt",side_effect=lambda x:x),
            patch.object(secure_store,"_decrypt",side_effect=lambda x:x),
        ]
        for each in mocks:
            each.start()
            self.addCleanup(each.stop)
        self.store=secure_store.SecureStore()
        self.person_a=self.store.create_profile("Pessoa A fictícia")
        self.person_b=self.store.create_profile("Pessoa B fictícia")

    def test_save_edit_delete_clinical_and_expense_without_profile_leaks(self):
        a=self.person_a["id"]
        b=self.person_b["id"]
        c=self.store.save_health_record(a,"clinical",CLINICAL)
        e=self.store.save_health_record(a,"expenses",EXPENSE)
        self.assertEqual(self.store.health_records(b,"clinical"),[])
        self.assertEqual(self.store.health_records(b,"expenses"),[])
        self.assertEqual(self.store.health_records(a,"clinical")[0]["title"],CLINICAL["title"])
        self.assertEqual(self.store.health_records(a,"expenses")[0]["amountCents"],3333)
        self.assertEqual(c["date"],"2026-11-04")
        self.assertEqual(e["date"],"2026-11-03")
        with self.assertRaises(secure_store.LocalStoreError):
            self.store.save_health_record(b,"clinical",CLINICAL,c["id"])
        with self.assertRaises(secure_store.LocalStoreError):
            self.store.delete_health_record(b,"expenses",e["id"])
        edited=self.store.save_health_record(
            a,"expenses",dict(EXPENSE,amountCents=5032),e["id"])
        self.assertEqual(edited["id"],e["id"])
        self.assertEqual(len(self.store.health_records(a,"expenses")),1)
        self.assertEqual(self.store.health_records(a,"expenses")[0]["amountCents"],5032)
        self.store.delete_health_record(a,"clinical",c["id"])
        self.assertEqual(self.store.health_records(a,"clinical"),[])
        self.assertEqual(len(self.store.health_records(a,"expenses")),1)

    def test_invalid_dates_amounts_and_statuses_do_not_mutate(self):
        a=self.person_a["id"]
        for wrong in (
            dict(CLINICAL,date="32/11/2026"),
            dict(CLINICAL,category="Diagnóstico automático"),
            dict(CLINICAL,title=""),
            dict(CLINICAL,next_date="2026-02-31"),
        ):
            with self.subTest(wrong=wrong),self.assertRaises(secure_store.LocalStoreError):
                self.store.save_health_record(a,"clinical",wrong)
        for wrong in (
            dict(EXPENSE,date="2026-02-30"),
            dict(EXPENSE,amountCents=3.5),
            dict(EXPENSE,reimbursedCents=True),
            dict(EXPENSE,taxStatus="IRS garantido"),
        ):
            with self.subTest(wrong=wrong),self.assertRaises(secure_store.LocalStoreError):
                self.store.save_health_record(a,"expenses",wrong)
        self.assertEqual(self.store.health_records(a,"clinical"),[])
        self.assertEqual(self.store.health_records(a,"expenses"),[])

    def test_attachment_rejects_other_profiles(self):
        a=self.person_a["id"]
        b=self.person_b["id"]
        hashval="a"*64
        self.store.data["imported_files"]=[{
            "profile_id":b,"sha256":hashval,
            "filename":"ficticio.pdf","display_name":"Documento fictício"}]
        with self.assertRaises(secure_store.LocalStoreError):
            self.store.save_health_record(a,"clinical",
                dict(CLINICAL,document_sha256=hashval))
        self.store.save_health_record(b,"clinical",
            dict(CLINICAL,document_sha256=hashval))
        self.assertEqual(self.store.health_records(a,"clinical"),[])
        self.assertEqual(self.store.health_records(b,"clinical")[0]["document_sha256"],hashval)

    def test_backup_roundtrip_preserves_records_and_original_medications(self):
        a=self.person_a["id"]
        self.store.add_medication(a,"Comprimido de teste","1 mg","08:00","oral")
        self.store.save_health_record(a,"clinical",CLINICAL)
        self.store.save_health_record(a,"expenses",EXPENSE)
        encrypted=self.store.export_backup("apenas-para-teste-2026")
        files=read_backup(encrypted,"apenas-para-teste-2026")
        metadata=json.loads(files[f"profiles/{a}/profile.json"])
        self.assertEqual(metadata["clinical_records"][0]["category"],
                         "Medicina do Trabalho")
        self.assertEqual(metadata["health_expenses"][0]["amountCents"],3333)
        self.assertNotIn("clinical_records",json.loads(
            files[f"profiles/{self.person_b['id']}/profile.json"]))
        with tempfile.TemporaryDirectory() as dest:
            with patch.object(secure_store,"_user_data_path",
                              return_value=Path(dest)/"new.dpapi"):
                receiver=secure_store.SecureStore()
                self.assertEqual(receiver.restore_backup(files),2)
                self.assertEqual(receiver.health_records(a,"expenses")[0]["amountCents"],3333)
                self.assertEqual(receiver.health_records(a,"clinical")[0]["title"],CLINICAL["title"])
                self.assertEqual(len(receiver.get_profile(a)["medications"]),1)

    def test_save_failure_rolls_back_all_persisted_data(self):
        a=self.person_a["id"]
        with patch.object(self.store,"save",side_effect=OSError("fake write fail")):
            with self.assertRaises(OSError):
                self.store.save_health_record(a,"clinical",CLINICAL)
        self.assertEqual(self.store.health_records(a,"clinical"),[])
        self.store.save_health_record(a,"clinical",CLINICAL)
        self.assertEqual(len(secure_store.SecureStore().health_records(a,"clinical")),1)


class GuiContractTests(unittest.TestCase):
    def test_modules_are_real_and_isolated(self):
        from windows.ui_catalog_v05 import MODULE_CARDS
        flags={k:enabled for k,icon,title,description,enabled in MODULE_CARDS}
        self.assertTrue(flags["clinical"])
        self.assertTrue(flags["expenses"])
        for key in ("water","activity","cycle"):
            self.assertTrue(flags[key])
        for key in ("nutrition","vision","symptoms",
                    "vaccines","emergency","pharmacy","residences"):
            self.assertTrue(flags[key])

    def test_real_forms_and_plaintext_disclosures(self):
        source=(Path(__file__).resolve().parents[1]/
                "health_records_ui_v088.py").read_text("utf-8")
        desktop=(Path(__file__).resolve().parents[1]/
                 "desktop_v04.py").read_text("utf-8")
        self.assertIn('VERSION = "0.8.19"',desktop)
        self.assertIn('self.page=="clinical"',desktop)
        self.assertIn('self.page=="expenses"',desktop)
        self.assertIn("self.store.health_records(person[\"id\"],kind)",source)
        self.assertIn("self.store.save_health_record(",source)
        self.assertIn("self.store.delete_health_record(",source)
        self.assertIn("self.store.imported_assets(profile_id)",source)
        self.assertIn("CSV contém informação pessoal",source)


if __name__=="__main__":
    unittest.main()
