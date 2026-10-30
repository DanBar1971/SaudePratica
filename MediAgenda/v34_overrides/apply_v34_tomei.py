from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1/app")
source=root/"src/main/java/com/mediagenda/app"
(source/"notifications/IntakeActionReceiver.kt").write_text(
    Path("MediAgenda/v34_overrides/IntakeActionReceiver.kt").read_text(encoding="utf-8"),
    encoding="utf-8")

manifest=root/"src/main/AndroidManifest.xml"
s=manifest.read_text(encoding="utf-8")
old='<receiver android:name=".notifications.NotificationReceiver" android:exported="false" />'
assert s.count(old)==1
s=s.replace(old,old+'''
        <receiver android:name=".notifications.IntakeActionReceiver"
            android:exported="false" />''',1)
manifest.write_text(s,encoding="utf-8")

scheduler=source/"notifications/NotificationScheduler.kt"
s=scheduler.read_text(encoding="utf-8")
needle='''            putExtra("reminder_kind", kind)'''
assert s.count(needle)==1
s=s.replace(needle,needle+'''
            putExtra("scheduled_at", millis)''',1)
scheduler.write_text(s,encoding="utf-8")

receiver=source/"notifications/NotificationReceiver.kt"
s=receiver.read_text(encoding="utf-8")
old='''            val isMedication=!medicationId.isNullOrBlank()'''
assert s.count(old)==1
s=s.replace(old,'''            val isMedication=!medicationId.isNullOrBlank() ||
                intent.getStringExtra("reminder_kind")=="medication"''',1)
old='''            // Box photos are optional. A deleted or inaccessible image never
            // prevents the reminder and always falls back to the normal alert.
            if (!medicationId.isNullOrBlank()) {'''
new='''            // "Tomei" exists only for a real scheduled medication alarm.
            // A test notification has no medication_id or scheduled_at and
            // must never create a false medication-intake record.
            val scheduledAt=intent.getLongExtra("scheduled_at",0L)
            if(!medicationId.isNullOrBlank() && scheduledAt>0L &&
                ProfileStore(context).all().any{it.id==profileId}){
                val action=Intent(context,IntakeActionReceiver::class.java).apply {
                    this.action=IntakeActionReceiver.ACTION
                    putExtra("profile_id",profileId)
                    putExtra("medication_id",medicationId)
                    putExtra("notification_id",id)
                    putExtra("scheduled_at",scheduledAt)
                }
                val uniqueRequest=(profileId+"|"+medicationId+"|"+scheduledAt).hashCode()
                val pending=PendingIntent.getBroadcast(context,uniqueRequest,action,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                builder.addAction(android.R.drawable.ic_input_add,"✓ Tomei",pending)
            }

            // Box photos are optional. A deleted or inaccessible image never
            // prevents the reminder and always falls back to the normal alert.
            if (!medicationId.isNullOrBlank()) {'''
assert s.count(old)==1
s=s.replace(old,new,1)
receiver.write_text(s,encoding="utf-8")
print("Live medication notifications have '✓ Tomei'; broadcasts save a real user-specific intake once and test alerts never count.")
