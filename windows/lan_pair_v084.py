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

SERVICE_TYPE="_saudepratica-sync._tcp.local."
PROTOCOL="sp-pair-test-0"
MAX_REPLY=4096


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
        from zeroconf import ServiceBrowser, Zeroconf
        self._zeroconf=Zeroconf()
        self._browser=ServiceBrowser(self._zeroconf,SERVICE_TYPE,
                                     handlers=[self._service_event])

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
