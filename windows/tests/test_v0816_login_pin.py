"""No private records: tests for Windows PIN gate and manual body backup."""
import unittest
from uuid import uuid4
from datetime import datetime
from windows import login_pin_v0816 as pin
from windows.health_connect_import_v0815 import (
    decode_manual_body,manual_body_diagnostic,merge_manual_body,
)


class FakeStore:
    def __init__(self):
        self.p={"id":str(uuid4()),"name":"Perfil de teste"}
        self.q={"id":str(uuid4()),"name":"Outro perfil"}
        self.data={"profiles":[self.p,self.q]}
        self.saves=0
    def profiles(self):
        return self.data["profiles"]
    def get_profile(self,ident):
        return next((p for p in self.profiles() if p["id"]==ident),None)
    def save(self):
        self.saves+=1


class WindowsPinAndBodyTests(unittest.TestCase):
    def test_pin_setup_unlocks_only_correct_pin_and_default_remains(self):
        s=FakeStore()
        pin.setup(s,"0319",s.p["id"])
        self.assertTrue(pin.configured(s))
        self.assertEqual(pin.default_profile(s),s.p["id"])
        self.assertNotIn("0319",str(s.data))
        self.assertEqual(pin.verify(s,"0319",now=1000),(True,0))
        pin.set_default(s,s.q["id"])
        self.assertEqual(pin.default_profile(s),s.q["id"])
        pin.change_pin(s,"0319","0926")
        self.assertEqual(pin.verify(s,"0319",now=1000),(False,0))
        self.assertEqual(pin.verify(s,"0926",now=1000),(True,0))

    def test_failed_pin_attempts_require_delay(self):
        s=FakeStore()
        pin.setup(s,"1234",s.p["id"])
        for _ in range(4):
            self.assertEqual(pin.verify(s,"0000",now=1000),(False,0))
        failed,wait=pin.verify(s,"0000",now=1000)
        self.assertFalse(failed)
        self.assertGreaterEqual(wait,30)
        self.assertEqual(pin.verify(s,"1234",now=1001)[0],False)
        self.assertEqual(pin.verify(s,"1234",now=1032),(True,0))

    def test_invalid_pins_cannot_set_or_change_protection(self):
        for bad in ("","123","12345","12a4","１２３４"):
            s=FakeStore()
            with self.assertRaises(ValueError):
                pin.setup(s,bad,s.p["id"])
            self.assertFalse(pin.configured(s))
        s=FakeStore()
        with self.assertRaises(ValueError):
            pin.setup(s,"1234","wrong-profile")

    def test_android_original_eight_weights_are_retained(self):
        s=FakeStore()
        source=s.p["id"]
        base=1793059200000
        weights=[
            {"at":base+i*86400000,"kg":kg}
            for i,kg in enumerate((106.0,104.0,103.4,102.8,
                                   103.8,102.7,103.5,104.2))
        ]
        import json
        prefs={"saudepratica_body_"+source:{
            "height_cm":{"t":"f","v":188.0},
            "weights":{"t":"s","v":json.dumps(weights)}}}
        result=decode_manual_body(prefs,source)
        self.assertEqual(len(result["weights"]),8)
        self.assertEqual(result["height_cm"],188.0)
        self.assertEqual(manual_body_diagnostic(
            prefs,source)["record_count"],8)
        self.assertEqual(manual_body_diagnostic(
            prefs,s.q["id"])["status"],"not_in_backup")
        profile={}
        self.assertEqual(merge_manual_body(profile,result),8)
        self.assertEqual(merge_manual_body(profile,result),0)
        self.assertEqual(len(profile["android_manual_body"]["weights"]),8)


if __name__=="__main__":
    unittest.main()
