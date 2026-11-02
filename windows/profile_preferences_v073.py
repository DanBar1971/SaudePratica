"""Decode only the selected Android patient's typed SharedPreferences.

The portable .spbackup embeds the *original* authenticated Android family ZIP.
Android stores clinical profile fields in per-profile preferences rather than in
the small portable profile.json. Never inspect another person's preferences.
No PIN, tokens, app alarms or secrets are imported into the Windows editor.
"""
from __future__ import annotations

from datetime import datetime
from windows.profile_fields_v066 import mapped_fields

DENY=("pin","password","token","secret","key","hash","password",
      "auth","credential","session","salt","private","fcm","api")
MAX_FIELD=4000

def unwrap_typed_profile(prefs:dict, source_id:str) -> tuple[dict,tuple]:
    if not isinstance(prefs,dict) or not isinstance(source_id,str):
        return {},()
    if source_id=="legacy":
        names=("mediagenda_profile",)
    else:
        if len(source_id)>48 or not all(c.isascii() and (c.isalnum() or c=="-") for c in source_id):
            return {},()
        names=("saudepratica_profile_"+source_id,
               "saudepratica_body_"+source_id)
    rows=[]
    combined={}
    for name in names:
        data=prefs.get(name)
        if not isinstance(data,dict):continue
        for key,item in data.items():
            if not isinstance(key,str) or not 1<=len(key)<=120:
                continue
            low=key.lower()
            if any(s in low for s in DENY):continue
            if not isinstance(item,dict) or item.get("t")!="s":
                # Only text is editable as text; boolean/integer metadata
                # are kept unmodified in the original encrypted Android ZIP.
                continue
            value=item.get("v")
            if not isinstance(value,str) or not value.strip() or len(value)>MAX_FIELD:
                continue
            combined.setdefault(key,value.strip())
            rows.append((key,value.strip()[:260]))
    # Typed values must be unpacked first; never inspect all family preferences
    # with a recursive mapper that could copy another person's identity.
    return mapped_fields(combined),tuple(rows[:100])
