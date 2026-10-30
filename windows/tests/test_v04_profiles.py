"""Windows v0.4 regression tests with fictitious information only."""
import base64
from io import BytesIO
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from windows.ui_v04_i18n import STRINGS, translate
from windows.secure_store import SecureStore, LocalStoreError


class TranslationsTests(unittest.TestCase):
    def test_all_five_language_packs_have_the_same_keys(self):
        english=set(STRINGS["pt"])
        for language in ("pt","en","fr","de","es"):
            self.assertEqual(set(STRINGS[language]),english,language)
            self.assertTrue(translate(language,"profiles"))
    def test_modern_main_entrypoint_and_original_assets(self):
        s=(ROOT/"windows/desktop_v04.py").read_text(encoding="utf-8")
        self.assertIn('saude_background.png',s)
        self.assertIn('saude_icon.png',s)
        self.assertIn('self._select_profile',s)
        self.assertIn('self._profile_form',s)
        self.assertIn('self._change_theme',s)
        self.assertIn('self._change_language',s)
        # In Tkinter, _options(cnf, kw) is a reserved internal method.
        # Accidentally overriding it caused the v0.4.0 launch failure.
        self.assertNotIn("def _options(self):",s)
        self.assertIn("def _settings_page(self):",s)
        self.assertIn('pyi_splash.close()',s)
        build=(ROOT/".github/workflows/windows-build.yml").read_text(encoding="utf-8")
        self.assertIn("windows/desktop_v04.py",build)
        self.assertIn("--collect-all customtkinter",build)


@unittest.skipUnless(sys.platform=="win32","DPAPI requires Windows.")
class ProfileV04Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.env=patch.dict(os.environ,{"LOCALAPPDATA":self.temp.name})
        self.env.start()
        self.store=SecureStore()
        self.old=self.store.create_profile("Pessoa de teste")

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def fake_photo(self):
        image=Image.new("RGB",(32,32),(50,200,180))
        data=BytesIO()
        image.save(data,format="JPEG")
        return base64.b64encode(data.getvalue()).decode("ascii")

    def test_edit_preserves_old_medications_and_profile_identity(self):
        old_id=self.old["id"]
        med=self.store.add_medication(old_id,"Medicamento fictício","10 mg","08:00","oral")
        p=self.store.save_profile({
            "name":"Pessoa de teste","birth_date":"1971-10-11",
            "phone":"900000000","niss":"12345678901","health_unit":"Unidade de teste",
            "address":"Morada fictícia","city":"Lisboa",
            "photo_b64":self.fake_photo(),"caregiver":True,
        },old_id)
        self.assertEqual(old_id,p["id"])
        self.assertEqual(p["medications"][0]["id"],med["id"])
        self.assertTrue(p["caregiver"])
        self.assertEqual(p["health_unit"],"Unidade de teste")
        self.assertTrue(SecureStore().get_profile(old_id)["photo_b64"])
        self.assertNotIn(b"Pessoa de teste",self.store.path.read_bytes())

    def test_settings_saved_and_active_profile_persisted(self):
        self.store.update_settings(theme="light",language="fr",active_profile=self.old["id"])
        config=SecureStore().settings()
        self.assertEqual(config["theme"],"light")
        self.assertEqual(config["language"],"fr")
        self.assertEqual(config["active_profile"],self.old["id"])

    def test_backup_preserves_new_profile_fields_and_restores_old(self):
        self.store.save_profile({
            "name":"Pessoa com foto","niss":"98765432100",
            "caregiver":True,"photo_b64":self.fake_photo()
        },self.old["id"])
        archive=self.store.export_backup("frase secreta de teste 2026")
        people, files=self.store.inspect_backup(archive,"frase secreta de teste 2026")
        self.assertEqual(len(people),1)
        with tempfile.TemporaryDirectory() as other:
            with patch.dict(os.environ,{"LOCALAPPDATA":other}):
                clean=SecureStore()
                self.assertEqual(clean.restore_backup(files),1)
                p=clean.profiles()[0]
                self.assertEqual(p["niss"],"98765432100")
                self.assertTrue(p["caregiver"])
                self.assertEqual(p["photo_b64"],self.store.profiles()[0]["photo_b64"])

    def test_bad_birth_date_is_rejected_without_modifying_profile(self):
        with self.assertRaises(LocalStoreError):
            self.store.save_profile({"name":"Novo","birth_date":"2050-99-01"},self.old["id"])
        self.assertEqual(self.store.profiles()[0]["name"],"Pessoa de teste")


if __name__=="__main__":
    unittest.main()
