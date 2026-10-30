#!/usr/bin/env python3
"""SaúdePrática 1.9.118: safety gates for medication group migration."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
src=root/"src/main/java/com/mediagenda/app"
m=(src/"model/Models.kt").read_text(encoding="utf8")
r=(src/"data/DataRepository.kt").read_text(encoding="utf8")
s=(src/"MainActivity.kt").read_text(encoding="utf8")
b=(src/"SafeMaterialAlertDialogBuilder.kt").read_text(encoding="utf8")
g=(root/"build.gradle.kts").read_text(encoding="utf8")
assert 'var administrationRoute: String = ""' in m
assert 'var injectionType: String = ""' in m
for k in ['administration_route','injection_type']:
    assert 'o.optString("'+k+'")' in r
    assert '.put("'+k+'", m.' in r
assert "val administrationRoutes=listOf(" in s
assert "val injectionTypes=listOf(" in s
assert "m.administrationRoute=selectedRoute" in s
assert 'm.injectionType=if(selectedRoute=="parenteral")selectedInjection else ""' in s
assert 'MedicationPhotoLoader.load(this,existing.images,180)' in s
assert 'expandableMedicationGroup("Prescrição",prescriptionGroup)' in s
assert 'expandableMedicationGroup("Repetições",repetitionGroup)' in s
assert 'expandableMedicationGroup("Informação",infoGroup)' in s
assert 'expandableMedicationGroup("Bula / Folheto informativo",leafletGroup)' in s
assert 'expandableMedicationGroup("Foto da embalagem",photoGroup)' in s
assert 'formTitle=="confirmar medicação"' in b
for field in ["name.container","dose.container","dosePatternButton",
              "indication.container","reminder.container","doseTimes.container",
              "disableMedicationAlarm","medicationNotes.container"]:
    assert 'box.addView('+field+')' in s or 'addView('+field+')' in s
for struc in ["suspensionGroup.forEach{box.addView(it)}",
              "repo.saveMedications(all); reschedule(); showMedication()",
              '.setPositiveButton("Guardar") { _, _ ->',
              '.setNegativeButton("Cancelar", null).show()']:
    assert struc in s
assert 'versionCode = 128' in g and 'versionName = "1.9.118"' in g
# v1.9.117 exact-alarm timing and lifecycle must remain unchanged.
scheduler=(src/"notifications/NotificationScheduler.kt").read_text(encoding="utf8")
alarm=(src/"notifications/MedicationAlarmService.kt").read_text(encoding="utf8")
assert 'setExactAndAllowWhileIdle' in scheduler
assert 'canScheduleExactAlarms()' in scheduler
assert 'ACTION_TIMEOUT' in alarm
print("v1.9.118: grouped editor + route JSON round-trip anchors + alarm invariants OK.")
