"""SaúdePrática Windows: safe full-family Android ZIP preview and import mapping.

The original, hash-verified Android ZIP is retained byte-for-byte under DPAPI.
Recognised categories become Windows records; unsupported Android data remains
preserved inside the original ZIP. No automatic reverse sync or alarms.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping
import json
import uuid

from windows.android_archive_v063 import (
    AndroidSource, ZipPlan, archive_sources, prepare_archive,
    validated_files, _names_from_prefs, _json,
)
from windows.android_import_v062 import AndroidImportError
from windows.profile_fields_v066 import mapped_fields

@dataclass(frozen=True)
class FamilyMember:
    source: AndroidSource
    profile_id: str
    create: bool
    original_profile: dict
    imported: ZipPlan

@dataclass(frozen=True)
class FamilyPlan:
    digest: str
    original_zip: bytes
    members: tuple[FamilyMember, ...]
    file_count: int
    size: int

def _original_profiles(header: dict) -> dict[str, dict]:
    # Untrusted metadata: never take arbitrary paths or executable instructions.
    prefs = header.get("prefs", {})
    node = prefs.get("saudepratica_profiles_v1", {}) if isinstance(prefs, dict) else {}
    value = node.get("profiles", {}) if isinstance(node, dict) else {}
    if not isinstance(value, dict) or not isinstance(value.get("v"), str):
        return {}
    raw = _json(value["v"].encode("utf-8"), "Perfis")
    if not isinstance(raw, list) or len(raw) > 100:
        raise AndroidImportError("A lista de perfis Android é inválida.")
    result = {}
    for person in raw:
        if isinstance(person, dict):
            key = person.get("id")
            if isinstance(key, str) and len(key) <= 48 and key not in result:
                result[key] = person
    return result

def _new_profile(source: AndroidSource, original: dict) -> dict:
    # Consistent generated UUID; the Android source identity is kept separately.
    destination_id = str(uuid.uuid5(uuid.NAMESPACE_URL, 
        "saudepratica-windows:android-profile:" + source.identifier))
    name = str(original.get("name") or source.name).strip()[:120]
    if not name:
        raise AndroidImportError("Perfil Android sem nome.")
    person = {
        "id": destination_id, "name": name,
        "medications": [], "appointments": [],
        "android_zip_source_id": source.identifier,
        "android_zip_source_name": source.name,
        "android_profile_original": dict(original),
    }
    # One explicit mapping for current and older Android field naming.
    # Do not fill fields with examples or assume absent values.
    person.update(mapped_fields(original))
    if isinstance(original.get("caregiver"), bool):
        person["caregiver"] = original["caregiver"]
    return person

def plan_family_archive(blob: bytes, existing_profiles: list[dict]) -> FamilyPlan:
    """Validate everything before UI confirmation. No write operations."""
    files, header = validated_files(blob)
    originals = _original_profiles(header)
    sources = archive_sources(blob)
    # The legacy pseudo-profile is only real if it carries data or is named.
    if "legacy" not in originals and not any(
        key in files for key in ("medicacao.json", "agenda.json")
    ):
        sources = tuple(s for s in sources if s.identifier != "legacy")
    if not sources:
        raise AndroidImportError("O backup não contém perfis ou dados reconhecidos.")
    if len(sources) > 100:
        raise AndroidImportError("O backup contém demasiados perfis.")
    planned = []
    used_ids = set()
    for source in sources:
        original = originals.get(source.identifier, {})
        existing = [p for p in existing_profiles
                    if p.get("android_zip_source_id") == source.identifier]
        if len(existing) > 1:
            raise AndroidImportError(
                "Dois perfis Windows apontam para a mesma origem Android. "
                "Corrige esta associação antes de importar.")
        target = existing[0] if existing else _new_profile(source, original)
        pid = target["id"]
        if pid in used_ids:
            raise AndroidImportError("Identificadores de perfis repetidos.")
        used_ids.add(pid)
        if not existing and any(p.get("id") == pid for p in existing_profiles):
            raise AndroidImportError("Já existe outro perfil com este identificador.")
        imported = prepare_archive(blob, source.identifier, target)
        planned.append(FamilyMember(source, pid, not bool(existing),
                                    dict(original), imported))
    return FamilyPlan(sha256(blob).hexdigest(), blob, tuple(planned),
                      len(files), len(blob))

def plan_summary(plan: FamilyPlan) -> dict:
    return {
        "profiles": len(plan.members),
        "new_profiles": sum(m.create for m in plan.members),
        "existing_profiles": sum(not m.create for m in plan.members),
        "medications": sum(len(m.imported.medications.new) for m in plan.members),
        "appointments": sum(len(m.imported.appointments.new) for m in plan.members),
        "attachments": sum(len(m.imported.attachments) for m in plan.members),
        "original_files": plan.file_count,
        "bytes": plan.size,
    }
