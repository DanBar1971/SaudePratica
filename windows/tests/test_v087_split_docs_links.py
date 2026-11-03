"""Windows 0.8.11 synthetic acceptance tests: split panels, preview, safe links."""
from __future__ import annotations

import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from windows import secure_store
from windows.document_split_v087 import document_kind, render_document
from windows.important_links_v087 import (
    DEFAULT_LINKS, upsert_link, move_link, delete_link, validated_links,
)
from windows.doses_calendar_v085 import appointments_for_day


class LinksTests(unittest.TestCase):
    def test_default_websites_and_complete_crud(self):
        self.assertEqual(
            [x["url"] for x in DEFAULT_LINKS],
            ["https://www.sns24.gov.pt/pt/inicio",
             "https://www.ipolisboa.min-saude.pt"])
        a = upsert_link(DEFAULT_LINKS,"Meu link","https://example.org/a")
        self.assertEqual(len(a),3)
        uid = a[-1]["id"]
        changed = upsert_link(a,"Novo nome","https://example.org/b",uid)
        self.assertEqual(changed[-1]["title"],"Novo nome")
        moved = move_link(changed,uid,-1)
        self.assertEqual(moved[1]["id"],uid)
        removed = delete_link(moved,uid)
        self.assertEqual(removed,validated_links(DEFAULT_LINKS))
        self.assertEqual(delete_link(removed,"sns24")[0]["id"],"ipo-lisboa")
        self.assertEqual(delete_link(delete_link(removed,"sns24"),"ipo-lisboa"),[])

    def test_reject_schemes_credentials_bad_identifiers_and_duplicates(self):
        for address in ("file:///C:/secrets","javascript:alert(1)",
                        "data:text/html;base64,aGk=",
                        "https://person:password@example.org",
                        "https://example.org/has space",
                        "https://example.org/hi\nbye",
                        "https://example.org:bad/path"):
            with self.subTest(address=address),self.assertRaises(ValueError):
                upsert_link([], "Teste",address)
        with self.assertRaises(ValueError):
            validated_links([DEFAULT_LINKS[0],DEFAULT_LINKS[0]])
        with self.assertRaises(ValueError):
            move_link(DEFAULT_LINKS,"sns24",4)

    def test_dpapi_store_persists_empty_links_no_default_resurrection(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"store.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=path), \
                 patch.object(secure_store,"_encrypt",side_effect=lambda x:x), \
                 patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                store=secure_store.SecureStore()
                person=store.create_profile("Pessoa Sintética")
                self.assertEqual(store.important_links(),DEFAULT_LINKS)
                self.assertEqual(store.save_important_links([]),[])
                reloaded=secure_store.SecureStore()
                self.assertEqual(reloaded.important_links(),[])
                self.assertEqual(reloaded.get_profile(person["id"])["name"],
                                 "Pessoa Sintética")
                self.assertNotIn("important_web_links",reloaded.get_profile(person["id"]))
                modified=upsert_link([], "Portal", "https://example.org")
                store.save_important_links(modified)
                self.assertEqual(secure_store.SecureStore().important_links(), modified)


class DocumentPreviewTests(unittest.TestCase):
    def test_image_preview_without_disk(self):
        pic=BytesIO()
        Image.new("RGB",(320,240),(24,95,96)).save(pic,"PNG")
        raw=pic.getvalue()
        self.assertEqual(document_kind(raw,"sintetico.png"),"image")
        frame,pages=render_document(raw,"sintetico.png",0,150,140)
        self.assertEqual(pages,1)
        self.assertTrue(frame.width<=150 and frame.height<=140)
        with self.assertRaises(ValueError):
            render_document(raw,"sintetico.png",1)
        with self.assertRaises(ValueError):
            document_kind(b"PK\x03\x04something.zip","bad.zip")

    def test_pdf_preview_multiple_pages_kept_in_memory(self):
        import fitz
        pdf=fitz.open()
        for number in ("Um","Dois"):
            page=pdf.new_page(width=500,height=700)
            page.insert_text((40,40),"Documento sintético "+number)
        raw=pdf.tobytes()
        pdf.close()
        self.assertEqual(document_kind(raw,"teste.pdf"),"pdf")
        image,total=render_document(raw,"teste.pdf",1,400,450)
        self.assertEqual(total,2)
        self.assertLessEqual(image.height,450)
        self.assertLessEqual(image.width,400)

    def test_document_source_uses_own_profile_and_no_plaintext_spool(self):
        source=(Path(__file__).resolve().parents[1]/
                "document_split_v087.py").read_text(encoding="utf-8")
        self.assertIn("self.store.imported_assets(person[\"id\"])",source)
        self.assertIn('item.get("profile_id") == person["id"]',source)
        self.assertIn("fitz.open(stream=raw",source)
        self.assertIn("ImageWin.Dib(image)",source)
        self.assertNotIn("os.startfile(",source)
        self.assertNotIn("NamedTemporaryFile",source)


class LayoutTests(unittest.TestCase):
    def test_calendar_panels_real_and_compact(self):
        base=Path(__file__).resolve().parents[1]
        code=(base/"calendar_split_v087.py").read_text("utf-8")
        desktop=(base/"desktop_v04.py").read_text("utf-8")
        self.assertIn('VERSION = "0.8.11"',desktop)
        self.assertIn("self._calendar_left = left",code)
        self.assertIn("self._calendar_right = right",code)
        self.assertIn('grid.pack(fill="x"',code)
        self.assertIn("self._calendar_day_cells[day] = tile",code)
        self.assertIn("appointments_for_day(profile, selected)",code)
        self.assertIn("self.store.get_profile(self.active_id)",code)
        self.assertIn("self._calendar_choose(chosen)",code)
        self.assertIn('self.page=="shortcuts"',desktop)
        self.assertIn('self.page=="info"',desktop)

    def test_document_list_and_viewer_are_side_by_side(self):
        source=(Path(__file__).resolve().parents[1]/
                "document_split_v087.py").read_text("utf-8")
        self.assertIn("self._doc_list_panel = left",source)
        self.assertIn("self._doc_preview_panel = right",source)
        self.assertIn("self._doc_open_viewer",source)
        self.assertIn("self._doc_print",source)
        self.assertIn("self._doc_step",source)

    def test_appointments_stay_in_exact_profile(self):
        a={"appointments":[{"id":"x","date":"2026-11-10","time":"10:00"}]}
        b={"appointments":[{"id":"y","date":"2026-11-10","time":"10:00"}]}
        from datetime import date
        self.assertEqual(appointments_for_day(a,date(2026,11,10))[0]["id"],"x")
        self.assertEqual(appointments_for_day(b,date(2026,11,10))[0]["id"],"y")


if __name__=="__main__":
    unittest.main()
