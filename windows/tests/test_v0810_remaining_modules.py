"""Windows 0.8.14: confidential seven-module records and Android food photos.

Only synthetic profiles and meal images; no personal uploads.
"""
from __future__ import annotations
import json
import tempfile
import unittest
from datetime import date,datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZipFile,ZIP_DEFLATED

from PIL import Image
from windows import secure_store
from windows.remaining_models_v0810 import (
    SCHEMAS,EMERGENCY_FIELDS,validate_record,validate_meal,
    validate_emergency,safe_money,text_money,
)
from windows.meal_android_import_v0810 import extract_meal_diary
from shared.python.saude_backup import read_backup

TODAY=date.today().isoformat()
UUID_A=str(uuid4())
UUID_B=str(uuid4())


def example(kind):
    samples={
        "vision":{"date":TODAY,"title":"Receita visual fictícia",
                  "right_sphere":"-1,25","left_sphere":"+0,50","right_axis":"90"},
        "symptoms":{"date":TODAY,"title":"Sintoma fictício",
                    "type":"Sintoma","severity":"4","details":"Registo de teste"},
        "vaccines":{"title":"Vacina fictícia","date":TODAY,"next":""},
        "pharmacy":{"title":"Farmácia fictícia",
                    "phone":"+351 210 000 000","website":"https://example.org"},
        "residences":{"title":"Instituição de teste","type":"ERPI",
                      "address":"Morada sintética"},
        "residence_invoices":{"title":"Instituição de teste",
                              "date":TODAY,"status":"Recebida",
                              "amount":"1250,25","paid":"1250,25",
                              "reimbursed":"0,00"},
        "supports":{"title":"Pedido de teste","date":TODAY,
                    "type":"ADSE","status":"Em preparação"},
    }
    return samples[kind]


def jpeg():
    buf=BytesIO()
    Image.new("RGB",(30,25),(0,95,120)).save(buf,format="JPEG")
    return buf.getvalue()


def family_zip(source_a,source_b):
    files={}
    for source, name in ((source_a,"Almoço sintético A"),
                         (source_b,"Refeição sintética B")):
        mid=str(uuid4())
        row={"id":mid,"at":int(datetime.now().timestamp()*1000),
             "meal":name,"foods":"Arroz 200 g","kcal":335.0,
             "protein_g":6.0,"carbs_g":67.0,"fat_g":3.0,"estimated":True,
             "note":"apenas teste","photo":mid+".jpg"}
        prefix=f"saudepratica_meal_diary/{source}/"
        files[prefix+"meals.json"]=json.dumps([row]).encode("utf-8")
        files[prefix+mid+".jpg"]=jpeg()
    manifest=[{"path":path,"size":len(value),"sha256":sha256(value).hexdigest()}
              for path,value in files.items()]
    head={"kind":"saudepratica-complete-backup","format":1,
          "files":manifest,"prefs":{}}
    buffer=BytesIO()
    with ZipFile(buffer,"w",compression=ZIP_DEFLATED) as z:
        z.writestr("backup.json",json.dumps(head).encode())
        for path,value in files.items():z.writestr("data/"+path,value)
    return buffer.getvalue()


class ModelTests(unittest.TestCase):
    def test_seven_schemas_are_typed_and_no_fake_status(self):
        self.assertEqual(len(SCHEMAS),7)
        for kind in SCHEMAS:
            with self.subTest(kind=kind):
                row=validate_record(kind,example(kind))
                self.assertTrue(row["title"])
                if kind=="residence_invoices":
                    self.assertEqual(row["amount_cents"],125025)
                    self.assertEqual(row["paid_cents"],125025)
        self.assertEqual(safe_money("1234,50"),123450)
        self.assertEqual(text_money(123450),"1234,50")
        with self.assertRaises(ValueError):
            validate_record("symptoms",dict(example("symptoms"),severity="20"))
        with self.assertRaises(ValueError):
            validate_record("vaccines",dict(example("vaccines"),date="31/02/2026"))
        with self.assertRaises(ValueError):
            validate_record("pharmacy",dict(example("pharmacy"),website="file:///C:/temp"))
        with self.assertRaises(ValueError):
            validate_record("vision",dict(example("vision"),right_axis="181"))
        with self.assertRaises(ValueError):
            validate_record("residence_invoices",dict(example("residence_invoices"),amount="-100,00"))
        with self.assertRaises(ValueError):
            validate_emergency({"contact_phone":"javascript:1"})

    def test_meals_reject_fabricated_estimates(self):
        row=validate_meal({"meal":"Almoço","foods":"Salada","kcal":250,
                           "protein_g":8,"carbs_g":18,"fat_g":12})
        self.assertEqual(row["kcal"],250.0)
        with self.assertRaises(ValueError):
            validate_meal({"foods":"","kcal":400})
        with self.assertRaises(ValueError):
            validate_meal({"foods":"X","kcal":"NaN"})


class ProfileStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for mock in (
            patch.object(secure_store,"_user_data_path",
                         return_value=Path(self.temp.name)/"records.dpapi"),
            patch.object(secure_store,"_encrypt",side_effect=lambda x:x),
            patch.object(secure_store,"_decrypt",side_effect=lambda x:x),
        ):
            mock.start()
            self.addCleanup(mock.stop)
        self.s=secure_store.SecureStore()
        self.a=self.s.create_profile("Pessoa A de teste")["id"]
        self.b=self.s.create_profile("Pessoa B de teste")["id"]

    def test_all_seven_modules_are_profile_scoped_and_editable(self):
        saved={}
        for kind in SCHEMAS:
            with self.subTest(kind=kind):
                row=self.s.save_remaining_record(self.a,kind,example(kind))
                saved[kind]=row
                self.assertEqual(len(self.s.remaining_records(self.a,kind)),1)
                self.assertEqual(self.s.remaining_records(self.b,kind),[])
                with self.assertRaises(secure_store.LocalStoreError):
                    self.s.save_remaining_record(self.b,kind,example(kind),row["id"])
                with self.assertRaises(secure_store.LocalStoreError):
                    self.s.delete_remaining_record(self.b,kind,row["id"])
                edited=self.s.save_remaining_record(
                    self.a,kind,dict(example(kind),title="Registo editado"),
                    row["id"])
                self.assertEqual(edited["id"],row["id"])
                self.assertEqual(edited["title"],"Registo editado")
        for kind,row in saved.items():
            self.s.delete_remaining_record(self.a,kind,row["id"])
            self.assertEqual(self.s.remaining_records(self.a,kind),[])

    def test_emergency_and_meal_photo_are_private_and_backup_safe(self):
        emergency=self.s.save_emergency_data(self.a,
                    {"contact_name":"Pessoa fictícia",
                     "contact_phone":"+351 219 000 000",
                     "allergies":"Apenas teste",
                     "chronic_conditions":"Não há dados de teste"})
        self.assertEqual(emergency["contact_name"],"Pessoa fictícia")
        self.assertEqual(self.s.emergency_data(self.b)["contact_name"],"")
        image=jpeg()
        meal=self.s.save_meal(
            self.a,{"date":TODAY,"clock":"13:15","meal":"Almoço",
                    "foods":"Massa 200 g","kcal":"440,5",
                    "protein_g":"20","carbs_g":"60","fat_g":"10","note":""},
            picture=image)
        self.assertEqual(self.s.meal_photo(self.a,meal["id"]),image)
        with self.assertRaises(secure_store.LocalStoreError):
            self.s.meal_photo(self.b,meal["id"])
        with self.assertRaises(secure_store.LocalStoreError):
            self.s.save_meal(self.b,{"date":TODAY,"clock":"13:15",
                "foods":"Outro prato","kcal":500},meal["id"])
        blob=self.s.export_backup("password-for-synthetic-test")
        files=read_backup(blob,"password-for-synthetic-test")
        profile=json.loads(files[f"profiles/{self.a}/profile.json"])
        self.assertEqual(profile["emergency_contact_data"]["contact_name"],"Pessoa fictícia")
        self.assertEqual(profile["meal_records"][0]["foods"],"Massa 200 g")
        digest=sha256(image).hexdigest()
        self.assertEqual(files["attachments/"+digest[:2]+"/"+digest+".bin"],image)

    def test_android_photo_import_is_exact_and_idempotent(self):
        source_a=str(uuid4())
        source_b=str(uuid4())
        original=family_zip(source_a,source_b)
        records,photos=extract_meal_diary(original,source_a)
        self.assertEqual(len(records),1)
        self.assertEqual(len(photos),1)
        self.assertEqual(records[0]["meal"],"Almoço sintético A")
        self.assertEqual(records[0]["source"],"android")
        digest=sha256(original).hexdigest()
        self.s._write_assets([(digest,original)])
        self.s.get_profile(self.a)["android_zip_source_id"]=source_a
        self.s.get_profile(self.b)["android_zip_source_id"]=source_b
        self.s.data["android_family_archives"]=[{
            "sha256":digest,"profile_ids":[self.a,self.b],
            "source_ids":[source_a,source_b],"bytes":len(original)
        }]
        self.s.save()
        result=self.s.import_meal_diary_android(self.a)
        self.assertEqual(result["added"],1)
        self.assertEqual(result["photos"],1)
        rows=self.s.meal_records(self.a)
        self.assertEqual(rows[0]["meal"],"Almoço sintético A")
        self.assertEqual(self.s.meal_photo(self.a,rows[0]["id"]),jpeg())
        self.assertEqual(self.s.import_meal_diary_android(self.a)["added"],0)
        self.assertEqual(self.s.meal_records(self.b),[])
        result_b=self.s.import_meal_diary_android(self.b)
        self.assertEqual(result_b["added"],1)
        self.assertEqual(self.s.meal_records(self.b)[0]["meal"],"Refeição sintética B")
        self.assertEqual(len(self.s.meal_records(self.a)),1)
        # Family backup (not profile backup) is needed for the shared source ZIP.
        with self.assertRaises(secure_store.LocalStoreError):
            self.s.export_backup("synthetic",profile_id=self.a)

    def test_write_failure_rolls_back_new_record(self):
        with patch.object(self.s,"save",side_effect=OSError("synthetic failure")):
            with self.assertRaises(OSError):
                self.s.save_remaining_record(self.a,"vision",example("vision"))
        self.assertEqual(self.s.remaining_records(self.a,"vision"),[])

class GuiContractTests(unittest.TestCase):
    def test_all_cards_and_routes_active(self):
        from windows.ui_catalog_v05 import MODULE_CARDS
        flags={key:active for key,icon,title,sub,active in MODULE_CARDS}
        for key in ("nutrition","vision","symptoms","vaccines","emergency",
                    "pharmacy","residences"):
            self.assertTrue(flags[key],key)
        code=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text("utf-8")
        self.assertIn('VERSION = "0.8.16"',code)
        for key in ("nutrition","vision","symptoms","vaccines",
                    "emergency","pharmacy","residences"):
            self.assertIn(f'self.page=="{key}"',code)
        self.assertIn("self._nutrition_photo_draft",code)
    def test_no_auto_emergency_contact_or_claims(self):
        ui=(Path(__file__).resolve().parents[1]/
            "remaining_ui_v0810.py").read_text("utf-8")
        self.assertIn("messagebox.askyesno",ui)
        self.assertIn('lambda:self._open_phone("112")',ui)
        self.assertIn("self.store.remaining_records(profile[\"id\"],kind)",ui)
        self.assertNotIn("requests.post(",ui)

if __name__=="__main__":
    unittest.main()
