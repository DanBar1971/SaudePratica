"""Windows-specific DPAPI persistence and restore tests with fictitious data."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from windows.secure_store import SecureStore
from shared.python.saude_backup import BackupError

@unittest.skipUnless(sys.platform=="win32","Windows DPAPI is only available on Windows.")
class SecureWindowsStoreTests(unittest.TestCase):
    def test_persistence_and_restore_without_silent_overwrite(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            with patch.dict(os.environ,{"LOCALAPPDATA":first}):
                original=SecureStore()
                person=original.create_profile("Perfil fictício")
                original.add_medication(person["id"],"Medicação de teste","5 mg","07:00","oral")
                disk=original.path.read_bytes()
                self.assertNotIn("Perfil fictício".encode("utf-8"),disk)
                reopened=SecureStore()
                self.assertEqual(len(reopened.profiles()[0]["medications"]),1)
                archive=reopened.export_backup("frase de teste 12345")

            with patch.dict(os.environ,{"LOCALAPPDATA":second}):
                restored=SecureStore()
                people,files=restored.inspect_backup(archive,"frase de teste 12345")
                self.assertEqual(len(people),1)
                self.assertEqual(restored.restore_backup(files),1)
                self.assertEqual(restored.profiles()[0]["name"],"Perfil fictício")
                with self.assertRaises(BackupError):
                    restored.restore_backup(files)
                self.assertEqual(len(restored.profiles()),1)

if __name__=="__main__":
    unittest.main()
