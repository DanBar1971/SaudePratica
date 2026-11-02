"""Windows medication details: editable, profile-isolated clinical metadata.

Raw Android records remain untouched in android_original. Explicit Windows
changes are stored on the medication only; no alarm is scheduled on Windows.
"""
from __future__ import annotations

from pathlib import PurePosixPath

# Small, validated, documented set. Never import unrelated profile/agenda fields.
GROUPS = (
    ("Prescrição", (
        ("prescription_date", "Data da prescrição", 40),
        ("prescriber", "Profissional prescritor", 180),
        ("prescription", "Identificação / referência da receita", 300),
        ("start_date", "Início da medicação", 40),
        ("end_date", "Fim previsto", 40),
    )),
    ("Repetições e posologia", (
        ("frequency", "Frequência", 120),
        ("frequency_hours", "Intervalo (horas)", 40),
        ("repetitions", "Número de repetições", 40),
        ("repeat_interval", "Intervalo de repetição", 100),
        ("repeat_type", "Tipo de repetição", 100),
        ("duration", "Duração prevista", 100),
        ("posology", "Posologia detalhada", 1200),
    )),
    ("Informação clínica", (
        ("medicine_type", "Tipo de medicamento", 120),
        ("active_ingredient", "Princípio ativo", 220),
        ("quantity", "Quantidade", 100),
        ("stock", "Stock", 100),
        ("instructions", "Instruções de administração", 1200),
        ("barcode", "Código de barras", 100),
        ("suspended_from", "Suspensa desde", 40),
        ("suspended_until", "Suspensa até", 40),
    )),
    ("Bula", (
        ("leaflet", "Notas / referência da bula", 900),
    )),
)

ALIASES = {
    "prescription_date":("prescriptionDate",),
    "start_date":("startDate",),
    "end_date":("endDate",),
    "frequency_hours":("frequencyHours",),
    "repeat_interval":("repeatInterval",),
    "repeat_type":("repeatType",),
    "medicine_type":("medicineType",),
    "active_ingredient":("activeIngredient",),
    "suspended_from":("suspendedFrom",),
    "suspended_until":("suspendedUntil",),
    "prescriber":("doctor",),
}

ALL_FIELDS = {key: limit for _,group in GROUPS for key,_,limit in group}
DOC_KEYS = ("prescription_asset_sha256", "leaflet_asset_sha256")

def source_value(record, key):
    """Prefer an explicit Windows edit over the original Android field."""
    if not isinstance(record,dict) or key not in ALL_FIELDS:
        return ""
    old=record.get("android_original")
    for parent in (record,old if isinstance(old,dict) else {}):
        for field in (key,)+ALIASES.get(key,()):
            value=parent.get(field)
            if isinstance(value,(str,int,float)) and not isinstance(value,bool):
                return str(value)
    return ""

def apply_extras(old, inputs):
    """Return normalized changed fields, without deleting unedited Android types."""
    if not isinstance(inputs,dict):
        raise ValueError("Campos complementares inválidos.")
    result={}
    for key,value in inputs.items():
        if key not in ALL_FIELDS:
            raise ValueError("Campo clínico complementar desconhecido.")
        if not isinstance(value,str) or len(value.strip())>ALL_FIELDS[key]:
            raise ValueError("Campo demasiado longo: "+key)
        value=value.strip()
        if value==source_value(old or {},key):
            continue  # preserving int/float and Android native schema
        result[key]=value
    return result

def medication_document_assets(assets):
    """Only own-profile PDF/images; never show files from another module/profile."""
    allowed={".pdf",".jpg",".jpeg",".png",".webp"}
    return [item for item in assets if
            isinstance(item.get("sha256"),str) and len(item["sha256"])==64
            and PurePosixPath(str(item.get("filename",""))).suffix.lower() in allowed]

def medication_document_option(assets, digest):
    """Match an existing attachment only by immutable SHA and profile-scoped list."""
    return next((entry for entry in assets if entry.get("sha256")==digest),None)
