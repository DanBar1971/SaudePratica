from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/notifications")
scheduler = root/"NotificationScheduler.kt"
receiver = root/"NotificationReceiver.kt"

def sub(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"SaúdePrática 1.9.4 missing {label}: {old[:110]}")
    return text.replace(old, new, 1)

s = scheduler.read_text(encoding="utf-8")
# Keep pending alarm identifiers unique for different people, but leave the
# spoken/current user's name to the receiver, which resolves renames in real time.
s = sub(s,
    '''"💊 " + (if (multiple) "$profileName: " else "") + m.medication,''',
    '''"💊 " + m.medication,''', "medication title")
s = sub(s,
    '''"📅 " + (if (multiple) "$profileName: " else "") + a.activity.ifBlank { a.department },''',
    '''"📅 " + a.activity.ifBlank { a.department },''', "appointment title")
s = sub(s,
    '''            putExtra("profile_id", profileId)''',
    '''            putExtra("profile_id", profileId)
            putExtra("profile_name", com.mediagenda.app.data.ProfileStore(context).all()
                .firstOrNull { it.id == profileId }?.name.orEmpty())''',
    "profile name hint")
scheduler.write_text(s, encoding="utf-8")

s = receiver.read_text(encoding="utf-8")
s = sub(s,
'''import android.graphics.Color''',
'''import android.graphics.Color
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.net.Uri
import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.data.ProfileStore''',
"imports")

s = sub(s,
'''            val title = intent.getStringExtra("title") ?: "SaúdePrática"
            val body = intent.getStringExtra("body") ?: "Aviso de medicação"
            val id = intent.getIntExtra("notification_id", title.hashCode())''',
'''            val rawTitle = intent.getStringExtra("title") ?: "SaúdePrática"
            val profileId = intent.getStringExtra("profile_id") ?: "legacy"
            val profileName = runCatching {
                ProfileStore(context).all().firstOrNull { it.id == profileId }?.name.orEmpty()
            }.getOrDefault("").ifBlank {
                intent.getStringExtra("profile_name").orEmpty()
            }
            // Always identify the patient at the very beginning, even with one profile.
            val title = if (profileName.isBlank()) rawTitle else "$profileName · $rawTitle"
            val body = intent.getStringExtra("body") ?: "Aviso de medicação"
            val id = intent.getIntExtra("notification_id", title.hashCode())''',
"notification title")
s = sub(s,
'''            if (tapIntent != null) builder.setContentIntent(tapIntent)
            manager.notify(id, builder.build())''',
'''            if (tapIntent != null) builder.setContentIntent(tapIntent)

            // Box photos are optional. A deleted or inaccessible image never
            // prevents the reminder and always falls back to the normal alert.
            if (!medicationId.isNullOrBlank()) {
                val photo = runCatching {
                    DataRepository(context, profileId).loadMedications()
                        .firstOrNull { it.id == medicationId }
                        ?.images?.firstOrNull()
                }.getOrNull()
                if (!photo.isNullOrBlank()) {
                    decodeMedicationPhoto(context, photo)?.let { bitmap ->
                        builder.setLargeIcon(bitmap)
                        builder.setStyle(NotificationCompat.BigPictureStyle()
                            .bigPicture(bitmap)
                            .bigLargeIcon(null as Bitmap?)
                            .setSummaryText(body))
                    }
                }
            }
            manager.notify(id, builder.build())''',
"medication image notification")
s = sub(s,
'''class NotificationReceiver : BroadcastReceiver() {
    override fun onReceive''',
'''class NotificationReceiver : BroadcastReceiver() {
    /**
     * A bounded thumbnail, not a full-resolution photo. It can be a private
     * FileProvider content Uri or a camera's file Uri. No network requests.
     */
    private fun decodeMedicationPhoto(context: Context, source: String): Bitmap? {
        return runCatching {
            val uri = Uri.parse(source)
            if (uri.scheme != "content" && uri.scheme != "file") return null
            val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            context.contentResolver.openInputStream(uri)?.use { stream ->
                BitmapFactory.decodeStream(stream, null, bounds)
            }
            if (bounds.outWidth <= 0 || bounds.outHeight <= 0) return null
            var sample = 1
            while (bounds.outWidth / sample > 900 || bounds.outHeight / sample > 900) {
                sample *= 2
            }
            val options = BitmapFactory.Options().apply {
                inSampleSize = sample
                inPreferredConfig = Bitmap.Config.RGB_565
            }
            context.contentResolver.openInputStream(uri)?.use { stream ->
                BitmapFactory.decodeStream(stream, null, options)
            }
        }.getOrNull()
    }

    override fun onReceive''', "photo decode helper")
receiver.write_text(s, encoding="utf-8")
print("SaúdePrática 1.9.4: all-profile notifications with patient name first and optional box photo.")
