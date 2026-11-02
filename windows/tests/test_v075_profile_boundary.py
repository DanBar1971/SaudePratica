import io,json,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from windows import secure_store
from shared.python.saude_backup import read_backup
from zipfile import ZipFile,ZIP_DEFLATED
from windows.android_profile_v067 import read_profile_extras
from windows.tests.test_v063_archive import make_zip,_archive_files
from windows.profile_data_guard_v075 import overlaps_medication
A="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
B="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

def fake_family():
    files=_archive_files()
    files[f"saudepratica_profiles/{A}/medicacao.json"]=json.dumps({"medications":[{"notes":"sample drug memo"}]}).encode()
    files[f"saudepratica_profiles/{A}/agenda.json"]=json.dumps({"appointments":[{"notes":"sample agenda memo"}]}).encode()
    blob=make_zip(files)
    output=io.BytesIO()
    with ZipFile(io.BytesIO(blob)) as old,ZipFile(output,"w",ZIP_DEFLATED) as new:
        for name in old.namelist():
            raw=old.read(name)
            if name=="backup.json":
                head=json.loads(raw)
                head["prefs"]["saudepratica_caregiver_v1"]={"caregiver_id":{"t":"s","v":A}}
                head["prefs"]["saudepratica_profile_"+A]={"father_name":{"t":"s","v":"Pai fictício"}}
                head["prefs"]["saudepratica_emergency_"+A]={"contact_phone":{"t":"s","v":"999000111"},"notes":{"t":"s","v":"sample emergency memo"}}
                raw=json.dumps(head).encode()
            new.writestr(name,raw)
    return output.getvalue()

class ProfileBoundaryTests(unittest.TestCase):
    def test_exact_android_caregiver(self):
        family=fake_family()
        a,_=read_profile_extras(family,A)
        b,_=read_profile_extras(family,"legacy")
        self.assertTrue(a["caregiver"])
        self.assertFalse(b["caregiver"])
        self.assertEqual(a["father"],"Pai fictício")
    def test_only_personal_data(self):
        value,_=read_profile_extras(fake_family(),A)
        self.assertNotIn("notes",value)
        self.assertNotIn("emergency_phone",value)
        self.assertNotIn("999000111",str(value))
        self.assertNotIn("sample drug memo",str(value))
        self.assertNotIn("sample agenda memo",str(value))
        self.assertNotIn("sample emergency memo",str(value))
    def test_export_separates_profile_and_medication_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            location=Path(tmp)/"profile_data.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=location),patch.object(secure_store,"_encrypt",side_effect=lambda x:x),patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                store=secure_store.SecureStore()
                p=store.create_profile("Pessoa Fictícia")
                p["notes"]="example"
                p["medications"]=[{"id":"m1","name":"Medicamento Exemplo","android_original":{"notes":"example"}}]
                payload=store.export_backup("password for only tests")
                verified=read_backup(payload,"password for only tests")
                profile=json.loads(verified[f"profiles/{p['id']}/profile.json"])
                medicine=json.loads(verified[f"profiles/{p['id']}/medicacao.json"])
                self.assertNotIn("notes",profile)
                self.assertEqual(medicine["medications"][0]["android_original"]["notes"],"example")
    def test_medication_guard_exact_match(self):
        person={"medications":[{"android_original":{"notes":"example"}}]}
        self.assertTrue(overlaps_medication(person,"example"))
        self.assertFalse(overlaps_medication(person,"example other"))
if __name__=="__main__":
    unittest.main()
