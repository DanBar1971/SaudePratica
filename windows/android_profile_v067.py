"""Selectively recover Android identity values and authentic CC images.

No clinical logs, documents, intake history or diagnostic rows are exposed in
the profile form. The entire original backup stays protected on disk.
"""
from __future__ import annotations

import json
import re
from windows.android_archive_v063 import validated_files
from windows.profile_fields_v066 import mapped_fields
from windows.profile_preferences_v073 import unwrap_typed_profile

SOURCE_ID = re.compile(r"^(?:legacy|[A-Fa-f0-9-]{36})$")


def _extract(files:dict, head:dict, source_id:str):
    if not isinstance(source_id,str) or not SOURCE_ID.fullmatch(source_id):
        return {}
    prefs=head.get("prefs")
    if not isinstance(prefs,dict):
        prefs={}
    node=prefs.get("saudepratica_profiles_v1",{})
    typed=node.get("profiles",{}) if isinstance(node,dict) else {}
    payload=typed.get("v","") if isinstance(typed,dict) else ""
    original={}
    if isinstance(payload,str):
        try:
            entries=json.loads(payload)
            if isinstance(entries,list):
                for person in entries[:80]:
                    if isinstance(person,dict) and person.get("id")==source_id:
                        original=person
                        break
        except (ValueError,TypeError):
            pass
    fields=mapped_fields(original)
    recovered,_=unwrap_typed_profile(prefs,source_id)
    fields.update({k:v for k,v in recovered.items() if not fields.get(k)})
    # Global caretaker status is a single source UUID in Android, not a
    # field of the patient's personal preferences. Never infer caregiver from
    # family_role or any other person's profile.
    caregiver=prefs.get("saudepratica_caregiver_v1",{})
    item=caregiver.get("caregiver_id",{}) if isinstance(caregiver,dict) else {}
    stored=item.get("v") if isinstance(item,dict) and item.get("t")=="s" else None
    if isinstance(stored,str) and SOURCE_ID.fullmatch(stored):
        fields["caregiver"]=(stored==source_id)
    elif isinstance(original.get("caregiver"),bool):
        fields["caregiver"]=original["caregiver"]
    # Profile identity files are the only eligible JSON sources. Do not walk
    # medication, appointment, clinical event or document index JSON.
    allowed_names={
        f"saudepratica_identity/{source_id}/records.json",
        f"saudepratica_identity/{source_id}/profile.json",
        f"saudepratica_profiles/{source_id}/profile.json",
    }
    for name,blob in files.items():
        if name not in allowed_names or len(blob)>128000:
            continue
        try:
            candidate=json.loads(blob)
            for k,v in mapped_fields(candidate).items():
                fields.setdefault(k,v)
        except (ValueError,UnicodeDecodeError):
            continue
    return fields


def read_profile_extras(archive:bytes,source_id:str):
    """Compatibility API: no raw diagnostic rows in the patient profile."""
    files,head=validated_files(archive)
    return _extract(files,head,source_id),()


def read_profile_view(archive:bytes,source_id:str):
    """Identity fields plus bounded authentic front/back CC JPEGs for this user."""
    files,head=validated_files(archive)
    fields=_extract(files,head,source_id)
    photos={}
    if not isinstance(source_id,str) or not SOURCE_ID.fullmatch(source_id):
        return fields,photos
    for kind in ("cc_front","cc_back"):
        data=files.get(f"saudepratica_identity/{source_id}/{kind}.jpg")
        if isinstance(data,bytes) and 30<=len(data)<=2_000_000 and data.startswith(b"\xff\xd8\xff"):
            photos[kind]=data
    return fields,photos
