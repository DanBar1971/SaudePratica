"""Windows 0.8.15: the REAL Android 1.9.134 snapshot schema imports safely.

All patients, weights and sensor readings in these tests are synthetic.
"""
from __future__ import annotations

from datetime import date,timedelta
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZipFile,ZIP_DEFLATED
import json
import tempfile
import unittest

from windows import secure_store
from windows.android_full_restore_v0813 import extract_profile_android,merge_snapshot
from windows.health_connect_import_v0815 import (
    decode_health_connect,merge_health_connect,
)
from windows.tests.test_v0813_real_android_restore import android_original
from windows.activity_health_connect_v0815 import (
    weekly_health,snapshot_value,format_value,recent_vitals
)


def synthetic_archive(daniel,camily,medication,photo,
                      health_owner=None,invalid_source=None):
    original=android_original(daniel,camily,medication,photo)
    with ZipFile(BytesIO(original)) as z:
        files={x.filename:z.read(x.filename) for x in z.infolist()}
    manifest=json.loads(files.pop("backup.json"))
    today=date.today()
    last=today.isoformat()
    yesterday=(today-timedelta(days=1)).isoformat()
    millis=1793700000000
    def reading(v):
        return {"value":v,"captured_at_ms":millis}
    path=f"saudepratica_health_connect/{health_owner or daniel}/daily.json"
    payload={
        "schema_version":1,"source":"health_connect",
        "profile_id":invalid_source or health_owner or daniel,
        "updated_at_ms":millis,
        "days":{
            last:{"steps":reading(1214),"distance_km":reading(0.69),
                  "active_kcal":reading(76),"sleep_minutes":reading(472),
                  "oxygen_percent":reading(95.0)},
            yesterday:{"steps":reading(5933),"distance_km":reading(3.1)},
        },
    }
    raw=json.dumps(payload).encode()
    files["data/"+path]=raw
    manifest["files"].append({"path":path,"sha256":sha256(raw).hexdigest(),
                              "size":len(raw)})
    # Saved Android manual body weights use typed preferences, not HC.
    manifest["prefs"]["saudepratica_body_"+daniel]={
        "height_cm":{"t":"f","v":188.0},
        "weights":{"t":"s","v":json.dumps([
            {"at":1793530800000,"kg":103.8},
            {"at":1793700000000,"kg":104.2},
        ])}}
    output=BytesIO()
    with ZipFile(output,"w",ZIP_DEFLATED) as z:
        z.writestr("backup.json",json.dumps(manifest))
        for path,raw in files.items():
            z.writestr(path,raw)
    return output.getvalue()


class HealthConnectSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.daniel=str(uuid4())
        self.camy=str(uuid4())
        self.med=str(uuid4())
        self.photo=str(uuid4())
        self.archive=synthetic_archive(self.daniel,self.camy,self.med,self.photo)

    def test_android_source_isolated_and_full_daily_values(self):
        d=extract_profile_android(self.archive,self.daniel)
        c=extract_profile_android(self.archive,self.camy)
        today=date.today().isoformat()
        self.assertEqual(snapshot_value(d["health_connect"],today,"steps"),1214)
        self.assertEqual(snapshot_value(d["health_connect"],today,"sleep_minutes"),472)
        self.assertEqual(snapshot_value(d["health_connect"],today,"oxygen_percent"),95)
        self.assertEqual(c["health_connect"]["days"],{})
        self.assertEqual(d["manual_body"]["height_cm"],188)
        self.assertEqual(len(d["manual_body"]["weights"]),2)
        self.assertEqual(len(c["manual_body"]),0)

    def test_merge_idempotent_and_manual_windows_preserved(self):
        snapshot=extract_profile_android(self.archive,self.daniel)
        profile={"id":self.daniel,"android_zip_source_id":self.daniel,
                 "medications":[],"appointments":[],
                 "wellness_activity":{"entries":[{
                     "date":date.today().isoformat(),"steps":777,
                     "source":"windows_manual"}]},
                 "android_health_measurements":[{
                     "id":"manual","title":"Medição manual","value":"104.6"}]}
        counts=merge_snapshot(profile,snapshot,
                              {self.daniel:self.daniel},[])[2]
        self.assertEqual(counts["health_connect"],7)
        self.assertEqual(counts["manual_body"],2)
        self.assertEqual(profile["wellness_activity"]["entries"][0]["steps"],777)
        self.assertEqual(profile["android_health_measurements"][0]["id"],"manual")
        again=merge_snapshot(profile,snapshot,{self.daniel:self.daniel},[])[2]
        self.assertEqual(again["health_connect"],0)
        self.assertEqual(again["manual_body"],0)
        rows=weekly_health(profile["android_health_connect"],
                          date.today().isoformat(),"steps")
        self.assertEqual(rows[-1][1],1214)
        self.assertEqual(rows[-2][1],5933)
        self.assertEqual(format_value("sleep_minutes",472),"7h 52m")
        self.assertEqual(recent_vitals(profile["android_health_connect"])[0][2],"95,0 %")

    def test_wrong_source_is_rejected_without_leaking_data(self):
        archive=synthetic_archive(self.daniel,self.camy,self.med,self.photo,
                                  invalid_source=self.camy)
        with self.assertRaises(ValueError):
            extract_profile_android(archive,self.daniel)

    def test_newer_capture_updates_old_without_loss(self):
        data=decode_health_connect({
            f"saudepratica_health_connect/{self.daniel}/daily.json":
                json.dumps({"schema_version":1,"source":"health_connect",
                            "profile_id":self.daniel,
                            "days":{date.today().isoformat():{
                                "steps":{"value":1214,"captured_at_ms":1793700000000}
                            }}}).encode()},self.daniel)
        p={}
        self.assertEqual(merge_health_connect(p,data),1)
        data["days"][date.today().isoformat()]["steps"]={
            "value":1714,"captured_at_ms":1793800000000}
        self.assertEqual(merge_health_connect(p,data),1)
        self.assertEqual(merge_health_connect(p,data),0)
        self.assertEqual(snapshot_value(p["android_health_connect"],
                         date.today().isoformat(),"steps"),1714)

    def test_existing_install_recovers_health_on_first_0815_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage=Path(tmp)/"data.dpapi"
            with (patch.object(secure_store,"_user_data_path",return_value=storage),
                  patch.object(secure_store,"_encrypt",side_effect=lambda b:b),
                  patch.object(secure_store,"_decrypt",side_effect=lambda b:b)):
                original=secure_store.SecureStore()
                digest=sha256(self.archive).hexdigest()
                original.data["profiles"]=[
                    {"id":self.daniel,"name":"Pessoa A",
                     "android_zip_source_id":self.daniel,
                     "medications":[],"appointments":[]},
                    {"id":self.camy,"name":"Pessoa B",
                     "android_zip_source_id":self.camy,
                     "medications":[],"appointments":[]}]
                original.data["android_family_archives"]=[{
                    "sha256":digest,"bytes":len(self.archive),
                    "profile_ids":[self.daniel,self.camy],
                    "source_ids":[self.daniel,self.camy]}]
                original._write_assets([(digest,self.archive)])
                original.data["_android_auto_recovery_0814"]="previous-migration"
                original.save()
                upgrade=secure_store.SecureStore()
                a=upgrade.get_profile(self.daniel)
                b=upgrade.get_profile(self.camy)
                self.assertEqual(
                    snapshot_value(a["android_health_connect"],
                                   date.today().isoformat(),"steps"),1214)
                self.assertFalse(b.get("android_health_connect",{}).get("days"))
                self.assertEqual(len(a["android_manual_body"]["weights"]),2)
                reopened=secure_store.SecureStore()
                self.assertEqual(len(reopened.get_profile(self.daniel)[
                    "android_manual_body"]["weights"]),2)
                self.assertIsNone(reopened._automatic_android_recovery_error)


if __name__=="__main__":
    unittest.main()
