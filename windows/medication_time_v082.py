"""Single, unambiguous medication clock in SaúdePrática Windows.

The Windows catalogue is not an alarm scheduler and does not sync edits back
to Android. The exported Android record remains immutable. Old Windows
records may contain a second HH:MM in 'time'; this is NOT a meal condition.
"""
from __future__ import annotations
import re
from windows.medication_flags_v076 import CLOCK,reminder_clock

def original_time(record):
    return str(record.get("time","")).strip() if isinstance(record,dict) else ""

def condition_value(record):
    """Only display text indicating a meal/administration condition, never HH:MM."""
    value=original_time(record)
    return "" if CLOCK.fullmatch(value) else value

def mismatched_legacy_clock(record):
    """Offer a conscious one-click choice; do not move clinical times silently."""
    legacy=original_time(record)
    official=reminder_clock(record)
    return legacy if CLOCK.fullmatch(legacy) and official and official!=legacy else ""

def time_for_store(previous,reminder,condition):
    """Keep the legacy time field consistent with the single visible clock.

    If the user enters a meal indication, retain that textual value, separate
    from reminder_time. If no textual indication exists, store the chosen
    reminder clock in both legacy time and the canonical reminder_time.
    """
    reminder=(reminder or "").strip()
    condition=(condition or "").strip()
    if condition and not CLOCK.fullmatch(condition):
        return condition
    if condition and re.fullmatch(r"\d{1,2}\s*[:hH]\s*\d{2}",condition):
        raise ValueError("Para alterar a hora, utiliza o campo Hora de aviso.")
    return reminder

def canonical_reminder_fields(reminder,condition):
    """Validated user input, ready for save_medication."""
    reminder=(reminder or "").strip()
    if reminder and not CLOCK.fullmatch(reminder):
        raise ValueError("A hora de aviso deve ser HH:MM, por exemplo 08:00.")
    return {"reminder_time":reminder,
            "time":time_for_store(None,reminder,condition)}
