"""Synthetic-only regression tests for complete family import/export Windows 0.6.4.

No actual patient data or production Android ZIPs are used.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from windows import secure_store
from windows.android_import_v062 import AndroidImportError
from windows.android_archive_v063 import validated_files
from windows.family_portability_v064 import plan_family_archive, plan_summary
from windows.secure_store import LocalStoreError
from windows.tests.test_v063_archive import make_zip
from shared.python.saude_backup import read_backup, BackupError

PASSWORD="synthetic password for family backups!"

class FamilyPortabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.first=Path(self.tmp.name)/"first"/"profile_data.dpapi"
        self.second=Path(self.tmp.name)/"second"/"profile_data.dpapi"
        self.first.parent.mkdir()
        self.second.parent.mkdir()
        # DPAPI is Windows-only; CI uses an identity substitute to exercise
        # file integrity and rollback. Production calls CryptProtectData.
        self.crypt=patch.object(secure_store,"_encrypt",side_effect=lambda raw:raw)
        self.uncrypt=patch.object(secure_store,"_decrypt",side_effect=lambda raw:raw)
        self.crypt.start();self.uncrypt.start()
        self.addCleanup(self.crypt.stop);self.addCleanup(self.uncrypt.stop)

    def store(self,path):
        with patch.object(secure_store,"_user_data_path",return_value=path):
            return secure_store.SecureStore()

    def test_import_all_preserves_original_zip_and_profiles(self):
        store=self.store(self.first)
        archive=make_zip()
        preview=plan_family_archive(archive,store.profiles())
        count=plan_summary(preview)
        self.assertEqual(count["profiles"],2)
        self.assertEqual(count["new_profiles"],2)
        self.assertEqual(count["original_files"],len(validated_files(archive)[0]))
        self.assertEqual(len(store.profiles()),0) # preview never writes
        outcome=store.import_android_family(preview)
        self.assertEqual(outcome["new_profiles"],2)
        self.assertEqual(len(store.profiles()),2)
        self.assertEqual(len(store.android_archives()),1)
        self.assertEqual(store.export_original_android_zip(preview.digest),archive)
        names={p["name"] for p in store.profiles()}
        self.assertIn("Pessoa principal fictícia",names)
        first=next(p for p in store.profiles() if p["android_zip_source_id"]=="legacy")
        self.assertEqual(len(first["medications"]),1)
        self.assertEqual(len(first["appointments"]),2) # exact duplicate skipped
        self.assertEqual(len(store.imported_assets(first["id"])),3)
        self.assertFalse(any("original_zip" in p for p in store.profiles()))
        # Zero duplicate imports, same profile associations and saved ZIP.
        repeated=plan_family_archive(archive,store.profiles())
        self.assertEqual(plan_summary(repeated)["new_profiles"],0)
        self.assertEqual(plan_summary(repeated)["medications"],0)
        store.import_android_family(repeated)
        self.assertEqual(len(store.profiles()),2)
        self.assertEqual(len(store.android_archives()),1)

    def test_encrypted_spbackup_roundtrip_retains_raw_android_bytes(self):
        first=self.store(self.first)
        source=make_zip()
        plan=plan_family_archive(source,first.profiles())
        first.import_android_family(plan)
        encrypted=first.export_backup(PASSWORD)
        self.assertTrue(encrypted.startswith(b"SAUDEPRATICA-BACKUP-V1\n"))
        self.assertNotIn(b"Pessoa principal",encrypted)
        original=read_backup(encrypted,PASSWORD)
        ids={p["id"] for p in first.profiles()}
        self.assertTrue(all(
            f"profiles/{pid}/android_archives.json" in original for pid in ids))
        restored=self.store(self.second)
        profiles,verified=restored.inspect_backup(encrypted,PASSWORD)
        self.assertEqual(len(profiles),2)
        self.assertEqual(restored.restore_backup(verified),2)
        self.assertEqual(len(restored.profiles()),2)
        self.assertEqual(restored.export_original_android_zip(plan.digest),source)
        self.assertEqual(len(restored.imported_assets(next(p["id"] for p in
            restored.profiles() if p["android_zip_source_id"]=="legacy"))),3)
        with self.assertRaises(BackupError):
            restored.restore_backup(verified)

    def test_invalid_zip_does_not_modify_store(self):
        store=self.store(self.first)
        with self.assertRaises(AndroidImportError):
            plan_family_archive(b"not-a-zip",store.profiles())
        self.assertEqual(store.profiles(),[])
        self.assertEqual(store.android_archives(),[])

    def test_stale_preview_and_disk_error_are_atomic(self):
        store=self.store(self.first)
        plan=plan_family_archive(make_zip(),store.profiles())
        # Another profile appeared after preview: no partial import.
        store.data["profiles"].append({
            "id":plan.members[0].profile_id,
            "name":"Another unrelated Windows person",
            "medications":[],"appointments":[]})
        store.save()
        before=json.dumps(store.data,sort_keys=True)
        with self.assertRaises(AndroidImportError):
            store.import_android_family(plan)
        self.assertEqual(json.dumps(store.data,sort_keys=True),before)
        self.assertEqual(len(store.android_archives()),0)

        newpath=self.second
        second=self.store(newpath)
        plan=plan_family_archive(make_zip(),second.profiles())
        with patch.object(second,"save",side_effect=OSError("synthetic disk error")):
            with self.assertRaises(OSError): second.import_android_family(plan)
        self.assertEqual(second.profiles(),[])
        self.assertEqual(second.android_archives(),[])
        assets=newpath.parent/"protected_assets"
        self.assertEqual(list(assets.glob("*.dpapi")),[])

    def test_archive_corruption_blocks_export(self):
        store=self.store(self.first)
        plan=plan_family_archive(make_zip(),store.profiles())
        store.import_android_family(plan)
        path=store._asset_path(plan.digest)
        path.write_bytes(b"broken ciphertext")
        with self.assertRaises(LocalStoreError):
            store.export_original_android_zip(plan.digest)

    def test_ui_routes_and_version(self):
        source=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text(encoding="utf-8")
        self.assertIn('VERSION = "0.6.8"',source)
        self.assertIn("family_controls(self)",source)
        self.assertIn("Reexportar ZIP Android original",source)
        ui=(Path(__file__).resolve().parents[1]/"family_ui_v064.py").read_text(encoding="utf-8")
        for keyword in ("Confirmar importação familiar","Backup completo encriptado",
                        "Importar ZIP familiar completo","askyesno","plan_family_archive"):
            self.assertIn(keyword,ui)

if __name__=="__main__":
    unittest.main()
