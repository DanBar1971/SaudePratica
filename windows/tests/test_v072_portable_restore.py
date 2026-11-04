"""Regression tests: full .spbackup family/profile replace, media and rollback.

Synthetic data only. DPAPI is stubbed in Linux CI; real Windows CI uses the
same SecureStore serialization but substitutes Windows account protection.
"""
import copy
import json
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from hashlib import sha256

from windows import secure_store
from windows.portable_restore_v072 import inspect
from shared.python.saude_backup import read_backup, BackupError

PASSWORD="synthetic password for tests 2026!"

class BackupRestoreV072Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.a=Path(self.tmp.name)/"a"/"profile_data.dpapi"
        self.b=Path(self.tmp.name)/"b"/"profile_data.dpapi"
        self.a.parent.mkdir();self.b.parent.mkdir()
        self.encrypt=patch.object(secure_store,"_encrypt",side_effect=lambda b:b)
        self.decrypt=patch.object(secure_store,"_decrypt",side_effect=lambda b:b)
        self.encrypt.start();self.decrypt.start()
        self.addCleanup(self.encrypt.stop);self.addCleanup(self.decrypt.stop)

    def store(self,path):
        with patch.object(secure_store,"_user_data_path",return_value=path):
            return secure_store.SecureStore()

    def test_family_replaces_without_duplication_and_keeps_photos(self):
        src=self.store(self.a)
        person=src.create_profile("Pessoa Fictícia")
        med={"id":"m1","name":"Medicamento fictício","dose":"2 mg",
             "photo_b64":"U3ludGhldGljIGZha2U="}
        src.data["profiles"][0]["medications"]=[med]
        src.data["profiles"][0]["photo_b64"]="cGhvdG9fb25seV9zeW50aGV0aWM="
        src.data["profiles"][0]["appointments"]=[{"id":"a1","title":"Consulta"}]
        raw=b"synthetic document content - not clinical data"
        digest=sha256(raw).hexdigest()
        src._write_assets([(digest,raw)])
        src.data["imported_files"]=[{
          "profile_id":person["id"],"sha256":digest,
          "path":"saudepratica_documents/"+person["id"]+"/doc.pdf",
          "filename":"doc.pdf","category":"documento",
          "display_name":"Documento fictício","bytes":len(raw)}]
        src.save()
        portable=src.export_backup(PASSWORD)
        dest=self.store(self.b)
        other=dest.create_profile("Outro perfil")
        # Same person already exists with a different local UUID.
        existing=dest.create_profile("Pessoa Fictícia")
        existing["medications"]=[{"id":"old","name":"Registo ultrapassado"}]
        dest.save()
        plan=dest.inspect_portable_backup(portable,PASSWORD)
        target=next(p for p in plan.people if p.name=="Pessoa Fictícia")
        self.assertEqual(target.operation,"replace")
        self.assertEqual(target.target_id,existing["id"])
        result=dest.restore_portable_backup(plan,PASSWORD)
        self.assertEqual(result["created"],0)
        self.assertEqual(result["replaced"],1)
        self.assertEqual(len(dest.profiles()),2)
        self.assertEqual(dest.get_profile(existing["id"])["medications"],[med])
        self.assertEqual(dest.get_profile(existing["id"])["photo_b64"],
                         "cGhvdG9fb25seV9zeW50aGV0aWM=")
        self.assertEqual(len(dest.imported_assets(existing["id"])),1)
        self.assertEqual(dest.read_imported_asset(dest.imported_assets(existing["id"])[0]),raw)
        self.assertEqual(dest.get_profile(other["id"])["name"],"Outro perfil")
        self.assertTrue(Path(result["recovery"]).exists())
        again=dest.inspect_portable_backup(portable,PASSWORD)
        self.assertEqual(again.people[0].operation,"replace")
        dest.restore_portable_backup(again,PASSWORD)
        self.assertEqual(len(dest.profiles()),2)

    def test_single_profile_export_does_not_include_other_patient(self):
        src=self.store(self.a)
        p=src.create_profile("Pessoa A")
        q=src.create_profile("Pessoa B")
        src.data["profiles"][0]["medications"]=[{"id":"m","name":"Medicamento A"}]
        src.data["profiles"][1]["medications"]=[{"id":"n","name":"Medicamento B"}]
        src.save()
        payload=src.export_backup(PASSWORD,p["id"])
        verified=read_backup(payload,PASSWORD)
        self.assertEqual(len([k for k in verified if k.endswith("/profile.json")]),1)
        self.assertNotIn(f"profiles/{q['id']}/profile.json",verified)
        self.assertEqual(json.loads(verified[f"profiles/{p['id']}/backup_scope.json"])["scope"],"profile")
        self.assertNotIn(b"Pessoa B",b"".join(verified.values()))

    def test_tampered_or_missing_attachment_rejects_before_write(self):
        src=self.store(self.a)
        person=src.create_profile("Pessoa de Ensaio")
        backup=src.export_backup(PASSWORD)
        files=read_backup(backup,PASSWORD)
        key=f"profiles/{person['id']}/attachments.json"
        docs=[{"profile_id":person["id"],
               "sha256":"a"*64,"path":"path/test.jpg"}]
        files[key]=json.dumps(docs).encode()
        with self.assertRaises(BackupError):
            inspect(files,[])

    def test_ambiguous_name_fails_closed(self):
        src=self.store(self.a);src.create_profile("Pessoa X")
        backup=src.export_backup(PASSWORD)
        dst=self.store(self.b)
        dst.create_profile("Pessoa X")
        # simulate existing historical duplicate imported profile
        dst.data["profiles"].append({"id":str(uuid.uuid4()),"name":"Pessoa X",
            "medications":[],"appointments":[]})
        with self.assertRaises(BackupError):
            dst.inspect_portable_backup(backup,PASSWORD)

    def test_failed_save_rolls_back_without_partial_patient_restore(self):
        src=self.store(self.a);src.create_profile("Pessoa Fictícia")
        backup=src.export_backup(PASSWORD)
        dest=self.store(self.b);dest.create_profile("Pessoa Fictícia")
        before=copy.deepcopy(dest.data)
        plan=dest.inspect_portable_backup(backup,PASSWORD)
        with patch.object(dest,"save",side_effect=OSError("synthetic disk error")):
            with self.assertRaises(OSError):
                dest.restore_portable_backup(plan,PASSWORD)
        self.assertEqual(before,dest.data)
