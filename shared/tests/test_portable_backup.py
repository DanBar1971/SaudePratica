"""Offline security tests with synthetic profiles only (no real medical data)."""
import json
import os
import sys
import unittest
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
from saude_backup import create_backup, read_backup, BackupError

class PortableBackupTests(unittest.TestCase):
    def setUp(self):
        self.profile = str(uuid.uuid4())
        self.path = "profiles/" + self.profile + "/medicacao.json"
        self.files = {
            self.path: json.dumps({"medications":[{"id":"test-001","name":"Medicamento fictício","dose":"10 mg","time":"07:00"}]}).encode("utf-8")
        }
        self.password = "correct horse battery cloud"

    def test_roundtrip(self):
        packed = create_backup(self.files, self.password)
        self.assertTrue(packed.startswith(b"SAUDEPRATICA-BACKUP-V1\n"))
        self.assertEqual(read_backup(packed, self.password), self.files)

    def test_wrong_password_is_rejected(self):
        packed = create_backup(self.files, self.password)
        with self.assertRaises(BackupError):
            read_backup(packed, "not the same password")

    def test_tampering_is_rejected(self):
        packed = bytearray(create_backup(self.files, self.password))
        packed[-5] ^= 1
        with self.assertRaises(BackupError):
            read_backup(bytes(packed), self.password)

    def test_zip_traversal_path_is_rejected(self):
        with self.assertRaises(BackupError):
            create_backup({"profiles/../secret.json": b"not allowed"}, self.password)

    def test_no_plain_data_in_backup_bytes(self):
        packed = create_backup(self.files, self.password)
        self.assertNotIn(b"Medicamento fict", packed)
        self.assertNotIn(b"test-001", packed)

if __name__=="__main__":
    unittest.main()
