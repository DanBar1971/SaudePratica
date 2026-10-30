"""SaúdePrática 1.9.66: persistent real medication alarms with full-screen display."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
main=root/"app/src/main"
base=main/"java/com/mediagenda/app"
def change(file,old,new,label):
    s=file.read_text(encoding="utf-8")
    count=s.count(old)
    if count!=1: raise RuntimeError(f"v84 {label}: expected one anchor, got {count}")
    file.write_text(s.replace(old,new,1),encoding="utf-8")

alarm=Path("MediAgenda/v84_overrides/MedicationAlarmService.kt")
(base/"notifications/MedicationAlarmService.kt").write_text(alarm.read_text(encoding="utf-8"),encoding="utf-8")

manifest=main/"AndroidManifest.xml"
change(manifest,'    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />',
'''    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="android.permission.USE_FULL_SCREEN_INTENT" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PLAYBACK" />
    <uses-permission android:name="android.permission.VIBRATE" />
''',"alarm permissions")
change(manifest,'        <receiver android:name=".notifications.NotificationReceiver" android:exported="false" />',
'''        <activity android:name=".notifications.MedicationAlarmActivity"
            android:exported="false" android:showWhenLocked="true"
            android:turnScreenOn="true" android:excludeFromRecents="true"
            android:launchMode="singleTop" />
        <service android:name=".notifications.MedicationAlarmService"
            android:exported="false" android:foregroundServiceType="mediaPlayback" />
        <receiver android:name=".notifications.MedicationAlarmActionReceiver"
            android:exported="false" />
        <receiver android:name=".notifications.NotificationReceiver" android:exported="false" />''',
    "alarm manifest components")
receiver=base/"notifications/NotificationReceiver.kt"
change(receiver,'            manager.notify(id, builder.build())',
'''            manager.notify(id, builder.build())
            // Foreground service keeps the alarm ringing until TOMEI or ADIAR.
            // Notification above remains a safe fallback if Android blocks the service.
            if(!medicationId.isNullOrBlank() && scheduledAt>0L &&
                ProfileStore(context).all().any{it.id==profileId}){
                runCatching{MedicationAlarmService.start(context,intent)}
                    .onFailure{android.util.Log.e("SaudePraticaAlarm",
                        "Alarm service start blocked",it)}
            }''',"start real alarm")
taken=base/"notifications/IntakeActionReceiver.kt"
change(taken,'        IntakeBadgeManager.refresh(context,profileId)',
'''        MedicationAlarmService.stop(context,notificationId)
        IntakeBadgeManager.refresh(context,profileId)''',"silence only after successful intake record")

gradle=root/"app/build.gradle.kts"
change(gradle,"versionCode = 75","versionCode = 76","version code")
change(gradle,'versionName = "1.9.65"','versionName = "1.9.66"',"version name")
print("v1.9.66: persistent lockscreen alarm, repeated sound/vibration, box photo, snooze 10m and TOMEI")
