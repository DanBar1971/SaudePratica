"""Local appointment reminder offsets, always in minutes.

Identical units to SaúdePrática Android's reminders_minutes field.
This module is pure Python so scheduling can be regression-tested without
Windows notification APIs or a personal profile backup.
"""
from __future__ import annotations
from datetime import datetime,timedelta
import hashlib
from .agenda_filter_v069 import appointment_datetime, appointment_status

CHOICES=((1440,"1 dia antes"),(120,"2 horas antes"),(60,"1 hora antes"),
         (30,"30 minutos antes"),(0,"Na hora da consulta"))
ALLOWED=frozenset(key for key,_ in CHOICES)
DEFAULT=(1440,120)

def normalize_offsets(value):
    if value is None:return []
    if not isinstance(value,list):
        raise ValueError("Os avisos devem ser uma lista de minutos.")
    if len(value)>24:
        raise ValueError("Existem demasiados avisos.")
    result=[]
    for item in value:
        if type(item) is not int or not 0<=item<=10080:
            raise ValueError("Aviso inválido. Deve estar entre 0 e 10080 minutos.")
        if item not in result:result.append(item)
    return sorted(result,reverse=True)

def record_offsets(record):
    """Preserve Android settings, including deliberately empty [] lists."""
    if "reminders_minutes" in record:
        return normalize_offsets(record["reminders_minutes"])
    original=record.get("android_original")
    if isinstance(original,dict) and "reminders_minutes" in original:
        return normalize_offsets(original["reminders_minutes"])
    return []   # no automatic alarms for old unknown records

def due_events(profiles,now=None,grace_minutes=10):
    """Find reminders due recently for active, future appointments.

    All time calculations are local Windows time and do not require network.
    A replay after sleep is limited to grace_minutes. Exact offset 0 is allowed.
    """
    now=now or datetime.now()
    result=[]
    seen=set()
    for profile in profiles:
        profile_id=profile.get("id")
        for item in profile.get("appointments",[]):
            if not isinstance(item,dict):continue
            planned=appointment_datetime(item)
            if planned is None or planned < now-timedelta(minutes=grace_minutes):
                continue
            if appointment_status(item,planned-timedelta(seconds=1)) in ("cancelled","done"):continue
            try:offsets=record_offsets(item)
            except ValueError:continue
            for minutes in offsets:
                trigger=planned-timedelta(minutes=minutes)
                elapsed=(now-trigger).total_seconds()
                if 0<=elapsed<=grace_minutes*60:
                    token=hashlib.sha256((
                        str(profile_id)+"|"+str(item.get("id"))+"|"+
                        planned.isoformat()+"|"+str(minutes)
                    ).encode("utf-8")).hexdigest()
                    if token not in seen:
                        result.append((token,planned,minutes))
                        seen.add(token)
    return result

def reminder_message(planned,minutes):
    """Avoid displaying patient names or medical services on lock screens."""
    when=planned.strftime("%d/%m/%Y às %H:%M")
    human={1440:"1 dia",120:"2 horas",60:"1 hora",30:"30 minutos",0:"agora"}
    lead=human.get(minutes,f"{minutes} minutos")
    return f"Tens uma marcação em {when}. Aviso: {lead} antes."
