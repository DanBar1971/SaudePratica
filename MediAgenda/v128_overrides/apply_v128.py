#!/usr/bin/env python3
"""SaúdePrática v1.9.108: automatic appointment completion, update checks, clinical legacy display, support buttons."""
from pathlib import Path
R=Path('build-src/MediAgenda_Android_v1/app')
BASE=R/'src/main/java/com/mediagenda/app'

def once(name,old,new,label):
    p=BASE/name
    s=p.read_text(encoding='utf-8')
    n=s.count(old)
    if n!=1: raise AssertionError(f'{label}: expected 1 occurrence; found {n}')
    p.write_text(s.replace(old,new,1),encoding='utf-8')

# One shared appointment rule, used in Agenda, monthly calendar, and data persistence.
status=BASE/'model/AppointmentStatus.kt'
status.write_text('''package com.mediagenda.app.model

import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime

/** Past appointments become completed automatically, without asking the patient.
 * No false completion of future appointments, cancelled items, or open-ended
 * recurring events. A rescheduled appointment becomes pending again when saved.
 */
object AppointmentStatus {
    fun hasPassed(a: Appointment, now: LocalDateTime=LocalDateTime.now()): Boolean {
        if(a.cancelled) return false
        // Medical certificates are relevant until their expiry date, not the issue date.
        if(a.type=="atestado" && a.expiryDate.isNotBlank()) {
            val expiry=runCatching{LocalDate.parse(a.expiryDate)}.getOrNull() ?: return false
            return now.toLocalDate().isAfter(expiry)
        }
        val recurrence=a.recurrence
        if(recurrence.mode.isNotBlank() && recurrence.mode!="none") {
            val until=runCatching{LocalDate.parse(recurrence.until)}.getOrNull() ?: return false
            return until.isBefore(now.toLocalDate())
        }
        val date=runCatching{LocalDate.parse(a.date)}.getOrNull() ?: return false
        // If the time is not known, the appointment is considered completed
        // on the following day; never assume that midnight was the appointment.
        val time=runCatching{LocalTime.parse(a.time)}.getOrNull()
        return if(time!=null) !date.atTime(time).isAfter(now)
            else date.isBefore(now.toLocalDate())
    }
    fun completed(a: Appointment, now: LocalDateTime=LocalDateTime.now()): Boolean =
        !a.cancelled && (a.done || hasPassed(a,now))
}
''',encoding='utf-8')

main='MainActivity.kt'
once(main,'import com.mediagenda.app.data.DataRepository',
     'import com.mediagenda.app.model.AppointmentStatus\nimport com.mediagenda.app.data.DataRepository','appointment status import')

# On unlock/login perform a normal request, with a session-level rate guard.
once(main,'        repo.ensureFiles()\n        profileDraft = null', '''        repo.ensureFiles()
        // Older appointments are migrated once to a stored REALIZADA state.
        // Each profile has its own agenda file; never touch other patients.
        completePastAppointments()
        // The PIN/splash gate has already finished at this point. A new
        // available version prompts the user, but never installs silently.
        SaudePraticaUpdateChecker.checkAfterLogin(this)
        profileDraft = null''','activation and login')

needle='''    private fun showProfileSelection() {'''
normalize='''    private fun completePastAppointments(): Boolean {
        val all=runCatching{repo.loadAppointments()}.getOrNull() ?: return false
        val changed=all.filter{!it.done && !it.cancelled && AppointmentStatus.hasPassed(it)}
        if(changed.isEmpty())return false
        changed.forEach{it.done=true}
        return runCatching{repo.saveAppointments(all);true}.getOrDefault(false)
    }

'''
once(main,needle,normalize+needle,'normalize appointments helper')

# App opened for a long time or returned from background when appointment ended.
once(main,'''        if(::repo.isInitialized && profiles.all().isNotEmpty()){
            val restore=getSharedPreferences("saudepratica_other_reminder_repair",MODE_PRIVATE)''', '''        if(::repo.isInitialized && profiles.all().any{it.id==activeProfileId}){
            if(completePastAppointments() && currentScreen=="Agenda")showAgenda()
        }
        if(::repo.isInitialized && profiles.all().isNotEmpty()){
            val restore=getSharedPreferences("saudepratica_other_reminder_repair",MODE_PRIVATE)''','normalize on resume')

once(main,'val outstanding=repo.loadAppointments().count{!it.done}',
          'val outstanding=repo.loadAppointments().count{!AppointmentStatus.completed(it) && !it.cancelled}',
          'dashboard appointment badge')
once(main,'"Pendentes" -> !appt.done && !appt.cancelled',
          '"Pendentes" -> !AppointmentStatus.completed(appt) && !appt.cancelled','pending filter')
once(main,'"Realizadas" -> appt.done && !appt.cancelled',
          '"Realizadas" -> AppointmentStatus.completed(appt) && !appt.cancelled','realized filter')
once(main,'        val allAppointments=repo.loadAppointments().sortedWith(',
          '        completePastAppointments()\n        val allAppointments=repo.loadAppointments().sortedWith(',
          'normalize when opening agenda')

# Remove manual confirmation. The only explicit choice is active or cancelled.
once(main,'''        val statusField=android.widget.Spinner(this).apply{
            adapter=android.widget.ArrayAdapter(this@MainActivity,
                android.R.layout.simple_spinner_dropdown_item,
                listOf("Pendente","Realizada","Cancelada"))
            setSelection(if(a.cancelled)2 else if(a.done)1 else 0)
        }
        box.addView(noteBox("Estado da marcação",
            "Escolhe Pendente, Realizada ou Cancelada. As marcações antigas não mudam de estado automaticamente."))''',
'''        val statusField=android.widget.Spinner(this).apply{
            adapter=android.widget.ArrayAdapter(this@MainActivity,
                android.R.layout.simple_spinner_dropdown_item,
                listOf("Agendada","Cancelada"))
            setSelection(if(a.cancelled)1 else 0)
        }
        box.addView(noteBox("Estado da marcação",
            "Não precisas confirmar a realização: a marcação passa a Realizada após a data e hora. Para reagendar, altera a data/hora. Podes cancelar sem a apagar."))''','simplify appointment states')
once(main,'''                a.done=statusField.selectedItemPosition==1
                a.cancelled=statusField.selectedItemPosition==2''',
'''                a.cancelled=statusField.selectedItemPosition==1
                // When moved to a future date, an old completed item becomes
                // pending again. Cancelled items never count as realized.
                a.done=!a.cancelled && AppointmentStatus.hasPassed(a)''','save automatic appointment state')

once(main,'        val completed=a.done && !a.cancelled',
          '        val completed=AppointmentStatus.completed(a)','appointment card status')
once(main,'''        // Completed is a recorded state; merely being in the past never implies performed.
        val expired=runCatching{java.time.LocalDate.parse(a.date).isBefore(java.time.LocalDate.now())}
            .getOrDefault(false)''',
'''        // Past appointments are automatically realized; no "POR CONFIRMAR"
        // remains simply because the user missed a manual confirmation.
        val expired=AppointmentStatus.hasPassed(a)''','remove old manual confirmation comments')
once(main,'            expired -> "⚠️ POR CONFIRMAR"',
          '            expired -> "✓ REALIZADA"','no expired unconfirmed')

# MaterialAlertDialogBuilder setMessage+setItems can hide the item list in
# Material theming (observed on Xiaomi). Use real separately clickable buttons.
start='''            val supportOptions=arrayOf(
                AppLanguage.t(this,"☕ Buy Me a Coffee (primeira opção)"),
                AppLanguage.t(this,"PayPal (alternativa)")
            )'''
end='''                .setNegativeButton(AppLanguage.t(this,"Cancelar"),null)
                .show()'''
p=BASE/main;s=p.read_text(encoding='utf-8');i=s.index(start);j=s.index(end,i)+len(end)
replacement='''            val choices=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL
                setPadding(dp(18),dp(10),dp(18),dp(8))
            }
            choices.addView(TextView(this).apply{
                text=AppLanguage.t(this@MainActivity,
                    "O apoio é opcional. Escolhe o valor na página de pagamento. A app não exige 10 € nem efetua pagamentos.")
                textSize=14f
                setTextColor(if(isDarkPalette)Color.WHITE else Color.rgb(27,43,58))
                setPadding(0,0,0,dp(12))
            })
            val supportDialog=MaterialAlertDialogBuilder(this)
                .setTitle(AppLanguage.t(this,"☕ Apoiar o autor"))
                .setView(choices)
                .setNegativeButton(AppLanguage.t(this,"Cancelar"),null)
                .create()
            fun openChosenSupport(url:String){
                runCatching{startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(url)))}
                    .onSuccess{supportDialog.dismiss()}
                    .onFailure{showError(AppLanguage.t(this,
                        "Não foi possível abrir a página de apoio."))}
            }
            choices.addView(secondaryButton(
                AppLanguage.t(this,"☕ Buy Me a Coffee (primeira opção)")){
                openChosenSupport(SupportHelpActivity.BUY_ME_A_COFFEE_URL)
            },LinearLayout.LayoutParams(-1,dp(54)).apply{bottomMargin=dp(10)})
            choices.addView(secondaryButton(
                AppLanguage.t(this,"PayPal (alternativa)")){
                openChosenSupport(SupportHelpActivity.PAYPAL_URL)
            },LinearLayout.LayoutParams(-1,dp(54)))
            supportDialog.show()'''
s=s[:i]+replacement+s[j:]
p.write_text(s,encoding='utf-8')

# Do not remove old data from disk. Remove only its obsolete user-facing label.
once('WorkMedicineActivity.kt', '''        if(old.isNotBlank())clinicalCard.addView(text(
            "Número antigo (preservado): $old",13f,false,muted))
''', '''        // Legacy observation_number remains stored for old backups and imports,
        // but is not shown twice in the new multiple-record clinical editor.
''','hide legacy reference')

# Monthly calendar uses same derived state even if not yet migrated.
once('MonthlyCalendarActivity.kt','import com.mediagenda.app.model.Appointment',
     'import com.mediagenda.app.model.Appointment\nimport com.mediagenda.app.model.AppointmentStatus','calendar status import')
once('MonthlyCalendarActivity.kt','else if(a.done)content.addView(label("Concluído",12f,c=teal))',
     'else if(AppointmentStatus.completed(a))content.addView(label("Realizada",12f,c=teal))','calendar realized status')

# The update checker already polls every 12h on resume; supplement it with a
# once-per-session check immediately after the authenticated profile is ready.
updates='SaudePraticaUpdateChecker.kt'
once(updates,'    @Volatile private var busy=false', '''    @Volatile private var busy=false
    @Volatile private var checkedAfterLogin=false
    private const val LOGIN_MIN_INTERVAL=30L*60L*1000L

    /** Query once after opening/unlocking the app, even if the 12h cadence
     * has not elapsed. Avoid repeated queries when switching profiles. */
    fun checkAfterLogin(activity:AppCompatActivity){
        synchronized(this){
            if(checkedAfterLogin)return
            checkedAfterLogin=true
        }
        check(activity,false,login=true)
    }''','login checking method')
once(updates,'fun check(activity:AppCompatActivity,manual:Boolean=false) {',
            'fun check(activity:AppCompatActivity,manual:Boolean=false,login:Boolean=false) {',
            'checker API')
once(updates,'''        if(!manual && now-prefs.getLong("last_checked",0)<EVERY)return''',
'''        val since=now-prefs.getLong("last_checked",0L)
        if(!manual && since<(if(login)LOGIN_MIN_INTERVAL else EVERY))return''',
'login throttle')
# No 12-hour suppression after an offline/error attempt: successful answers only.
once(updates,'        if(!manual)prefs.edit().putLong("last_checked",now).apply()','        // Record a successful read only; offline starts remain retryable.','do not suppress network retries')
once(updates,'''                busy=false
                if(activity.isFinishing || activity.isDestroyed)return@runOnUiThread''',
'''                busy=false
                if(answer.status=="current" || answer.status=="update" ||
                    answer.status=="no_apk" || answer.status=="no_release")
                    prefs.edit().putLong("last_checked",System.currentTimeMillis()).apply()
                if(activity.isFinishing || activity.isDestroyed)return@runOnUiThread''','record successful release check')
once(updates,'''            if(!manual && prefs.getString("prompted_tag",null)==a.tag)return
            prefs.edit().putString("prompted_tag",a.tag).apply()''',
'''            val already=prefs.getString("prompted_tag",null)==a.tag
            val promptAge=System.currentTimeMillis()-prefs.getLong("prompted_at",0L)
            if(!manual && already && promptAge<EVERY)return
            prefs.edit().putString("prompted_tag",a.tag)
                .putLong("prompted_at",System.currentTimeMillis()).apply()''','allow periodic reminders after later')

lang=BASE/'i18n/AppLanguage.kt'
s=lang.read_text(encoding='utf-8')
entries='''O apoio é opcional. Escolhe o valor na página de pagamento. A app não exige 10 € nem efetua pagamentos.\tSupport is optional. Choose the amount on the payment page. The app does not require €10 or make payments.\tLe soutien est facultatif. Choisissez le montant sur le site de paiement. L’application n’impose pas 10 € et n’effectue aucun paiement.\tUnterstützung ist freiwillig. Wähle den Betrag auf der Zahlungsseite. Die App verlangt keine 10 € und führt keine Zahlungen aus.\tEl apoyo es opcional. Elige el importe en la página de pago. La aplicación no exige 10 € ni realiza pagos.
Agendada\tScheduled\tPlanifiée\tGeplant\tProgramada
Não precisas confirmar a realização: a marcação passa a Realizada após a data e hora. Para reagendar, altera a data/hora. Podes cancelar sem a apagar.\tNo manual confirmation needed: the appointment becomes Completed after its date and time. To reschedule, change the date/time. You can cancel without deleting.\tAucune confirmation requise : le rendez-vous passe à Terminé après sa date et son heure. Pour reporter, modifiez la date et l’heure. Vous pouvez annuler sans supprimer.\tKeine Bestätigung erforderlich: Nach Datum und Uhrzeit wird der Termin als Erledigt markiert. Zum Verschieben Datum/Uhrzeit ändern. Absagen ohne Löschen ist möglich.\tNo hace falta confirmar: la cita pasa a Realizada después de su fecha y hora. Para reprogramarla cambia fecha/hora. Puedes cancelarla sin borrarla.
'''
assert all(len(x.split('\t'))==5 for x in entries.strip().splitlines())
anchor='    private val source="""\n'
assert s.count(anchor)==1
lang.write_text(s.replace(anchor,anchor+entries,1),encoding='utf-8')

gradle=R/'build.gradle.kts'
g=gradle.read_text(encoding='utf-8')
assert g.count('versionCode = 117')==1 and g.count('versionName = "1.9.107"')==1
gradle.write_text(g.replace('versionCode = 117','versionCode = 118').replace('versionName = "1.9.107"','versionName = "1.9.108"'),encoding='utf-8')
print('v1.9.108 patch applied: completed appointments by date, login update, support buttons, legacy hidden')