"""Synthetic Android ZIP interop and DPAPI attachment round-trip tests.
Never commit real patient JSON, photos, documents or family backup.
"""
import io,json,hashlib,sys,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from windows.android_import_v062 import plan_json,apply_plan,AndroidImportError
from windows.android_archive_v063 import archive_sources,prepare_archive,validated_files,apply_archive
from windows import secure_store
from windows.secure_store import LocalStoreError
from shared.python.saude_backup import BackupError

def _payload(key,values):
    return json.dumps({key:values},ensure_ascii=False).encode()
def _archive_files():
    from PIL import Image
    img=io.BytesIO()
    Image.new("RGB",(20,20),"cyan").save(img,format="JPEG")
    data=img.getvalue()
    return {
      "agenda.json":_payload("appointments",[
        {"id":"same-id","date":"2026-11-01","time":"09:00",
         "activity":"Consulta sintética","department":"Hospital fictício"},
        {"id":"same-id","date":"2026-11-01","time":"11:00",
         "activity":"Exame sintético","department":"Hospital fictício"},
        {"id":"same-id","date":"2026-11-01","time":"09:00",
         "activity":"Consulta sintética","department":"Hospital fictício"},
      ]),
      "medicacao.json":_payload("medications",[
        {"id":"x","medication":"Comprimido fictício","dose":"5 mg",
         "time":"Jejum","reminder_time":"07:00",
         "images":["/data/user/0/example/files/medication_photos/img.jpg"]}]),
      "medication_photos/img.jpg":data,
      "saudepratica_documents/legacy/index.json":json.dumps([
          {"id":"doc1","fileName":"0001.pdf","name":"Relatório fictício"}]).encode(),
      "saudepratica_documents/legacy/0001.pdf":b"%PDF-1.4\n% fake document for synthetic test",
      "saudepratica_identity/legacy/avatar.jpg":data,
      "saudepratica_profiles/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/agenda.json":
        _payload("appointments",[]),
      "saudepratica_profiles/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/medicacao.json":
        _payload("medications",[]),
    }
def make_zip(files=None):
    files=files if files is not None else _archive_files()
    header={"kind":"saudepratica-complete-backup","format":1,
            "prefs":{"saudepratica_profiles_v1":{"profiles":{
                "t":"s","v":json.dumps([
                    {"id":"legacy","name":"Pessoa principal fictícia"},
                    {"id":"aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa","name":"Pessoa B fictícia"}])}}},
            "files":[{"path":p,"sha256":hashlib.sha256(b).hexdigest(),"size":len(b)}
                     for p,b in sorted(files.items())]}
    output=io.BytesIO()
    with ZipFile(output,"w",compression=ZIP_DEFLATED) as z:
        z.writestr("backup.json",json.dumps(header))
        for p,b in files.items():z.writestr("data/"+p,b)
    return output.getvalue()

class ImportRealAndroidSchemaTests(unittest.TestCase):
    def setUp(self):
        self.profile={"id":"11111111-1111-4111-8111-111111111111",
                      "name":"Perfil fictício","appointments":[],"medications":[]}
    def test_duplicate_android_appointment_id_keeps_different_times(self):
        data=json.loads(_archive_files()["agenda.json"])
        plan=plan_json(_payload("appointments",data["appointments"]),
             "appointments",self.profile)
        self.assertEqual(len(plan.new),2)
        self.assertEqual(plan.repeated,1)
        self.assertEqual(len({m["id"] for m in plan.new}),2)
        self.assertEqual(plan.new[0]["title"],"Consulta sintética")
    def test_zip_sources_and_document_mapping(self):
        blob=make_zip()
        sources=archive_sources(blob)
        self.assertEqual(len(sources),2)
        self.assertEqual(sources[0].medications,1)
        self.assertEqual(sources[0].appointments,3)
        plan=prepare_archive(blob,"legacy",self.profile)
        self.assertEqual(len(plan.appointments.new),2)
        self.assertEqual(len(plan.medications.new),1)
        self.assertEqual(len(plan.attachments),3)
        self.assertTrue(plan.avatar_b64)
        self.assertTrue(any(x[4]=="Relatório fictício" for x in plan.attachments))
        self.assertTrue(plan.medications.new[0]["photo_b64"])
    def test_zip_manifest_tamper_rejected(self):
        files=_archive_files()
        blob=make_zip(files)
        altered=bytearray(blob)
        # The ZIP remains structural, but any changed manifest size/hash fails.
        with ZipFile(io.BytesIO(blob)) as z:
            header=json.loads(z.read("backup.json"))
            header["files"][0]["sha256"]="0"*64
            output=io.BytesIO()
            with ZipFile(output,"w") as w:
                w.writestr("backup.json",json.dumps(header))
                for entry in z.infolist():
                    if entry.filename!="backup.json":
                        w.writestr(entry.filename,z.read(entry.filename))
        with self.assertRaises(AndroidImportError):validated_files(output.getvalue())
    def test_zip_path_traversal_rejected(self):
        files=_archive_files()
        files["../path.pdf"]=b"bad"
        with self.assertRaises(AndroidImportError):validated_files(make_zip(files))
    def test_secure_import_and_spbackup_roundtrip(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            first=Path(folder)/"first"/"profile_data.dpapi"
            second=Path(folder)/"second"/"profile_data.dpapi"
            first.parent.mkdir()
            second.parent.mkdir()
            # Tests substitute encryption only. Production uses Windows DPAPI.
            with patch.object(secure_store,"_user_data_path",return_value=first),\
                 patch.object(secure_store,"_encrypt",side_effect=lambda x:x),\
                 patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                store=secure_store.SecureStore()
                profile=store.save_profile({"name":"Exemplo"})
                plan=prepare_archive(make_zip(),"legacy",profile)
                result=apply_archive(store,plan)
                self.assertEqual(result["appointments"],2)
                self.assertEqual(result["medications"],1)
                self.assertEqual(result["attachments"],3)
                self.assertEqual(len(store.imported_assets(profile["id"])),3)
                sp=store.export_backup("uma palavra-passe longa")
                self.assertTrue(sp.startswith(b"SAUDEPRATICA-BACKUP-V1"))
                with patch.object(secure_store,"_user_data_path",return_value=second):
                    target=secure_store.SecureStore()
                    people,verified=target.inspect_backup(sp,"uma palavra-passe longa")
                    self.assertEqual(len(people),1)
                    self.assertEqual(target.restore_backup(verified),1)
                    new_id=people[0]["id"]
                    self.assertEqual(len(target.get_profile(new_id)["appointments"]),2)
                    files=target.imported_assets(new_id)
                    self.assertEqual(len(files),3)
                    self.assertTrue(target.read_imported_asset(files[0]))
    def test_import_same_zip_again_only_skips(self):
        with tempfile.TemporaryDirectory() as folder:
            store_path=Path(folder)/"profile_data.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=store_path),\
                 patch.object(secure_store,"_encrypt",side_effect=lambda x:x),\
                 patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                store=secure_store.SecureStore()
                profile=store.save_profile({"name":"Exemplo"})
                blob=make_zip()
                apply_archive(store,prepare_archive(blob,"legacy",profile))
                plan=prepare_archive(blob,"legacy",profile)
                result=apply_archive(store,plan)
                self.assertEqual(result,{"medications":0,"appointments":0,"attachments":0})

    def test_reimport_rejects_corrupted_existing_photo_without_data_loss(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"profile_data.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=path),\
                 patch.object(secure_store,"_encrypt",side_effect=lambda x:x),\
                 patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                store=secure_store.SecureStore()
                profile=store.save_profile({"name":"Perfil de teste"})
                archive=make_zip()
                apply_archive(store,prepare_archive(archive,"legacy",profile))
                entry=store.imported_assets(profile["id"])[0]
                store._asset_path(entry["sha256"]).write_bytes(b"corrupted ciphertext")
                medications_before=list(profile["medications"])
                appointments_before=list(profile["appointments"])
                with self.assertRaisesRegex(AndroidImportError,"corrompido"):
                    apply_archive(store,prepare_archive(archive,"legacy",profile))
                self.assertEqual(profile["medications"],medications_before)
                self.assertEqual(profile["appointments"],appointments_before)

    def test_restore_rejects_existing_corrupted_dpapi_blob_atomically(self):
        with tempfile.TemporaryDirectory() as folder:
            first=Path(folder)/"source"/"profile_data.dpapi"
            second=Path(folder)/"target"/"profile_data.dpapi"
            first.parent.mkdir()
            second.parent.mkdir()
            with patch.object(secure_store,"_encrypt",side_effect=lambda x:x),\
                 patch.object(secure_store,"_decrypt",side_effect=lambda x:x),\
                 patch.object(secure_store,"_user_data_path",return_value=first):
                source=secure_store.SecureStore()
                person=source.save_profile({"name":"Perfil fictício"})
                apply_archive(source,prepare_archive(make_zip(),"legacy",person))
                exported=source.export_backup("palavra-passe de teste")
                digest=source.imported_assets(person["id"])[0]["sha256"]
                with patch.object(secure_store,"_user_data_path",return_value=second):
                    target=secure_store.SecureStore()
                    _,verified=target.inspect_backup(exported,"palavra-passe de teste")
                    target._asset_path(digest).write_bytes(b"bad DPAPI content")
                    with self.assertRaisesRegex(LocalStoreError,"corrompido"):
                        target.restore_backup(verified)
                    self.assertEqual(len(target.profiles()),0)
                    self.assertEqual(target.imported_assets(person["id"]),[])

    def test_restore_rejects_mismatched_profile_path_without_creating_profiles(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"profile_data.dpapi"
            with patch.object(secure_store,"_user_data_path",return_value=path),\
                 patch.object(secure_store,"_encrypt",side_effect=lambda x:x),\
                 patch.object(secure_store,"_decrypt",side_effect=lambda x:x):
                target=secure_store.SecureStore()
                identifier="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
                root="profiles/"+identifier+"/"
                files={
                    "profiles/not-the-same/profile.json":
                        json.dumps({"id":identifier,"name":"Teste"}).encode(),
                    root+"medicacao.json":_payload("medications",[]),
                    root+"agenda.json":_payload("appointments",[]),
                }
                with self.assertRaisesRegex(BackupError,"Caminho"):
                    target.restore_backup(files)
                self.assertEqual(target.profiles(),[])

if __name__=="__main__":unittest.main()
