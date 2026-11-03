"""Windows 0.8.5: synthetic-only regression tests for Calendar and Takes."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

from windows import secure_store
from windows.doses_calendar_v085 import (
    appointments_for_day, month_cells, month_shift, dose_entries, dose_counts,
    expected_slots,
)
from shared.python.saude_backup import read_backup


class CalendarTests(unittest.TestCase):
    def test_month_selection_and_person_boundary(self):
        a = {"appointments": [
            {"id": "a", "title": "Consulta fictícia", "date": "2028-02-29", "time": "08:20"},
            {"id": "b", "date": "2028-03-01", "time": "09:00"}]}
        b = {"appointments": [{"id": "c", "date": "2028-02-29", "time": "11:00"}]}
        self.assertEqual([x["id"] for x in appointments_for_day(a,date(2028,2,29))], ["a"])
        self.assertEqual([x["id"] for x in appointments_for_day(b,date(2028,2,29))], ["c"])
        cells = month_cells(a,2028,2)
        self.assertEqual(sum(count for row in cells for day,in_month,count in row
                             if in_month), 1)
        self.assertEqual({day.weekday() for row in cells for day,_,_ in row[:1]}, {0})
        self.assertEqual(month_shift(2028,1,-1),(2027,12))
        self.assertEqual(month_shift(2028,12,1),(2029,1))

    def test_unknown_or_cancelled_rows_never_invent_date(self):
        profile={"appointments":[{"id":"x","date":"not-a-date"}]}
        self.assertEqual(appointments_for_day(profile,date(2028,2,29)),[])
        self.assertEqual(sum(x[2] for w in month_cells(profile,2028,2) for x in w),0)


class DoseLogicTests(unittest.TestCase):
    def setUp(self):
        self.m={"id":"med1","name":"Medicação de teste","dose":"10 mg",
                "reminder_time":"07:00","repeat_mode":"daily"}
        self.p={"medications":[self.m],"intakes":[]}

    def test_confirmed_only_when_recorded(self):
        day=date(2026,11,3)
        pending=dose_entries(self.p,day,datetime(2026,11,3,7,10))
        self.assertEqual(len(pending),1)
        self.assertEqual(pending[0]["status"],"pending")
        self.assertEqual(dose_entries(self.p,day,datetime(2026,11,3,7,16))[0]["status"],"late")
        self.p["intakes"]=[{
            "id":"take1","medication_id":"med1",
            "scheduled_at":"2026-11-03T07:00",
            "confirmed_at":"2026-11-03T07:25:00","status":"confirmed"}]
        self.assertEqual(dose_entries(self.p,day,datetime(2026,11,3,8))[0]["status"],"confirmed")
        self.assertEqual(dose_counts(self.p,day,datetime(2026,11,3,8))["confirmed"],1)

    def test_no_schedule_no_fake_pending(self):
        day=date(2026,11,3)
        for value in ({"repeat_mode":""},{"no_alarm":True},{"suspended":True},
                      {"reminder_time":""},{"dose_pattern":"SOS","no_alarm":True}):
            with self.subTest(value=value):
                m=dict(self.m,**value)
                self.assertEqual(expected_slots({"medications":[m]},day),[])

    def test_date_bounds_and_android_weekdays(self):
        day=date(2026,11,2)  # Monday = Android weekday 1
        m=dict(self.m,repeat_mode="weekly",repeat_weekdays=[1],
               repeat_start="2026-11-01",repeat_until="2026-11-30")
        self.assertEqual(len(expected_slots({"medications":[m]},day)),1)
        self.assertEqual(expected_slots({"medications":[m]},date(2026,11,3)),[])
        self.assertEqual(expected_slots({"medications":[m]},date(2026,12,7)),[])

    def test_original_recurring_fields_and_local_override(self):
        m=dict(self.m)
        m.pop("repeat_mode")
        m["android_original"]={"repeat_mode":"daily"}
        self.assertEqual(len(expected_slots({"medications":[m]},date(2026,11,3))),1)
        m["repeat_mode"]="none"
        self.assertEqual(expected_slots({"medications":[m]},date(2026,11,3)),[])


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.stack=[
            patch.object(secure_store,"_user_data_path",
                         return_value=Path(self.temp.name)/"p.dpapi"),
            patch.object(secure_store,"_encrypt",side_effect=lambda raw:raw),
            patch.object(secure_store,"_decrypt",side_effect=lambda raw:raw),
        ]
        for item in self.stack:
            item.start()
            self.addCleanup(item.stop)
        self.store=secure_store.SecureStore()
        self.a=self.store.create_profile("Pessoa A, teste")
        self.b=self.store.create_profile("Pessoa B, teste")
        self.ma=self.store.save_medication(self.a["id"],{
            "name":"Comprimido A","dose":"5 mg",
            "reminder_time":"09:00","time":"09:00",
            "administration_route":"oral","repeat_mode":"daily"})
        self.mb=self.store.save_medication(self.b["id"],{
            "name":"Comprimido B","dose":"10 mg",
            "reminder_time":"10:00","time":"10:00",
            "administration_route":"oral","repeat_mode":"daily"})

    def test_exact_profile_medication_identity(self):
        with self.assertRaises(secure_store.LocalStoreError):
            self.store.confirm_intake(self.a["id"],self.mb["id"])
        self.assertFalse(self.store.get_profile(self.a["id"]).get("intakes"))
        self.assertFalse(self.store.get_profile(self.b["id"]).get("intakes"))

    def test_manual_is_real_saved_and_backed_up(self):
        item=self.store.confirm_intake(self.a["id"],self.ma["id"],
                                      confirmed_at="2026-11-03T08:45:00")
        self.assertEqual(item["status"],"confirmed")
        self.assertEqual(len(self.store.get_profile(self.a["id"])["intakes"]),1)
        self.assertFalse(self.store.get_profile(self.b["id"]).get("intakes"))
        raw=self.store.export_backup("synthetic-password-for-test")
        files=read_backup(raw,"synthetic-password-for-test")
        metadata=json.loads(files[f"profiles/{self.a['id']}/profile.json"])
        self.assertEqual(metadata["intakes"][0]["medication_id"],self.ma["id"])
        self.store.delete_intake(self.a["id"],item["id"])
        self.assertEqual(self.store.get_profile(self.a["id"])["intakes"],[])

    def test_duplicate_planned_blocked_and_wrong_owner_denied(self):
        self.ma["repeat_mode"]="daily"
        self.store.save()
        first=self.store.confirm_intake(self.a["id"],self.ma["id"],
            confirmed_at="2026-11-03T09:05",scheduled_at="2026-11-03T09:00")
        self.assertEqual(first["status"],"confirmed")
        with self.assertRaises(secure_store.LocalStoreError):
            self.store.confirm_intake(self.a["id"],self.ma["id"],
                confirmed_at="2026-11-03T09:10",scheduled_at="2026-11-03T09:00")
        with self.assertRaises(secure_store.LocalStoreError):
            self.store.confirm_intake(self.b["id"],self.mb["id"],
                confirmed_at="2026-11-03T10:05",scheduled_at="2026-11-03T09:00")
        with self.assertRaises(secure_store.LocalStoreError):
            self.store.delete_intake(self.b["id"],first["id"])


if __name__ == "__main__":
    unittest.main()
