"""Verified SaúdePrática Android 1.9.134 Health Connect backup decoder.

Read-only import of an explicit per-profile JSON snapshot in the original
Android ZIP. Never read local Windows sensors, infer missing measurements, or
mix accounts. Health Connect and manual body measurements remain separate.
"""
from __future__ import annotations

from datetime import date,datetime
import json
import math
import re

KEYS={
    "steps":(0,1_000_000),
    "distance_km":(0,5_000),
    "active_kcal":(0,100_000),
    "sleep_minutes":(0,5_000),
    "heart_bpm":(0,300),
    "total_kcal":(0,100_000),
    "weight_kg":(0,350),
    "oxygen_percent":(0,100),
    "resting_heart_bpm":(0,300),
    "systolic_mmhg":(0,400),
    "diastolic_mmhg":(0,300),
    "respiratory_per_min":(0,200),
    "temperature_c":(0,100),
}
SOURCE=re.compile(r"^(?:legacy|[a-fA-F0-9-]{36})$")
MIN_TIME=946684800000
MAX_TIME=4102444800000


def _millis(raw):
    return raw if type(raw) is int and MIN_TIME<=raw<=MAX_TIME else None


def _number(raw,lower,upper):
    if type(raw) not in (float,int) or not math.isfinite(raw):
        return None
    return float(raw) if lower<=raw<=upper else None


def _day(raw):
    if not isinstance(raw,str) or not re.fullmatch(r"20\d\d-\d\d-\d\d",raw):
        return False
    try:
        return date.fromisoformat(raw).isoformat()==raw
    except ValueError:
        return False


def decode_health_connect(files:dict[str,bytes],source:str)->dict:
    """Return only valid observed values for this Android source identifier."""
    if not SOURCE.fullmatch(source):
        raise ValueError("Origem Android Health Connect inválida.")
    path=f"saudepratica_health_connect/{source}/daily.json"
    raw=files.get(path)
    if raw is None:
        return {"schema_version":1,"source":"health_connect","days":{}}
    if not isinstance(raw,bytes) or not 0<len(raw)<=2_000_000:
        raise ValueError("Tamanho do Health Connect inválido.")
    try:
        root=json.loads(raw.decode("utf-8"))
    except (UnicodeError,ValueError) as exc:
        raise ValueError("Histórico Health Connect inválido.") from exc
    if (not isinstance(root,dict) or root.get("schema_version")!=1 or
            root.get("source")!="health_connect" or
            root.get("profile_id")!=source or
            not isinstance(root.get("days"),dict) or
            len(root["days"])>5000):
        raise ValueError("Backup Health Connect sem associação segura ao perfil.")
    clean={}
    for iso_day,metrics in root["days"].items():
        if not _day(iso_day) or not isinstance(metrics,dict):
            continue
        day={}
        for key,limits in KEYS.items():
            row=metrics.get(key)
            if not isinstance(row,dict):
                continue
            value=_number(row.get("value"),*limits)
            captured=_millis(row.get("captured_at_ms"))
            if value is None or captured is None:
                continue
            record={"value":value,"captured_at_ms":captured}
            observed=_millis(row.get("observed_at_ms"))
            if observed is not None:
                record["observed_at_ms"]=observed
            day[key]=record
        if day:
            clean[iso_day]=day
    return {"schema_version":1,"source":"health_connect","days":clean}


def merge_health_connect(profile:dict,snapshot:dict)->int:
    """Merge by date+metric, newest capture wins. Never edit manual records."""
    latest=snapshot.get("days",{})
    if not latest:
        return 0
    own=profile.setdefault("android_health_connect",{
        "schema_version":1,"source":"health_connect","days":{}})
    if (not isinstance(own,dict) or
            own.get("schema_version")!=1 or
            not isinstance(own.get("days"),dict)):
        raise ValueError("Dados Health Connect Windows inválidos.")
    count=0
    days=own["days"]
    for iso_day,metrics in latest.items():
        if not isinstance(days.get(iso_day),dict):
            days[iso_day]={}
        target=days[iso_day]
        for key,row in metrics.items():
            old=target.get(key,{})
            if not isinstance(old,dict):
                old={}
            if row["captured_at_ms"]>old.get("captured_at_ms",-1):
                target[key]=dict(row)
                count+=1
    return count


def _typed_value(node,key,kind):
    row=node.get(key)
    if isinstance(row,dict) and row.get("t")==kind:
        return row.get("v")
    return None


def decode_manual_body(prefs:dict,source:str)->dict:
    """Android BodyMeasurements: distinct from Health Connect weight records."""
    node=prefs.get("saudepratica_body_"+source,{})
    if not isinstance(node,dict):
        return {}
    height=_number(_typed_value(node,"height_cm","f"),90,230)
    if height is None:
        # Some older Android versions stored a floating point value as string.
        value=_typed_value(node,"height_cm","s")
        try:
            height=_number(float(value.replace(",",".")),90,230) if isinstance(value,str) else None
        except ValueError:
            height=None
    raw=_typed_value(node,"weights","s")
    try:
        data=json.loads(raw) if isinstance(raw,str) and len(raw)<300_000 else []
    except ValueError:
        data=[]
    if not isinstance(data,list):
        data=[]
    weights=[]
    ids=set()
    for row in data[:3000]:
        if not isinstance(row,dict):
            continue
        at=_millis(row.get("at"))
        kg=_number(row.get("kg"),20,350)
        if at is None or kg is None or at in ids:
            continue
        ids.add(at)
        weights.append({"at":at,"kg":kg,
                        "date":datetime.fromtimestamp(at/1000).date().isoformat()})
    return {"height_cm":height,"weights":weights} if height or weights else {}


def manual_body_diagnostic(prefs:dict,source:str)->dict:
    """Import status without exposing another profile's measurements."""
    node=prefs.get("saudepratica_body_"+source)
    if node is None:
        return {"status":"not_in_backup","record_count":0}
    if not isinstance(node,dict):
        return {"status":"invalid_format","record_count":0}
    count=len(decode_manual_body(prefs,source).get("weights",[]))
    return {"status":"importable" if count else "no_valid_weights",
            "record_count":count}


def merge_manual_body(profile:dict,body:dict)->int:
    if not body:
        return 0
    own=profile.setdefault("android_manual_body",{"height_cm":None,"weights":[]})
    if not isinstance(own,dict) or not isinstance(own.get("weights"),list):
        raise ValueError("Histórico de peso Android inválido.")
    if not own.get("height_cm") and body.get("height_cm"):
        own["height_cm"]=body["height_cm"]
    seen={x.get("at") for x in own["weights"] if isinstance(x,dict)}
    number=0
    for row in body.get("weights",[]):
        if row["at"] not in seen:
            own["weights"].append(dict(row))
            seen.add(row["at"])
            number+=1
    return number
