"""SaúdePrática Windows 0.8.5: per-profile calendar and honest dose history.

Never infer that an alarm fired, a medicine was taken, or a dose was missed.
Expected slots are *projections* only when the original scheduling rule
provides a reliable daily/weekly/specific-date recurrence.
"""
from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from windows.agenda_filter_v069 import appointment_datetime
from windows.medication_flags_v076 import active_reminder, reminder_clock

WEEKDAYS = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
MONTHS = ("Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
          "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro")


def _date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            pass
    return None


def month_cells(profile: dict, year: int, month: int):
    """Rows of (date, belongs_to_month, appointment_count), Monday first."""
    if not 1 <= int(month) <= 12 or not 1 <= int(year) <= 9999:
        raise ValueError("Mês ou ano inválido.")
    counts = {}
    for item in profile.get("appointments", []):
        if not isinstance(item, dict):
            continue
        dt = appointment_datetime(item)
        if dt:
            counts[dt.date()] = counts.get(dt.date(), 0) + 1
    rows = calendar.Calendar(firstweekday=0).monthdatescalendar(int(year), int(month))
    return [[(day, day.month == int(month), counts.get(day, 0))
             for day in row] for row in rows]


def appointments_for_day(profile: dict, day: date):
    """Only appointments belonging to the exact supplied profile and day."""
    matches = []
    for item in profile.get("appointments", []):
        if not isinstance(item, dict):
            continue
        dt = appointment_datetime(item)
        if dt and dt.date() == day:
            matches.append(item)
    return sorted(matches, key=lambda x: appointment_datetime(x))


def month_shift(year: int, month: int, delta: int):
    index = year * 12 + (month - 1) + delta
    if not 12 <= index < 120000:
        raise ValueError("Mês fora do intervalo.")
    return index // 12, index % 12 + 1


def _source(record):
    original = record.get("android_original")
    return original if isinstance(original, dict) else record


def _occurs_on(record, day: date):
    if not active_reminder(record):
        return False
    src = _source(record)
    def field(key):
        # An explicit Windows edit takes precedence over the imported source.
        return record.get(key) if key in record else src.get(key)
    start = _date(field("repeat_start") or field("start_date"))
    until = _date(field("repeat_until") or field("end_date"))
    if start and day < start:
        return False
    if until and day > until:
        return False
    specific = field("schedule")
    if isinstance(specific, dict):
        selected = specific.get(day.strftime("%Y-%m"))
        if isinstance(selected, list) and day.day in selected:
            return True
        # A concrete calendar selection wins; never infer missing dates.
        if specific:
            return False
    mode = str(field("repeat_mode") or "").strip().lower()
    if mode == "daily":
        return True
    if mode == "weekly":
        days = field("repeat_weekdays")
        if not isinstance(days, list):
            return False
        # Android weekdays: Sunday=0, Monday=1 ... Saturday=6.
        return (day.weekday() + 1) % 7 in days
    return False


def expected_slots(profile: dict, day: date):
    """Show scheduled expectations, never manufacture pending SOS/one-off doses."""
    slots = []
    for med in profile.get("medications", []):
        if not isinstance(med, dict) or not med.get("id") or not _occurs_on(med, day):
            continue
        clock = reminder_clock(med)
        if not clock:
            continue
        try:
            hour, minute = map(int, clock.split(":"))
            base = datetime.combine(day, datetime.min.time()).replace(
                hour=hour, minute=minute)
        except (ValueError, TypeError):
            continue
        original = _source(med)
        pattern = str(med.get("dose_pattern") or original.get("dose_pattern") or "").lower()
        interval = next((h for h in (4, 6, 12)
                         if f"de {h} em {h} horas" in pattern), None)
        repeats = range(0, 24, interval) if interval else (0,)
        for hours in repeats:
            scheduled = base + timedelta(hours=hours)
            if scheduled.date() != day:
                continue
            slots.append({
                "medication_id": med["id"],
                "medication": str(med.get("name") or original.get("medication") or "Medicação"),
                "dose": str(med.get("dose") or ""),
                "scheduled_at": scheduled.isoformat(timespec="minutes"),
                "time": scheduled.strftime("%H:%M"),
            })
    return sorted(slots, key=lambda x: (x["scheduled_at"], x["medication"]))


def dose_entries(profile: dict, day: date, now: datetime | None = None):
    """Pending projections + actual confirmations, deduplicated by planned slot.

    A dose more than 15 minutes late means 'atrasada por confirmar',
    never 'omitted' or 'confirmed'. Existing manual entries remain visible.
    """
    now = now or datetime.now()
    records = [r for r in profile.get("intakes", []) if isinstance(r, dict)]
    planned = expected_slots(profile, day)
    matched = set()
    result = []
    for slot in planned:
        confirmation = next((r for r in records if
            r.get("medication_id") == slot["medication_id"] and
            r.get("scheduled_at") == slot["scheduled_at"] and
            r.get("status") == "confirmed"), None)
        if confirmation:
            matched.add(str(confirmation.get("id")))
            result.append({**slot, "id": confirmation.get("id"),
                           "status": "confirmed",
                           "confirmed_at": confirmation.get("confirmed_at", "")})
        else:
            planned_at = datetime.fromisoformat(slot["scheduled_at"])
            state = ("late" if planned_at + timedelta(minutes=15) < now
                     else "pending")
            result.append({**slot, "status": state})
    for rec in records:
        if rec.get("status") != "confirmed" or str(rec.get("id")) in matched:
            continue
        confirmation = str(rec.get("confirmed_at") or "")
        try:
            when = datetime.fromisoformat(confirmation)
        except ValueError:
            continue
        if when.date() != day:
            continue
        result.append({
            "id": rec.get("id"),
            "medication_id": rec.get("medication_id"),
            "medication": rec.get("medication") or "Medicação",
            "dose": rec.get("dose") or "",
            "scheduled_at": rec.get("scheduled_at") or "",
            "time": when.strftime("%H:%M"),
            "status": "confirmed",
            "confirmed_at": confirmation,
        })
    return sorted(result, key=lambda item:
                  (item["time"], item["medication"], item["status"]))


def dose_counts(profile: dict, day: date, now: datetime | None = None):
    values = dose_entries(profile, day, now)
    return {
        "confirmed": sum(x["status"] == "confirmed" for x in values),
        "pending": sum(x["status"] == "pending" for x in values),
        "late": sum(x["status"] == "late" for x in values),
    }
