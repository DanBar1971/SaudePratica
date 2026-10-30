#!/usr/bin/env python3
"""SaúdePrática 1.9.106: backwards-compatible UX regression assertions."""
from pathlib import Path
base=Path('build-src/MediAgenda_Android_v1/app')
code=base/'src/main/java/com/mediagenda/app'
read=lambda path:(code/path).read_text(encoding='utf-8')
main=read('MainActivity.kt')
clinical=read('WorkMedicineActivity.kt')
wizard=read('ProfileWizardActivity.kt')
models=read('model/Models.kt')
storage=read('data/DataRepository.kt')
assert "versionCode = 116" in (base/'build.gradle.kts').read_text()
assert 'versionName = "1.9.106"' in (base/'build.gradle.kts').read_text()
assert 'applicationId = "com.mediagenda.app.stable"' in (base/'build.gradle.kts').read_text()
assert "val clinicalEntries=obs.lines()" in clinical
assert "chooseClinicalDistrict{selected->hospital.setText(selected)}" in clinical
assert "HealthcareCatalog.facilities(this,district,municipality)" in clinical
assert "Editar número antigo (opcional)" not in clinical
assert 'putString("observations_by_unit",encoded)' in clinical
assert "var cancelled: Boolean = false" in models
assert 'o.optBoolean("cancelled", false)' in storage
assert '.put("cancelled", a.cancelled)' in storage
assert 'if (a.done || a.cancelled) return' in read('notifications/NotificationScheduler.kt')
assert "saudepratica_agenda_filters" in main
for state in ('Pendentes','Realizadas','Canceladas'):
    assert state in main
assert 'statusField.selectedItemPosition==2' in main
assert 'h.stateBadge.text=' in main
assert '"category" -> allItems.sortedWith' in main
assert '"status" -> allItems.sortedWith' in main
assert 'Color.argb(224,248,251,252)' in main
assert 'Color.argb(224,248,251,252)' in clinical
assert 'Color.argb(224,248,251,252)' in wizard
assert 'Color.argb(224,248,251,252)' in read('MealAiActivity.kt')
assert "if(step<5)" in wizard
assert 'step+1}/6' in wizard
assert 'putString("contact_name",emergencyName.trim())' in wizard
assert 'putString("health_unit",healthUnit.trim())' in wizard
assert "val wizardInk" in wizard
assert "Analisada com Gemini" in read('MealAiActivity.kt')
lang=read('i18n/AppLanguage.kt')
assert "Buy the author a beer" not in lang
assert "Offrir une bière" not in lang
assert "Invitar a una cerveza" not in lang
assert "Offer a coffee via PayPal" in lang
assert "Apoiar o autor ☕" in lang
print("SaúdePrática v1.9.106 source gates OK — data and signing identities unchanged")
