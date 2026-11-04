"""Windows 0.8.13: original Android data really populates Windows after restore.

All test patients, meals, images and doses are synthesized. Real family backup
never leaves the user's machine or enters this repository/CI.
"""
from __future__ import annotations

from datetime import datetime,date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZipFile,ZIP_DEFLATED

from PIL import Image

from windows import secure_store
from windows.android_full_restore_v0813 import extract_profile_android,merge_snapshot
from windows.doses_calendar_v085 import dose_entries
from shared.python.saude_backup import create_backup,read_backup

PASSWORD="senha-sintetica-do-teste"


def typed(values):
    result={}
    for key,value in values.items():
        if isinstance(value,int) and not isinstance(value,bool):
            result[key]={"t":"i","v":value}
        elif isinstance(value,list):
            result[key]={"t":"set","v":value}
        else:
            result[key]={"t":"s","v":value}
    return result


def make_jpg():
    out=BytesIO()
    Image.new("RGB",(32,26),(20,105,95)).save(out,format="JPEG")
    return out.getvalue()


def android_original(daniel,camily,native_mid,photo_id):
    now=date.today()
    scheduled=datetime.combine(now,datetime.min.time()).replace(hour=7)
    ms=int(scheduled.timestamp()*1000)
    meal={"id":photo_id,"at":ms,"meal":"Almoço fictício",
          "foods":"Prato de teste","kcal":200,"protein_g":12,
          "carbs_g":20,"fat_g":7,"note":"ficção",
          "photo":photo_id+".jpg"}
    rows=[
        {"id":str(uuid4()),"kind":"intakes","timestamp":ms+1600,
         "title":"Toma de teste","fields":{
             "medication_id":native_mid,"scheduled_at":str(ms),
             "source":"manual"}},
        {"id":str(uuid4()),"kind":"symptoms","timestamp":ms+3200,
         "title":"Sintoma fictício","fields":{
             "tipo":"Sintoma","severity":"4","details":"Detalhe sintético"}},
        {"id":str(uuid4()),"kind":"measurements","timestamp":ms+4800,
         "title":"Medição fictícia","fields":{
             "value":"42","unidade":"un","notes":"teste"}},
    ]
    files={
        f"saudepratica_meal_diary/{daniel}/meals.json":
            json.dumps([meal]).encode(),
        f"saudepratica_meal_diary/{daniel}/{photo_id}.jpg":make_jpg(),
        f"saudepratica_health/{daniel}/records.json":
            json.dumps(rows).encode(),
    }
    prefs={
        f"saudepratica_wellness_{daniel}":typed({
            "water_logged_date":now.isoformat(),
            "water_logged_ml":900,
            "water_glass_ml":180,"water_target_ml":800,
        }),
        f"saudepratica_emergency_{daniel}":typed({
            "contact_name":"Contacto fictício","contact_phone":"+351 210 000 000"
        }),
        f"saudepratica_care_home_v1_{camily}":typed({
            "institution":"Lar sintético Camy","valence":"ERPI",
            "address":"Morada imaginária","phone":"+351 220 000 000",
        }),
        "saudepratica_care_home_institution_v2":typed({
            "residents":[camily],"institution":"Instituição fictícia geral",
        }),
        "saudepratica_caregiver_v1":typed({"caregiver_id":daniel}),
    }
    records=[{"path":path,"size":len(raw),
              "sha256":sha256(raw).hexdigest()} for path,raw in files.items()]
    manifest={"kind":"saudepratica-complete-backup","format":1,
              "prefs":prefs,"files":records}
    bio=BytesIO()
    with ZipFile(bio,"w",ZIP_DEFLATED) as z:
        z.writestr("backup.json",json.dumps(manifest))
        for path,raw in files.items():
            z.writestr("data/"+path,raw)
    return bio.getvalue()


def portable_backup(source,daniel,camily,native_med):
    digest=sha256(source).hexdigest()
    archive={
        "sha256":digest,"bytes":len(source),
        "filename":"original-android.zip",
        "profile_ids":[daniel,camily],
        "source_ids":[daniel,camily],
    }
    files={f"attachments/{digest[:2]}/{digest}.bin":source}
    for pid,name in ((daniel,"Daniel teste"),(camily,"Camy teste")):
        profile={"id":pid,"name":name,"android_zip_source_id":pid}
        meds=[{"id":str(uuid4()),"name":"Medicamento fictício",
               "dose":"1 mg","time":"07:00","reminder_time":"07:00",
               "repeat_mode":"daily",
               "android_source_id":native_med,
               "no_alarm":False}] if pid==daniel else []
        prefix=f"profiles/{pid}/"
        files.update({
            prefix+"profile.json":json.dumps(profile).encode(),
            prefix+"medicacao.json":json.dumps({"medications":meds}).encode(),
            prefix+"agenda.json":b'{"appointments":[]}',
            prefix+"android_archives.json":json.dumps([archive]).encode(),
            prefix+"attachments.json":b"[]",
            prefix+"backup_scope.json":json.dumps({
                "scope":"family","format":2,"profile_count":2}).encode(),
        })
    return create_backup(files,PASSWORD)


class BridgeModelTests(unittest.TestCase):
    def setUp(self):
        self.daniel=str(uuid4())
        self.camy=str(uuid4())
        self.medication=str(uuid4())
        self.photo=str(uuid4())
        self.original=android_original(
            self.daniel,self.camy,self.medication,self.photo)

    def test_converts_actual_water_meals_photos_symptoms_intakes_sos(self):
        d=extract_profile_android(self.original,self.daniel)
        c=extract_profile_android(self.original,self.camy)
        self.assertEqual(len(d["meals"]),1)
        self.assertEqual(len(d["meal_photos"]),1)
        self.assertEqual(d["water"]["entries"][0]["ml"],900)
        self.assertEqual(d["water"]["entries"][0]["time"],"")
        self.assertEqual(d["water"]["settings"]["target_ml"],800)
        self.assertEqual(len(d["symptoms"]),1)
        self.assertEqual(len(d["measurements"]),1)
        self.assertEqual(len(d["intakes"]),1)
        self.assertEqual(d["sos"]["contact_name"],"Contacto fictício")
        self.assertEqual(len(d["residences"]),0)
        self.assertEqual(len(c["meals"]),0)
        self.assertEqual(len(c["intakes"]),0)
        self.assertEqual(len(c["residences"]),1)
        self.assertEqual(d["caregiver_source"],self.daniel)
        self.assertIn(self.camy,d["resident_sources"])

    def test_mapping_is_additive_and_deduplicated(self):
        med={"id":str(uuid4()),"name":"Medicamento fictício",
             "android_source_id":self.medication}
        profile={"id":self.daniel,"android_zip_source_id":self.daniel,
                 "medications":[med],"appointments":[],
                 "wellness_water":{"settings":{
                     "glass_ml":250,"target_ml":1200,
                     "water_start":"09:00","water_end":"20:00",
                     "water_interval":120},"entries":[]},
                 "emergency_contact_data":{"contact_name":"Contacto Windows"}}
        selected=extract_profile_android(self.original,self.daniel)
        mapping={self.daniel:self.daniel,self.camy:self.camy}
        descriptors,assets,counts=merge_snapshot(profile,selected,mapping,[])
        self.assertEqual(counts["intakes"],1)
        self.assertEqual(counts["water"],1)
        self.assertEqual(counts["symptoms"],1)
        self.assertEqual(profile["wellness_water"]["settings"]["target_ml"],1200)
        self.assertEqual(profile["emergency_contact_data"]["contact_name"],
                         "Contacto Windows")
        self.assertEqual(profile["care_home_residents"],[self.camy])
        self.assertEqual(len(descriptors),1)
        self.assertEqual(len(assets),1)
        self.assertEqual(len(profile["intakes"]),1)
        self.assertEqual(profile["intakes"][0]["medication_id"],med["id"])
        again=merge_snapshot(profile,selected,mapping,descriptors)
        self.assertEqual(sum(again[2].values()),0)
        self.assertEqual(len(profile["intakes"]),1)

    def test_reject_unknown_profile_and_source(self):
        d=extract_profile_android(self.original,self.daniel)
        with self.assertRaises(ValueError):
            merge_snapshot({"id":self.camy,
                            "android_zip_source_id":self.camy},d,{},[])
        with self.assertRaises(ValueError):
            extract_profile_android(self.original,"../evil")


class RealPortableRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for mock in (
            patch.object(secure_store,"_user_data_path",
                         return_value=Path(self.temp.name)/"data.dpapi"),
            patch.object(secure_store,"_encrypt",side_effect=lambda p:p),
            patch.object(secure_store,"_decrypt",side_effect=lambda p:p),
        ):
            mock.start()
            self.addCleanup(mock.stop)
        self.store=secure_store.SecureStore()
        self.daniel=str(uuid4())
        self.camy=str(uuid4())
        self.med=str(uuid4())
        self.photo=str(uuid4())
        self.android=android_original(
            self.daniel,self.camy,self.med,self.photo)
        self.encrypted=portable_backup(
            self.android,self.daniel,self.camy,self.med)

    def restore(self):
        plan=self.store.inspect_portable_backup(self.encrypted,PASSWORD)
        return self.store.restore_portable_backup(plan,PASSWORD)

    def test_restore_new_profiles_populates_all_modules_correctly(self):
        result=self.restore()
        self.assertEqual(result["profiles"],2)
        self.assertEqual(result["created"],2)
        counts=result["android_modules"]
        for k in ("water","meals","meal_photos","symptoms","intakes",
                  "measurements","sos","residences"):
            self.assertGreater(counts[k],0,k)
        d=self.store.get_profile(self.daniel)
        c=self.store.get_profile(self.camy)
        self.assertTrue(d["caregiver"])
        self.assertEqual(d["care_home_residents"],[self.camy])
        self.assertTrue(c["care_home_resident"])
        self.assertEqual(len(self.store.meal_records(self.daniel)),1)
        meal=self.store.meal_records(self.daniel)[0]
        self.assertEqual(self.store.meal_photo(self.daniel,meal["id"]),
                         make_jpg())
        self.assertEqual(len(self.store.remaining_records(self.daniel,"symptoms")),1)
        self.assertEqual(len(self.store.remaining_records(self.camy,"symptoms")),0)
        self.assertEqual(len(self.store.remaining_records(self.camy,"residences")),1)
        self.assertEqual(self.store.remaining_records(self.daniel,"residences"),[])
        self.assertEqual(self.store.wellness_data(self.daniel,"water")["entries"][0]["ml"],900)
        self.assertEqual(self.store.emergency_data(self.daniel)["contact_name"],
                         "Contacto fictício")
        today=date.today()
        doses=dose_entries(d,today,now=datetime.combine(today,datetime.min.time()).replace(hour=9))
        self.assertTrue(any(x.get("status")=="confirmed" for x in doses),doses)

    def test_repeat_restore_does_not_erase_extra_windows_modules(self):
        self.restore()
        d=self.store.get_profile(self.daniel)
        d["clinical_records"]=[{"id":str(uuid4()),"title":"Extra sintético",
                                "date":date.today().isoformat()}]
        self.store.save()
        counts_before={
            "meal":len(d["meal_records"]),
            "intakes":len(d["intakes"]),
            "symptoms":len(d["symptom_records"]),
        }
        result=self.restore()
        self.assertEqual(result["replaced"],2)
        self.assertTrue(result["recovery"])
        d=self.store.get_profile(self.daniel)
        self.assertEqual(len(d["clinical_records"]),1)
        self.assertEqual(counts_before["meal"],len(d["meal_records"]))
        self.assertEqual(counts_before["intakes"],len(d["intakes"]))
        self.assertEqual(counts_before["symptoms"],len(d["symptom_records"]))
        self.assertEqual(result["android_modules"]["intakes"],0)
        self.assertEqual(result["android_modules"]["meals"],0)

    def test_recover_from_existing_stored_archives_is_idempotent(self):
        self.restore()
        d=self.store.get_profile(self.daniel)
        d.pop("meal_records",None)
        d.pop("wellness_water",None)
        d.pop("intakes",None)
        d.pop("emergency_contact_data",None)
        c=self.store.get_profile(self.camy)
        c.pop("residence_records",None)
        self.store.save()
        result=self.store.recover_android_modules()
        self.assertEqual(result["profiles"],2)
        self.assertGreater(result["android_modules"]["intakes"],0)
        self.assertGreater(result["android_modules"]["water"],0)
        self.assertGreater(result["android_modules"]["residences"],0)
        next_run=self.store.recover_android_modules()
        self.assertEqual(sum(next_run["android_modules"].values()),0)

    def test_safety_rollback_on_write_failure(self):
        self.restore()
        self.store.get_profile(self.daniel).pop("symptom_records")
        self.store.save()
        before=json.dumps(self.store.data,sort_keys=True)
        with patch.object(self.store,"save",side_effect=OSError("fake disk error")):
            with self.assertRaises(OSError):
                self.store.recover_android_modules()
        self.assertEqual(json.dumps(self.store.data,sort_keys=True),before)

    def test_preserved_restored_backup_keeps_original_and_photos(self):
        self.restore()
        exported=self.store.export_backup(PASSWORD)
        files=read_backup(exported,PASSWORD)
        profile=json.loads(files[f"profiles/{self.daniel}/profile.json"])
        self.assertEqual(len(profile["meal_records"]),1)
        self.assertEqual(len(profile["intakes"]),1)
        self.assertEqual(len(profile["symptom_records"]),1)
        self.assertEqual(files[
            "attachments/"+sha256(self.android).hexdigest()[:2]+"/"+
            sha256(self.android).hexdigest()+".bin"],self.android)


if __name__=="__main__":
    unittest.main()
