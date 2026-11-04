"""SaúdePrática Windows 0.8.18: view Android hospital dossiers after secure restore.

Read-only, per-profile, local. The source is a manifest-verified Android ZIP
preserved inside the protected Windows store. No access to IPO/SNS services.
"""
from __future__ import annotations
import json
import re
from windows.android_archive_v063 import validated_files

SOURCE_ID=re.compile(r"[A-Za-z0-9_-]{1,100}")
IMAGE=re.compile(r"process_[a-f0-9]{20}\.jpg")
KEY=re.compile(r"[a-f0-9]{64}")

def _text(value,limit=240):
    return value[:limit].strip() if isinstance(value,str) else ""

def _records(raw,maximum):
    if not isinstance(raw,list) or len(raw)>maximum:
        raise ValueError("Lista hospitalar inválida ou demasiado longa.")
    return [x for x in raw if isinstance(x,dict)]

def _parse(files:dict[str,bytes],source_id:str):
    path=f"saudepratica_workplace/{source_id}/hospital_processes.json"
    blob=files.get(path)
    if blob is None:return ()
    if len(blob)>2_000_000:raise ValueError("Arquivo de processos demasiado grande.")
    document=json.loads(blob.decode("utf-8-sig"))
    if not isinstance(document,dict) or document.get("version")!=1:
        raise ValueError("Versão de arquivo hospitalar desconhecida.")
    items=document.get("processes",{})
    if not isinstance(items,dict) or len(items)>150:
        raise ValueError("Índice de processos inválido.")
    result=[]
    for fingerprint,item in items.items():
        if not isinstance(fingerprint,str) or not KEY.fullmatch(fingerprint):
            raise ValueError("Identificador de processo inválido.")
        if not isinstance(item,dict):raise ValueError("Processo inválido.")
        unit=_text(item.get("unit"),180)
        number=_text(item.get("number"),120)
        if not number:continue
        staff=[]
        for row in _records(item.get("team",[]),300):
            name=_text(row.get("name"),140)
            if name:
                staff.append(dict(name=name,specialty=_text(row.get("specialty"),120),
                    email=_text(row.get("email"),180),phone=_text(row.get("phone"),40),
                    notes=_text(row.get("notes"),400)))
        charges=[]
        for row in _records(item.get("charges",[]),2000):
            kind=_text(row.get("category"),50)
            state=_text(row.get("status"),45)
            value=row.get("cents")
            if kind not in ("Consultas","Exames","Análises") or state not in (
                "Por pagar","Pago","Isento","Anulado"):
                continue
            if isinstance(value,bool) or not isinstance(value,int) or not 0<=value<=100000000:
                continue
            charges.append(dict(category=kind,status=state,cents=value,
                date=_text(row.get("date"),25),notes=_text(row.get("notes"),300)))
        transports=[]
        for row in _records(item.get("transports",[]),1000):
            description=_text(row.get("description"),160)
            if description:
                transports.append(dict(description=description,
                    status=_text(row.get("status"),60),
                    date=_text(row.get("date"),25),
                    reference=_text(row.get("reference"),80),
                    notes=_text(row.get("notes"),300)))
        pic=item.get("identity_image")
        image_path=""
        if isinstance(pic,str) and IMAGE.fullmatch(pic):
            candidate=f"saudepratica_workplace/{source_id}/{pic}"
            if candidate in files and len(files[candidate])<=12*1024*1024:
                image_path=candidate
        result.append(dict(key=fingerprint,unit=unit,number=number,
            team=tuple(staff),charges=tuple(charges),transports=tuple(transports),
            image_path=image_path))
    return tuple(sorted(result,key=lambda x:(x["unit"].casefold(),x["number"])))

def parse_hospital_archive(blob:bytes,source_id:str):
    """Return isolated, bounded dossier summaries plus their validated image bytes."""
    if not isinstance(source_id,str) or not SOURCE_ID.fullmatch(source_id):
        raise ValueError("Perfil Android inválido.")
    files,_=validated_files(blob)  # signed/hashed by Android backup manifest
    items=_parse(files,source_id)
    images={item["image_path"]:files[item["image_path"]]
            for item in items if item["image_path"]}
    return items,images

def read_hospital_processes(store,profile_id:str):
    """Read only the selected Windows profile's linked Android backup.

    Do not consult family members or any private document before explicit login.
    Repeated restore uses the latest linked source; never merge unrelated sources.
    """
    patient=store.get_profile(profile_id)
    if not patient:return (),{}
    source=patient.get("android_zip_source_id")
    if not isinstance(source,str) or not SOURCE_ID.fullmatch(source):
        return (),{}
    archives=store.android_archives()
    for entry in reversed(archives):
        if profile_id not in entry.get("profile_ids",[]):continue
        digest=entry.get("sha256")
        if not isinstance(digest,str) or not KEY.fullmatch(digest):continue
        raw=store.read_imported_asset({"sha256":digest})
        entries,images=parse_hospital_archive(raw,source)
        if entries:return entries,images
    return (),{}
