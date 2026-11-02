"""Read-only medication state adapter for raw Android and Windows records.

Android exports suspend dates as `suspended_from` and a separate
`reminder_time` without `suspended` or `no_alarm` booleans. Old Windows
.spbackup versions can contain these raw source records unchanged.
Never change the original, and never schedule an alarm on Windows.
"""
import re

CLOCK = re.compile(r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")

def _original(record):
    source=record.get("android_original")
    return source if isinstance(source,dict) else {}

def suspended(record):
    if "suspended" in record and type(record["suspended"]) is bool:
        return record["suspended"]
    source=_original(record)
    value=record.get("suspended_from") or source.get("suspended_from")
    return bool(value) if isinstance(value,(str,bool)) else False

def no_alarm(record):
    if "no_alarm" in record and type(record["no_alarm"]) is bool:
        return record["no_alarm"]
    source=_original(record)
    for key in ("no_alarm","noAlarm"):
        value=record.get(key)
        if type(value) is bool:return value
        value=source.get(key)
        if type(value) is bool:return value
    return False

def reminder_clock(record):
    source=_original(record)
    for key in ("reminder_time","alarmTime","time"):
        for obj in (record,source):
            value=obj.get(key)
            if isinstance(value,str) and CLOCK.fullmatch(value.strip()):
                return value.strip()
    return ""

def configured_reminder(record):
    return bool(reminder_clock(record)) and not no_alarm(record)

def active_reminder(record):
    return configured_reminder(record) and not suspended(record)
