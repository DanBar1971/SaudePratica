"""Synthetic tests for the four Android-like Agenda filters on Windows."""
import unittest
from datetime import datetime
from pathlib import Path
from windows.agenda_filter_v069 import FILTERS,appointment_status,appointment_datetime,filtered_appointments

class AgendaFiltersTests(unittest.TestCase):
    NOW=datetime(2026,10,31,11,0)

    def test_all_four_filters_are_available(self):
        self.assertEqual([label for _,label in FILTERS],
                         ["Todas","Pendentes","Realizadas","Canceladas"])

    def test_future_pending_past_auto_realized(self):
        self.assertEqual(appointment_status({"date":"2026-11-10","time":"09:00"},self.NOW),"pending")
        self.assertEqual(appointment_status({"date":"2026-10-21","time":"12:00"},self.NOW),"done")

    def test_cancelled_has_priority_even_when_past(self):
        row={"date":"2026-10-20","time":"12:00","status":"CANCELADA"}
        self.assertEqual(appointment_status(row,self.NOW),"cancelled")
        self.assertEqual(appointment_status({"date":"2026-11-10","cancelled":True},self.NOW),"cancelled")

    def test_future_with_explicit_completed_status(self):
        self.assertEqual(appointment_status({"date":"2026-11-11","state":"Realizada"},self.NOW),"done")
        self.assertEqual(appointment_status({"date":"2026-11-11","isDone":True},self.NOW),"done")

    def test_preserves_metadata_and_handles_unknown_dates(self):
        rows=[
            {"id":"a","date":"2026-10-23","name":"Evento fictício"},
            {"id":"b","date":"2026-11-15","name":"Evento fictício"},
            {"id":"c","date":"2026-11-15","status":"cancelada"},
            {"id":"d","date":"invalid"},
        ]
        before=[dict(i) for i in rows]
        self.assertEqual([x["id"] for x in filtered_appointments(rows,"pending",self.NOW)],["b","d"])
        self.assertEqual([x["id"] for x in filtered_appointments(rows,"done",self.NOW)],["a"])
        self.assertEqual([x["id"] for x in filtered_appointments(rows,"cancelled",self.NOW)],["c"])
        self.assertEqual(len(filtered_appointments(rows,"all",self.NOW)),4)
        self.assertEqual(rows,before)

    def test_original_android_status_remains_recognised(self):
        row={"date":"2026-11-10","android_original":{"status":"Cancelado"}}
        self.assertEqual(appointment_status(row,self.NOW),"cancelled")
        self.assertIsNone(appointment_datetime({"date":"broken","time":"XX"}))

    def test_ui_has_filter_row_and_callback(self):
        source=(Path(__file__).resolve().parents[2]/"windows/desktop_v04.py").read_text(encoding="utf-8")
        self.assertIn("self.agenda_filter",source)
        self.assertIn("def _set_agenda_filter(",source)
        self.assertIn("filtered_appointments(",source)
        self.assertIn("for key,label in AGENDA_FILTERS:",source)

if __name__=="__main__": unittest.main()
