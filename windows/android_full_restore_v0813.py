"""Recover REAL Android categories from a verified original family ZIP.

Portable .spbackup embeds the exact Android ZIP, not converted wellness,
nutrition or intake records. Convert only the linked source per Windows profile
without overwriting existing Windows edits. This module never sends data out.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import copy
import json
import re
import uuid

from windows.android_archive_v063 import validated_files
from windows.android_sos_lares_v0811 import _typed_text, _sos, _care
from windows.meal_android_import_v0810 import extract_meal_diary
from windows.remaining_models_v0810 import validate_record
from windows.wellness_models_v089 import water_settings
from windows.health_connect_import_v0815 import (
    decode_health_connect,merge_health_connect,
    decode_manual_body,merge_manual_body,
)

SOURCE_ID=re.compile(r"^(?:legacy|[0-9a-fA-F-]{36})$")
MAX_HEALTH=6000
MODULE_KEYS=("meal_records","symptom_records","intakes",
             "wellness_water","emergency_contact_data","residence_records",
             "residence_invoices")


def _timestamp(ms):
    """Android epoch millis -> system-local naive datetime (Windows UI time).

    Never infer a clinical time if the original timestamp is absent.
    """
    if isinstance(ms,bool):
        return None
    try:
        value=int(ms)
        if not 946684800000<=value<=4102444800000:
            return None
        return datetime.fromtimestamp(value/1000)
    except (ValueError,TypeError,OverflowError,OSError):
        return None


def _typed(node,key,kind):
    value=node.get(key)
    if not isinstance(value,dict) or value.get("t")!=kind:
        return None
    data=value.get("v")
    if kind=="s":
        return data if isinstance(data,str) else None
    if kind=="i":
        return data if isinstance(data,int) and not isinstance(data,bool) else None
    if kind=="set":
        return data if isinstance(data,list) and all(isinstance(x,str) for x in data) else None
    return None


def _read_water(prefs,source):
    node=prefs.get("saudepratica_wellness_"+source,{})
    if not isinstance(node,dict):
        return None
    day=_typed(node,"water_logged_date","s")
    amount=_typed(node,"water_logged_ml","i")
    config={}
    mapping={"water_glass_ml":"glass_ml","water_target_ml":"target_ml",
             "water_start":"water_start","water_end":"water_end",
             "water_interval":"water_interval"}
    for native,field in mapping.items():
        kind="s" if native in ("water_start","water_end") else "i"
        value=_typed(node,native,kind)
        if value is not None:
            config[field]=value
    try:
        settings=water_settings(config)
    except ValueError:
        # Invalid settings must not block import of historical medical data.
        settings=water_settings()
    entries=[]
    if (isinstance(day,str) and re.fullmatch(r"20\d\d-\d\d-\d\d",day)
            and isinstance(amount,int) and 0<amount<=100000):
        try:
            datetime.fromisoformat(day)
            entries=[{"id":str(uuid.uuid5(uuid.NAMESPACE_URL,
                        f"saudepratica/android/water/{source}/{day}")),
                      "date":day,"time":"","ml":amount,
                      "source":"android_daily_total",
                      "aggregate":True,
                      "note":"Total diário importado do Android. Horas de cada copo desconhecidas."}]
        except ValueError:
            pass
    return {"settings":settings,"entries":entries} if entries or config else None


def _read_health(files,source):
    path=f"saudepratica_health/{source}/records.json"
    raw=files.get(path)
    if raw is None:
        return [],[],[]
    if len(raw)>8*1024*1024:
        raise ValueError("Histórico Android acima do limite.")
    try:
        data=json.loads(raw.decode("utf-8-sig"))
    except (UnicodeError,ValueError) as exc:
        raise ValueError("Registos Android de saúde inválidos.") from exc
    if not isinstance(data,list) or len(data)>MAX_HEALTH:
        raise ValueError("Histórico Android com estrutura inválida.")
    deleted={r.get("fields",{}).get("deleted_intake_id")
             for r in data if isinstance(r,dict) and
             r.get("kind")=="deleted_intakes" and
             isinstance(r.get("fields"),dict)}
    symptoms=[]
    intakes=[]
    measurements=[]
    for record in data:
        if not isinstance(record,dict) or not isinstance(record.get("fields"),dict):
            continue
        rid=record.get("id")
        if not isinstance(rid,str) or len(rid)>120 or not rid:
            continue
        timestamp=_timestamp(record.get("timestamp"))
        if timestamp is None:
            continue
        fields=record["fields"]
        if record.get("kind")=="symptoms":
            severity=str(fields.get("severity","")).strip()
            if not severity.isdigit() or not 0<=int(severity)<=10:
                continue
            native_type=str(fields.get("tipo","")).strip()
            kind=("Possível efeito secundário"
                  if "efeito" in native_type.casefold() else "Sintoma")
            details=str(fields.get("details",""))[:2800]
            if native_type and native_type not in ("Sintoma","",kind):
                details=("Tipo no Android: "+native_type[:90]+"\n"+details)[:3000]
            try:
                clean=validate_record("symptoms",{
                    "date":timestamp.date().isoformat(),
                    "title":str(record.get("title","")).strip()[:160],
                    "type":kind,
                    "severity":severity,
                    "details":details})
            except ValueError:
                continue
            symptoms.append({
                "id":str(uuid.uuid5(uuid.NAMESPACE_URL,
                                   f"saudepratica/android/symptom/{source}/{rid}")),
                **clean,"android_source":source,"android_id":rid,
                "source":"android_health_records"})
        elif record.get("kind")=="measurements":
            value=fields.get("value")
            unit=fields.get("unidade")
            if value is None or not isinstance(unit,str):
                continue
            measurements.append({
                "id":str(uuid.uuid5(uuid.NAMESPACE_URL,
                    f"saudepratica/android/measurement/{source}/{rid}")),
                "title":str(record.get("title") or "Medição")[:160],
                "date":timestamp.date().isoformat(),
                "time":timestamp.strftime("%H:%M"),
                "value":str(value)[:100],
                "unit":unit[:80],
                "notes":str(fields.get("notes",""))[:1000],
                "source":"android_health_records",
                "android_source":source,
            })
        elif record.get("kind")=="intakes" and rid not in deleted:
            mid=fields.get("medication_id")
            if not isinstance(mid,str) or not mid:
                continue
            scheduled=_timestamp(fields.get("scheduled_at"))
            intakes.append({
                "android_id":rid, "android_medication_id":mid,
                "confirmed_at":timestamp.isoformat(timespec="seconds"),
                "scheduled_at":scheduled.isoformat(timespec="minutes") if scheduled else "",
                "status":"confirmed","source":"android_health_records"})
    return symptoms,intakes,measurements


def extract_profile_android(original_zip:bytes,source_id:str) -> dict:
    """Only the requested member's data, plus non-clinical caregiver link."""
    if not isinstance(source_id,str) or not SOURCE_ID.fullmatch(source_id):
        raise ValueError("Identificador de origem Android inválido.")
    files,manifest=validated_files(original_zip)
    prefs=manifest.get("prefs",{})
    if not isinstance(prefs,dict):
        raise ValueError("Preferências Android inválidas.")
    sos=_sos(_typed_text(prefs,"saudepratica_emergency_"+source_id))
    raw_care=_typed_text(
        prefs,"saudepratica_care_home_v1_"+source_id,limit=300000)
    residents=_typed(
        prefs.get("saudepratica_care_home_institution_v2",{}),
        "residents","set") or []
    resident_ids=[x for x in residents if SOURCE_ID.fullmatch(x) and x!="legacy"]
    # On newer Android versions the institution is stored centrally, while
    # the resident association remains explicit. Never show this data for
    # unrelated profiles.
    if source_id in resident_ids:
        central=_typed_text(prefs,"saudepratica_care_home_institution_v2")
        for field in ("institution","address","phone","email","website"):
            if not raw_care.get(field) and central.get(field):
                raw_care[field]=central[field]
    institutions,invoices=_care(raw_care,source_id)
    meals,photos=extract_meal_diary(original_zip,source_id)
    symptoms,intakes,measurements=_read_health(files,source_id)
    health_connect=decode_health_connect(files,source_id)
    manual_body=decode_manual_body(prefs,source_id)
    caretaker=_typed(prefs.get("saudepratica_caregiver_v1",{}),
                     "caregiver_id","s")
    return {
        "source_id":source_id,
        "water":_read_water(prefs,source_id),
        "meals":meals,
        "meal_photos":photos,
        "symptoms":symptoms,
        "intakes":intakes,
        "measurements":measurements,
        "health_connect":health_connect,
        "manual_body":manual_body,
        "sos":sos,
        "residences":institutions,
        "invoices":invoices,
        "caregiver_source":caretaker,
        "resident_sources":resident_ids,
    }


def merge_snapshot(profile:dict,snapshot:dict,source_to_target:dict,
                   attached:list[dict]):
    """Additive and idempotent; call on a copied profile in one transaction.

    Image metadata is profile-scoped, and image bytes go only to protected DPAPI.
    """
    pid=profile["id"]
    source=profile.get("android_zip_source_id")
    if source!=snapshot["source_id"]:
        raise ValueError("Origem Android não corresponde ao perfil de destino.")
    counts={"meals":0,"meal_photos":0,"water":0,"symptoms":0,
            "intakes":0,"measurements":0,
            "health_connect":0,"manual_body":0,
            "sos":0,"residences":0,"invoices":0}
    photo_meta=[]
    photo_blobs=[]
    for key,rows,label in (
        ("meal_records",snapshot["meals"],"meals"),
        ("symptom_records",snapshot["symptoms"],"symptoms"),
        ("android_health_measurements",snapshot["measurements"],"measurements"),
        ("residence_records",snapshot["residences"],"residences"),
        ("residence_invoices",snapshot["invoices"],"invoices"),
    ):
        current=profile.setdefault(key,[])
        if not isinstance(current,list):
            raise ValueError("Dados do módulo Windows inválidos.")
        ids={x.get("id") for x in current if isinstance(x,dict)}
        for row in rows:
            if row["id"] not in ids:
                # Preserve an older manually entered institution/fatura
                # rather than introducing a second copy.
                if label in ("residences","invoices") and any(
                    isinstance(x,dict) and
                    str(x.get("title","")).strip().casefold()==str(row.get("title","")).strip().casefold() and
                    (label=="residences" or str(x.get("date",""))[:7]==str(row.get("date",""))[:7])
                    for x in current):
                    continue
                current.append(copy.deepcopy(row))
                ids.add(row["id"])
                counts[label]+=1
    # Auto-import all authorised Health Connect readings from the Android
    # 1.9.134 profile-scoped snapshot. Never merge these into manually edited
    # Windows activity rows or raw Android body measurements.
    counts["health_connect"]=merge_health_connect(
        profile,snapshot["health_connect"])
    counts["manual_body"]=merge_manual_body(profile,snapshot["manual_body"])
    # Only the actual stored Android daily aggregate, never individual cups.
    water=snapshot.get("water")
    if water:
        stored=profile.setdefault("wellness_water",{})
        if not isinstance(stored,dict):
            raise ValueError("Histórico de água Windows inválido.")
        if not stored.get("settings"):
            stored["settings"]=copy.deepcopy(water["settings"])
        rows=stored.setdefault("entries",[])
        if not isinstance(rows,list):
            raise ValueError("Registos de água Windows inválidos.")
        current_ids={x.get("id") for x in rows if isinstance(x,dict)}
        for row in water["entries"]:
            if row["id"] not in current_ids:
                rows.append(copy.deepcopy(row))
                counts["water"]+=1
    # Never mark anything confirmed from a reminder. These are historical,
    # explicitly logged Android intake events, with original epoch times.
    meds={}
    for medication in profile.get("medications",[]):
        if not isinstance(medication,dict):
            continue
        native=medication.get("android_source_id")
        source_original=medication.get("android_original")
        if not native and isinstance(source_original,dict):
            native=source_original.get("id")
        if native:
            meds[str(native)]=medication
    intake_rows=profile.setdefault("intakes",[])
    if not isinstance(intake_rows,list):
        raise ValueError("Histórico de tomas Windows inválido.")
    ids={x.get("id") for x in intake_rows if isinstance(x,dict)}
    for entry in snapshot["intakes"]:
        medication=meds.get(entry["android_medication_id"])
        if medication is None:
            # Do not mix unknown medicine IDs with a different profile.
            continue
        imported_id=str(uuid.uuid5(uuid.NAMESPACE_URL,
            f"saudepratica/android/intake/{source}/{entry['android_id']}"))
        if imported_id in ids:
            continue
        mid=medication["id"]
        if any(isinstance(x,dict) and x.get("status")=="confirmed" and
               x.get("medication_id")==mid and
               x.get("scheduled_at")==entry["scheduled_at"] and
               bool(entry["scheduled_at"]) for x in intake_rows):
            continue
        item={
            "id":imported_id,
            "medication_id":mid,
            "medication":str(medication.get("name") or medication.get("medication") or "Medicação"),
            "dose":str(medication.get("dose") or ""),
            "scheduled_at":entry["scheduled_at"],
            "confirmed_at":entry["confirmed_at"],
            "source":entry["source"],
            "android_source":source,
            "android_id":entry["android_id"],
            "status":"confirmed",
        }
        intake_rows.append(item)
        ids.add(imported_id)
        counts["intakes"]+=1
    sos=profile.setdefault("emergency_contact_data",{})
    if not isinstance(sos,dict):
        raise ValueError("Ficha SOS Windows inválida.")
    for key,value in snapshot["sos"].items():
        if value and not sos.get(key):
            sos[key]=value
            counts["sos"]+=1
    if snapshot.get("caregiver_source")==source:
        profile["caregiver"]=True
        profile["care_home_residents"]=[
            source_to_target[s] for s in snapshot["resident_sources"]
            if s in source_to_target and source_to_target[s]!=pid]
    if source in snapshot.get("resident_sources",[]):
        profile["care_home_resident"]=True
    existing={(x.get("profile_id"),x.get("sha256"))
              for x in attached if isinstance(x,dict)}
    # Only store images actually linked to the given member's meals.
    expected={x.get("photo_sha256") for x in profile.get("meal_records",[])
              if isinstance(x,dict)}
    for digest,raw,name in snapshot["meal_photos"]:
        if digest not in expected or (pid,digest) in existing:
            continue
        photo_meta.append({
            "profile_id":pid,
            "path":f"saudepratica_meal_diary/{source}/{name}",
            "filename":name,
            "display_name":"Fotografia de refeição Android",
            "category":"fotografia de refeição",
            "sha256":digest,
            "bytes":len(raw),
            "android_source":source,
        })
        photo_blobs.append((digest,raw))
        existing.add((pid,digest))
        counts["meal_photos"]+=1
    return photo_meta,photo_blobs,counts
