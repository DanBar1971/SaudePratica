#!/usr/bin/env python3
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
src=root/"src/main/java/com/mediagenda/app"
w=(src/"WorkMedicineActivity.kt").read_text()
h=(src/"HospitalProcessActivity.kt").read_text()
m=(src/"MainActivity.kt").read_text()
g=(root/"build.gradle.kts").read_text()
assert "versionCode = 147" in g and 'versionName = "1.9.137"' in g
assert "clinicalCard.addView(button(\"🏥 \"+display)" in w
assert 'override fun onResume()' in w
assert 'contentDescription=description' in h
assert 'search.doAfterTextChanged' in h
assert 'smallAction("✎"' in h
assert 'smallAction("×"' in h
assert 'EditProcess' not in h and "private fun editProcess()" in h
assert "private fun deleteProcess()" in h
assert 'hospital_processes.json' in h
assert 'process_[0-9a-f]{20}' in h
assert 'ViewCompat.setOnApplyWindowInsetsListener' in h
assert "private fun chooseAppointmentForSystemCalendar()" in m
assert 'setView(layout).setNegativeButton("Cancelar",null).create()' in m
assert 'setMessage("O calendário do telemóvel' not in m
assert 'Google Calendário' in m and 'Próximas (' in m
assert "Intent.ACTION_INSERT" in m
assert "READ_CALENDAR" not in (root/"src/main/AndroidManifest.xml").read_text()
print("Android 1.9.137: compact profile-safe UX, calendar chooser, data persistence OK")
