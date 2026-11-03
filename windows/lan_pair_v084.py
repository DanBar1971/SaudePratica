"""SaúdePrática Windows LAN link-test v0: discovery and explicit approval only.

NO medical records, credentials, photos, profile names, or files are exchanged.
The HTTP proof-of-connection is deliberately NOT a clinical sync channel.
A future clinical protocol must use authenticated encryption and validated
record merging; this test must never be reused to transport medical data.
"""
from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from typing import Callable
import http.client
import json
import secrets
import threading
import select
import socket
import time

SERVICE_TYPE="_saudepratica-sync._tcp.local."
PROTOCOL="sp-pair-test-0"
MAX_REPLY=4096
UDP_DISCOVERY_PORT=43838
UDP_QUESTION="SP_DISCOVER_1:"
UDP_ANSWER="SP_FOUND_1:"


class LinkError(ValueError):
    pass


@dataclass(frozen=True)
class Phone:
    service: str
    name: str
    host: str
    port: int
    protocol: str = PROTOCOL

    @property
    def target(self):
        return f"{self.host}:{self.port}"


def lan_ip(host: str) -> str:
    """Only private, loopback or link-local IPv4; never connect to Internet."""
    try:
        addr=ip_address(host.strip())
    except (ValueError,AttributeError) as exc:
        raise LinkError("Introduz um endereço IPv4 local válido.") from exc
    permitted=tuple(ip_network(net) for net in (
        "10.0.0.0/8","172.16.0.0/12","192.168.0.0/16",
        "169.254.0.0/16","127.0.0.0/8"))
    if addr.version!=4 or addr.is_multicast or addr.is_unspecified or not any(
            addr in network for network in permitted):
        raise LinkError("A ligação de teste só aceita IPv4 privado/local (RFC 1918).")
    return str(addr)


def phone_from_service(service: str, name: str, address: str, port: int,
                       protocol: str) -> Phone:
    host=lan_ip(address)
    if not isinstance(port,int) or not 1<=port<=65535:
        raise LinkError("Porta inválida.")
    if protocol!=PROTOCOL:
        raise LinkError("Protocolo de emparelhamento incompatível.")
    safe_name="".join(c for c in name if c.isprintable()).strip()[:64]
    if not safe_name:
        safe_name="Telemóvel Android"
    return Phone(service=service,name=safe_name,host=host,port=port)




def local_broadcast_interfaces() -> list[tuple[str,str]]:
    """Enumerate real IPv4 adapters, not the first hostname/VPN guess.

    Use the ifaddr library already installed as a dependency of zeroconf.
    The source IPv4 selects the correct Windows Wi-Fi/Ethernet interface.
    """
    from ipaddress import ip_interface
    try:
        import ifaddr
        adapters=ifaddr.get_adapters()
    except (ImportError,OSError):
        return []
    items=[]
    seen=set()
    for adapter in adapters:
        for item in adapter.ips:
            if not isinstance(item.ip,str):
                continue
            try:
                address=ip_address(item.ip)
                prefix=item.network_prefix
                if (address.version!=4 or address.is_loopback or
                        not (address.is_private or address.is_link_local) or
                        not isinstance(prefix,int) or not 1<=prefix<=30):
                    continue
                broadcast=str(ip_interface(f"{address}/{prefix}").network.broadcast_address)
                entry=(str(address),broadcast)
                if entry not in seen:
                    seen.add(entry)
                    items.append(entry)
            except (ValueError,TypeError):
                continue
    return items[:16]


def decode_udp_reply(packet: bytes, nonce: str, host: str) -> Phone:
    """Only validates an advertised endpoint; HTTP verification follows."""
    if len(packet)>256:
        raise LinkError("Resposta de descoberta demasiado grande.")
    try:
        message=packet.decode("utf-8")
    except UnicodeError as exc:
        raise LinkError("Resposta de descoberta inválida.") from exc
    fields=message.split(":",3)
    if (len(fields)!=4 or fields[0]!="SP_FOUND_1" or
            fields[1]!=nonce or not fields[2].isascii() or
            not fields[2].isdigit()):
        raise LinkError("Dispositivo não corresponde ao pedido.")
    port=int(fields[2])
    return phone_from_service(
        f"udp-{host}-{port}",fields[3],host,port,PROTOCOL)


def discover_udp(*, target_interfaces: list[tuple[str,str]] | None = None,
                 destination_port: int = UDP_DISCOVERY_PORT,
                 duration: float = 2.4) -> list[Phone]:
    """Active LAN broadcast, no scanning of IP ranges and no patient data.

    Send a random 128-bit nonce to the broadcast of each local adapter.
    Accept only an exact nonce echo from a private IP and then verify
    the HTTP /v1/status endpoint before exposing a device in the UI.
    """
    if target_interfaces is None:
        target_interfaces=local_broadcast_interfaces()
    if not 1<=destination_port<=65535:
        raise LinkError("Porta UDP de descoberta inválida.")
    nonce=secrets.token_hex(16)
    question=(UDP_QUESTION+nonce).encode("ascii")
    sockets=[]
    found={}
    try:
        for bind, broadcast in target_interfaces[:16]:
            try:
                lan_ip(bind)
                if broadcast!="255.255.255.255":
                    # Directed broadcasts can end in a private subnet's .255
                    # but are not direct phone endpoints and need no lan_ip().
                    ip_address(broadcast)
                sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
                sock.bind((bind,0))
                sock.setblocking(False)
                sockets.append((sock,broadcast))
            except (OSError,ValueError,LinkError):
                continue
        if not sockets:
            return []
        deadline=time.monotonic()+max(0.1,min(4.0,duration))
        next_send=0.0
        round_count=0
        while time.monotonic()<deadline and len(found)<12:
            now=time.monotonic()
            if now>=next_send and round_count<3:
                for sock,broadcast in sockets:
                    try:
                        sock.sendto(question,(broadcast,destination_port))
                        # 255.255.255.255 reaches APs that discard directed
                        # broadcast on a particular Wi-Fi adapter.
                        if broadcast!="255.255.255.255":
                            sock.sendto(question,("255.255.255.255",destination_port))
                    except OSError:
                        continue
                next_send=now+0.75
                round_count+=1
            timeout=max(0.0,min(0.25,deadline-time.monotonic()))
            try:
                readable,_,_=select.select([x[0] for x in sockets],[],[],timeout)
            except (OSError,ValueError):
                break
            for sock in readable:
                try:
                    data,peer=sock.recvfrom(512)
                    host=lan_ip(peer[0])
                    phone=decode_udp_reply(data,nonce,host)
                except (OSError,ValueError,LinkError):
                    continue
                if phone.target in found:
                    continue
                try:
                    status=check_phone(phone)
                except (LinkError,OSError,ValueError):
                    continue
                if status.get("ready") is False:
                    continue
                found[phone.target]=phone
        return list(found.values())
    finally:
        for sock,_ in sockets:
            sock.close()

class PhoneDiscovery:
    """Zeroconf watcher. Delivers changes through a thread-safe callback."""
    def __init__(self,on_event:Callable[[str,Phone|str],None]):
        self._on_event=on_event
        self._zeroconf=None
        self._browser=None
        self._lock=threading.Lock()
        self.phones:dict[str,Phone]={}

    def start(self):
        if self._zeroconf is not None:return
        from zeroconf import ServiceBrowser, Zeroconf, InterfaceChoice
        self._zeroconf=Zeroconf(interfaces=InterfaceChoice.All)
        self._browser=ServiceBrowser(self._zeroconf,SERVICE_TYPE,
                                     handlers=[self._service_event])

    def refresh(self):
        """A genuine new mDNS browse PLUS active broadcast probe.

        Called from LanUi's background thread. Not from the Tk thread.
        """
        if self._zeroconf is None:
            self.start()
        from zeroconf import ServiceBrowser
        # Discard stale entries and rediscover devices still reachable.
        with self._lock:
            self.phones.clear()
        if self._browser is not None:
            self._browser.cancel()
        self._browser=ServiceBrowser(
            self._zeroconf,SERVICE_TYPE,handlers=[self._service_event])
        devices=discover_udp()
        for phone in devices:
            with self._lock:
                current=next((p for p in self.phones.values()
                              if p.host==phone.host and p.port==phone.port),None)
                if current is not None:
                    continue
                self.phones[phone.service]=phone
            self._on_event("found",phone)

    def _service_event(self,zc,service_type,name,state):
        from zeroconf import ServiceStateChange
        if state is ServiceStateChange.Removed:
            with self._lock:
                self.phones.pop(name,None)
            self._on_event("removed",name)
            return
        info=zc.get_service_info(service_type,name,timeout=1800)
        if info is None:return
        props={}
        for key,value in info.properties.items():
            try:
                props[key.decode("utf-8")]=value.decode("utf-8")
            except (UnicodeError,AttributeError):
                continue
        if props.get("proto")!=PROTOCOL or props.get("mode")!="link-only":
            return
        for address in info.parsed_addresses():
            try:
                phone=phone_from_service(
                    name,props.get("name","Telemóvel Android"),
                    address,info.port,props["proto"])
            except LinkError:
                continue
            with self._lock:
                self.phones[name]=phone
            self._on_event("found",phone)
            return

    def snapshot(self)->list[Phone]:
        with self._lock:
            return list(self.phones.values())

    def close(self):
        if self._zeroconf is None:return
        try:
            if self._browser is not None:
                self._browser.cancel()
            self._zeroconf.close()
        finally:
            self._zeroconf=None
            self._browser=None
            with self._lock:
                self.phones.clear()


def _exchange(phone:Phone,method:str,path:str,body:dict|None=None)->dict:
    # Bound the entire payload: this protocol can never carry patient data.
    if phone.protocol!=PROTOCOL:
        raise LinkError("Protocolo incompatível.")
    lan_ip(phone.host)
    if not 1<=phone.port<=65535:
        raise LinkError("Porta inválida.")
    raw=json.dumps(body,separators=(",",":")).encode("utf-8") if body is not None else b""
    if len(raw)>1024:raise LinkError("Pedido de ligação demasiado grande.")
    conn=http.client.HTTPConnection(phone.host,phone.port,timeout=3)
    try:
        headers={"Accept":"application/json"}
        if method=="POST":
            headers["Content-Type"]="application/json; charset=utf-8"
        conn.request(method,path,body=raw if method=="POST" else None,headers=headers)
        response=conn.getresponse()
        data=response.read(MAX_REPLY+1)
        if len(data)>MAX_REPLY:raise LinkError("Resposta demasiado grande.")
        try:
            decoded=json.loads(data.decode("utf-8"))
        except (UnicodeError,ValueError) as exc:
            raise LinkError("Resposta de ligação inválida.") from exc
        if not isinstance(decoded,dict) or response.status not in (200,202):
            raise LinkError("Ligação recusada pelo dispositivo.")
        return decoded
    except (TimeoutError,OSError,http.client.HTTPException) as exc:
        raise LinkError("Não foi possível contactar o telemóvel na rede local.") from exc
    finally:
        conn.close()


def check_phone(phone:Phone)->dict:
    status=_exchange(phone,"GET","/v1/status")
    if status.get("protocol")!=PROTOCOL or status.get("mode")!="link-only":
        raise LinkError("O dispositivo não suporta este teste.")
    return status


def ask_to_pair(phone:Phone)->tuple[str,str]:
    """Returns user-readable six-digit code and a request ID.

    The phone MUST display the code and require a local tap on Accept.
    No medical data or trust token is sent/stored. No TLS in this *link-only*
    prototype: it is NOT allowed to sync medical data over this channel.
    """
    check_phone(phone)
    code=f"{secrets.randbelow(1000000):06d}"
    nonce=secrets.token_hex(16)
    result=_exchange(phone,"POST","/v1/request",
                     {"protocol":PROTOCOL,"code":code,"nonce":nonce})
    request_id=result.get("request_id")
    if not isinstance(request_id,str) or len(request_id)>100:
        raise LinkError("Identificador de pedido inválido.")
    return code,request_id


def get_pair_result(phone:Phone,request_id:str)->str:
    if not isinstance(request_id,str) or not (1<=len(request_id)<=100) or not all(
        ch.isascii() and (ch.isalnum() or ch in "-_") for ch in request_id):
        raise LinkError("Identificador de pedido inválido.")
    result=_exchange(phone,"GET","/v1/result?id="+request_id)
    state=result.get("state")
    if state not in ("pending","accepted","rejected","expired"):
        raise LinkError("Resposta de emparelhamento inválida.")
    return state
