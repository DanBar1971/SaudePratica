"""Typed per-profile health/expense records for Windows 0.8.8.

Clinical records are a private personal log, NOT a diagnosis or medical device.
Expense tax status is entered by the user; there is no automatic IRS validation.
Amounts are integer euro cents, never floating point.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import re

CLINICAL_TYPES = (
    "Medicina do Trabalho", "Consulta", "Diagnóstico / condição",
    "Análises / Exames", "Tratamento", "Relatório", "Outro",
)
CLINICAL_STATES = ("Por avaliar", "Em acompanhamento", "Concluído")
EXPENSE_TYPES = (
    "Farmácia", "Consulta", "Exame", "Tratamento", "Óculos / Lentes",
    "Dispositivo médico", "Seguro / ADSE", "Outros",
)
TAX_STATES = (
    "Por verificar", "Pendente no e-Fatura",
    "Confirmado no e-Fatura", "Não aplicável",
)


def date_iso(value: str, *, optional: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError("Data inválida.")
    value = value.strip()
    if not value and optional:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError("Indica uma data real no formato DD/MM/AAAA.")


def cents_from_pt(value: str) -> int:
    """Parse 0, 10,25, 1234.50, 1.234,50 without float rounding."""
    if not isinstance(value, str):
        raise ValueError("Valor monetário inválido.")
    value = value.strip().replace("€", "").replace(" ", "")
    if not value:
        return 0
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    elif value.count(".") > 1:
        raise ValueError("Valor monetário inválido.")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Valor monetário inválido.") from exc
    if not amount.is_finite() or amount < 0 or amount > Decimal("100000000.00"):
        raise ValueError("Valor fora dos limites.")
    if amount != amount.quantize(Decimal(".01")):
        raise ValueError("Máximo duas casas decimais.")
    return int(amount * 100)


def euro_text(cents: int) -> str:
    if not isinstance(cents, int) or cents < 0:
        raise ValueError("Cêntimos inválidos.")
    return f"{cents // 100:,}".replace(",", ".") + f",{cents % 100:02d} €"


def _txt(data: dict, key: str, max_len: int, *, required: bool = False) -> str:
    value = data.get(key, "")
    if not isinstance(value, str) or len(value) > max_len:
        raise ValueError("Campo inválido: " + key)
    text = value.strip()
    if required and not text:
        raise ValueError("Campo obrigatório: " + key)
    return text


def _document(data: dict) -> str:
    digest = _txt(data, "document_sha256", 64)
    if digest and not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("Identificador de anexo inválido.")
    return digest


def clinical_record(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Registo clínico inválido.")
    title = _txt(data, "title", 160, required=True)
    category = _txt(data, "category", 60)
    status = _txt(data, "status", 50)
    if category not in CLINICAL_TYPES or status not in CLINICAL_STATES:
        raise ValueError("Tipo ou estado clínico inválido.")
    return {
        "title": title,
        "date": date_iso(_txt(data, "date", 15, required=True)),
        "category": category,
        "status": status,
        "unit": _txt(data, "unit", 180),
        "professional": _txt(data, "professional", 160),
        "description": _txt(data, "description", 4000),
        "next_date": date_iso(_txt(data, "next_date", 15), optional=True),
        "document_sha256": _document(data),
    }


def expense_record(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Despesa inválida.")
    category = _txt(data, "category", 60)
    state = _txt(data, "taxStatus", 60)
    if category not in EXPENSE_TYPES or state not in TAX_STATES:
        raise ValueError("Categoria ou estado fiscal inválido.")
    amount = data.get("amountCents")
    returned = data.get("reimbursedCents")
    for val in (amount, returned):
        if isinstance(val, bool) or not isinstance(val, int) or not 0 <= val <= 10_000_000_000:
            raise ValueError("Valor da despesa/reembolso inválido.")
    return {
        "date": date_iso(_txt(data, "date", 15, required=True)),
        "category": category,
        "merchant": _txt(data, "merchant", 160),
        "description": _txt(data, "description", 400),
        "receiptNumber": _txt(data, "receiptNumber", 100),
        "supplierNif": _txt(data, "supplierNif", 40),
        "amountCents": amount,
        "reimbursedCents": returned,
        "taxStatus": state,
        "notes": _txt(data, "notes", 1500),
        "document_sha256": _document(data),
    }


def annual_summary(records: list[dict], year: int) -> dict:
    if not isinstance(year, int) or not 1900 <= year <= 9999:
        raise ValueError("Ano inválido.")
    items = [x for x in records if isinstance(x, dict)
             and str(x.get("date", "")).startswith(f"{year:04d}-")]
    total = sum(int(x.get("amountCents", 0)) for x in items)
    reimbursed = sum(int(x.get("reimbursedCents", 0)) for x in items)
    return {
        "count": len(items),
        "amountCents": total,
        "reimbursedCents": reimbursed,
        "remainingCents": max(0, total - reimbursed),
    }
