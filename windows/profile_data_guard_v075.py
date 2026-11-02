def overlaps_medication(profile, value):
    if not isinstance(value, str) or not value.strip():
        return False
    for item in profile.get('medications', []):
        if not isinstance(item, dict):
            continue
        for entry in (item, item.get('android_original', {})):
            if isinstance(entry, dict) and any(isinstance(entry.get(k), str) and entry[k].strip() == value.strip() for k in ('note', 'notes')):
                return True
    return False
