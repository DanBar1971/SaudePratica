"""Synthetic regressions for Android clinical profile field transport and Windows UI.

Uses only generated fake data. Ensures independent patients stay isolated.
"""
import io
import json
import tempfile
import unittest
import uuid
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED
from windows import secure_store
from windows.android_profile_v067 import read_profile_extras
from windows.tests.test_v063_archive import _archive_files, make_zip
from shared.python.saude_backup import read_backup

SRC="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OTHER="bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
PWD="Test-only fake password 2026"

def synthetic_profile_zip():
    original=make_zip(_archive_files())
    buf=io.BytesIO()
    with ZipFile(io.BytesIO(original)) as old, ZipFile(buf,"w",ZIP_DEFLATED) as new:
        for name in old.namelist():
            raw=old.read(name)
            if name=="backup.json":
                head=json.loads(raw)
                head["prefs"]["saudepratica_profile_"+SRC]={
                    "full_name":{"t":"s","v":"Nome Completo Fictício"},
                    "birth_date":{"t":"s","v":"03/05/1984"},
                    "phone":{"t":"s","v":"900000001"},
                    "nif":{"t":"s","v":"000000000"},
                    "sns_number":{"t":"s","v":"000000001"},
                    "niss":{"t":"s","v":"00000000001"},
                    "health_unit":{"t":"s","v":"Unidade Fictícia"},
                    "address":{"t":"s","v":"Rua de Teste"},
                    "postal_code":{"t":"s","v":"1000-001"},
                    "password":{"t":"s","v":"secret must not be exposed"},
                }
                head["prefs"]["saudepratica_profile_"+OTHER]={
                    "full_name":{"t":"s","v":"Other Person Secret"},
                }
                head["prefs"]["saudepratica_profiles_v1"]["profiles"]["v"]=json.dumps([
                    {"id":"legacy","name":"Pessoa principal fictícia"},
                    {"id":SRC,"name":"Pessoa Exemplo","caregiver":True},
                    {"id":OTHER,"name":"Outro"},{"id":"extraneous","name":"Ignored"}])
                raw=json.dumps(head).encode()
            new.writestr(name,raw)
    return buf.getvalue()

class AndroidProfileV073(unittest.TestCase):
    def test_typed_preferences_from_correct_person_only(self):
        fields, rows=read_profile_extras(synthetic_profile_zip(),SRC)
        self.assertEqual(fields["full_name"],"Nome Completo Fictício")
        self.assertEqual(fields["birth_date"],"1984-05-03")
        self.assertEqual(fields["health_unit"],"Unidade Fictícia")
        self.assertEqual(fields["nif"],"000000000")
        self.assertEqual(fields["sns_number"],"000000001")
        self.assertTrue(fields["caregiver"])
        self.assertNotIn("Other Person Secret",str(fields))
        self.assertNotIn("secret must not be exposed",str(rows))

    def test_portable_family_roundtrip_hydrates_fields_and_saves_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/"source"/"data.dpapi"
            b=Path(tmp)/"target"/"data.dpapi"
            a.parent.mkdir();b.parent.mkdir()
            with patch.object(secure_store,"_encrypt",side_effect=lambda x:x),patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                with patch.object(secure_store,"_user_data_path",return_value=a):
                    src=secure_store.SecureStore()
                p=src.create_profile("Pessoa Exemplo")
                p["android_zip_source_id"]=SRC
                raw=synthetic_profile_zip()
                digest=sha256(raw).hexdigest()
                src._write_assets([(digest,raw)])
                src.data["android_family_archives"]=[{
                    "sha256":digest,"bytes":len(raw),"filename":"synthetic-android.zip",
                    "profile_ids":[p["id"]],"source_ids":[SRC]}]
                src.save()
                portable=src.export_backup(PWD)
                with patch.object(secure_store,"_user_data_path",return_value=b):
                    dst=secure_store.SecureStore()
                plan=dst.inspect_portable_backup(portable,PWD)
                out=dst.restore_portable_backup(plan,PWD)
                self.assertEqual(out["profiles"],1)
                saved=dst.profiles()[0]
                self.assertEqual(saved["full_name"],"Nome Completo Fictício")
                self.assertEqual(saved["birth_date"],"1984-05-03")
                self.assertEqual(saved["niss"],"00000000001")
                self.assertTrue(saved["caregiver"])
                changed=dst.save_profile({"name":"Pessoa Exemplo",
                    "full_name":"Alteração no Windows",
                    "birth_date":"1984-05-03",
                    "niss":"00000000001","sns_number":"000000001",
                    "phone":"900000001","caregiver":True},saved["id"])
                self.assertEqual(changed["full_name"],"Alteração no Windows")
                outgoing=read_backup(dst.export_backup(PWD),PWD)
                filename=f"profiles/{saved['id']}/profile.json"
                restored=json.loads(outgoing[filename])
                self.assertEqual(restored["full_name"],"Alteração no Windows")
                self.assertEqual(restored["sns_number"],"000000001")

    def test_current_profile_ui_contains_complete_editable_fields(self):
        code=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text(encoding="utf-8")
        for token in ['"full_name"','"birth_place"','"sns_number"','"nif"','"adse_number"']:
            self.assertIn(token,code)
        self.assertIn("self.profile_widgets[key]",code)

if __name__=="__main__":
    unittest.main()
