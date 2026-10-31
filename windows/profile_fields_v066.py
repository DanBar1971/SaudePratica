"""Conservative Android profile field mapping for Windows; never invent clinical data."""
from __future__ import annotations

FIELD_ALIASES = {
    "birth_date": ("birth_date", "birthDate", "dateOfBirth", "dob", "dataNascimento"),
    "phone": ("phone", "phoneNumber", "mobile", "mobilePhone", "telemovel",
              "telefone", "contactPhone", "contact_phone"),
    "email": ("email", "emailAddress", "mail"),
    "niss": ("niss", "NISS", "socialSecurityNumber"),
    "health_unit": ("health_unit", "healthUnit", "healthcareUnit",
                    "unidadeSaude", "unidade_saude", "healthCenter"),
    "address": ("address", "morada", "street", "streetAddress"),
    "city": ("city", "localidade", "locality"),
    "postal_code": ("postal_code", "postalCode", "zipCode",
                    "codigoPostal", "codigo_postal"),
    "emergency_name": ("emergency_name", "emergencyName"),
    "emergency_phone": ("emergency_phone", "emergencyPhone"),
    "notes": ("notes", "notas"),
}

LIMITS = {
    "birth_date": 10, "phone": 50, "email": 160, "niss": 40,
    "health_unit": 180, "address": 250, "city": 100,
    "postal_code": 24, "emergency_name": 120,
    "emergency_phone": 50, "notes": 3000,
}

def mapped_fields(original: dict) -> dict[str, str]:
    """Only populate fields found in source, never sample/default identities.

    Android versions have used camelCase and snake_case fields. Unknown fields
    remain available in the untouched android_profile_original object.
    """
    if not isinstance(original, dict):
        return {}
    # Profile values have moved between fields across Android versions.
    # Inspect only bounded profile dictionaries (not arbitrary encrypted prefs).
    sources=[]
    def collect(node,depth=0):
        if depth>4 or len(sources)>100:return
        if isinstance(node,dict):
            sources.append(node)
            for value in node.values():
                if isinstance(value,(dict,list)):
                    collect(value,depth+1)
        elif isinstance(node,list):
            for value in node[:30]:collect(value,depth+1)
    collect(original)
    result={}
    normalized=lambda key: "".join(c.lower() for c in key if c.isalnum())
    for field,aliases in FIELD_ALIASES.items():
        names={normalized(a) for a in aliases}
        for source in sources:
            found=""
            for key,value in source.items():
                if isinstance(key,str) and normalized(key) in names:
                    if isinstance(value,(str,int)) and not isinstance(value,bool):
                        found=str(value).strip()
                    if found:break
            if not found:
                # Some Android versions store field/value records rather
                # than a flat profile object.
                label=str(source.get("field") or source.get("key") or "")
                val=source.get("value")
                if normalized(label) in names and isinstance(val,(str,int)):
                    found=str(val).strip()
            if found and len(found)<=LIMITS[field]:
                result[field]=found
                break
    # The Windows birth date field only accepts strict ISO format.
    from datetime import date
    if "birth_date" in result:
        try:date.fromisoformat(result["birth_date"])
        except ValueError:result.pop("birth_date")
    return result

def missing_profile_fields(profile: dict, original: dict) -> dict[str, str]:
    """No overwriting saved Windows edits, even if Android later changes."""
    return {k:v for k,v in mapped_fields(original).items()
            if not profile.get(k)}
