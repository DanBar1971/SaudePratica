"""SaúdePrática v1.9.64: med form selection summary, notes, alarm channel."""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
def change(path,old,new,what):
    s=path.read_text(encoding='utf-8')
    if s.count(old)!=1: raise RuntimeError(f'v82 {what}: expected 1 anchor, got {s.count(old)}')
    path.write_text(s.replace(old,new,1),encoding='utf-8')
model=base/'model/Models.kt'
change(model,'    var doseTimes: String = "",','    var doseTimes: String = "",\n    var notes: String = "",','notes model')
repo=base/'data/DataRepository.kt'
change(repo,'                doseTimes = o.optString("dose_times"),','                doseTimes = o.optString("dose_times"),\n                notes = o.optString("notes"),','read notes')
change(repo,'                .put("dose_times", m.doseTimes)','                .put("dose_times", m.doseTimes)\n                .put("notes", m.notes)','write notes')
main=base/'MainActivity.kt'
change(main,'        val doseTimes = input("Horas às refeições (HH:mm, HH:mm, HH:mm)", m.doseTimes)','        val doseTimes = input("Horas às refeições (HH:mm, HH:mm, HH:mm)", m.doseTimes)\n        val medicationNotes = inputMulti("Notas da medicação", m.notes)','notes input')
change(main,'        lateinit var dosePatternButton:MaterialButton','        val chosenPatternText=input("Tipo de toma prescrito",patterns.first{it.second==chosenPattern}.first)\n        chosenPatternText.edit.isEnabled=false\n        lateinit var dosePatternButton:MaterialButton','pattern summary input')
change(main,'                    chosenPattern=patterns[index].second\n                    dosePatternButton.text="Tipo de toma: "+patterns[index].first','                    chosenPattern=patterns[index].second\n                    chosenPatternText.edit.setText(patterns[index].first)\n                    dosePatternButton.text="Tipo de toma: "+patterns[index].first','pattern updates')
change(main,'        box.addView(dosePatternButton)','        box.addView(chosenPatternText.container)\n        box.addView(dosePatternButton)','pattern summary display')
change(main,'        box.addView(reminder.container);box.addView(doseTimes.container)','        box.addView(reminder.container);box.addView(doseTimes.container)\n        box.addView(medicationNotes.container)','notes display')
change(main,'                m.doseTimes=doseTimes.edit.text.toString().trim()','                m.doseTimes=doseTimes.edit.text.toString().trim()\n                m.notes=medicationNotes.edit.text.toString().trim()','notes save')
receiver=base/'notifications/NotificationReceiver.kt'
# Android notification channels are immutable after first creation.
# A fresh medication channel renews alarm sound/vibration without touching
# the quiet appointments channel or the existing TOMEI action.
change(receiver,'isMedication->"saudepratica_medication_alarm_v2"',
       'isMedication->"saudepratica_medication_alarm_v3"','renew medication alarm channel')

build=root/'app/build.gradle.kts'
change(build,'versionCode = 73','versionCode = 74','versionCode')
change(build,'versionName = "1.9.63"','versionName = "1.9.64"','versionName')
print('v1.9.64 medication intake selection persists visibly; notes saved; dedicated high priority channel; TOMEI retained')
