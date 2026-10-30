"""SaúdePrática 1.9.68: Portuguese spoken medication alarm and quiet missed-intake badge."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def change(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1: raise RuntimeError(f"v86 {label}: expected 1 anchor, got {n}")
    path.write_text(s.replace(old,new,1),encoding="utf-8")

alarm=base/"notifications/MedicationAlarmService.kt"
change(alarm,"import android.os.*","import android.os.*\nimport android.speech.tts.TextToSpeech\nimport java.util.Locale","TTS imports")
change(alarm,"    private var currentId: Int = 0",
"""    private var currentId: Int = 0
    private var speaker: TextToSpeech? = null
    private val repeatHandler = Handler(Looper.getMainLooper())
    private var repeatSpeech: Runnable? = null
    private var speechSession = 0
    private fun announce(name: String, dose: String) {
        val session = ++speechSession
        val words = "Alarme de medicação. Está na hora de tomar $name. " +
            (if(dose.isNotBlank()) "Dose: $dose. " else "") +
            "Por favor, confirme a toma na SaúdePrática."
        val tts = TextToSpeech(applicationContext) { status ->
            if(status == TextToSpeech.SUCCESS && session == speechSession) {
                val engine = speaker ?: return@TextToSpeech
                val portuguese = Locale("pt", "PT")
                val result = engine.setLanguage(portuguese)
                if(result == TextToSpeech.LANG_MISSING_DATA ||
                    result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    android.util.Log.w("SaudePraticaAlarm",
                        "Portuguese speech not available; falling back to device voice")
                    engine.language = Locale.getDefault()
                }
                engine.setAudioAttributes(AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
                engine.setSpeechRate(0.87f)
                val repeat = object : Runnable {
                    override fun run() {
                        if(session != speechSession) return
                        engine.speak(words, TextToSpeech.QUEUE_FLUSH, null,
                            "saudepratica-medication-$session")
                        repeatHandler.postDelayed(this, 18_000L)
                    }
                }
                repeatSpeech = repeat
                repeatHandler.post(repeat)
            } else if(session == speechSession) {
                android.util.Log.w("SaudePraticaAlarm",
                    "TTS unavailable; retain repeated alarm tone")
            }
        }
        speaker = tts
    }""","TTS fields")
change(alarm,"        silence()\n        try {\n            val tone = RingtoneManager.getDefaultUri",
"""        silence()
        announce(med.medication, med.dose)
        try {
            val tone = RingtoneManager.getDefaultUri""","announce on alarm")
change(alarm,"    private fun silence() {\n        runCatching { player?.stop() }",
"""    private fun silence() {
        ++speechSession
        repeatSpeech?.let { repeatHandler.removeCallbacks(it) }
        repeatSpeech = null
        runCatching { speaker?.stop(); speaker?.shutdown() }
        speaker = null
        runCatching { player?.stop() }""","stop voice with TOMEI/ADIAR")

change(alarm,
"""                repeatSpeech = repeat
                repeatHandler.post(repeat)""",
"""                // Prefer speech to the old ringtone; audio fallback is used
                // only when Portuguese text-to-speech is unavailable.
                runCatching { player?.stop(); player?.release() }
                player = null
                repeatSpeech = repeat
                repeatHandler.post(repeat)""",
"voice replaces ringtone once ready")

badge=base/"notifications/IntakeBadgeManager.kt"
change(badge,'private const val CHANNEL="saudepratica_intake_counter_v1"',
       'private const val CHANNEL="saudepratica_intake_counter_quiet_v2"',
       "new quiet badge channel")
change(badge,
'''        if(count<=0){manager.cancel(NOTIFICATION);return}
        if(Build.VERSION.SDK_INT>=33''',
'''        if(count<=0){
            prefs(context).edit().remove("last_notified_count").apply()
            manager.cancel(NOTIFICATION)
            return
        }
        // Do not repost the same counter on every foreground refresh:
        // some Xiaomi launchers display each repost as a floating banner.
        if(prefs(context).getInt("last_notified_count",-1)==count) return
        if(Build.VERSION.SDK_INT>=33''',
"avoid repeated heads-up")
change(badge,
'''        manager.createNotificationChannel(NotificationChannel(CHANNEL,"Tomas por confirmar",
            NotificationManager.IMPORTANCE_LOW).apply{''',
'''        manager.createNotificationChannel(NotificationChannel(CHANNEL,"Tomas por confirmar",
            NotificationManager.IMPORTANCE_MIN).apply{''',
"quiet badge importance")
change(badge,
'''            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setVisibility(NotificationCompat.VISIBILITY_SECRET)''',
'''            .setPriority(NotificationCompat.PRIORITY_MIN)
            .setSilent(true)
            .setVisibility(NotificationCompat.VISIBILITY_SECRET)''',
"silent notification")
change(badge,
'''        manager.notify(NOTIFICATION,notification.build())''',
'''        manager.notify(NOTIFICATION,notification.build())
        prefs(context).edit().putInt("last_notified_count",count).apply()''',
"cache count")
build=root/"app/build.gradle.kts"
change(build,"versionCode = 77","versionCode = 78","versionCode")
change(build,'versionName = "1.9.67"','versionName = "1.9.68"',"versionName")
print("v1.9.68: spoken PT-PT medication alarms, no repeated missed-dose banners")
