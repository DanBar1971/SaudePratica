"""Safe, additive Android JSON importer for ONE selected Windows profile.

Android files are rooted as {"medications":[...]} and {"appointments":[...]}.
Never restore or overwrite a full Android ZIP: Android's original backup
contains photos, encrypted settings and documents not yet mapped to Windows.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import PurePosixPath
from dataclasses import dataclass
import uuid
from zipfile import ZipFile, BadZipFile
from io import BytesIO

MAX_JSON = 8*1024*1024
MAX_RECORDS = 2000
DATA_KEYS = {"medications": "medications", "appointments": "appointments"}

class AndroidImportError(ValueError):
    pass

@dataclass(frozen=True)
class ImportPlan:
    kind: str
    entries: tuple[dict, ...]
    new: tuple[dict, ...]
    repeated: int
    names: tuple[str, ...]
    profile_id: str

def _text(value, max_length=220):
    if isinstance(value, (int,float)) and not isinstance(value,bool):
        value=str(value)
    return value.strip()[:max_length] if isinstance(value,str) else ""

def _fingerprint(item):
    encoded=json.dumps(item,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def _field_name(item,kind):
    if kind=="medications":
        return _text(item.get("medication") or item.get("name") or item.get("nome"),160)
    # Real Android Agenda records use activity/department, not title/name.
    return _text(item.get("title") or item.get("name") or item.get("activity") or
                 item.get("department") or item.get("specialty") or
                 item.get("type") or item.get("description"),160)

def _identity(item,kind):
    """Android appointment ID is NOT unique: combine its ID with event fields."""
    if kind=="medications":
        return "med:"+(_text(item.get("id"),120) or _fingerprint(item))
    fields=("id","date","time","activity","department","resource","location",
            "type","specialty")
    return "apt:"+_fingerprint({k:item.get(k) for k in fields})

def _converted(item,kind,profile_id):
    source_id=_text(item.get("id"),120)
    digest=_fingerprint(item)
    name=_field_name(item,kind)
    if not name:raise AndroidImportError("Há registos sem nome/título reconhecível. Nada foi importado.")
    unique=_identity(item,kind)
    uid=str(uuid.uuid5(uuid.NAMESPACE_URL,
         "saudepratica-android:"+profile_id+":"+kind+":"+unique))
    record=dict(item)
    record["id"]=uid
    record["android_source_id"]=source_id
    record["android_source_key"]=unique
    record["android_source_hash"]=digest
    record["android_origin"]="android-json-experimental"
    record["android_original"]=item
    if kind=="medications":
        record["name"]=name
        record["dose"]=_text(item.get("dose") or item.get("dosage") or item.get("strength"),90)
        record["time"]=_text(item.get("reminder_time") or item.get("alarmTime") or
                             item.get("time") or item.get("hour"),40)
        record["suspended"]=bool(item.get("suspended") or item.get("suspended_from"))
        # Preserve Android medication alarm preferences without scheduling desktop alarms.
        record["no_alarm"]=bool(item.get("no_alarm",item.get("noAlarm",False)))
        if not isinstance(record.get("notes"),str):record["notes"]=""
    else:
        record["title"]=name
        record["date"]=_text(item.get("date") or item.get("day") or item.get("appointmentDate"),40)
        record["time"]=_text(item.get("time") or item.get("hour") or item.get("appointmentTime"),40)
    return record

def _existing_map(target,kind):
    found={}
    for item in target:
        if not isinstance(item,dict):continue
        original=item.get("android_original")
        key=item.get("android_source_key")
        if not key and isinstance(original,dict):
            key=_identity(original,kind)
        if key:
            found[str(key)]=item.get("android_source_hash") or (
                _fingerprint(original) if isinstance(original,dict) else "")
    return found

def plan_json(blob:bytes,kind:str,profile:dict)->ImportPlan:
    if kind not in DATA_KEYS:raise AndroidImportError("Categoria de importação desconhecida.")
    if not isinstance(blob,bytes) or len(blob)>MAX_JSON:
        raise AndroidImportError("Ficheiro superior a 8 MB ou inválido.")
    if not profile or not isinstance(profile.get("id"),str):
        raise AndroidImportError("Seleciona primeiro o perfil de destino.")
    try:
        root=json.loads(blob.decode("utf-8-sig"))
    except (ValueError,UnicodeDecodeError) as ex:
        raise AndroidImportError("JSON inválido ou não está em UTF-8.") from ex
    if not isinstance(root,dict) or not isinstance(root.get(DATA_KEYS[kind]),list):
        raise AndroidImportError("O ficheiro não tem o formato Android esperado: "+DATA_KEYS[kind]+".")
    incoming=root[DATA_KEYS[kind]]
    if len(incoming)>MAX_RECORDS:
        raise AndroidImportError("O ficheiro contém demasiados registos.")
    if any(not isinstance(x,dict) for x in incoming):
        raise AndroidImportError("Há registos com estrutura inválida.")
    target=profile.get(kind,[])
    if not isinstance(target,list):raise AndroidImportError("O destino contém dados inválidos.")
    existing=_existing_map(target,kind)
    names=[]
    pending=[]
    repeated=0
    seen={}
    for raw in incoming:
        record=_converted(raw,kind,profile["id"])
        h=record["android_source_hash"]
        key=record["android_source_key"]
        # Exact repeated records (even when Android repeats a native ID) are skipped.
        # Contradictory records with same composite identity require manual review.
        if key in seen:
            if seen[key]!=h:
                raise AndroidImportError("Existem alterações contraditórias na mesma marcação.")
            repeated+=1
            continue
        seen[key]=h
        names.append(record["name"] if kind=="medications" else record["title"])
        if key in existing:
            if existing[key]!=h:
                raise AndroidImportError("Conflito com um registo já importado. Sem substituição automática.")
            repeated+=1
            continue
        pending.append(record)
    return ImportPlan(kind,tuple(incoming),tuple(pending),repeated,tuple(names),profile["id"])

def apply_plan(store,plan:ImportPlan):
    if not isinstance(plan,ImportPlan):raise AndroidImportError("Pré-visualização em falta.")
    profile=store.get_profile(plan.profile_id)
    if profile is None:raise AndroidImportError("O perfil de destino desapareceu.")
    existing=profile.get(plan.kind,[])
    if not isinstance(existing,list):raise AndroidImportError("Categoria do destino inválida.")
    seen=_existing_map(existing,plan.kind)
    for record in plan.new:
        if record["android_source_key"] in seen:
            raise AndroidImportError("Os dados mudaram desde a pré-visualização. Importa novamente.")
    original=profile[plan.kind]
    profile[plan.kind]=original+list(plan.new)
    try:store.save()
    except Exception:
        profile[plan.kind]=original
        raise
    return len(plan.new)

def inspect_android_zip(blob:bytes)->dict:
    """Read-only inspection; never extract, never treat as portable restore."""
    if not isinstance(blob,bytes) or len(blob)>80*1024*1024:
        raise AndroidImportError("O ZIP é demasiado grande ou inválido.")
    try:
        z=ZipFile(BytesIO(blob))
        with z:
            entries=z.infolist()
            if len(entries)>1000:raise AndroidImportError("Demasiados ficheiros no ZIP.")
            total=0
            paths=[]
            for entry in entries:
                p=PurePosixPath(entry.filename)
                if (entry.filename.startswith("/") or "\\" in entry.filename or
                    ":" in entry.filename or ".." in p.parts or
                    entry.file_size>MAX_JSON):
                    raise AndroidImportError("ZIP com caminho ou tamanho inseguro.")
                total+=entry.file_size
                if total>96*1024*1024:raise AndroidImportError("ZIP demasiado grande ao descomprimir.")
                paths.append(entry.filename)
            meds=[p for p in paths if p.endswith("/medicacao.json") or p=="medicacao.json"]
            agenda=[p for p in paths if p.endswith("/agenda.json") or p=="agenda.json"]
            return {"files":len(entries),"medications":len(meds),"appointments":len(agenda),
                    "warning":"Análise apenas. O ZIP Android NÃO é restaurado na versão Windows experimental."}
    except (BadZipFile,ValueError,RuntimeError) as ex:
        raise AndroidImportError("O ficheiro não é um ZIP Android válido ou seguro.") from ex
