#!/usr/bin/env python3
"""Verificação das regras da eliminação de perfis na v1.9.115."""
from pathlib import Path
base=Path("build-src/MediAgenda_Android_v1/app")
s=(base/"src/main/java/com/mediagenda/app/MainActivity.kt").read_text(encoding="utf-8")
start=s.index("    private fun confirmDeleteSelectedProfile(profile:HealthProfile) {")
end=s.find("\n    private fun ",start+15)
method=s[start:end if end!=-1 else len(s)]
assert "if(!pinStore.enabled())" in method
assert 'val pin=input("PIN da SaúdePrática (4 dígitos)", "")' in method
assert "if(!pinStore.verify(pin.edit.text.toString()))" in method
assert 'ProfileDeletionStore(this).delete(profile.id)' in method
assert "phrase.edit" not in method
assert 'Para confirmar, escreve:' not in method
assert "form.addView(pin.container)" in method
assert 'profile.id.takeLast(8)' in method
assert '.setTitle("Eliminar perfil?")' in method
g=(base/"build.gradle.kts").read_text(encoding="utf-8")
assert 'versionName = "1.9.115"' in g and "versionCode = 125" in g
print("v1.9.115: PIN mandatory; confirmation phrase removed; exact profile ID retained.")
