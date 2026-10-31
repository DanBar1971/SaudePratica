"""Synthetic tests for privacy-safe background appointment reminders."""
import unittest, tempfile
from datetime import datetime,timedelta
from pathlib import Path
from windows.appointment_reminders_v071 import (
    DEFAULT,CHOICES,normalize_offsets,record_offsets,due_events,reminder_message)
from windows.appointment_editor_v070 import clean_appointment_fields
from windows.reminder_agent_v071 import _read_sent,_save_sent,_agent_command
from windows import secure_store
from unittest.mock import patch

class ReminderTests(unittest.TestCase):
    NOW=datetime(2026,11,9,11,30)
    def sample(self,extras=None,profile="p1"):
        doc={"id":"appt-1","title":"Consulta fictícia","date":"2026-11-10",
             "time":"11:30","reminders_minutes":[1440,120]}
        if extras:doc.update(extras)
        return [{"id":profile,"appointments":[doc]}]
    def test_android_offset_codes(self):
        self.assertEqual(dict(CHOICES)[1440],"1 dia antes")
        self.assertEqual(dict(CHOICES)[120],"2 horas antes")
        self.assertEqual(normalize_offsets([120,1440,120]),[1440,120])
        self.assertEqual(list(DEFAULT),[1440,120])
        self.assertEqual(record_offsets({"reminders_minutes":[]}),[])
        self.assertEqual(record_offsets({"android_original":{"reminders_minutes":[1440,120]}}),[1440,120])
    def test_outdated_custom_offsets_are_preserved(self):
        self.assertEqual(normalize_offsets([10,1440,10]),[1440,10])
        for bad in ([True],["1440"],[-1],[10081],None if False else [0]*25):
            with self.assertRaises(ValueError):normalize_offsets(bad)
    def test_one_day_before(self):
        notifications=due_events(self.sample(),self.NOW)
        self.assertEqual(len(notifications),1)
        self.assertEqual(notifications[0][2],1440)
        self.assertEqual(notifications[0][1],datetime(2026,11,10,11,30))
    def test_two_hours_before(self):
        now=datetime(2026,11,10,9,30)
        self.assertEqual([r[2] for r in due_events(self.sample(),now)],[120])
    def test_at_appointment_time(self):
        now=datetime(2026,11,10,11,31)
        doc=self.sample({"reminders_minutes":[0]})
        self.assertEqual([r[2] for r in due_events(doc,now)],[0])
        self.assertEqual(len(due_events(doc,now+timedelta(minutes=15))),0)
    def test_cancelled_and_done_do_not_alert(self):
        for status in ("cancelled","done"):
            profiles=self.sample({"desktop_status":status})
            self.assertEqual(due_events(profiles,self.NOW),[])
    def test_deliberate_empty_set_has_no_alerts(self):
        self.assertEqual(due_events(self.sample({"reminders_minutes":[]}),self.NOW),[])
    def test_no_alarm_schedule_without_a_valid_date(self):
        self.assertEqual(due_events(self.sample({"date":"bad"}),self.NOW),[])
    def test_rescheduled_event_receives_distinct_dedup_token(self):
        before=due_events(self.sample(),self.NOW)[0][0]
        after=due_events(self.sample({"date":"2026-11-11"}),
                         self.NOW+timedelta(days=1))[0][0]
        self.assertNotEqual(before,after)
    def test_generic_lock_screen_message_has_no_patient_data(self):
        message=reminder_message(datetime(2026,11,10,11,30),120)
        self.assertIn("2 horas",message)
        self.assertNotIn("hospital",message.lower())
        self.assertNotIn("regina",message.lower())
    def test_validator_allows_no_reminders(self):
        old={"title":"Fictício","reminders_minutes":[1440,120]}
        self.assertEqual(clean_appointment_fields({"reminders_minutes":[]},old)["reminders_minutes"],[])
        self.assertEqual(clean_appointment_fields({"reminders_minutes":[120]},old)["reminders_minutes"],[120])
    def test_sent_token_persists_without_clinical_details(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"sent.json"
            sent={"a"*64:datetime.now().isoformat()}
            _save_sent(path,sent)
            self.assertEqual(_read_sent(path),sent)
            self.assertNotIn("Consulta fictícia",path.read_text(encoding="utf-8"))
    def test_full_ui_and_startup_are_wired(self):
        root=Path(__file__).resolve().parents[2]
        ui=(root/"windows/desktop_v04.py").read_text(encoding="utf-8")
        setup=(root/"windows/installer/SaudePratica.iss").read_text(encoding="utf-8")
        self.assertIn("self.reminder_vars",ui)
        self.assertIn("data[\"reminders_minutes\"]",ui)
        self.assertIn("enable_background_reminders()",ui)
        self.assertIn("--reminder-agent",ui)
        self.assertIn("--reminder-agent",setup)
        self.assertIn("HKCU",setup)

if __name__=="__main__":unittest.main()
