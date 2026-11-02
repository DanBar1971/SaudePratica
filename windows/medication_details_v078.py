"""Conservative, read-only view of additional medication fields from Android.

Never traverse profile/appointment dictionaries: the only input is the medication
record and its own android_original. Excludes identifiers and internal metadata.
"""
from __future__ import annotations

DETAILS = (
    ("suspended_from", "Suspensa desde"),
    ("suspended_until", "Suspensa até"),
    ("start_date", "Data de início"),
    ("end_date", "Data de fim"),
    ("prescription_date", "Data da prescrição"),
    ("prescriber", "Prescritor"),
    ("doctor", "Médico"),
    ("frequency", "Frequência"),
    ("frequency_hours", "Intervalo (horas)"),
    ("duration", "Duração"),
    ("quantity", "Quantidade"),
    ("stock", "Stock"),
    ("repetitions", "Repetições"),
    ("repeat_interval", "Intervalo de repetição"),
    ("repeat_type", "Tipo de repetição"),
    ("prescription", "Prescrição"),
    ("posology", "Posologia"),
    ("instructions", "Instruções"),
    ("medicine_type", "Tipo de medicação"),
    ("active_ingredient", "Princípio ativo"),
    ("leaflet", "Bula"),
    ("barcode", "Código de barras"),
)
_ALIASES = {
    "start_date": ("startDate",),
    "end_date": ("endDate",),
    "prescription_date": ("prescriptionDate",),
    "frequency_hours": ("frequencyHours",),
    "repeat_interval": ("repeatInterval",),
    "repeat_type": ("repeatType",),
    "suspended_from": ("suspendedFrom",),
    "suspended_until": ("suspendedUntil",),
    "medicine_type": ("medicineType",),
    "active_ingredient": ("activeIngredient",),
}
def additional_medication_fields(record: dict) -> list[tuple[str,str]]:
    """Display simple native values only. No JSON blobs, paths or cross-module data."""
    if not isinstance(record,dict):
        return []
    original=record.get("android_original")
    sources=(record,original) if isinstance(original,dict) else (record,)
    result=[]
    for key,label in DETAILS:
        names=(key,)+_ALIASES.get(key,())
        value=None
        for source in sources:
            for name in names:
                v=source.get(name)
                if isinstance(v,(str,int,float)) and not isinstance(v,bool) and str(v).strip():
                    value=str(v).strip()[:350]
                    break
            if value is not None: break
        if value is not None:
            result.append((label,value))
    return result
