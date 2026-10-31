"""Agenda filters for SaúdePrática Windows.

Imported appointment metadata is read-only: never rewrite a clinical record.
Android's agenda marks an elapsed appointment completed automatically unless it
was explicitly cancelled. A past date alone is NOT a reason to delete a record.
"""
from __future__ import annotations
from datetime import datetime
from unicodedata import normalize as unicode_normalize

FILTERS=(("all","Todas"),("pending","Pendentes"),("done","Realizadas"),("cancelled","Canceladas"))

def _clean(value):
    if value is None:return ""
    text=str(value).strip().lower()
    return "".join(ch for ch in unicode_normalize("NFD",text) if ord(ch)<128 or ch.isascii())

def appointment_datetime(item):
    day=item.get("date") or item.get("day") or item.get("appointmentDate")
    hour=item.get("time") or item.get("hour") or item.get("appointmentTime") or "00:00"
    if not isinstance(day,str) or not day.strip():return None
    if not isinstance(hour,str):return None
    try:
        return datetime.fromisoformat(day.strip()[:10]+"T"+hour.strip())
    except (TypeError,ValueError):return None

def appointment_status(item, now=None):
    """Return pending/done/cancelled using explicit flags and status first.

    For historic Android items without explicit flags, an elapsed date means
    Realizada, matching SaúdePrática's automatic post-date status convention.
    """
    now=now or datetime.now()
    # Deliberate Windows edits take precedence over immutable Android history.
    # In particular, reopening a cancelled appointment as pending must work.
    override=item.get("desktop_status")
    if override in ("pending","done","cancelled"):
        return override
    original=item.get("android_original")
    source=original if isinstance(original,dict) else {}
    fields=(item,source)
    cancel_flags=("cancelled","canceled","is_cancelled","isCanceled","isCancelled",
                  "cancelada","cancelado")
    done_flags=("done","completed","is_done","isDone","isCompleted","realizada","realizado")
    for obj in fields:
        if any(obj.get(key) is True for key in cancel_flags):
            return "cancelled"
    keys=("status","state","situacao","situação","estado","appointmentStatus",
          "appointment_status","statusAgendamento","scheduleStatus")
    status_texts=[_clean(obj.get(key)) for obj in fields for key in keys
                  if obj.get(key) is not None]
    if any(t in ("cancelada","cancelado","cancelled","canceled","cancel","anulada",
                 "anulado") or "cancel" in t for t in status_texts):
        return "cancelled"
    if any(obj.get(key) is True for obj in fields for key in done_flags):
        return "done"
    if any(t in ("realizada","realizado","concluida","concluido","completed",
                 "complete","done","finished","executada","efetuada","realised",
                 "realized") for t in status_texts):
        return "done"
    planned=appointment_datetime(item)
    if planned and planned<now:
        return "done"
    return "pending"

def filtered_appointments(items,category,now=None):
    if category not in {key for key,_ in FILTERS}:category="all"
    return [item for item in items if category=="all" or
            appointment_status(item,now)==category]
