"""Medication statuses and gallery filters across Android/Windows backup versions.

This is display-only: Windows does not schedule medication alarms.
"""
from windows.medication_schedule_v066 import next_medication_label
from windows.medication_flags_v076 import (
    suspended, no_alarm, configured_reminder, active_reminder, reminder_clock
)

def undefined_schedule(record):
    if no_alarm(record):return False
    probe={**record,"suspended":False,"no_alarm":False}
    source=record.get("android_original")
    if isinstance(source,dict):
        probe["android_original"]={**source,"suspended_from":None,"no_alarm":False}
    label=next_medication_label(probe)
    return label.startswith(("Hora da toma por definir",
                             "Data da próxima toma por definir"))

def medication_filter_matches(record,category):
    if category=="all":return True
    if category=="active":return not suspended(record)
    if category=="suspended":return suspended(record)
    if category=="with_alarm":return active_reminder(record)
    if category=="no_alarm":return no_alarm(record)
    if category=="undefined":return undefined_schedule(record)
    return False

def medication_status(record):
    if suspended(record):return "Suspensa","#b72c3c","#ffffff"
    if no_alarm(record):return "Sem alarme","#f3bf43","#25200b"
    if configured_reminder(record):
        return "Aviso "+reminder_clock(record),"#238e51","#ffffff"
    return "Ativa","#238e51","#ffffff"
