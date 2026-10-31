"""Read-only medication gallery semantics; does not create Windows alarms."""
from windows.medication_schedule_v066 import next_medication_label

def no_alarm(record):
    src=record.get("android_original")
    return bool(record.get("no_alarm") or
                (isinstance(src,dict) and src.get("no_alarm")))

def undefined_schedule(record):
    if no_alarm(record):return False
    probe={**record,"suspended":False,"no_alarm":False}
    src=record.get("android_original")
    if isinstance(src,dict):
        probe["android_original"]={**src,"suspended_from":None,"no_alarm":False}
    label=next_medication_label(probe)
    return label.startswith(("Hora da toma por definir",
                             "Data da próxima toma por definir"))

def medication_filter_matches(record,category):
    if category=="all":return True
    if category=="active":return not bool(record.get("suspended"))
    if category=="suspended":return bool(record.get("suspended"))
    if category=="no_alarm":return no_alarm(record)
    if category=="undefined":return undefined_schedule(record)
    return False

def medication_status(record):
    if record.get("suspended"):return "Suspensa","#b72c3c","#ffffff"
    if no_alarm(record):return "Sem alarme","#f3bf43","#25200b"
    return "Ativa","#238e51","#ffffff"
