"""Fake-person tests: no patient data, real-looking ZIP structure only."""
import io
import json
import unittest
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from windows.android_profile_v067 import read_profile_extras,read_profile_view
from windows.tests.test_v063_archive import make_zip,_archive_files
from windows.profile_fields_v066 import mapped_fields

A="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
B="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

def fake_android_zip():
    files=_archive_files()
    img=files["saudepratica_identity/legacy/avatar.jpg"]
    files[f"saudepratica_identity/{A}/cc_front.jpg"]=img
    files[f"saudepratica_identity/{A}/cc_back.jpg"]=img
    files[f"saudepratica_identity/{B}/cc_front.jpg"]=b"\xff\xd8\xff"+b"another-person"
    original=make_zip(files)
    buffer=io.BytesIO()
    with ZipFile(io.BytesIO(original)) as source,ZipFile(buffer,"w",ZIP_DEFLATED) as result:
        for name in source.namelist():
            data=source.read(name)
            if name=="backup.json":
                head=json.loads(data)
                head["prefs"]["saudepratica_profile_"+A]={
                   "full_name":{"t":"s","v":"Pessoa Fictícia"},
                   "father_name":{"t":"s","v":"Pai de Teste"},
                   "mother_name":{"t":"s","v":"Mãe de Teste"},
                   "cc_number":{"t":"s","v":"11111-FAKE"},
                   "cc_valid_until":{"t":"s","v":"01/01/2030"}}
                head["prefs"]["saudepratica_profile_"+B]={
                   "father_name":{"t":"s","v":"NÃO COPIAR"}}
                data=json.dumps(head,ensure_ascii=False).encode("utf-8")
            result.writestr(name,data)
    return buffer.getvalue()

class ProfileV074Tests(unittest.TestCase):
    def test_exact_father_mother_alias_and_cc(self):
        values=mapped_fields({"father_name":"Pai","mother_name":"Mãe",
                              "cc_number":"AB","cc_valid_until":"10/09/2031"})
        self.assertEqual(values["father"],"Pai")
        self.assertEqual(values["mother"],"Mãe")
        self.assertEqual(values["cc_number"],"AB")
        self.assertEqual(values["cc_valid_until"],"10/09/2031")

    def test_own_authentic_cc_photos_and_no_other_patient(self):
        blob=fake_android_zip()
        fields,photos=read_profile_view(blob,A)
        self.assertEqual(fields["father"],"Pai de Teste")
        self.assertEqual(fields["mother"],"Mãe de Teste")
        self.assertEqual(set(photos),{"cc_front","cc_back"})
        self.assertTrue(all(raw.startswith(b"\xff\xd8\xff") for raw in photos.values()))
        self.assertNotIn("NÃO COPIAR",str(fields))
        other,other_photos=read_profile_view(blob,B)
        self.assertEqual(other["father"],"NÃO COPIAR")
        self.assertEqual(other_photos,{})  # not accidentally borrowing A's CC
        _,rows=read_profile_extras(blob,A)
        self.assertEqual(rows,())

    def test_navigation_is_lazy_and_no_debug_data_render(self):
        root=Path(__file__).resolve().parents[1]
        src=(root/"desktop_v04.py").read_text(encoding="utf-8")
        method=src.split("    def _profile_form(self,frame):",1)[1].split("    def _refresh_photo(self):",1)[0]
        self.assertNotIn("profile_android_extras(",method)
        self.assertNotIn("profile_extra_rows",method)
        self.assertNotIn("saudepratica_health / records.json",method)
        self.assertIn("cc_photo_host",method)
        self.assertIn("self.profile_edit_open=False",src)
        self.assertIn("threading.Thread(target=read,daemon=True)",src)
        self.assertIn('VERSION = "0.7.7"',src)

if __name__=="__main__":
    unittest.main()
