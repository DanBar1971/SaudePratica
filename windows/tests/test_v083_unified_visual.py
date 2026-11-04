"""0.8.3: test time controls, editable dropdowns and global visual contracts.

All fixture medicine records and photos in CI are synthetic.
"""
from pathlib import Path
import unittest
from windows.editor_controls_v083 import (
    CONDITIONS,FREQUENCIES,REPETITIONS,REPEAT_TYPES,
    EXTRA_COMBO_CHOICES,shift_clock
)

class UnifiedEditorControls083(unittest.TestCase):
    def test_clock_arrows_increment_five_minutes_and_wrap_day(self):
        self.assertEqual(shift_clock("08:00",1),"08:05")
        self.assertEqual(shift_clock("08:00",-1),"07:55")
        self.assertEqual(shift_clock("23:58",1),"00:03")
        self.assertEqual(shift_clock("00:02",-1),"23:57")
        self.assertEqual(shift_clock("",1),"08:05")
        with self.assertRaises(ValueError):shift_clock("24:00",1)
        with self.assertRaises(ValueError):shift_clock("08:00",0)
        with self.assertRaises(ValueError):shift_clock("08:00",1,4)

    def test_choices_include_android_like_options_and_keep_free_text(self):
        self.assertIn("Jejum",CONDITIONS)
        self.assertIn("Às refeições",CONDITIONS)
        self.assertIn("1 vez ao dia",FREQUENCIES)
        self.assertIn("De 12 em 12 horas",FREQUENCIES)
        self.assertIn("Contínuo (sem fim)",REPETITIONS)
        self.assertIn("Diária",REPEAT_TYPES)
        self.assertEqual(set(EXTRA_COMBO_CHOICES),
                         {"frequency","repetitions","repeat_type"})

    def test_ui_presents_single_clock_with_spin_arrows_and_larger_real_photo(self):
        source=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text(encoding="utf-8")
        med=source.split("    def _med_form(self,frame,med):",1)[1].split(
            "    def _med_document_line(",1)[0]
        preview=source.split("    def _update_med_preview(self):",1)[1].split(
            "    def _remove_med_photo",1)[0]
        self.assertIn('VERSION = "0.8.13"',source)
        self.assertIn('self._time_stepper(',med)
        self.assertIn('self._editable_choice(',med)
        self.assertIn('EXTRA_COMBO_CHOICES[key]',med)
        self.assertIn('self._med_card_photo(self.med_photo_draft,width,height)',preview)
        self.assertIn('max(280,min(535,self.winfo_width()//3))',med)
        self.assertNotIn('self._authentic_thumb(self.med_photo_draft,85,62)',source)
        self.assertIn('("▲",1),("▼",-1)',source)
        self.assertIn('fields.update(canonical_reminder_fields(',source)

    def test_consistent_global_buttons_tabs_back_navigation(self):
        source=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text(encoding="utf-8")
        self.assertIn('def _editor_tabs(self,parent):',source)
        self.assertIn('segmented_button_selected_color="#078f93"',source)
        self.assertIn('corner_radius=14,border_width=1',source)
        self.assertIn('def _back_button(self,parent,label,command,width=155):',source)
        for label in ("Voltar à medicação","Voltar à Agenda",
                      "Voltar aos perfis","Voltar ao menu"):
            self.assertIn(label,source)
        self.assertEqual(source.count('tabs=self._editor_tabs(left)'),2)
        backup=(Path(__file__).resolve().parents[1]/"backup_ui_v072.py").read_text(encoding="utf-8")
        self.assertIn('height=35,corner_radius=10',backup)

if __name__=="__main__":
    unittest.main()
