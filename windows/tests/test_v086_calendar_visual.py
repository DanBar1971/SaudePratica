"""Windows 0.8.6: real calendar appearance and exact profile-bound event counts."""
from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from windows.calendar_ui_v086 import (
    LONG_WEEKDAYS, calendar_day_colors, calendar_event_title,
    calendar_status_badge,
)
from windows.doses_calendar_v085 import month_cells, appointments_for_day


class CalendarVisualTests(unittest.TestCase):
    def test_every_day_with_an_appointment_is_visibly_coloured(self):
        for light in (True, False):
            for in_month in (True, False):
                quiet=calendar_day_colors(
                    has_appointments=False, selected=False,
                    today=False, in_month=in_month, light=light)
                marked=calendar_day_colors(
                    has_appointments=True, selected=False,
                    today=False, in_month=in_month, light=light)
                self.assertNotEqual(quiet["background"],marked["background"])
                self.assertNotEqual(quiet["border"],marked["border"])
                self.assertNotEqual(quiet["badge_bg"],marked["badge_bg"])
                self.assertTrue(marked["number"])
                self.assertTrue(marked["preview"])

    def test_today_selected_and_event_combination_have_distinct_states(self):
        for light in (True,False):
            event=dict(has_appointments=True,light=light,in_month=True)
            normal=calendar_day_colors(**event,selected=False,today=False)
            selected=calendar_day_colors(**event,selected=True,today=False)
            today=calendar_day_colors(**event,selected=False,today=True)
            both=calendar_day_colors(**event,selected=True,today=True)
            self.assertNotEqual(normal["background"],selected["background"])
            self.assertNotEqual(normal["border"],today["border"])
            self.assertEqual(today["border"],both["border"])
            self.assertEqual(selected["background"],both["background"])
            self.assertTrue(both["badge_text"])

    def test_user_profile_boundary_and_original_appointment_titles(self):
        # Synthetic profiles with overlapping dates: event count must NEVER
        # leak from person B into the Calendar being painted for person A.
        alice={"appointments":[
            {"id":"a","title":"Consulta fictícia A",
             "date":"2026-11-10","time":"08:00"},
            {"id":"a2","activity":"Análise fictícia",
             "date":"2026-11-10","time":"09:30"},
            {"id":"a3","title":"Exame", "date":"2026-12-01","time":"12:00"},
        ]}
        bob={"appointments":[
            {"id":"b","title":"Consulta fictícia B",
             "date":"2026-11-10","time":"11:00"}]}
        self.assertEqual(len(appointments_for_day(alice,date(2026,11,10))),2)
        self.assertEqual(len(appointments_for_day(bob,date(2026,11,10))),1)
        a=sum(count for row in month_cells(alice,2026,11)
              for day,in_month,count in row if day==date(2026,11,10))
        b=sum(count for row in month_cells(bob,2026,11)
              for day,in_month,count in row if day==date(2026,11,10))
        self.assertEqual((a,b),(2,1))
        self.assertEqual(calendar_event_title(alice["appointments"][0]),
                         "Consulta fictícia A")
        self.assertEqual(calendar_event_title(alice["appointments"][1]),
                         "Análise fictícia")
        self.assertEqual(calendar_event_title({}),"Marcação")

    def test_cancelled_and_done_states_are_legible_and_keep_all_events(self):
        cancelled={"date":"2028-01-10","time":"12:00","desktop_status":"cancelled"}
        done={"date":"2028-01-10","time":"09:00","desktop_status":"done"}
        pending={"date":"2028-01-10","time":"13:00","desktop_status":"pending"}
        p={"appointments":[cancelled,done,pending]}
        self.assertEqual(len(appointments_for_day(p,date(2028,1,10))),3)
        for light in (True,False):
            self.assertEqual(calendar_status_badge(cancelled,light=light)[0],"Cancelada")
            self.assertEqual(calendar_status_badge(done,light=light)[0],"Realizada")
            self.assertEqual(calendar_status_badge(pending,light=light)[0],"Pendente")
        self.assertEqual(len(LONG_WEEKDAYS),7)

    def test_desktop_overrides_calendar_but_preserves_takes(self):
        root=Path(__file__).resolve().parents[1]
        source=(root/"desktop_v04.py").read_text("utf-8")
        gui=(root/"calendar_ui_v086.py").read_text("utf-8")
        self.assertIn("CalendarVisualV086, DosesCalendarUi",source)
        self.assertIn('VERSION = "0.8.6"',source)
        self.assertIn("self.store.get_profile(self.active_id)",gui)
        self.assertIn("self._calendar_day_cells[day] = card",gui)
        self.assertIn("self._calendar_choose(target)",gui)
        self.assertIn("self._open_calendar_appointment(uid)",gui)
        self.assertIn("self._calendar_new_appointment",gui)
        self.assertNotIn("self.store.save_appointment(",gui)
        self.assertNotIn("self.store.save_medication(",gui)


if __name__ == "__main__":
    unittest.main()
