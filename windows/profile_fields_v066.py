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
    sources=[original]
    for key in ("personal", "personalInfo", "details", "contacts", "health", "profile"):
        child=original.get(key)
        if isinstance(child,dict):
            sources.append(child)
    result={}
    for field,aliases in FIELD_ALIASES.items():
        for source in sources:
            found=next((source[k].strip() for k in aliases
                if isinstance(source.get(k),str) and source[k].strip()), "")
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
