"""No real patient or institution data: synthetic backup and profile tests."""
import hashlib,json,unittest
from windows.hospital_processes_v0818 import (
    parse_hospital_archive, read_hospital_processes)
from windows.tests.test_v063_archive import make_zip,_archive_files
PROFILE="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
NAME="saudepratica_workplace/"+PROFILE+"/hospital_processes.json"
PHOTO="process_"+"a"*20+".jpg"
KEY="f"*64

def sample():
    files=_archive_files()
    payload={"version":1,"processes":{KEY:{
        "unit":"Hospital fictício","number":"PROC-123",
        "team":[{"name":"Profissional de Teste","specialty":"Exames",
                 "email":"teste@example.invalid"}],
        "charges":[{"category":"Consultas","status":"Por pagar",
                    "cents":700,"date":"2026-11-02"},
                   {"category":"Análises","status":"Pago","cents":0}],
        "transports":[{"description":"Transporte de teste",
                       "status":"A aguardar","date":"2026-11-02"}],
        "identity_image":PHOTO}}}
    files[NAME]=json.dumps(payload,ensure_ascii=False).encode()
    files["saudepratica_workplace/"+PROFILE+"/"+PHOTO]=b"\xff\xd8\xff"+b"A"*30
    return make_zip(files)

class HospitalReaderTests(unittest.TestCase):
    def test_one_profile_only(self):
        original=sample()
        rec,photos=parse_hospital_archive(original,PROFILE)
        self.assertEqual(len(rec),1)
        self.assertEqual(rec[0]["unit"],"Hospital fictício")
        self.assertEqual(rec[0]["team"][0]["name"],"Profissional de Teste")
        self.assertEqual(rec[0]["charges"][0]["cents"],700)
        self.assertEqual(rec[0]["transports"][0]["status"],"A aguardar")
        self.assertEqual(len(photos),1)
        other,other_photos=parse_hospital_archive(original,"legacy")
        self.assertEqual((other,other_photos),((),{}))
    def test_invalid_image_reference_is_not_read(self):
        files=_archive_files()
        files[NAME]=json.dumps({"version":1,"processes":{KEY:{
          "unit":"U","number":"123","team":[],"charges":[],
          "transports":[],"identity_image":"../sensitive.jpg"}}}).encode()
        result,photos=parse_hospital_archive(make_zip(files),PROFILE)
        self.assertEqual(result[0]["image_path"],"")
        self.assertFalse(photos)
    def test_detect_tamper_and_invalid_key(self):
        files=_archive_files()
        files[NAME]=json.dumps({"version":1,"processes":{"bad key":{
          "number":"1","team":[],"charges":[],"transports":[]}}}).encode()
        with self.assertRaisesRegex(ValueError,"Identificador"):
            parse_hospital_archive(make_zip(files),PROFILE)
    def test_store_never_exposes_another_members_archive(self):
        raw=sample()
        class FakeStore:
            def get_profile(self,pid):
                return {"id":pid,"android_zip_source_id":PROFILE} if pid=="windows-p1" else None
            def android_archives(self):
                return [{"sha256":"a"*64,"profile_ids":["windows-p2"]},
                        {"sha256":"b"*64,"profile_ids":["windows-p1"]}]
            def read_imported_asset(self,entry):
                if entry["sha256"]!="b"*64:
                    raise AssertionError("Tried to load the wrong profile's archive")
                return raw
        rows,photos=read_hospital_processes(FakeStore(),"windows-p1")
        self.assertEqual(len(rows),1)
        self.assertEqual(len(photos),1)
        self.assertEqual(read_hospital_processes(FakeStore(),"windows-p2"),((),{}))
