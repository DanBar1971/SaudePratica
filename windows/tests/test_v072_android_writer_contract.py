"""Portable format compatibility with the Android writer's documented fields.

These tests simulate Android's on-disk JSON/ZIP output in Python and exercise
the REAL Windows parser and store. An Android device still must run a later
end-to-end test of the Kotlin implementation.
"""
import base64
import hashlib
import io
import json
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

from shared.python.saude_backup import create_backup,read_backup
from windows import secure_store


PASSWORD="synthetic 2026 password for tests"


def synthetic_android_backup():
    """Same path names, field layout and digest as PortableWindowsBackup.kt."""
    android_id=str(uuid.uuid4())
    windows_id=android_id
    medication_image=b"\xff\xd8" + bytes(range(256)) * 8 + b"\xff\xd9"
    avatar=b"\xff\xd8" + bytes(range(255,-1,-1)) * 5 + b"\xff\xd9"
    document=b"%PDF-1.4\nSynthetic, not a real medical document.\n%%EOF\n"
    medias=[
        ("medication_photos/medphoto.jpg",medication_image,"fotografia de medicamento"),
        (f"saudepratica_identity/{android_id}/avatar.jpg",avatar,"documento"),
        (f"saudepratica_documents/{android_id}/report.pdf",document,"documento"),
    ]
    original=io.BytesIO()
    with zipfile.ZipFile(original,"w",zipfile.ZIP_DEFLATED) as arc:
        for path,raw,_ in medias:
            arc.writestr("data/"+path,raw)
        arc.writestr(
            f"data/saudepratica_profiles/{android_id}/medicacao.json",
            json.dumps({"medications":[{"id":"med-1","medication":"Medicamento fictício",
                 "dose":"5 mg","images":["medication_photos/medphoto.jpg"]}]}))
        arc.writestr(
            f"data/saudepratica_profiles/{android_id}/agenda.json",
            json.dumps({"appointments":[{"id":"apt-1","date":"2026-11-20",
                "activity":"Consulta fictícia","time":"09:30"}]}))
        arc.writestr("backup.json",json.dumps({
            "kind":"saudepratica-complete-backup","format":1,"profiles":1,
            "files":[],"prefs":{}}))
    rawzip=original.getvalue()
    digest=hashlib.sha256(rawzip).hexdigest()
    descriptor={
        "sha256":digest,"bytes":len(rawzip),
        "filename":"SaudePratica-backup-Android-original.zip",
        "profile_ids":[windows_id],"source_ids":[android_id],
    }
    pfx=f"profiles/{windows_id}/"
    profile={
        "id":windows_id,"name":"Pessoa de teste Android",
        "android_zip_source_id":android_id,
        "android_zip_source_name":"Pessoa de teste Android",
        "android_profile_original":{"id":android_id,"name":"Pessoa de teste Android"},
        "photo_b64":base64.b64encode(avatar).decode("ascii"),
    }
    med={
        "id":str(uuid.uuid4()),"name":"Medicamento fictício","dose":"5 mg",
        "android_source_key":"med:med-1",
        "android_source_id":"med-1",
        "android_original":{"id":"med-1","medication":"Medicamento fictício",
            "dose":"5 mg","images":["medication_photos/medphoto.jpg"]},
        "photo_b64":base64.b64encode(medication_image).decode("ascii"),
    }
    agenda={"id":str(uuid.uuid4()),"title":"Consulta fictícia","date":"2026-11-20",
            "time":"09:30"}
    files={
        pfx+"profile.json":json.dumps(profile).encode(),
        pfx+"medicacao.json":json.dumps({"medications":[med]}).encode(),
        pfx+"agenda.json":json.dumps({"appointments":[agenda]}).encode(),
        pfx+"backup_scope.json":json.dumps({"scope":"family","format":2,
            "profile_count":1}).encode(),
        pfx+"android_archives.json":json.dumps([descriptor]).encode(),
        f"attachments/{digest[:2]}/{digest}.bin":rawzip,
    }
    attachments=[]
    for path,raw,category in medias:
        h=hashlib.sha256(raw).hexdigest()
        files[f"attachments/{h[:2]}/{h}.bin"]=raw
        attachments.append({
            "profile_id":windows_id,
            "path":path,"filename":path.split("/")[-1],
            "display_name":path.split("/")[-1],
            "category":category,"sha256":h,"bytes":len(raw),
        })
    files[pfx+"attachments.json"]=json.dumps(attachments).encode()
    return create_backup(files,PASSWORD),windows_id,rawzip,medication_image,avatar


class AndroidWriterShapeCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"userdata"/"profile_data.dpapi"
        self.path.parent.mkdir()
        encrypt=patch.object(secure_store,"_encrypt",side_effect=lambda b:b)
        decrypt=patch.object(secure_store,"_decrypt",side_effect=lambda b:b)
        encrypt.start();decrypt.start()
        self.addCleanup(encrypt.stop);self.addCleanup(decrypt.stop)

    def store(self):
        with patch.object(secure_store,"_user_data_path",return_value=self.path):
            return secure_store.SecureStore()

    def test_android_layout_to_windows_then_reexport_with_all_images(self):
        data,pid,original,medimage,avatar=synthetic_android_backup()
        source=read_backup(data,PASSWORD)
        self.assertEqual(len(source),9)
        target=self.store()
        plan=target.inspect_portable_backup(data,PASSWORD)
        self.assertEqual(len(plan.people),1)
        self.assertEqual(plan.people[0].medications,1)
        self.assertEqual(plan.people[0].appointments,1)
        self.assertEqual(plan.people[0].attachments,3)
        result=target.restore_portable_backup(plan,PASSWORD)
        self.assertEqual(result["created"],1)
        self.assertEqual(result["replaced"],0)
        self.assertEqual(len(target.profiles()),1)
        profile=target.get_profile(pid)
        self.assertEqual(base64.b64decode(profile["photo_b64"]),avatar)
        self.assertEqual(base64.b64decode(
            profile["medications"][0]["photo_b64"]),medimage)
        self.assertEqual(len(target.imported_assets(pid)),3)
        hashes=[x["sha256"] for x in target.imported_assets(pid)]
        self.assertIn(hashlib.sha256(medimage).hexdigest(),hashes)
        self.assertEqual(target.export_original_android_zip(hashlib.sha256(
            original).hexdigest()),original)
        exported=target.export_backup(PASSWORD)
        exported_files=read_backup(exported,PASSWORD)
        self.assertIn(f"profiles/{pid}/medicacao.json",exported_files)
        self.assertIn(f"profiles/{pid}/attachments.json",exported_files)
        repeated=target.inspect_portable_backup(exported,PASSWORD)
        self.assertEqual(repeated.people[0].operation,"replace")
        result=target.restore_portable_backup(repeated,PASSWORD)
        self.assertEqual(result["replaced"],1)
        self.assertEqual(len(target.profiles()),1)
        self.assertEqual(len(target.imported_assets(pid)),3)

    def test_incomplete_portable_metadata_does_not_replace_patients(self):
        data,pid,*_=synthetic_android_backup()
        store=self.store()
        existing=store.create_profile("Pessoa existente no Windows")
        original_count=len(store.profiles())
        verified=read_backup(data,PASSWORD)
        key=f"profiles/{pid}/attachments.json"
        listed=json.loads(verified[key])
        # The declared original document digest is missing in the package.
        omitted=listed[0]["sha256"]
        verified.pop(f"attachments/{omitted[:2]}/{omitted}.bin")
        from windows.portable_restore_v072 import inspect
        from shared.python.saude_backup import BackupError
        with self.assertRaises(BackupError):
            inspect(verified,store.profiles())
        self.assertEqual(len(store.profiles()),original_count)
        self.assertEqual(store.get_profile(existing["id"])["name"],
                         "Pessoa existente no Windows")


if __name__=="__main__":
    unittest.main()
