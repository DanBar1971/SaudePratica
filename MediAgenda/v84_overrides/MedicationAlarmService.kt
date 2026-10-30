package com.mediagenda.app.notifications

import android.app.*
import android.content.*
import android.graphics.Color
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.media.RingtoneManager
import android.net.Uri
import android.os.*
import android.view.Gravity
import android.view.WindowManager
import android.widget.*
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.data.MedicationPhotoLoader
import com.mediagenda.app.data.ProfileStore

/** Loud, persistent medication alarm. Never confirms a dose without an explicit TOMEI press. */
class MedicationAlarmService : Service() {
    companion object {
        const val CHANNEL = "saudepratica_fullscreen_medication_v1"
        const val ACTION_START = "com.mediagenda.app.MED_ALARM_START"
        const val ACTION_STOP = "com.mediagenda.app.MED_ALARM_STOP"
        const val ACTION_SNOOZE = "com.mediagenda.app.MED_ALARM_SNOOZE"
        fun start(context: Context, original: Intent) {
            val intent = Intent(context, MedicationAlarmService::class.java).apply {
                action = ACTION_START
                putExtras(original)
            }
            ContextCompat.startForegroundService(context, intent)
        }
        fun stop(context: Context, id: Int) {
            context.startService(Intent(context, MedicationAlarmService::class.java).apply {
                action = ACTION_STOP
                putExtra("notification_id", id)
            })
        }
    }
    private var player: MediaPlayer? = null
    private var vibrator: android.os.Vibrator? = null
    private var currentId: Int = 0

    override fun onBind(intent: Intent?) = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            silence()
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
            return START_NOT_STICKY
        }
        if (intent?.action != ACTION_START) return START_NOT_STICKY
        val profileId = intent.getStringExtra("profile_id").orEmpty()
        val medicationId = intent.getStringExtra("medication_id").orEmpty()
        val scheduledAt = intent.getLongExtra("scheduled_at", 0L)
        if (profileId.isBlank() || medicationId.isBlank() || scheduledAt <= 0L ||
            ProfileStore(this).all().none { it.id == profileId }) {
            stopSelf()
            return START_NOT_STICKY
        }
        val med = DataRepository(this, profileId).loadMedications().firstOrNull {
            it.id == medicationId
        } ?: run { stopSelf(); return START_NOT_STICKY }
        currentId = intent.getIntExtra("notification_id", 990100)
        val profileName = ProfileStore(this).all().firstOrNull { it.id == profileId }?.name.orEmpty()
        val title = (profileName.ifBlank { "SaúdePrática" }) + " · " + med.medication
        val open = Intent(this, MedicationAlarmActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or
                Intent.FLAG_ACTIVITY_SINGLE_TOP)
            putExtras(intent)
        }
        val full = PendingIntent.getActivity(this, currentId, open,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val taken = Intent(this, IntakeActionReceiver::class.java).apply {
            action = IntakeActionReceiver.ACTION
            putExtra("profile_id", profileId)
            putExtra("medication_id", medicationId)
            putExtra("scheduled_at", scheduledAt)
            putExtra("notification_id", currentId)
        }
        val snooze = Intent(this, MedicationAlarmActionReceiver::class.java).apply {
            action = ACTION_SNOOZE
            putExtras(intent)
            data = Uri.parse("saudepratica://snooze/$profileId/$medicationId/$scheduledAt")
        }
        val takenPi = PendingIntent.getBroadcast(this,
            ("taken|$profileId|$medicationId|$scheduledAt").hashCode(), taken,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val snoozePi = PendingIntent.getBroadcast(this,
            ("snooze|$profileId|$medicationId|$scheduledAt").hashCode(), snooze,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val mgr = getSystemService(NotificationManager::class.java)
        mgr.createNotificationChannel(NotificationChannel(
            CHANNEL, "ALARMES DE MEDICAÇÃO — ecrã completo",
            NotificationManager.IMPORTANCE_HIGH).apply {
            description = "Alarme persistente; parar com TOMEI ou ADIAR"
            lockscreenVisibility = Notification.VISIBILITY_PRIVATE
            enableVibration(true)
            vibrationPattern = longArrayOf(0, 600, 350, 900)
            setSound(null, null) // The foreground player owns the continuous audio.
        })
        val n = NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
            .setContentTitle(title)
            .setContentText("ALARME DE MEDICAÇÃO · " + med.dose)
            .setStyle(NotificationCompat.BigTextStyle().bigText(
                "Alarme a tocar. Escolhe TOMEI depois de tomar ou ADIAR 10 MIN."))
            .setContentIntent(full)
            .setFullScreenIntent(full, true)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
            .setOngoing(true)
            .setAutoCancel(false)
            .addAction(android.R.drawable.ic_media_pause, "ADIAR 10 MIN", snoozePi)
            .addAction(android.R.drawable.checkbox_on_background, "✓ TOMEI", takenPi)
        MedicationPhotoLoader.load(this, med.images, 780)?.let { photo ->
            n.setLargeIcon(photo)
            n.setStyle(NotificationCompat.BigPictureStyle().bigPicture(photo)
                .bigLargeIcon(null as android.graphics.Bitmap?))
        }
        try {
            startForeground(currentId, n.build())
        } catch (e: Exception) {
            android.util.Log.e("SaudePraticaAlarm", "Foreground alarm unavailable", e)
            stopSelf()
            return START_NOT_STICKY
        }
        silence()
        try {
            val tone = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            player = MediaPlayer().apply {
                setAudioAttributes(AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build())
                setDataSource(this@MedicationAlarmService, tone)
                isLooping = true
                prepare()
                start()
            }
        } catch (e: Exception) {
            android.util.Log.e("SaudePraticaAlarm", "Could not start alarm audio", e)
        }
        try {
            val pattern = longArrayOf(0, 750, 400, 750, 900)
            val vm = getSystemService(android.os.VibratorManager::class.java)
            vibrator = vm.defaultVibrator
            vibrator?.vibrate(android.os.VibrationEffect.createWaveform(pattern, 0))
        } catch (_: Exception) {}
        return START_NOT_STICKY
    }

    private fun silence() {
        runCatching { player?.stop() }
        runCatching { player?.release() }
        player = null
        runCatching { vibrator?.cancel() }
        vibrator = null
    }
    override fun onDestroy() {
        silence()
        super.onDestroy()
    }
}

/** Visible over the lock screen when Android permits full-screen alarm intents. */
class MedicationAlarmActivity : Activity() {
    private fun dp(n: Int) = (n * resources.displayMetrics.density).toInt()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setShowWhenLocked(true)
        setTurnScreenOn(true)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        window.statusBarColor = Color.rgb(5, 24, 31)
        window.navigationBarColor = Color.rgb(5, 24, 31)
        val profile = intent.getStringExtra("profile_id").orEmpty()
        val medId = intent.getStringExtra("medication_id").orEmpty()
        val medicine = DataRepository(this, profile).loadMedications().firstOrNull { it.id == medId }
        val person = ProfileStore(this).all().firstOrNull { it.id == profile }?.name.orEmpty()
        val root = ScrollView(this).apply { setBackgroundColor(Color.rgb(5, 24, 31)) }
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            setPadding(dp(24), dp(36), dp(24), dp(30))
        }
        fun label(value: String, size: Float): TextView = TextView(this).apply {
            text = value
            textSize = size
            setTextColor(Color.WHITE)
            gravity = Gravity.CENTER
            setPadding(dp(4), dp(14), dp(4), dp(14))
        }
        layout.addView(label("⏰ ALARME DE MEDICAÇÃO", 25f))
        layout.addView(label(person, 22f))
        layout.addView(label(medicine?.medication ?: "Medicação", 29f))
        layout.addView(label(medicine?.dose.orEmpty(), 23f))
        medicine?.let { med ->
            MedicationPhotoLoader.load(this, med.images, 900)?.let { photo ->
                layout.addView(ImageView(this).apply {
                    setImageBitmap(photo)
                    adjustViewBounds = true
                    scaleType = ImageView.ScaleType.FIT_CENTER
                    layoutParams = LinearLayout.LayoutParams(-1, dp(300))
                })
            }
        }
        layout.addView(label("O alarme só termina quando escolheres uma ação.", 17f))
        fun control(text: String, background: Int, action: () -> Unit) = Button(this).apply {
            this.text = text
            textSize = 21f
            setTextColor(Color.WHITE)
            setBackgroundColor(background)
            setOnClickListener { action() }
            layoutParams = LinearLayout.LayoutParams(-1, dp(76)).apply {
                topMargin = dp(16)
            }
        }
        layout.addView(control("ADIAR 10 MIN", Color.rgb(42, 89, 111)) {
            sendBroadcast(Intent(this, MedicationAlarmActionReceiver::class.java).apply {
                action = MedicationAlarmService.ACTION_SNOOZE
                putExtras(intent)
            })
            finish()
        })
        layout.addView(control("✓ TOMEI", Color.rgb(0, 125, 102)) {
            sendBroadcast(Intent(this, IntakeActionReceiver::class.java).apply {
                action = IntakeActionReceiver.ACTION
                putExtra("profile_id", profile)
                putExtra("medication_id", medId)
                putExtra("scheduled_at", intent.getLongExtra("scheduled_at", 0L))
                putExtra("notification_id", intent.getIntExtra("notification_id", 0))
            })
            finish()
        })
        root.addView(layout)
        setContentView(root)
    }
}

/** A snooze is never a confirmation; preserve the original scheduled dose identity. */
class MedicationAlarmActionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != MedicationAlarmService.ACTION_SNOOZE) return
        val profile = intent.getStringExtra("profile_id").orEmpty()
        val medId = intent.getStringExtra("medication_id").orEmpty()
        val whenOriginal = intent.getLongExtra("scheduled_at", 0L)
        if (profile.isBlank() || medId.isBlank() || whenOriginal <= 0L) return
        val upcoming = Intent(context, NotificationReceiver::class.java).apply {
            putExtras(intent)
            action = "com.mediagenda.app.MED_ALARM_SNOOZED_FIRE"
            data = Uri.parse("saudepratica://med/$profile/$medId/$whenOriginal")
        }
        val pi = PendingIntent.getBroadcast(context,
            ("snoozed|$profile|$medId|$whenOriginal").hashCode(),
            upcoming, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val alarm = context.getSystemService(AlarmManager::class.java)
        val delay = System.currentTimeMillis() + 10 * 60_000L
        try {
            if (Build.VERSION.SDK_INT >= 31 && !alarm.canScheduleExactAlarms())
                alarm.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, delay, pi)
            else alarm.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, delay, pi)
        } catch (e: SecurityException) {
            alarm.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, delay, pi)
        }
        MedicationAlarmService.stop(context, intent.getIntExtra("notification_id", 0))
    }
}
