"""Regression tests for visible dual-pane OCR workflow, synthetic examples only."""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
import unittest
import pymupdf
from PIL import Image, ImageDraw, ImageFont
from windows.document_ocr_v081 import (
    preview_document, recognize_document, suggest_fields, DocumentRecognitionError
)

class V081DocumentOCRTests(unittest.TestCase):
    def test_pdf_extracts_native_text_and_generates_preview(self):
        doc=pymupdf.open()
        page=doc.new_page(width=600,height=700)
        page.insert_text((50,70),"Medicamento: Ficticio de teste",fontsize=14)
        page.insert_text((50,98),"Dose: 25 mg",fontsize=14)
        page.insert_text((50,125),"Data da receita: 03/11/2026",fontsize=14)
        raw=doc.tobytes()
        doc.close()
        text=recognize_document(raw,"prescricao.pdf")
        self.assertIn("Ficticio de teste",text)
        self.assertIn("Dose: 25 mg",text)
        self.assertTrue(preview_document(raw,"prescricao.pdf").startswith(b"\xff\xd8\xff"))

    def test_suggests_only_labelled_clinical_fields(self):
        recognized=("Medicamento: Levotiroxina\nDose: 0.025 mg\n"
                    "Data da prescrição: 15/10/2026\n"
                    "Prescritor: Pessoa de teste")
        m=suggest_fields("medication",recognized)
        self.assertEqual(m["name"],"Levotiroxina")
        self.assertEqual(m["dose"],"0.025 mg")
        self.assertEqual(m["prescription_date"],"2026-10-15")
        self.assertNotIn("reminder_time",m)
        appointment=("Data: 10/11/2026\nHora: 11:30\n"
                     "Local: Hospital fictício\nServiço: Hematologia")
        a=suggest_fields("appointment",appointment)
        self.assertEqual(a["date"],"2026-11-10")
        self.assertEqual(a["time"],"11:30")
        self.assertEqual(a["location"],"Hospital fictício")
        self.assertEqual(a["department"],"Hematologia")

    def test_invalid_file_is_rejected(self):
        with self.assertRaises(DocumentRecognitionError):
            recognize_document(b"{}", "a.json")

    def test_image_ocr_offline_engine(self):
        im=Image.new("RGB",(1100,230),"white")
        draw=ImageDraw.Draw(im)
        try:font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",54)
        except OSError:font=ImageFont.load_default()
        draw.text((40,60),"DOSE: 25 mg",font=font,fill="black")
        out=BytesIO(); im.save(out,format="PNG")
        result=recognize_document(out.getvalue(),"medication.png")
        self.assertTrue(result.strip(), "O motor OCR deve ler texto de uma imagem.")

    def test_dual_pane_and_no_raw_technical_fields(self):
        source=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text(encoding="utf-8")
        med=source.split("    def _med_form(self,frame,med):",1)[1].split(
            "    def _attach_med_document(self,key,dropdown):",1)[0]
        apt=source.split("    def _appointment_form(self,person):",1)[1].split(
            "    def _set_agenda_filter(self,key):",1)[0]
        self.assertIn("self._editor_split(frame)",med)
        self.assertIn('tabs.add("Principal")',med)
        self.assertIn('self._editor_split(self.body)',apt)
        self.assertIn('tabs.add("Marcação")',apt)
        self.assertIn('self._build_document_panel(right,"appointment",values)',apt)
        self.assertNotIn("appointment_extras(values)",apt)
        self.assertNotIn("parse_appointment_extra",apt)
        self.assertIn('VERSION = "0.8.15"',source)

if __name__=="__main__":
    unittest.main()
