"""Local Windows entry PIN gate, independent of portable backup PIN.

DPAPI protects persisted state. This 4-digit PIN is a convenience UI gate and
does not substitute Windows account security or full-disk encryption.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import time

PIN_PATTERN=re.compile(r"^[0-9]{4}$")
ITERATIONS=600_000
DATA_KEY="pin_login_v1"


def valid_pin(pin):
    return isinstance(pin,str) and PIN_PATTERN.fullmatch(pin) is not None


def _digest(pin:str,salt:bytes):
    return hashlib.pbkdf2_hmac("sha256",pin.encode("ascii"),salt,ITERATIONS,32)


def configured(store):
    row=store.data.get(DATA_KEY)
    return isinstance(row,dict) and bool(row.get("digest"))


def setup(store,pin,default_id=None):
    if configured(store):
        raise ValueError("O PIN inicial já está definido.")
    if not valid_pin(pin):
        raise ValueError("Introduz um PIN com quatro números.")
    people=store.profiles()
    if people and not store.get_profile(default_id):
        raise ValueError("Escolhe o perfil predefinido.")
    salt=os.urandom(16)
    data={
        "salt":base64.b64encode(salt).decode("ascii"),
        "digest":base64.b64encode(_digest(pin,salt)).decode("ascii"),
        "default_profile_id":default_id if people else None,
        "failed":0,
        "blocked_until":0,
    }
    old=store.data.get(DATA_KEY)
    store.data[DATA_KEY]=data
    try:
        store.save()
    except Exception:
        if old is None:store.data.pop(DATA_KEY,None)
        else:store.data[DATA_KEY]=old
        raise


def default_profile(store):
    row=store.data.get(DATA_KEY,{})
    ident=row.get("default_profile_id") if isinstance(row,dict) else None
    return ident if ident and store.get_profile(ident) else None


def _verify_hash(pin,row):
    if not valid_pin(pin):
        return False
    try:
        salt=base64.b64decode(row["salt"],validate=True)
        expected=base64.b64decode(row["digest"],validate=True)
        if len(salt)!=16 or len(expected)!=32:
            return False
        return hmac.compare_digest(_digest(pin,salt),expected)
    except (KeyError,ValueError,TypeError):
        return False


def verify(store,pin,now=None):
    """(ok, wait_seconds). Persist attempts without disclosing PIN."""
    row=store.data.get(DATA_KEY)
    if not configured(store):
        return False,0
    moment=time.time() if now is None else now
    wait=max(0,int(row.get("blocked_until",0)-moment+0.999))
    if wait:
        return False,wait
    if _verify_hash(pin,row):
        if row.get("failed") or row.get("blocked_until"):
            row.update(failed=0,blocked_until=0)
            store.save()
        return True,0
    failed=min(int(row.get("failed",0))+1,99)
    row["failed"]=failed
    if failed>=5:
        # Increasing delay in same Windows user store; not a defence
        # against offline cracking of a copied portable backup.
        delay=min(3600,30*2**min(failed-5,7))
        row["blocked_until"]=int(moment)+delay
    store.save()
    return False,max(0,int(row.get("blocked_until",0)-moment+0.999))


def set_default(store,profile_id):
    if not configured(store):
        raise ValueError("Configura primeiro o PIN de entrada.")
    if not store.get_profile(profile_id):
        raise ValueError("Escolhe um perfil existente.")
    row=store.data[DATA_KEY]
    previous=row.get("default_profile_id")
    row["default_profile_id"]=profile_id
    try:store.save()
    except Exception:
        row["default_profile_id"]=previous
        raise


def change_pin(store,current,new):
    if not configured(store) or not _verify_hash(current,store.data[DATA_KEY]):
        raise ValueError("PIN atual incorreto.")
    if not valid_pin(new):
        raise ValueError("O novo PIN deve ter quatro números.")
    row=store.data[DATA_KEY]
    old=dict(row)
    salt=os.urandom(16)
    row.update(salt=base64.b64encode(salt).decode("ascii"),
               digest=base64.b64encode(_digest(new,salt)).decode("ascii"),
               failed=0,blocked_until=0)
    try:store.save()
    except Exception:
        store.data[DATA_KEY]=old
        raise
