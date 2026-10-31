"""Synthetic-only tests: no real patient data or Android files in CI."""
import io
import json
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from windows.android_import_v062 import (
    plan_json,apply_plan,inspect_android_zip,AndroidImportError)

class FakeStore:
    def __init__(self):
        self.profile={"id":"11111111-1111-4111-8111-111111111111",
                      "name":"Pessoa fictícia","medications":[],"appointments":[]}
        self.saves=0
        self.fail=False
    def get_profile(self,id):
        return self.profile if id==self.profile["id"] else None
    def save(self):
        if self.fail:raise OSError("disk error")
        self.saves+=1

class AndroidJsonImportTests(unittest.TestCase):
    def setUp(self):self.store=FakeStore()
    def payload(self,key,items):
        return json.dumps({key:items},ensure_ascii=False).encode()

    def test_medication_import_add_only_preserves_extra_fields(self):
        b=self.payload("medications",[{"id":"android-m1","name":"Medicamento fictício",
             "dose":"10 mg","times":["07:00","19:00"],"images":["blister.jpg"],
             "android_schedule_metadata":{"frequency":"12h"}}])
        plan=plan_json(b,"medications",self.store.profile)
        self.assertEqual(len(plan.new),1)
        self.assertEqual(self.store.saves,0)
        self.assertEqual(apply_plan(self.store,plan),1)
        m=self.store.profile["medications"][0]
        self.assertEqual(m["time"],"07:00")
        self.assertEqual(m["times"],["07:00","19:00"])
        self.assertEqual(m["images"],["blister.jpg"])
        self.assertFalse(m["no_alarm"])  # preserve Android original, Windows never schedules alarms
        self.assertEqual(m["android_original"]["times"],["07:00","19:00"])
        self.assertEqual(self.store.saves,1)
        second=plan_json(b,"medications",self.store.profile)
        self.assertEqual(len(second.new),0)
        self.assertEqual(second.repeated,1)
        self.assertEqual(apply_plan(self.store,second),0)

    def test_agenda_import_no_clinical_fields_lost(self):
        b=self.payload("appointments",[{"id":"apt-1","title":"Consulta fictícia",
          "date":"2026-11-10","time":"10:30","location":"Hospital de teste",
          "cancelled":False,"custom_field":{"code":17}}])
        plan=plan_json(b,"appointments",self.store.profile)
        self.assertEqual(apply_plan(self.store,plan),1)
        a=self.store.profile["appointments"][0]
        self.assertEqual(a["title"],"Consulta fictícia")
        self.assertEqual(a["location"],"Hospital de teste")
        self.assertEqual(a["custom_field"],{"code":17})

    def test_wrong_json_type_rejected(self):
        b=self.payload("appointments",[])
        with self.assertRaises(AndroidImportError):
            plan_json(b,"medications",self.store.profile)
        with self.assertRaises(AndroidImportError):
            plan_json(b"not json","appointments",self.store.profile)
        with self.assertRaises(AndroidImportError):
            plan_json(self.payload("medications",[{"id":"1","dose":"10mg"}]),
                      "medications",self.store.profile)

    def test_duplicate_id_in_file_rejected(self):
        b=self.payload("medications",[{"id":"x","name":"A"},{"id":"x","name":"B"}])
        with self.assertRaises(AndroidImportError):
            plan_json(b,"medications",self.store.profile)

    def test_changed_existing_medication_has_conflict_not_silent_overwrite(self):
        old=self.payload("medications",[{"id":"x","name":"Comprimido teste","dose":"10"}])
        changed=self.payload("medications",[{"id":"x","name":"Comprimido teste","dose":"20"}])
        apply_plan(self.store,plan_json(old,"medications",self.store.profile))
        with self.assertRaises(AndroidImportError):
            plan_json(changed,"medications",self.store.profile)
        self.assertEqual(len(self.store.profile["medications"]),1)

    def test_stale_plan_cannot_overwrite(self):
        b=self.payload("medications",[{"id":"x","name":"A"}])
        plan=plan_json(b,"medications",self.store.profile)
        self.assertEqual(apply_plan(self.store,plan),1)
        with self.assertRaises(AndroidImportError):
            apply_plan(self.store,plan)

    def test_atomic_rollback_on_storage_failure(self):
        b=self.payload("appointments",[{"id":"a","title":"Consulta de teste"}])
        plan=plan_json(b,"appointments",self.store.profile)
        self.store.fail=True
        with self.assertRaises(OSError): apply_plan(self.store,plan)
        self.assertEqual(self.store.profile["appointments"],[])

    def test_zip_read_only_inspection_and_traversal_block(self):
        output=io.BytesIO()
        with ZipFile(output,"w") as z:
            z.writestr("saudepratica_profiles/test/medicacao.json",'{"medications":[]}')
            z.writestr("saudepratica_profiles/test/agenda.json",'{"appointments":[]}')
        info=inspect_android_zip(output.getvalue())
        self.assertEqual(info["medications"],1)
        self.assertEqual(info["appointments"],1)
        output=io.BytesIO()
        with ZipFile(output,"w") as z:z.writestr("../secrets.txt","unsafe")
        with self.assertRaises(AndroidImportError):inspect_android_zip(output.getvalue())

    def test_full_page_ui_and_no_search_field(self):
        desktop=(ROOT/"windows/desktop_v04.py").read_text(encoding="utf-8")
        dashboard=(ROOT/"windows/dashboard_v06.py").read_text(encoding="utf-8")
        self.assertIn('VERSION = "0.6.6"',desktop)
        self.assertIn("def _android_import_page(self):",desktop)
        self.assertIn('elif self.page=="agenda": self._agenda()',desktop)
        self.assertIn('right=ctk.CTkFrame(container,fg_color="transparent"',desktop)
        self.assertNotIn("self.create_window(w-27,self._module_top-24,window=self.search_field",dashboard)
        self.assertNotIn("self.search_field=tk.Entry(",dashboard)

if __name__=="__main__":unittest.main()
