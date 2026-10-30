"""SaúdePrática 1.9.74: compact alarm, one visible alarm notification, silent snooze status."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def change(p,a,b,label):
 s=p.read_text(encoding="utf-8")
 n=s.count(a)
 if n!=1:raise RuntimeError(f"v92 {label}: expected 1 anchor, got {n}")
 p.write_text(s.replace(a,b,1),encoding="utf-8")

# When the foreground medication service starts successfully, it already
# publishes the mandatory Android notification with the full-screen intent.
# Posting another normal alarm notification was making two UI events compete.
receiver=base/"notifications/NotificationReceiver.kt"
change(receiver,'''                runCatching{MedicationAlarmService.start(context,intent)}
                    .onFailure{android.util.Log.e("SaudePraticaAlarm",
                        "Scheduled service blocked; audible fallback",it)}
                manager.notify(alarmId,n.build())
                return''','''                SnoozedMedicationNotice.clear(context,profileId,
                    medicationId,scheduledDoseAt)
                val started=runCatching{
                    MedicationAlarmService.start(context,intent)
                    true
                }.onFailure{android.util.Log.e("SaudePraticaAlarm",
                    "Scheduled service blocked; audible fallback",it)
                }.getOrDefault(false)
                // Only show the separate audible notification if foreground
                // service startup fails. In normal use the foreground service
                // publishes one full-screen alarm notification itself.
                if(!started)manager.notify(alarmId,n.build())
                return''',"avoid two notifications")

alarm=base/"notifications/MedicationAlarmService.kt"
change(alarm,"import android.view.WindowManager","import android.view.WindowManager\nimport android.view.View","view import")
change(alarm,'''        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(dp(24), dp(36), dp(24), dp(30))
        }''','''        root.isFillViewport=true
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(dp(15),dp(10),dp(15),dp(12))
        }''',"compact body")
change(alarm,'''            setPadding(dp(4), dp(14), dp(4), dp(14))''','''            setPadding(dp(2),dp(5),dp(2),dp(5))''',"compact headings")
change(alarm,'''        layout.addView(label("⏰ ALARME DE MEDICAÇÃO", 25f))
        layout.addView(label(person, 22f))
        layout.addView(label(medicine?.medication?:if(demo)"Medicamento de teste" else "Medicação",36f))
        layout.addView(label(medicine?.dose.orEmpty(), 27f))''','''        layout.addView(label("⏰ ALARME DE MEDICAÇÃO",20f))
        layout.addView(label(person,18f))
        layout.addView(label(medicine?.medication?:
            if(demo)"Medicamento de teste" else "Medicação",29f))
        layout.addView(label(medicine?.dose.orEmpty(),21f))''',"smaller headings")
change(alarm,'''                    layoutParams = LinearLayout.LayoutParams(-1, dp(350))''','''                    layoutParams=LinearLayout.LayoutParams(-1,
                        dp((resources.displayMetrics.heightPixels/
                            resources.displayMetrics.density*0.27f)
                            .toInt().coerceIn(135,220)))''',"responsive image")
change(alarm,'''            " segundos. Sem resposta, fica por confirmar.",17f))''','''            " segundos. Sem resposta, fica por confirmar.",13f))''',"compact hint")
change(alarm,'''        fun control(text: String, background: Int, action: () -> Unit) = Button(this).apply {
            this.text = text
            textSize = 21f
            setTextColor(Color.WHITE)
            setBackgroundColor(background)
            setOnClickListener { action() }
            layoutParams = LinearLayout.LayoutParams(-1, dp(76)).apply {
                topMargin = dp(16)
            }
        }''','''        val actionRow=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER
            setPadding(0,dp(7),0,dp(5))
        }
        fun control(text: String, background: Int, action: () -> Unit) = Button(this).apply {
            this.text=text
            textSize=15f
            isAllCaps=false
            setTextColor(Color.WHITE)
            minWidth=0
            minimumWidth=0
            setPadding(dp(2),0,dp(2),0)
            setBackground(android.graphics.drawable.GradientDrawable().apply{
                shape=android.graphics.drawable.GradientDrawable.RECTANGLE
                cornerRadius=dp(14).toFloat()
                setColor(background)
                setStroke(dp(1),Color.argb(145,185,228,229))
            })
            elevation=dp(3).toFloat()
            setOnClickListener{action()}
            layoutParams=LinearLayout.LayoutParams(0,dp(60),1f)
        }''',"compact buttons")
change(alarm,'''        layout.addView(control(if(demo)"PARAR TESTE" else "ADIAR 10 MIN",
            Color.rgb(42,89,111)){''','''        actionRow.addView(control(if(demo)"PARAR TESTE" else "⏰ ADIAR 10 MIN",
            Color.rgb(37,82,108)){''',"first side button")
change(alarm,'''        if(!demo)layout.addView(control("✓ TOMEI",Color.rgb(0,125,102)){''','''        if(!demo){
            actionRow.addView(View(this).apply{
                layoutParams=LinearLayout.LayoutParams(dp(10),dp(1))
            })
            actionRow.addView(control("✓ TOMEI",Color.rgb(0,132,108)){''',"second side button")
change(alarm,'''                putExtra("notification_id", intent.getIntExtra("notification_id", 0))
            })
            finish()
        })
        root.addView(layout)''','''                putExtra("notification_id", intent.getIntExtra("notification_id", 0))
            })
            finish()
        })}
        layout.addView(actionRow)
        root.addView(layout)''',"close action row")

# The snooze status is deliberately quiet and is only shown AFTER a user
# presses ADIAR. It is removed as soon as the delayed alarm fires.
change(alarm,'''/** A snooze is never a confirmation; preserve the original scheduled dose identity. */
class MedicationAlarmActionReceiver : BroadcastReceiver() {''','''/** Quiet status while medication is explicitly postponed by 10 minutes. */
object SnoozedMedicationNotice {
    private const val CHANNEL="saudepratica_medication_postponed_v1"
    fun id(profile:String,medication:String,scheduledAt:Long):Int=
        ("postponed|$profile|$medication|$scheduledAt").hashCode()
    fun clear(context:Context,profile:String,medication:String,scheduledAt:Long){
        context.getSystemService(NotificationManager::class.java)
            .cancel(id(profile,medication,scheduledAt))
    }
    fun show(context:Context,profile:String,medication:String,
             scheduledAt:Long,until:Long){
        val manager=context.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel(
            CHANNEL,"Medicação adiada",NotificationManager.IMPORTANCE_LOW).apply {
            description="Aviso silencioso de medicação adiada 10 minutos"
            setSound(null,null)
            enableVibration(false)
            lockscreenVisibility=Notification.VISIBILITY_PRIVATE
        })
        val person=ProfileStore(context).all().firstOrNull{it.id==profile}
            ?.name.orEmpty().ifBlank{"SaúdePrática"}
        val name=runCatching{
            DataRepository(context,profile).loadMedications()
                .firstOrNull{it.id==medication}?.medication
        }.getOrNull().orEmpty().ifBlank{"Medicação"}
        val time=java.text.SimpleDateFormat("HH:mm",
            Locale("pt","PT")).format(java.util.Date(until))
        val open=context.packageManager.getLaunchIntentForPackage(context.packageName)
        val pi=open?.let{
            PendingIntent.getActivity(context,id(profile,medication,scheduledAt),
                it,PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        }
        val notice=NotificationCompat.Builder(context,CHANNEL)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle("⏳ $person · $name")
            .setContentText("Adiado até às $time · novo alarme em 10 min.")
            .setCategory(NotificationCompat.CATEGORY_STATUS)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setSilent(true)
            .setOngoing(false)
            .setAutoCancel(true)
        if(pi!=null)notice.setContentIntent(pi)
        manager.notify(id(profile,medication,scheduledAt),notice.build())
    }
}

/** A snooze is never a confirmation; preserve the original scheduled dose identity. */
class MedicationAlarmActionReceiver : BroadcastReceiver() {''',"snooze status helper")
change(alarm,'''        MedicationAlarmService.stop(context, intent.getIntExtra("notification_id", 0))
    }
}''','''        MedicationAlarmService.stop(context,intent.getIntExtra("notification_id",0))
        SnoozedMedicationNotice.show(context,profile,medId,whenOriginal,delay)
    }
}''',"show status after snooze")
intake=base/"notifications/IntakeActionReceiver.kt"
change(intake,'''        MedicationAlarmService.stop(context,notificationId)
        IntakeBadgeManager.refresh(context,profileId)''','''        MedicationAlarmService.stop(context,notificationId)
        SnoozedMedicationNotice.clear(context,profileId,medId,scheduledAt)
        IntakeBadgeManager.refresh(context,profileId)''',"clear status on confirmed")

gradle=root/"app/build.gradle.kts"
change(gradle,"versionCode = 83","versionCode = 84","code")
change(gradle,'versionName = "1.9.73"','versionName = "1.9.74"',"name")
print("SaúdePrática v1.9.74 alarm screen compact and two buttons with quiet snooze status")
