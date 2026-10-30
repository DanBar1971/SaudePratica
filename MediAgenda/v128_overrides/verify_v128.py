#!/usr/bin/env python3
"""SaúdePrática 1.9.108 regression gates for appointment, update, legacy reference and support."""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1/app');src=root/'src/main/java/com/mediagenda/app'
get=lambda f:(src/f).read_text(encoding='utf-8')
main=get('MainActivity.kt');checker=get('SaudePraticaUpdateChecker.kt')
appointments=get('model/AppointmentStatus.kt');cal=get('MonthlyCalendarActivity.kt')
clinical=get('WorkMedicineActivity.kt');lang=get('i18n/AppLanguage.kt')
gradle=(root/'build.gradle.kts').read_text(encoding='utf-8')
assert 'versionCode = 118' in gradle and 'versionName = "1.9.108"' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert 'fun hasPassed(a: Appointment' in appointments
assert 'if(a.cancelled) return false' in appointments
assert 'else date.isBefore(now.toLocalDate())' in appointments
assert 'return until.isBefore(now.toLocalDate())' in appointments
assert 'completePastAppointments()' in main
assert 'SaudePraticaUpdateChecker.checkAfterLogin(this)' in main
assert 'changed.forEach{it.done=true}' in main
assert 'repo.saveAppointments(all)' in main
assert '"Pendentes" -> !AppointmentStatus.completed(appt)' in main
assert '"Realizadas" -> AppointmentStatus.completed(appt)' in main
assert 'val completed=AppointmentStatus.completed(a)' in main
assert 'a.done=!a.cancelled && AppointmentStatus.hasPassed(a)' in main
assert 'listOf("Agendada","Cancelada")' in main
assert '"⚠️ POR CONFIRMAR"' not in main
assert 'AppointmentStatus.completed(a)' in cal
assert 'Número antigo (preservado): $old' not in clinical
assert '.getString("observation_number"' in clinical or '"observation_number"' in clinical
assert 'fun checkAfterLogin(activity:AppCompatActivity)' in checker
assert 'if(login)LOGIN_MIN_INTERVAL else EVERY' in checker
assert 'if(!manual && already && promptAge<EVERY)return' in checker
assert 'val choices=LinearLayout(this).apply' in main
assert 'supportDialog.show()' in main
assert 'setItems(supportOptions)' not in main
assert 'SupportHelpActivity.BUY_ME_A_COFFEE_URL' in main
assert 'SupportHelpActivity.PAYPAL_URL' in main
assert 'buymeacoffee.com/danielbarr7' in get('SupportHelpActivity.kt')
assert 'O apoio é opcional.' in lang
print('PASS SaúdePrática 1.9.108 appointment state, login updates, clinical legacy, and payment buttons')