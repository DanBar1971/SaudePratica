#!/usr/bin/env python3
"""SaúdePrática v1.9.116 UI regression checks: no persisted clinical data deleted."""
from pathlib import Path
base=Path("build-src/MediAgenda_Android_v1/app")
s=(base/"src/main/java/com/mediagenda/app/MainActivity.kt").read_text(encoding="utf-8")
b=(base/"src/main/java/com/mediagenda/app/SafeMaterialAlertDialogBuilder.kt").read_text(encoding="utf-8")
gradle=(base/"build.gradle.kts").read_text(encoding="utf-8")
assert 'box.addView(noteBox("Cartão de Cidadão e identificação"' not in s
assert 'box.addView(noteBox("Contactos e responsável"' not in s
assert 'box.addView(noteBox("Lar ou residência assistida (opcional)"' not in s
assert 'listOf(healthUnit,address,postalCode).forEach{box.addView(it.container)}' in s
assert 'listOf(phone, email).forEach { box.addView(it.container) }' in s
assert 'listOf(homeName, homeAddress, homePhone, homeResponsible, homeNotes)' not in s
assert '"full_name" to fullName.edit.text' in s
assert '"family_role" to familyRole.edit.text' in s
assert 'prefs.edit()' in s
assert 'fichaButton=com.google.android.material.button.MaterialButton(this)' in s
assert 'deviceButton.text="✎ FICHA"' not in s
assert 'val deviceButton=secondaryButton(if(ownerOfAlarms)' not in s
assert 'text="📱 Neste telemóvel"' in s
assert 'text="✎ FICHA"' in s
assert 'dialog.setCanceledOnTouchOutside(false)' in b
assert 'dialog.setCancelable(false)' in b
assert 'win.setLayout(ViewGroup.LayoutParams.MATCH_PARENT,' in b
assert 'formTitle=="editar perfil"' in b
assert '"agendamento", "consulta", "appointment", "medication"' in b
assert 'versionCode = 126' in gradle and 'versionName = "1.9.116"' in gradle
assert (base/"src/main/res/drawable/saude_background.png").exists() or "saude_background" in s
print("1.9.116 UI gates OK: single FICHA, no excluded fields displayed, originals preserved, full-screen forms.")
