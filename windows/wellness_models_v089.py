"""SaúdePrática 0.8.9: validation and date-based projections for personal wellness.

Manual Windows records are not Health Connect measurements and do not imply
clinical advice. Menstrual estimates are approximate, never fertility or
contraception predictions. Hydration targets are chosen by the user.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, time, timedelta
import re

WATER_DEFAULTS = {
    "glass_ml": 200,
    "target_ml": 0,
    "water_start": "09:00",
    "water_end": "20:00",
    "water_interval": 120,
}
CYCLE_DEFAULTS = {
    "cycle_days": 28,
    "pill_pattern": "off",
    "pill_start": "",
    "pill_time": "21:00",
}
PILL_PATTERNS = {
    "Sem registo de pílula": "off",
    "Diariamente": "daily",
    "21 dias + 7 dias de pausa": "21_7",
    "24 dias + 4 dias de pausa": "24_4",
}
ACTIVITY_FIELDS = {
    "steps": (0, 250000),
    "distance_m": (0, 300000),
    "active_kcal": (0, 20000),
    "sleep_minutes": (0, 1440),
    "heart_bpm": (20, 250),
    "weight_grams": (1000, 500000),
    "systolic": (40, 300),
    "diastolic": (20, 250),
}
ACTIVITY_LABELS = {
    "steps": "Passos",
    "distance_m": "Distância (metros)",
    "active_kcal": "Energia ativa (kcal)",
    "sleep_minutes": "Sono (minutos)",
    "heart_bpm": "Ritmo cardíaco médio (bpm)",
    "weight_grams": "Peso (gramas)",
    "systolic": "Tensão sistólica (mmHg)",
    "diastolic": "Tensão diastólica (mmHg)",
}


def iso_date(value: str, *, optional: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError("Data inválida.")
    value = value.strip()
    if optional and not value:
        return ""
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        try:
            return datetime.strptime(value, "%d/%m/%Y").date().isoformat()
        except ValueError as exc:
            raise ValueError("Data inválida. Utiliza DD/MM/AAAA.") from exc


def clock(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{2}:\d{2}", value):
        raise ValueError("Hora inválida. Utiliza HH:MM.")
    try:
        return time.fromisoformat(value).strftime("%H:%M")
    except ValueError as exc:
        raise ValueError("Hora inválida. Utiliza HH:MM.") from exc


def bounded_int(value, lo: int, hi: int, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(label + " inválido.")
    try:
        if isinstance(value, int):
            n=value
        elif isinstance(value, str) and re.fullmatch(r"[0-9]+", value.strip()):
            n=int(value.strip())
        else:
            raise ValueError
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(label + " deve ser um número inteiro.") from exc
    if not lo <= n <= hi:
        raise ValueError(f"{label}: intervalo permitido {lo}–{hi}.")
    return n


def water_settings(value: dict | None = None) -> dict:
    if value is None:
        value={}
    if not isinstance(value, dict):
        raise ValueError("Configuração da hidratação inválida.")
    settings={**WATER_DEFAULTS, **{k:v for k,v in value.items() if k in WATER_DEFAULTS}}
    result={
        "glass_ml":bounded_int(settings["glass_ml"],30,1000,"Volume do copo"),
        "target_ml":bounded_int(settings["target_ml"],0,10000,"Objetivo diário"),
        "water_start":clock(settings["water_start"]),
        "water_end":clock(settings["water_end"]),
        "water_interval":bounded_int(settings["water_interval"],30,360,"Intervalo"),
    }
    if result["water_end"] <= result["water_start"]:
        raise ValueError("A hora final deve ser posterior à inicial.")
    return result


def water_record(day: str, hhmm: str, milliliters: int) -> dict:
    d=iso_date(day)
    if d > date.today().isoformat():
        raise ValueError("Não podes confirmar água consumida numa data futura.")
    return {
        "date": d,
        "time":clock(hhmm),
        "ml":bounded_int(milliliters,1,5000,"Quantidade de água"),
    }


def water_total(entries: list, day: str) -> int:
    chosen=iso_date(day)
    return sum(int(x.get("ml",0)) for x in entries
               if isinstance(x,dict) and x.get("date")==chosen)


def progress_pct(total: int, goal: int) -> int | None:
    if not goal:
        return None
    return round(total*100/goal)


def activity_record(value: dict) -> dict:
    if not isinstance(value,dict):
        raise ValueError("Registo de atividade inválido.")
    day=iso_date(value.get("date",""))
    if day > date.today().isoformat():
        raise ValueError("Não podes confirmar medições em datas futuras.")
    note=value.get("notes","")
    if not isinstance(note,str) or len(note)>1000:
        raise ValueError("Observações demasiado longas.")
    record={"date":day,"notes":note.strip(),"source":"windows_manual"}
    any_metric=False
    for key,(lo,hi) in ACTIVITY_FIELDS.items():
        raw=value.get(key)
        if raw in (None,""):
            record[key]=None
            continue
        record[key]=bounded_int(raw,lo,hi,ACTIVITY_LABELS[key])
        any_metric=True
    if not any_metric and not record["notes"]:
        raise ValueError("Indica pelo menos uma medição ou observação.")
    sys=record["systolic"]
    dia=record["diastolic"]
    if sys is not None and dia is not None and sys <= dia:
        raise ValueError("Confirma os valores de tensão arterial introduzidos.")
    return record


def weekly_series(records: list[dict], key: str, ending: str) -> list[tuple[str,int|None]]:
    if key not in ACTIVITY_FIELDS:
        raise ValueError("Métrica inválida.")
    last=date.fromisoformat(iso_date(ending))
    index={x["date"]:x for x in records if isinstance(x,dict) and
           isinstance(x.get("date"),str)}
    return [(d.isoformat(),index.get(d.isoformat(),{}).get(key))
            for d in (last-timedelta(days=n) for n in range(6,-1,-1))]


def cycle_settings(value: dict | None = None) -> dict:
    if value is None:
        value={}
    if not isinstance(value,dict):
        raise ValueError("Configuração do ciclo inválida.")
    settings={**CYCLE_DEFAULTS,**{k:v for k,v in value.items() if k in CYCLE_DEFAULTS}}
    days=bounded_int(settings["cycle_days"],21,45,"Duração do ciclo")
    pattern=settings["pill_pattern"]
    if not isinstance(pattern,str) or pattern not in PILL_PATTERNS.values():
        raise ValueError("Esquema de pílula desconhecido.")
    start=iso_date(settings["pill_start"],optional=True)
    pill_time=clock(settings["pill_time"])
    if pattern!="off" and not start:
        raise ValueError("Indica a data de início do esquema de pílula.")
    return {"cycle_days":days,"pill_pattern":pattern,
            "pill_start":start,"pill_time":pill_time}


def period_record(start: str, end: str, note: str = "") -> dict:
    first=iso_date(start)
    last=iso_date(end)
    if first>last or (date.fromisoformat(last)-date.fromisoformat(first)).days>14:
        raise ValueError("O período deve ter entre 1 e 15 dias.")
    if last>date.today().isoformat():
        raise ValueError("Regista apenas períodos que já aconteceram.")
    if not isinstance(note,str) or len(note)>500:
        raise ValueError("Nota demasiado longa.")
    return {"start":first,"end":last,"notes":note.strip()}


def ensure_no_period_overlap(periods: list[dict], new: dict) -> None:
    if any(not (new["end"]<p["start"] or new["start"]>p["end"])
           for p in periods if isinstance(p,dict)):
        raise ValueError("Estas datas já estão incluídas noutro período.")


def estimated_next_period(periods: list[dict], length: int, today: str | None = None) -> str | None:
    if not periods:
        return None
    cycle_days=bounded_int(length,21,45,"Duração do ciclo")
    today_date=date.fromisoformat(iso_date(today or date.today().isoformat()))
    latest=max(date.fromisoformat(p["start"]) for p in periods if isinstance(p,dict))
    upcoming=latest+timedelta(days=cycle_days)
    while upcoming<today_date and upcoming<latest+timedelta(days=365*3):
        upcoming+=timedelta(days=cycle_days)
    return upcoming.isoformat()


def pill_scheduled(day: str, settings: dict) -> bool:
    s=cycle_settings(settings)
    if s["pill_pattern"]=="off":
        return False
    when=date.fromisoformat(iso_date(day))
    beginning=date.fromisoformat(s["pill_start"])
    if when<beginning:
        return False
    n=(when-beginning).days%28
    if s["pill_pattern"]=="daily":
        return True
    return n<(21 if s["pill_pattern"]=="21_7" else 24)
