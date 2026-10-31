"""Read-only recovery of Android profile metadata already inside protected ZIP backups.

Only the matching profile's files are inspected. Never logs or publishes patient
data; original ZIP stays encrypted by DPAPI in SecureStore.
"""
from __future__ import annotations
import json
import re
from windows.android_archive_v063 import validated_files
from windows.profile_fields_v066 import mapped_fields

OMIT = ("password", "pin", "secret", "token", "key", "hash", "fingerprint",
        "base64", "signature", "path", "uri", "photo", "image", "blob", "binary")
RELEVANT = ("saudepratica_identity", "saudepratica_health",
            "saudepratica_profiles", "saudepratica_workplace",
            "saudepratica_documents", "saudepratica_labs")

def _rows(obj, section, depth=0):
    if depth > 4: return
    if isinstance(obj, dict):
        for k,v in obj.items():
            if not isinstance(k,str) or any(w in k.lower() for w in OMIT):
                continue
            label=(section+" · " if section else "")+k
            if isinstance(v,(dict,list)):
                yield from _rows(v,label,depth+1)
            elif isinstance(v,(str,int,float,bool)) and not isinstance(v,bytes):
                val=str(v).strip()
                if val and len(val)<260 and val.lower() not in ("null","undefined"):
                    yield label,val
    elif isinstance(obj,list):
        for i,v in enumerate(obj[:80]):
            yield from _rows(v,section+f" [{i+1}]",depth+1)

def read_profile_extras(archive:bytes,source_id:str):
    """Return recognised field values and remaining read-only profile entries.

    All source files are digest-verified by the ZIP validator. Ignore nested
    file references to other profiles, opaque blobs and secrets.
    """
    files,head=validated_files(archive)
    original={}
    prefs=head.get("prefs")
    prefs=prefs if isinstance(prefs,dict) else {}
    node=prefs.get("saudepratica_profiles_v1",{})
    payload=(node.get("profiles",{}).get("v","")
             if isinstance(node,dict) else "")
    if isinstance(payload,str):
        try:
            for person in json.loads(payload):
                if isinstance(person,dict) and person.get("id")==source_id:
                    original=person
                    break
        except (ValueError,TypeError):pass
    sections={"Perfil Android":original}
    candidates=[]
    for filename,data in files.items():
        bits=filename.split("/")
        if len(bits)>=3 and bits[1]==source_id and bits[0] in RELEVANT:
            if filename.endswith(".json") and len(data)<2_000_000:
                try:
                    obj=json.loads(data.decode("utf-8-sig"))
                    sections[bits[0]+" / "+bits[-1]]=obj
                    candidates.append(obj)
                except (UnicodeDecodeError,ValueError):pass
        elif len(bits)==3 and bits[0]=="saudepratica_profiles" and bits[1]==source_id:
            if filename.endswith(".json") and len(data)<2_000_000:
                try:candidates.append(json.loads(data.decode("utf-8-sig")))
                except (UnicodeDecodeError,ValueError):pass
    fields=mapped_fields(original)
    # Try profile-specific clinical/identity files as a secondary source.
    for candidate in candidates:
        if isinstance(candidate,dict):
            for k,v in mapped_fields(candidate).items():
                fields.setdefault(k,v)
        elif isinstance(candidate,list):
            for entry in candidate[:100]:
                if not isinstance(entry,dict):continue
                for k,v in mapped_fields(entry).items():
                    fields.setdefault(k,v)
    display=[]
    seen=set()
    for name,node in sections.items():
        for label,value in _rows(node,name):
            key=(label,value)
            if key not in seen:
                display.append((label[:160],value[:260]))
                seen.add(key)
            if len(display)>=250:break
        if len(display)>=250:break
    return fields,tuple(display)
