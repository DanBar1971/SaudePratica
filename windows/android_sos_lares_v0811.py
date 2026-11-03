"""Android SOS and Lares recovery from original protected family ZIP.

The Android stores SOS values in SharedPreferences
'saudepratica_emergency_<source_id>' and care-home data in
'saudepratica_care_home_v1_<source_id>'. The complete backup's
backup.json includes typed preferences. Only an explicitly linked source
is ever inspected. No other relative's preferences can be read.
"""
from __future__ import annotations

import json
import re
from uuid import NAMESPACE_URL, uuid5

from windows.android_archive_v063 import validated_files
from windows.remaining_models_v0810 import (
    SCHEMAS, EMERGENCY_FIELDS, validate_emergency, validate_record,
)

SOURCE_ID = re.compile(r"(?:legacy|[0-9a-fA-F-]{36})\Z")
MAX_MONTHS = 240
STATE_MAP = {
    "PENDENTE": "Por pedir",
    "PEDIDA": "Pedida",
    "RECEBIDA": "Recebida",
    "SUBMETIDA": "Submetida",
    "ANALISE": "Em análise",
    "CORRIGIR": "Pendente de correção",
    "REEMBOLSADA": "Reembolsada",
}
VALENCE_MAP = {
    "ERPI": "ERPI",
    "SAD": "Serviço de Apoio Domiciliário",
    "DIA": "Centro de Dia",
}
SOS_KEYS = tuple(x[0] for x in EMERGENCY_FIELDS)


def _typed_text(prefs: dict, group: str, limit: int = 4000) -> dict[str, str]:
    """Decode only string-typed values, as written by FamilyBackupStore.kt."""
    node = prefs.get(group, {})
    if not isinstance(node, dict):
        return {}
    result = {}
    for key, item in node.items():
        if (not isinstance(key, str) or len(key) > 120 or
                not isinstance(item, dict) or item.get("t") != "s"):
            continue
        value = item.get("v")
        if isinstance(value, str) and len(value) <= limit:
            result[key] = value.strip()
    return result


def _sos(raw: dict) -> dict:
    """Import exact Android SOS keys; never infer blood group/allergies."""
    data = {key: raw.get(key, "") for key in SOS_KEYS}
    for key, label, maximum in EMERGENCY_FIELDS:
        data[key] = data[key][:maximum]
    return validate_emergency(data)


def _care(raw: dict, source_id: str):
    name = raw.get("institution", "").strip()[:160]
    valence = VALENCE_MAP.get(raw.get("valence", "ERPI"), "Outra")
    institution = []
    if name:
        entry = validate_record("residences", {
            "title": name,
            "type": valence,
            "address": raw.get("address", "")[:240],
            "phone": raw.get("phone", "")[:30],
            "email": raw.get("email", "")[:160],
            "website": raw.get("website", "")[:1000],
            "contact": raw.get("contact", "")[:140],
            "notes": raw.get("notes", "")[:3000],
        })
        entry["id"] = str(uuid5(
            NAMESPACE_URL, f"saudepratica/android/care/{source_id}/institution"))
        entry["source"] = "android"
        entry["android_source"] = source_id
        institution = [entry]

    months = raw.get("months", "")
    if not months:
        return institution, []
    if len(months) > 250000:
        raise ValueError("Registo de mensalidades Android excessivo.")
    try:
        amounts = json.loads(months)
    except (TypeError, ValueError) as exc:
        raise ValueError("Índice de faturas do lar Android inválido.") from exc
    if not isinstance(amounts, dict) or len(amounts) > MAX_MONTHS:
        raise ValueError("Histórico de mensalidades Android inválido.")
    invoices = []
    for month, details in amounts.items():
        if (not isinstance(month, str) or
                not re.fullmatch(r"(?:19|20)\d{2}-(?:0[1-9]|1[0-2])", month) or
                not isinstance(details, dict)):
            continue
        original_status = str(details.get("state", "PENDENTE")).upper()
        status = STATE_MAP.get(original_status)
        if status is None:
            # Do not downgrade an unknown recorded state to 'Por pedir'.
            continue
        original_doc = str(details.get("document_name", ""))[:140]
        text = raw.get("notes", "")
        note = (f"Documento Android: {original_doc}\n" if original_doc else "")
        if details.get("updated_at"):
            note += "Última atualização no Android (ms): " + str(
                details.get("updated_at"))[:26] + "\n"
        if text:
            note += str(text)[:1700]
        form = {
            "title": name or f"Mensalidade {month} (Android)",
            "date": month + "-01",
            "status": status,
            "amount": str(details.get("total", "") or "0"),
            "paid": str(details.get("paid", "") or "0"),
            "reimbursed": str(details.get("refunded", "") or "0"),
            "reference": str(details.get("adse_reference", ""))[:160],
            "notes": note[:2500],
        }
        try:
            invoice = validate_record("residence_invoices", form)
        except ValueError:
            # Preserve original ZIP untouched instead of inventing amounts.
            continue
        invoice["id"] = str(uuid5(
            NAMESPACE_URL, f"saudepratica/android/care/{source_id}/{month}"))
        invoice["source"] = "android"
        invoice["android_source"] = source_id
        invoice["android_month"] = month
        if details.get("document_id"):
            invoice["android_document_id"] = str(details["document_id"])[:120]
        invoices.append(invoice)
    return institution, sorted(invoices, key=lambda x: x["date"], reverse=True)


def extract_sos_care(archive: bytes, source_id: str):
    """Return own SOS + own institution + own invoices from verified ZIP."""
    if not isinstance(source_id, str) or not SOURCE_ID.fullmatch(source_id):
        raise ValueError("Perfil Android inválido.")
    _, manifest = validated_files(archive)
    prefs = manifest.get("prefs", {})
    if not isinstance(prefs, dict):
        raise ValueError("Preferências Android inválidas.")
    sos = _sos(_typed_text(prefs, "saudepratica_emergency_" + source_id))
    raw_care = _typed_text(
        prefs, "saudepratica_care_home_v1_" + source_id, limit=300000)
    residences, invoices = _care(raw_care, source_id)
    return {
        "sos": sos,
        "residences": residences,
        "residence_invoices": invoices,
    }
