from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'

def patch(path, old, new, label):
    content=path.read_text(encoding='utf-8')
    n=content.count(old)
    if n!=1: raise RuntimeError(f'v1.9.48 {label}: {n} matches, expected 1')
    path.write_text(content.replace(old,new,1),encoding='utf-8')

p=base/'data/WellnessStore.kt'
patch(p,'''    fun removeLastGlass(): Int {''','''    /** Notification taps are idempotent and can only register today's reminder.
     * Synchronous commit keeps a BroadcastReceiver's changes safely persisted.
     */
    fun recordReminderGlass(scheduledAt: Long): Int? = synchronized(WellnessStore::class.java) {
        if (scheduledAt <= 0L || scheduledAt > System.currentTimeMillis() + 300000L)
            return@synchronized null
        val reminderDate = java.time.Instant.ofEpochMilli(scheduledAt)
            .atZone(java.time.ZoneId.systemDefault()).toLocalDate()
        val today = LocalDate.now()
        if (reminderDate != today) return@synchronized null
        val date = today.toString()
        val previousIds = if (prefs.getString("water_action_date", "") == date)
            prefs.getStringSet("water_action_ids", emptySet()).orEmpty() else emptySet()
        val marker = scheduledAt.toString()
        if (marker in previousIds) return@synchronized null
        val amount = (todayMl() + glassMl).coerceAtMost(100000)
        val saved = prefs.edit()
            .putString("water_logged_date", date)
            .putInt("water_logged_ml", amount)
            .putString("water_action_date", date)
            .putStringSet("water_action_ids", previousIds.toMutableSet().apply { add(marker) })
            .commit()
        if (saved) amount else null
    }

    fun markGoalNotificationOnce(): Boolean = synchronized(WellnessStore::class.java) {
        val today=LocalDate.now().toString()
        if (optionalTargetMl <= 0 || todayMl() < optionalTargetMl ||
            prefs.getString("water_goal_notified_date", "") == today) return@synchronized false
        prefs.edit().putString("water_goal_notified_date", today).commit()
    }

    fun removeLastGlass(): Int {''','water action deduplication and goal state')

p=base/'notifications/NotificationScheduler.kt'
patch(p,'''        val interval = prefs.waterInterval
        val now = LocalDateTime.now(zone)''','''        val interval = prefs.waterInterval
        val now = LocalDateTime.now(zone)
        // After reaching a user-defined target, do not remind again today.
        val todayCompleted=prefs.optionalTargetMl>0 &&
            prefs.todayMl()>=prefs.optionalTargetMl''','water completed check')
patch(p,'''                val date = now.toLocalDate().plusDays(addDays.toLong())
                generateSequence(first)''','''                val date = now.toLocalDate().plusDays(addDays.toLong())
                if (addDays == 0 && todayCompleted) emptySequence()
                else generateSequence(first)''','water skip today')

p=base/'notifications/NotificationReceiver.kt'
patch(p,'''import com.mediagenda.app.data.PersonalHealthStore''','''import com.mediagenda.app.data.PersonalHealthStore
import com.mediagenda.app.data.WellnessStore''','water store import')
patch(p,'''            val rawTitle = intent.getStringExtra("title") ?: "SaúdePrática"''','''            val isWater=intent.getStringExtra("reminder_kind")=="water"
            if (isWater) {
                if (ProfileStore(context).all().none { it.id ==
                    intent.getStringExtra("profile_id") }) return
                val hydration=WellnessStore(context,
                    intent.getStringExtra("profile_id") ?: "legacy")
                if (!hydration.waterEnabled || (hydration.optionalTargetMl>0 &&
                    hydration.todayMl()>=hydration.optionalTargetMl)) return
            }
            val rawTitle = intent.getStringExtra("title") ?: "SaúdePrática"''','water reminder filtering')
patch(p,'''            // Box photos are optional. A deleted or inaccessible image never''','''            if(isWater){
                val scheduledAt=intent.getLongExtra("scheduled_at",0L)
                if(scheduledAt>0){
                    val action=Intent(context,WaterActionReceiver::class.java).apply{
                        this.action=WaterActionReceiver.ACTION
                        putExtra("profile_id",profileId)
                        putExtra("scheduled_at",scheduledAt)
                        putExtra("notification_id",id)
                    }
                    val request=("water-action|"+profileId+"|"+scheduledAt).hashCode()
                    val pending=PendingIntent.getBroadcast(context,request,action,
                        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                    builder.addAction(android.R.drawable.ic_input_add,
                        "🥛 Copo de água tomado",pending)
                }
            }

            // Box photos are optional. A deleted or inaccessible image never''','water notification action')

p=base/'WellnessActivity.kt'
patch(p,'''import com.mediagenda.app.notifications.NotificationScheduler''','''import com.mediagenda.app.notifications.NotificationScheduler
import com.mediagenda.app.notifications.WaterGoalNotifier''','notifier import')
patch(p,'''    private fun showWater() {
        heading("💧", "Beber água", "Avisos opcionais e registo diário")
        val amount = store.todayMl()
        val goal = store.optionalTargetMl
        card(content, "Hoje: $amount ml",
            if (goal > 0) "Objetivo escolhido: $goal ml" else "Sem objetivo diário obrigatório.",
            "🥛 Registar ${store.glassMl} ml") {
            store.recordGlass()
            showWater()
        }''','''    private fun showWater() {
        heading("💧", "Beber água", "Avisos opcionais e registo diário")
        val amount = store.todayMl()
        val goal = store.optionalTargetMl
        val remaining = (goal-amount).coerceAtLeast(0)
        val goalStatus=when {
            goal<=0 -> "Sem objetivo diário obrigatório."
            remaining==0 -> "🎉 Objetivo diário atingido! ($goal ml)"
            else -> "Objetivo: $goal ml · Faltam $remaining ml"
        }
        card(content, "Hoje: $amount ml",goalStatus,
            "🥛 Registar ${store.glassMl} ml") {
            store.recordGlass()
            WaterGoalNotifier.congratulateIfCompleted(this,profileId)
            if (goal>0 && store.todayMl()>=goal)
                NotificationScheduler(this).scheduleNextWater(profileId)
            showWater()
        }''','water UI remaining and goal')
patch(p,'''    private fun showGlasses() {''','''    override fun onResume(){
        super.onResume()
        // Reflect water logged from a notification while this screen was paused.
        if (::content.isInitialized && ::store.isInitialized &&
            intent.getStringExtra(EXTRA_SECTION)=="water") showWater()
    }

    private fun showGlasses() {''','water resume refresh')

manifest=root/'app/src/main/AndroidManifest.xml'
patch(manifest,'''        <receiver android:name=".notifications.NotificationReceiver" android:exported="false" />''','''        <receiver android:name=".notifications.NotificationReceiver" android:exported="false" />
        <receiver android:name=".notifications.WaterActionReceiver" android:exported="false" />''','manifest water receiver')

(base/'notifications/WaterActionReceiver.kt').write_text('''package com.mediagenda.app.notifications

import android.app.NotificationManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.data.WellnessStore

/** Registers each scheduled water reminder at most once, on its original day. */
class WaterActionReceiver:BroadcastReceiver(){
    companion object { const val ACTION="com.mediagenda.app.WATER_DRANK" }

    override fun onReceive(context:Context,intent:Intent){
        if(intent.action!=ACTION)return
        val profileId=intent.getStringExtra("profile_id").orEmpty()
        if(ProfileStore(context).all().none{it.id==profileId})return
        val scheduledAt=intent.getLongExtra("scheduled_at",0L)
        val store=WellnessStore(context,profileId)
        val newAmount=store.recordReminderGlass(scheduledAt) ?: return
        val manager=context.getSystemService(NotificationManager::class.java)
        manager.cancel(intent.getIntExtra("notification_id",0))
        WaterGoalNotifier.congratulateIfCompleted(context,profileId)
        // Reschedule after the recorded cup: if goal reached, next alarm is tomorrow.
        runCatching{NotificationScheduler(context).scheduleNextWater(profileId)}
        android.util.Log.i("SaudePratica","Hydration recorded: "+newAmount+" ml")
    }
}
''',encoding='utf-8')

(base/'notifications/WaterGoalNotifier.kt').write_text('''package com.mediagenda.app.notifications

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.mediagenda.app.WellnessActivity
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.data.WellnessStore

/** Exactly one completion notification per profile and day, if a target exists. */
object WaterGoalNotifier {
    fun congratulateIfCompleted(context:Context, profileId:String){
        val owner=ProfileStore(context).all().firstOrNull{it.id==profileId}?:return
        val store=WellnessStore(context,profileId)
        if(store.optionalTargetMl<=0 || store.todayMl()<store.optionalTargetMl)return
        if(Build.VERSION.SDK_INT>=33 && ContextCompat.checkSelfPermission(
            context,Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return
        if(!store.markGoalNotificationOnce())return
        val manager=context.getSystemService(NotificationManager::class.java)
        val channel="saudepratica_hydration_goal_v1"
        manager.createNotificationChannel(NotificationChannel(channel,
            "Objetivos de hidratação",NotificationManager.IMPORTANCE_DEFAULT).apply{
            description="Mensagem ao atingir o objetivo diário escolhido"
            lockscreenVisibility=android.app.Notification.VISIBILITY_PRIVATE
        })
        val open=Intent(context,WellnessActivity::class.java).apply{
            flags=Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra(WellnessActivity.EXTRA_PROFILE_ID,profileId)
            putExtra(WellnessActivity.EXTRA_SECTION,"water")
        }
        val id=("water-goal|"+profileId).hashCode()
        val pending=PendingIntent.getActivity(context,id,open,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val message="Cumpriste o teu objetivo de "+store.optionalTargetMl+
            " ml! Manter uma hidratação adequada ajuda a regular a temperatura " +
            "corporal e ao bom funcionamento do organismo. Respeita as restrições médicas."
        manager.notify(id,NotificationCompat.Builder(context,channel)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle(owner.name+" · 🎉 Parabéns pela hidratação!")
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
            .setContentIntent(pending)
            .setAutoCancel(true)
            .build())
    }
}
''',encoding='utf-8')

gradle=root/'app/build.gradle.kts'
patch(gradle,'versionCode = 57','versionCode = 58','version code')
patch(gradle,'versionName = "1.9.47"','versionName = "1.9.48"','version name')
print('v1.9.48: actionable water reminders, per-day idempotent glass logging, remaining target and completion congratulations.')