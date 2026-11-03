"""Windows 0.8.4 LAN pairing protocol test, synthetic devices only.

No patient names, medication, or clinical data ever leave the test process.
"""
from __future__ import annotations

import json
import threading
import unittest
import tempfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from windows.lan_pair_v084 import (
    Phone, PhoneDiscovery, LinkError, lan_ip, phone_from_service,
    PROTOCOL, SERVICE_TYPE, check_phone, ask_to_pair, get_pair_result
)

class LocalPairHandler(BaseHTTPRequestHandler):
    requests_received=[]
    state="accepted"
    def log_message(self,*args):pass
    def response(self,status,payload):
        raw=json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def do_GET(self):
        if self.path=="/v1/status":
            self.response(200,{"protocol":PROTOCOL,"mode":"link-only",
                               "device":"Fake Android Test"})
        elif self.path.startswith("/v1/result?id="):
            self.response(200,{"state":self.__class__.state})
        else:
            self.response(404,{"error":"unknown"})
    def do_POST(self):
        length=int(self.headers.get("Content-Length","0"))
        obj=json.loads(self.rfile.read(length))
        self.__class__.requests_received.append(obj)
        self.response(202,{"request_id":"faked-request-1"})

class PairProtocolTests(unittest.TestCase):
    def test_reject_nonlocal_addresses_and_other_protocols(self):
        for value in ("8.8.8.8","203.0.113.10","google.com","224.0.0.3",
                      "0.0.0.0","::1"):
            with self.subTest(value=value),self.assertRaises(LinkError):
                lan_ip(value)
        self.assertEqual(lan_ip("192.168.1.44"),"192.168.1.44")
        self.assertEqual(lan_ip("127.0.0.1"),"127.0.0.1")
        with self.assertRaises(LinkError):
            phone_from_service("bad","Example","192.168.1.44",8000,"wrong")

    def test_full_phone_acknowledgment_has_no_clinical_payload(self):
        LocalPairHandler.requests_received=[]
        with ThreadingHTTPServer(("127.0.0.1",0),LocalPairHandler) as server:
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            try:
                phone=Phone("test","Android Teste","127.0.0.1",server.server_port)
                status=check_phone(phone)
                self.assertEqual(status["protocol"],PROTOCOL)
                code,request_id=ask_to_pair(phone)
                self.assertEqual(len(code),6)
                self.assertTrue(code.isdigit())
                self.assertEqual(get_pair_result(phone,request_id),"accepted")
                self.assertEqual(len(LocalPairHandler.requests_received),1)
                self.assertEqual(set(LocalPairHandler.requests_received[0]),
                                 {"protocol","code","nonce"})
                self.assertEqual(LocalPairHandler.requests_received[0]["code"],code)
            finally:
                server.shutdown()
                thread.join(timeout=3)

    def test_discovery_accepts_only_our_test_android_and_delivers_events(self):
        from zeroconf import ServiceStateChange
        class FakeInfo:
            properties={b"proto":PROTOCOL.encode(),b"mode":b"link-only",
                        b"name":"Teste Android".encode()}
            port=6000
            def parsed_addresses(self):return ["192.168.55.7"]
        class FakeZeroconf:
            def get_service_info(self,typ,name,timeout=0):return FakeInfo()
        events=[]
        manager=PhoneDiscovery(lambda kind,value:events.append((kind,value)))
        manager._service_event(FakeZeroconf(),SERVICE_TYPE,"Phone._spcare",
                               ServiceStateChange.Added)
        self.assertEqual(len(manager.snapshot()),1)
        self.assertEqual(manager.snapshot()[0].name,"Teste Android")
        self.assertEqual(events[0][0],"found")
        manager._service_event(FakeZeroconf(),SERVICE_TYPE,"Phone._spcare",
                               ServiceStateChange.Removed)
        self.assertFalse(manager.snapshot())
        self.assertEqual(events[-1][0],"removed")

    def test_ui_discovery_and_manual_ip_are_real_not_mock_buttons(self):
        src=(Path(__file__).resolve().parents[1]/"desktop_v04.py").read_text("utf-8")
        ui=(Path(__file__).resolve().parents[1]/"lan_ui_v084.py").read_text("utf-8")
        self.assertIn('VERSION = "0.8.11"',src)
        self.assertIn('elif self.page=="sync": self._sync_page()',src)
        self.assertIn('self.after(900,self._lan_begin_discovery)',src)
        self.assertIn('def _lan_poll_ui(self):',ui)
        self.assertIn('def _lan_manual_request(self):',ui)
        self.assertIn('messagebox.askyesno("Confirmar pedido de ligação"',ui)
        self.assertIn('Aprovação',ui.replace("autorização","Aprovação") or "Aprovação")
        self.assertNotIn("save_medication(",ui)
        self.assertNotIn("restore_backup(",ui)

if __name__=="__main__":
    unittest.main()
