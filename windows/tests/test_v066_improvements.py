"""No patient examples: synthetic regression tests for Windows 0.6.6."""
import unittest
from datetime import datetime
from windows.profile_fields_v066 import mapped_fields, missing_profile_fields
from windows.medication_schedule_v066 import next_medication_label

class ProfilesMappingTests(unittest.TestCase):
    def test_realistic_android_aliases_fill_missing_fields_only(self):
        original={"birthDate":"1984-05-03","mobile":"900000000",
                  "healthUnit":"USF fictícia","morada":"Rua Exemplo",
                  "codigoPostal":"1000-001","NISS":"00000000000"}
        mapped=mapped_fields(original)
        self.assertEqual(mapped["health_unit"],"USF fictícia")
        self.assertEqual(mapped["birth_date"],"1984-05-03")
        self.assertNotIn("email",mapped)
        current={"phone":"999999999","address":""}
        missing=missing_profile_fields(current,original)
        self.assertNotIn("phone",missing)
        self.assertEqual(missing["address"],"Rua Exemplo")
    def test_invalid_birthday_not_written(self):
        self.assertNotIn("birth_date",mapped_fields({"birthDate":"03/05/1984"}))
        self.assertEqual(mapped_fields({}),{})

class MedicationScheduleTests(unittest.TestCase):
    def test_daily_recurrence_after_hour_today(self):
        item={"name":"Fictício","android_original":{
            "reminder_time":"09:30","repeat_mode":"daily"}}
        self.assertEqual(next_medication_label(item,datetime(2026,11,1,10,0)),
            "Próxima toma prevista: 2026-11-02 · 09:30")
    def test_weekly_sunday_is_js_zero(self):
        item={"android_original":{"reminder_time":"09:30","repeat_mode":"weekly",
                                 "repeat_weekdays":[0]}}
        self.assertEqual(next_medication_label(item,datetime(2026,10,31,10,0)),
            "Próxima toma prevista: 2026-11-01 · 09:30")
    def test_unknown_frequency_shows_no_invented_date(self):
        self.assertEqual(next_medication_label({"time":"08:30"},
             datetime(2026,10,31,7,0)),"Data da próxima toma por definir · 08:30")
    def test_suspended_has_no_next_reminder(self):
        self.assertEqual(next_medication_label({"suspended":True,"time":"07:00"},
            datetime(2026,10,31,6,0)),"Medicação suspensa")
    def test_dated_schedule(self):
        item={"android_original":{"reminder_time":"08:00",
              "schedule":{"2026-11":[2,5]}}}
        self.assertEqual(next_medication_label(item,datetime(2026,10,31,12,0)),
            "Próxima toma prevista: 2026-11-02 · 08:00")

if __name__=="__main__":unittest.main()
