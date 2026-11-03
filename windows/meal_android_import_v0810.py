"""Import existing Android meal diary and original photos from a verified ZIP.

The full Android family backup is preserved and encrypted by SecureStore.
Only `saudepratica_meal_diary/<linked Android source ID>/` is considered;
all other family members, shared assets and unknown folders are ignored.
Import is explicit, idempotent and never overwrites manually created meals.
"""
from __future__ import annotations
from datetime import datetime
from hashlib import sha256
from uuid import UUID, uuid5, NAMESPACE_URL
import json
import re

from windows.android_archive_v063 import validated_files
from windows.remaining_models_v0810 import validate_meal

SOURCE_ID=re.compile(r"(?:legacy|[0-9a-fA-F-]{36})\Z")
MAX_MEALS=2500
MAX_PHOTO=8*1024*1024

def extract_meal_diary(blob:bytes,source_id:str):
    if not isinstance(source_id,str) or not SOURCE_ID.fullmatch(source_id):
        raise ValueError("Origem Android inválida.")
    files,_=validated_files(blob)
    prefix=f"saudepratica_meal_diary/{source_id}/"
    index=files.get(prefix+"meals.json")
    if index is None:
        return [],[]
    if len(index)>4*1024*1024:
        raise ValueError("Índice nutricional demasiado grande.")
    try:rows=json.loads(index.decode("utf-8-sig"))
    except (UnicodeError,ValueError) as exc:
        raise ValueError("Histórico nutricional Android inválido.") from exc
    if not isinstance(rows,list) or len(rows)>MAX_MEALS:
        raise ValueError("Número de refeições fora do limite.")
    records,assets=[],[]
    seen=set()
    for row in rows:
        if not isinstance(row,dict):
            continue
        original_id=row.get("id")
        if not isinstance(original_id,str):
            continue
        try:UID=UUID(original_id)
        except (ValueError,AttributeError):continue
        unique=str(UID)
        if unique in seen:continue
        at=row.get("at")
        if isinstance(at,bool) or not isinstance(at,(int,float)) or at<946684800000 or at>4102444800000:
            continue
        try:
            result=validate_meal(row)
            local=datetime.fromtimestamp(at/1000)
        except (OSError,OverflowError,ValueError):
            continue
        seen.add(unique)
        photo_name=row.get("photo","")
        photo_sha=""
        if isinstance(photo_name,str) and photo_name==f"{unique}.jpg":
            raw=files.get(prefix+photo_name)
            if (isinstance(raw,bytes) and 100<=len(raw)<=MAX_PHOTO
                    and raw.startswith(b"\xff\xd8\xff")):
                photo_sha=sha256(raw).hexdigest()
                assets.append((photo_sha,raw,photo_name))
        record={
            "id":str(uuid5(NAMESPACE_URL,f"saudepratica/android/meal/{source_id}/{unique}")),
            **result, "date":local.strftime("%Y-%m-%d"),
            "clock":local.strftime("%H:%M"),
            "source":"android", "android_source":source_id,
            "android_id":unique, "android_at":int(at),
            "photo_sha256":photo_sha,
            "estimated":bool(row.get("estimated",False)),
        }
        records.append(record)
    return records,assets
