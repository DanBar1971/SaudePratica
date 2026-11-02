"""Synthetic 1:1 Android->Windows medication state tests. No user data."""
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from windows import secure_store
from windows.medication_gallery_v068 import medication_filter_matches, medication_status
from windows.medication_flags_v076 import (
    suspended, no_alarm, configured_reminder, active_reminder, reminder_clock
)
from windows.medication_schedule_v066 import next_medication_label
from shared.python.saude_backup import read_backup

def synthetic_medication(name,**source):
    return {"id":name,"name":name,"dose":"5 mg","android_original":source,
            **source}

class AndroidMedicationSemantics(unittest.TestCase):
    def setUp(self):
        self.suspended=synthetic_medication("suspenso",suspended_from="2026-10-28",
            reminder_time="08:30",time="Jejum")
        self.alert=synthetic_medication("aviso",suspended_from="",
            reminder_time="07:00",time="Pequeno-almoço")
        self.noclock=synthetic_medication("sem hora",suspended_from="",
            reminder_time="",time="Jantar")
        self.disabled=synthetic_medication("sem alarme",suspended_from="",
            reminder_time="12:00",no_alarm=True,time="Jejum")

    def test_suspension_is_read_from_android_date(self):
        self.assertTrue(suspended(self.suspended))
        self.assertTrue(medication_filter_matches(self.suspended,"suspended"))
        self.assertFalse(medication_filter_matches(self.suspended,"active"))
        self.assertEqual(medication_status(self.suspended)[0],"Suspensa")
        self.assertEqual(next_medication_label(self.suspended),"Medicação suspensa")

    def test_real_clock_does_not_equal_meal_type(self):
        self.assertEqual(reminder_clock(self.alert),"07:00")
        self.assertEqual(reminder_clock(self.suspended),"08:30")
        self.assertEqual(reminder_clock(self.noclock),"")
        self.assertFalse(active_reminder(self.suspended))
        self.assertTrue(configured_reminder(self.suspended))
        self.assertTrue(active_reminder(self.alert))
        self.assertFalse(active_reminder(self.noclock))
        self.assertEqual(medication_status(self.alert)[0],"Aviso 07:00")
        self.assertTrue(medication_filter_matches(self.alert,"with_alarm"))
        self.assertFalse(medication_filter_matches(self.noclock,"with_alarm"))
        self.assertEqual(
            next_medication_label(self.alert,datetime(2026,11,2,6,0)),
            "Data da próxima toma por definir · 07:00")

    def test_explicit_disabled_flag_and_local_overrides(self):
        self.assertTrue(no_alarm(self.disabled))
        self.assertFalse(active_reminder(self.disabled))
        self.assertTrue(medication_filter_matches(self.disabled,"no_alarm"))
        edited={**self.suspended,"suspended":False,"no_alarm":False}
        self.assertFalse(suspended(edited))
        self.assertTrue(active_reminder(edited))
        self.assertNotEqual(next_medication_label(edited),"Medicação suspensa")
        self.assertFalse(no_alarm({**self.disabled,"no_alarm":False}))
        cleared={**self.alert,"reminder_time":"","suspended":False}
        self.assertEqual(reminder_clock(cleared),"")
        self.assertFalse(active_reminder(cleared))
        self.assertEqual(cleared["android_original"]["reminder_time"],"07:00")

    def test_export_and_restore_does_not_lose_android_source_flags(self):
        with tempfile.TemporaryDirectory() as temp:
            file_a=Path(temp)/"source.dpapi"
            file_b=Path(temp)/"target.dpapi"
            with patch.object(secure_store,"_encrypt",side_effect=lambda x:x),patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                with patch.object(secure_store,"_user_data_path",return_value=file_a):
                    a=secure_store.SecureStore()
                person=a.create_profile("Perfil fictício")
                person["medications"]=[self.suspended,self.alert,self.noclock,self.disabled]
                a.save()
                blob=a.export_backup("synthetic test password")
                with patch.object(secure_store,"_user_data_path",return_value=file_b):
                    b=secure_store.SecureStore()
                b.restore_portable_backup(b.inspect_portable_backup(blob,"synthetic test password"),"synthetic test password")
                meds=b.profiles()[0]["medications"]
                self.assertEqual(len(meds),4)
                self.assertEqual(sum(suspended(x) for x in meds),1)
                self.assertEqual(sum(configured_reminder(x) for x in meds),2)
                self.assertEqual(sum(active_reminder(x) for x in meds),1)
                edited=b.save_medication(b.profiles()[0]["id"],{
                    "name":"aviso","dose":"5 mg","time":"Pequeno-almoço",
                    "reminder_time":"07:00","suspended":False,"no_alarm":False,
                },"aviso")
                self.assertEqual(edited["reminder_time"],"07:00")
                self.assertEqual(edited["android_original"]["time"],"Pequeno-almoço")

    def test_ui_keeps_alarm_and_meal_separate(self):
        text=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text(encoding="utf-8")
        self.assertIn('("with_alarm","Com aviso")',text)
        self.assertIn('self.suspended_var=ctk.BooleanVar(value=is_suspended(fields))',text)
        self.assertIn('value=reminder_clock(fields) if k=="reminder_time"',text)
        self.assertIn('VERSION = "0.7.6"',text)

if __name__=="__main__":
    unittest.main()
