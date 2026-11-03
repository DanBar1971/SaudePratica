"""0.8.2: eliminate conflicting hours in Windows medication cards.

Synthetic medicines only; tests must never rely on real patient records.
"""
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest
from windows import secure_store
from windows.medication_flags_v076 import reminder_clock
from windows.medication_gallery_v068 import medication_status
from windows.medication_schedule_v066 import next_medication_label
from windows.medication_time_v082 import (
    condition_value,mismatched_legacy_clock,canonical_reminder_fields
)

class MedicationSingleClockTests(unittest.TestCase):
    def test_find_conflicting_legacy_time_without_changing_an_alarm(self):
        med={"name":"Medicamento fictício","time":"08:00",
             "reminder_time":"07:00","android_original":{
                 "time":"07:00","reminder_time":"07:00"}}
        self.assertEqual(mismatched_legacy_clock(med),"08:00")
        self.assertEqual(condition_value(med),"")
        self.assertEqual(reminder_clock(med),"07:00")
        self.assertEqual(medication_status(med)[0],"Aviso 07:00")

    def test_one_clock_and_meal_condition_are_not_confused(self):
        self.assertEqual(canonical_reminder_fields("08:00",""),{
            "reminder_time":"08:00","time":"08:00"})
        self.assertEqual(canonical_reminder_fields("08:00","Jejum"),{
            "reminder_time":"08:00","time":"Jejum"})
        self.assertEqual(condition_value({"time":"Pequeno-almoço"}),"Pequeno-almoço")
        for wrong in ("08:01","7h00","23:80"):
            with self.subTest(wrong=wrong):
                with self.assertRaises(ValueError):
                    canonical_reminder_fields("08:00",wrong)
        with self.assertRaises(ValueError):
            canonical_reminder_fields("25:01","")

    def test_save_edit_reload_card_date_and_android_original(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/"synthetic.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=file),patch.object(
                secure_store,"_encrypt",side_effect=lambda b:b),patch.object(
                secure_store,"_decrypt",side_effect=lambda b:b):
                store=secure_store.SecureStore()
                person=store.create_profile("Pessoa fictícia")
                record=store.save_medication(person["id"],{
                    "name":"Medicamento fictício","dose":"5 mg",
                    "time":"07:00","reminder_time":"07:00","no_alarm":False,
                    "administration_route":"oral"})
                record["time"]="08:00"  # old version wrote the wrong field
                record["android_original"]={
                    "time":"07:00","reminder_time":"07:00",
                    "repeat_mode":"daily"}
                store.save()
                self.assertEqual(mismatched_legacy_clock(record),"08:00")
                change=canonical_reminder_fields("08:00","")
                edited=store.save_medication(person["id"],{
                    "name":"Medicamento fictício","dose":"5 mg",
                    **change,"no_alarm":False,"suspended":False,
                    "administration_route":"oral"},record["id"])
                self.assertEqual(edited["time"],"08:00")
                self.assertEqual(edited["reminder_time"],"08:00")
                self.assertEqual(edited["android_original"]["reminder_time"],"07:00")
                again=secure_store.SecureStore().get_profile(person["id"])
                saved=again["medications"][0]
                self.assertEqual(medication_status(saved)[0],"Aviso 08:00")
                self.assertEqual(reminder_clock(saved),"08:00")
                self.assertEqual(next_medication_label(saved,datetime(2026,11,3,6,30)),
                                 "Próxima toma prevista: 2026-11-03 · 08:00")
                self.assertEqual(mismatched_legacy_clock(saved),"")

    def test_prevent_conflicting_time_fields_on_store(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/"test.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=file),patch.object(
                secure_store,"_encrypt",side_effect=lambda b:b),patch.object(
                secure_store,"_decrypt",side_effect=lambda b:b):
                store=secure_store.SecureStore()
                pid=store.create_profile("Fictício")["id"]
                with self.assertRaises(secure_store.LocalStoreError):
                    store.save_medication(pid,{"name":"Exemplo","dose":"5 mg",
                        "time":"08:00","reminder_time":"07:00"})
                self.assertEqual(store.get_profile(pid)["medications"],[])

    def test_ui_shows_one_editable_hour_and_recovery_button(self):
        text=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text("utf-8")
        self.assertIn('VERSION = "0.8.6"',text)
        self.assertNotIn('"Hora / indicação da toma"',text)
        self.assertIn('basic,"Condição da toma (ex.: jejum)",condition_value(fields)',text)
        self.assertIn('"Usar hora anterior "+old_clock',text)
        self.assertIn('fields.update(canonical_reminder_fields(',text)

if __name__=="__main__":
    unittest.main()
