"""Windows 0.8.14 synthetic regression tests for profile-scoped wellness."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from windows import secure_store
from windows.wellness_models_v089 import (
    WATER_DEFAULTS, PILL_PATTERNS,water_settings,water_record,water_total,
    progress_pct,activity_record,weekly_series,cycle_settings,
    period_record,estimated_next_period,pill_scheduled,
)
from windows.activity_ui_v089 import (
    activity_display,parse_activity_fields,
)
from shared.python.saude_backup import read_backup


class WellnessModelsTests(unittest.TestCase):
    def test_android_water_settings_limits_and_no_fake_goal(self):
        self.assertEqual(water_settings()["glass_ml"],200)
        self.assertEqual(water_settings()["target_ml"],0)
        self.assertEqual(progress_pct(500,0),None)
        self.assertEqual(progress_pct(400,800),50)
        self.assertEqual(water_settings({"target_ml":"1500"})["target_ml"],1500)
        for bad in ({"glass_ml":29},{"glass_ml":1001},
                    {"target_ml":10001},{"water_interval":10},
                    {"water_start":"22:00","water_end":"08:00"},
                    {"water_end":"25:00"}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                water_settings(bad)

    def test_water_records_exact_dates_and_volumes(self):
        today=date.today().isoformat()
        entry=water_record(today,"13:09",250)
        self.assertEqual(water_total([entry],today),250)
        with self.assertRaises(ValueError):
            water_record((date.today()+timedelta(days=1)).isoformat(),"12:00",100)
        with self.assertRaises(ValueError):
            water_record(today,"25:00",100)
        with self.assertRaises(ValueError):
            water_record(today,"12:00",0)

    def test_activity_manual_validation_and_week(self):
        today=date.today().isoformat()
        record=activity_record({
            "date":today,"steps":"7000","distance_m":4200,
            "sleep_minutes":450,"heart_bpm":75,"notes":"fictício"})
        self.assertEqual(record["steps"],7000)
        self.assertEqual(record["sleep_minutes"],450)
        self.assertEqual(weekly_series([record],"steps",today)[-1],(today,7000))
        self.assertEqual(activity_display(record,"distance_km"),"4,2")
        self.assertEqual(activity_display(record,"sleep_hm"),"7:30")
        self.assertEqual(activity_display({"weight_grams":72500},"weight_kg"),"72,5")
        for wrong in (
            {"date":today},
            {"date":today,"steps":-2},
            {"date":today,"heart_bpm":500},
            {"date":today,"systolic":85,"diastolic":100},
            {"date":(date.today()+timedelta(days=1)).isoformat(),"steps":1},
        ):
            with self.subTest(wrong=wrong),self.assertRaises(ValueError):
                activity_record(wrong)

    def test_pill_patterns_are_personal_settings_not_medical_advice(self):
        today=date.today()
        start=(today-timedelta(days=29)).isoformat()
        values=cycle_settings({"cycle_days":28,"pill_pattern":"21_7",
                                "pill_start":start,"pill_time":"21:00"})
        beginning=date.fromisoformat(start)
        self.assertTrue(pill_scheduled(beginning.isoformat(),values))
        self.assertTrue(pill_scheduled((beginning+timedelta(days=20)).isoformat(),values))
        self.assertFalse(pill_scheduled((beginning+timedelta(days=21)).isoformat(),values))
        self.assertTrue(pill_scheduled((beginning+timedelta(days=28)).isoformat(),values))
        daily=cycle_settings({"pill_pattern":"daily","pill_start":start})
        self.assertTrue(pill_scheduled(today.isoformat(),daily))
        self.assertTrue(pill_scheduled((beginning+timedelta(days=400)).isoformat(),daily))
        with self.assertRaises(ValueError):
            cycle_settings({"pill_pattern":"24_4","pill_start":""})
        with self.assertRaises(ValueError):
            cycle_settings({"cycle_days":12})

    def test_periods_max_15_days_and_estimates(self):
        first=date.today()-timedelta(days=30)
        end=first+timedelta(days=4)
        row=period_record(first.isoformat(),end.isoformat())
        self.assertEqual(estimated_next_period([row],28,first.isoformat()),
                         (first+timedelta(days=28)).isoformat())
        with self.assertRaises(ValueError):
            period_record(first.isoformat(),(first+timedelta(days=15)).isoformat())
        with self.assertRaises(ValueError):
            period_record((date.today()+timedelta(days=1)).isoformat(),
                          (date.today()+timedelta(days=1)).isoformat())
        self.assertIsNone(estimated_next_period([],28))

class ProfileIsolationTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        mocks=[
            patch.object(secure_store,"_user_data_path",
                         return_value=Path(temp.name)/"store.dpapi"),
            patch.object(secure_store,"_encrypt",side_effect=lambda x:x),
            patch.object(secure_store,"_decrypt",side_effect=lambda x:x),
        ]
        for patcher in mocks:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.s=secure_store.SecureStore()
        self.a=self.s.create_profile("Pessoa de teste A")["id"]
        self.b=self.s.create_profile("Pessoa de teste B")["id"]
        self.today=date.today().isoformat()

    def test_water_history_and_profile_boundary(self):
        self.s.set_water_settings(self.a,{"target_ml":1700,"glass_ml":250})
        self.assertEqual(self.s.wellness_data(self.b,"water")["settings"]["target_ml"],0)
        record=self.s.add_water(self.a,self.today,"10:30",250)
        self.assertEqual(water_total(self.s.wellness_data(self.a,"water")["entries"],
                                     self.today),250)
        self.assertEqual(self.s.wellness_data(self.b,"water")["entries"],[])
        with self.assertRaises(secure_store.LocalStoreError):
            self.s.remove_water(self.b,record["id"])
        self.s.remove_water(self.a,record["id"])
        self.assertEqual(self.s.wellness_data(self.a,"water")["entries"],[])

    def test_activity_daily_unique_and_not_shared(self):
        self.s.save_activity_day(self.a,{"date":self.today,"steps":"5000"})
        self.s.save_activity_day(self.a,{"date":self.today,"sleep_minutes":"450"})
        vals=self.s.wellness_data(self.a,"activity")["entries"]
        self.assertEqual(len(vals),1)
        self.assertIsNone(vals[0]["steps"])
        self.assertEqual(vals[0]["sleep_minutes"],450)
        self.assertEqual(self.s.wellness_data(self.b,"activity")["entries"],[])
        with self.assertRaises(secure_store.LocalStoreError):
            self.s.delete_activity_day(self.b,self.today)
        self.s.delete_activity_day(self.a,self.today)
        self.assertEqual(self.s.wellness_data(self.a,"activity")["entries"],[])

    def test_cycle_overlap_pills_and_cross_profile(self):
        first=date.today()-timedelta(days=4)
        last=first+timedelta(days=3)
        self.s.set_cycle_settings(self.a,{
            "cycle_days":30,"pill_pattern":"daily",
            "pill_start":first.isoformat(),"pill_time":"20:30"})
        period=self.s.add_cycle_period(self.a,first.isoformat(),last.isoformat())
        with self.assertRaises(secure_store.LocalStoreError):
            self.s.add_cycle_period(self.a,first.isoformat(),last.isoformat())
        with self.assertRaises(secure_store.LocalStoreError):
            self.s.delete_cycle_period(self.b,period["id"])
        self.s.set_pill_taken(self.a,self.today,True)
        self.assertIn(self.today,self.s.wellness_data(self.a,"cycle")["pill_taken"])
        self.assertEqual(self.s.wellness_data(self.b,"cycle")["pill_taken"],[])
        with self.assertRaises(secure_store.LocalStoreError):
            self.s.set_pill_taken(self.a,
                (date.today()+timedelta(days=1)).isoformat(),True)
        with self.assertRaises(secure_store.LocalStoreError):
            self.s.set_pill_taken(self.b,self.today,True)
        self.s.set_pill_taken(self.a,self.today,False)
        self.assertNotIn(self.today,self.s.wellness_data(self.a,"cycle")["pill_taken"])
        self.s.delete_cycle_period(self.a,period["id"])
        self.assertEqual(self.s.wellness_data(self.a,"cycle")["periods"],[])

    def test_all_three_modules_preserved_in_encrypted_backup_and_restore(self):
        self.s.add_medication(self.a,"Dose fictícia","1 mg","07:00","oral")
        self.s.add_water(self.a,self.today,"09:00",200)
        self.s.save_activity_day(self.a,{"date":self.today,"steps":9000})
        first=(date.today()-timedelta(days=3)).isoformat()
        self.s.add_cycle_period(self.a,first,self.today)
        secret="senha exclusivamente de teste"
        blob=self.s.export_backup(secret)
        files=read_backup(blob,secret)
        info=json.loads(files[f"profiles/{self.a}/profile.json"])
        self.assertEqual(info["wellness_water"]["entries"][0]["ml"],200)
        self.assertEqual(info["wellness_activity"]["entries"][0]["steps"],9000)
        self.assertEqual(info["wellness_cycle"]["periods"][0]["start"],first)
        other=json.loads(files[f"profiles/{self.b}/profile.json"])
        self.assertNotIn("wellness_water",other)
        self.assertNotIn("wellness_cycle",other)
        with tempfile.TemporaryDirectory() as dest:
            with patch.object(secure_store,"_user_data_path",
                              return_value=Path(dest)/"other.dpapi"):
                clean=secure_store.SecureStore()
                self.assertEqual(clean.restore_backup(files),2)
                self.assertEqual(clean.wellness_data(self.a,"water")["entries"][0]["ml"],200)
                self.assertEqual(clean.wellness_data(self.a,"activity")["entries"][0]["steps"],9000)
                self.assertEqual(len(clean.wellness_data(self.a,"cycle")["periods"]),1)
                self.assertEqual(len(clean.get_profile(self.a)["medications"]),1)

    def test_failed_save_leaves_all_three_unmodified(self):
        settings_before=self.s.wellness_data(self.a,"water")
        with patch.object(self.s,"save",side_effect=OSError("write failure")):
            with self.assertRaises(OSError):
                self.s.add_water(self.a,self.today,"12:00",200)
        self.assertEqual(self.s.wellness_data(self.a,"water"),settings_before)

    def test_no_global_data_exposure_or_auto_sensor_fabrication(self):
        from windows.ui_catalog_v05 import MODULE_CARDS
        statuses={k:enabled for k,icon,title,subtitle,enabled in MODULE_CARDS}
        for key in ("water","activity","cycle"):
            self.assertTrue(statuses[key])
        desktop=(Path(__file__).resolve().parents[1]/
                 "desktop_v04.py").read_text("utf-8")
        self.assertIn('VERSION = "0.8.16"',desktop)
        for needle in ('self.page=="water"','self.page=="activity"',
                       'self.page=="cycle"'):
            self.assertIn(needle,desktop)
        for filename in ("water_ui_v089.py","activity_ui_v089.py",
                         "cycle_ui_v089.py"):
            source=(Path(__file__).resolve().parents[1]/filename).read_text("utf-8")
            self.assertIn("self.store.get_profile(self.active_id)",source)
        self.assertIn("A versão Windows ainda não envia alarmes de pílula",
            (Path(__file__).resolve().parents[1]/
             "cycle_ui_v089.py").read_text("utf-8"))


if __name__=="__main__":
    unittest.main()
