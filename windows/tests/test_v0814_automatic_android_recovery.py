"""0.8.14: automatic and idempotent Android module recovery.

Uses only synthetic profiles and generated photographs; no real clinical data.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from windows import secure_store
from windows.tests.test_v0813_real_android_restore import android_original
from windows.family_portability_v064 import plan_family_archive
from windows.tests.test_v063_archive import make_zip


class AutomaticAndroidRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"profile_data.dpapi"
        for mock in (
            patch.object(secure_store,"_user_data_path",return_value=self.path),
            patch.object(secure_store,"_encrypt",side_effect=lambda value:value),
            patch.object(secure_store,"_decrypt",side_effect=lambda value:value),
        ):
            mock.start()
            self.addCleanup(mock.stop)

    def test_upgrade_populates_old_restored_backup_without_manual_clicks(self):
        caregiver=str(uuid4())
        resident=str(uuid4())
        medication=str(uuid4())
        photo=str(uuid4())
        android=android_original(caregiver,resident,medication,photo)
        digest=sha256(android).hexdigest()
        source={
            "sha256":digest,"bytes":len(android),
            "profile_ids":[caregiver,resident],
            "source_ids":[caregiver,resident],
        }
        old=secure_store.SecureStore()
        old.data["profiles"]=[
            {"id":caregiver,"name":"Cuidador fictício",
             "android_zip_source_id":caregiver,
             "medications":[{"id":str(uuid4()),"name":"Comprimido fictício",
                              "android_source_id":medication}],
             "appointments":[],
             "emergency_contact_data":{"contact_name":"Editado no Windows"}},
            {"id":resident,"name":"Residente fictício",
             "android_zip_source_id":resident,
             "medications":[],"appointments":[]},
        ]
        old.data["android_family_archives"]=[source]
        old._write_assets([(digest,android)])
        old.save()

        # Apenas abrir a aplicação nova deve converter todos os módulos.
        upgraded=secure_store.SecureStore()
        person=upgraded.get_profile(caregiver)
        dependent=upgraded.get_profile(resident)
        self.assertEqual(len(upgraded.meal_records(caregiver)),1)
        self.assertEqual(len(upgraded.remaining_records(caregiver,"symptoms")),1)
        self.assertEqual(upgraded.wellness_data(caregiver,"water")["entries"][0]["ml"],900)
        self.assertEqual(len(person["intakes"]),1)
        self.assertEqual(person["emergency_contact_data"]["contact_name"],
                         "Editado no Windows")
        self.assertEqual(person["care_home_residents"],[resident])
        self.assertEqual(len(upgraded.remaining_records(resident,"residences")),1)
        self.assertTrue(dependent["care_home_resident"])
        self.assertIsNotNone(upgraded.meal_photo(
            caregiver,upgraded.meal_records(caregiver)[0]["id"]))

        # Segunda abertura não duplica nem altera dados.
        again=secure_store.SecureStore()
        self.assertEqual(len(again.meal_records(caregiver)),1)
        self.assertEqual(len(again.get_profile(caregiver)["intakes"]),1)
        self.assertEqual(len(again.remaining_records(resident,"residences")),1)
        self.assertTrue(list((self.path.parent/"restores").glob(
            "before-automatic-restore-*.dpapi")))

    def test_importing_family_zip_imports_modules_before_first_open(self):
        store=secure_store.SecureStore()
        archive=make_zip()
        plan=plan_family_archive(archive,store.profiles())
        result=store.import_android_family(plan)
        self.assertIn("android_modules",result)
        self.assertEqual(len(store.profiles()),len(plan.members))
        reloaded=secure_store.SecureStore()
        self.assertEqual(len(reloaded.profiles()),len(plan.members))


if __name__=="__main__":
    unittest.main()
