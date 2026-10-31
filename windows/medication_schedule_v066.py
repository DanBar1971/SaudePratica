"""Read-only next medication occurrence; NOT a Windows alarm scheduler."""
from __future__ import annotations
from datetime import date, datetime, timedelta

def _day(value):
    if not isinstance(value,str) or not value:
        return None
    try:return date.fromisoformat(value[:10])
    except ValueError:return None

def _clock(value):
    if not isinstance(value,str) or len(value)!=5 or value[2]!=":":
        return None
    try:
        h,m=map(int,(value[:2],value[3:]))
        if 0<=h<24 and 0<=m<60:return (h,m)
    except ValueError:pass
    return None

def next_medication_label(record: dict, now: datetime|None=None) -> str:
    """Only display a date when source scheduling information supports it.

    Unknown frequency/one-off date never becomes an invented daily reminder.
    Weekly Android weekdays follow JS convention (Sunday=0).
    """
    now=now or datetime.now()
    original=record.get("android_original")
    src=original if isinstance(original,dict) else record
    if record.get("suspended") or src.get("suspended_from"):
        return "Medicação suspensa"
    if record.get("no_alarm") or src.get("no_alarm"):
        return "Sem alarme definido"
    time_value=src.get("reminder_time") or src.get("alarmTime") or record.get("time") or ""
    clock=_clock(time_value)
    if clock is None:
        return "Hora da toma por definir"
    time_text=f"{clock[0]:02d}:{clock[1]:02d}"
    start=_day(src.get("repeat_start") or src.get("start_date"))
    until=_day(src.get("repeat_until") or src.get("end_date"))
    mode=str(src.get("repeat_mode") or "").lower()
    days=src.get("repeat_weekdays",[])
    weekdays={v for v in days if type(v) is int and 0<=v<=6} if isinstance(days,list) else set()
    # Specific dated selections take precedence when present in the source.
    selected=src.get("schedule")
    choices=[]
    if isinstance(selected,dict):
        for month,values in selected.items():
            if not isinstance(month,str) or not isinstance(values,list):continue
            for d in values:
                if type(d) is not int:continue
                try:choices.append(date.fromisoformat(f"{month}-{d:02d}"))
                except ValueError:continue
    for target in sorted(set(choices)):
        dt=datetime.combine(target,datetime.min.time()).replace(hour=clock[0],minute=clock[1])
        if dt>=now and (not start or target>=start) and (not until or target<=until):
            return f"Próxima toma prevista: {target.isoformat()} · {time_text}"
    if mode in ("daily","weekly"):
        for delta in range(367):
            target=now.date()+timedelta(days=delta)
            if start and target<start:continue
            if until and target>until:break
            if mode=="weekly":
                if not weekdays or (target.weekday()+1)%7 not in weekdays:continue
            dt=datetime.combine(target,datetime.min.time()).replace(hour=clock[0],minute=clock[1])
            if dt>=now:
                return f"Próxima toma prevista: {target.isoformat()} · {time_text}"
    # No reliable recurring schedule: show the actual time but not a fabricated date.
    return f"Data da próxima toma por definir · {time_text}"
