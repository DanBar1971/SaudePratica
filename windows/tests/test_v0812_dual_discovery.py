"""Windows 0.8.13: discover an Android without manually entering IP/port.

Only synthetic UDP/HTTP responders are exercised; no medical data is sent.
"""
from __future__ import annotations
import json
import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from windows.lan_pair_v084 import (
    Phone, PhoneDiscovery, LinkError, decode_udp_reply, discover_udp,
    local_broadcast_interfaces, UDP_DISCOVERY_PORT, PROTOCOL,
)


class FakeAndroidHttp(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_GET(self):
        obj=({"protocol":PROTOCOL,"mode":"link-only","ready":True}
             if self.path=="/v1/status" else {"error":"wrong path"})
        raw=json.dumps(obj).encode()
        self.send_response(200 if self.path=="/v1/status" else 404)
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class FakeAndroidUdp:
    def __init__(self,tcp_port,port=0):
        self.port=port
        self.tcp_port=tcp_port
        self.replied=False
        self.sent=[]
        self.alive=True
        self.udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.udp.bind(("127.0.0.1",port))
        self.port=self.udp.getsockname()[1]
        self.udp.settimeout(0.4)
        self.thread=threading.Thread(target=self._serve,daemon=True)
        self.thread.start()

    def _serve(self):
        while self.alive:
            try:data,peer=self.udp.recvfrom(512)
            except (OSError,TimeoutError):continue
            if not data.startswith(b"SP_DISCOVER_1:") or len(data)!=46:
                continue
            nonce=data.decode().split(":")[1]
            answer=f"SP_FOUND_1:{nonce}:{self.tcp_port}:SaúdePrática Android fictício"
            self.sent.append(data)
            self.udp.sendto(answer.encode(),peer)
            self.replied=True

    def close(self):
        self.alive=False
        self.udp.close()
        self.thread.join(timeout=2)


class ProtocolTests(unittest.TestCase):
    def test_response_must_echo_nonce_and_private_source(self):
        nonce="0"*32
        valid=f"SP_FOUND_1:{nonce}:6172:SaúdePrática Teste".encode()
        phone=decode_udp_reply(valid,nonce,"192.168.1.7")
        self.assertEqual(phone.host,"192.168.1.7")
        self.assertEqual(phone.port,6172)
        self.assertTrue(phone.name.startswith("SaúdePrática"))
        for wrong in (
            b"SP_FOUND_1:"+b"1"*32+b":6172:unknown",
            b"SP_FOUND_1:"+b"0"*32+b":0:unknown",
            b"SP_FOUND_1:"+b"0"*32+b":99999:unknown",
            b"SP_FOUND_1:"+b"0"*32+b":12:unknown"+b"x"*300,
            b"HELLO:"+b"0"*32+b":6172:unknown",
        ):
            with self.subTest(wrong=wrong[:40]),self.assertRaises(LinkError):
                decode_udp_reply(wrong,nonce,"192.168.1.7")
        with self.assertRaises(LinkError):
            decode_udp_reply(valid,nonce,"8.8.8.8")

    def test_active_broadcast_receives_and_verifies_own_http_status(self):
        with ThreadingHTTPServer(("127.0.0.1",0),FakeAndroidHttp) as web:
            server_thread=threading.Thread(target=web.serve_forever,daemon=True)
            server_thread.start()
            fake=FakeAndroidUdp(web.server_port)
            try:
                candidates=discover_udp(
                    target_interfaces=[("127.0.0.1","127.0.0.1")],
                    destination_port=fake.port,duration=1.0)
                self.assertTrue(fake.replied)
                self.assertEqual(len(candidates),1)
                self.assertEqual(candidates[0].host,"127.0.0.1")
                self.assertEqual(candidates[0].port,web.server_port)
                self.assertTrue(fake.sent[0].startswith(b"SP_DISCOVER_1:"))
            finally:
                fake.close()
                web.shutdown()
                server_thread.join(timeout=2)

    def test_wrong_tcp_server_is_not_shown_as_android(self):
        # UDP response is ignored when the advertised port does not
        # respond as a valid, ready link-only Android.
        fake=FakeAndroidUdp(65534)
        try:
            found=discover_udp(
                target_interfaces=[("127.0.0.1","127.0.0.1")],
                destination_port=fake.port,duration=0.55)
            self.assertEqual(found,[])
        finally:fake.close()

    def test_refresh_does_not_just_return_when_watcher_started(self):
        fake=Phone("udp-127.0.0.1-6000","Android fictício",
                   "127.0.0.1",6000)
        events=[]
        d=PhoneDiscovery(lambda action,value:events.append((action,value)))
        class FakeBrowser:
            def __init__(self,*a,**k):self.cancelled=False
            def cancel(self):self.cancelled=True
        previous=FakeBrowser()
        d._zeroconf=object()
        d._browser=previous
        with patch("zeroconf.ServiceBrowser",FakeBrowser),patch(
            "windows.lan_pair_v084.discover_udp",return_value=[fake]) as probe:
            d.refresh()
            self.assertTrue(previous.cancelled)
            probe.assert_called_once()
            self.assertEqual(events[0][0],"found")
            self.assertEqual(d.snapshot()[0].host,"127.0.0.1")
            d.refresh()
            self.assertEqual(probe.call_count,2)
            self.assertEqual(len(d.snapshot()),1)

    def test_win_ui_retries_even_if_android_starts_after_windows(self):
        ui=(Path(__file__).resolve().parents[1]/
            "lan_ui_v084.py").read_text("utf-8")
        self.assertIn("self._lan_manager.refresh()",ui)
        self.assertIn("time.monotonic()-getattr(self,\"_lan_last_scan\",0)>12",ui)
        self.assertIn("self._lan_devices.clear()",ui)
        self.assertIn("broadcast UDP",ui)

    def test_real_adapter_ips_not_only_hostname_guesses(self):
        # No assumption that the primary Windows adapter is Wi-Fi.
        source=(Path(__file__).resolve().parents[1]/
                "lan_pair_v084.py").read_text("utf-8")
        self.assertIn("ifaddr.get_adapters()",source)
        self.assertIn("network.broadcast_address",source)
        self.assertNotIn("socket.gethostbyname(socket.gethostname())",source)


if __name__=="__main__":
    unittest.main()
