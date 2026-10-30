from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
source=Path('MediAgenda/v51_overrides')
folder=base/'sync'
folder.mkdir(parents=True,exist_ok=True)
for name in ('NearbySyncStore.kt','NearbySyncActivity.kt'):
    (folder/name).write_text((source/name).read_text(encoding='utf-8'),encoding='utf-8')

def patch(file,old,new,label):
    s=file.read_text(encoding='utf-8')
    if s.count(old)!=1:
        raise RuntimeError(f'Nearby v1.9.32 {label}: anchor count {s.count(old)}')
    file.write_text(s.replace(old,new,1),encoding='utf-8')

main=base/'MainActivity.kt'
patch(main,'        box.addView(infoCard("📦", "Backup completo da família",',
'''        box.addView(infoCard("🔄", "Sincronização familiar (Bluetooth / Wi-Fi)",
            "Trocar dados com outro telemóvel SaúdePrática, sem apagar registos") {
            startActivity(Intent(this,com.mediagenda.app.sync.NearbySyncActivity::class.java))
        })
        box.addView(infoCard("📦", "Backup completo da família",''',"menu Mais")

manifest=root/'app/src/main/AndroidManifest.xml'
patch(manifest,'    <uses-permission android:name="android.permission.CAMERA" />',
'''    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.CHANGE_WIFI_STATE" />
    <uses-permission android:name="android.permission.BLUETOOTH" android:maxSdkVersion="30" />
    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" android:maxSdkVersion="30" />
    <uses-permission android:name="android.permission.BLUETOOTH_ADVERTISE" />
    <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
    <uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
    <uses-permission android:name="android.permission.NEARBY_WIFI_DEVICES"
        android:usesPermissionFlags="neverForLocation" />''',"permissions")
patch(manifest,'        <activity android:name=".MainActivity" android:exported="false" />',
'''        <activity android:name=".MainActivity" android:exported="false" />
        <activity android:name=".sync.NearbySyncActivity" android:exported="false" />''',"activity")

gradle=root/'app/build.gradle.kts'
patch(gradle,'    implementation("com.google.android.gms:play-services-location:21.3.0")',
'''    implementation("com.google.android.gms:play-services-location:21.3.0")
    implementation("com.google.android.gms:play-services-nearby:19.3.0")''',"Nearby dependency")
patch(gradle,'versionCode = 41','versionCode = 42',"code")
patch(gradle,'versionName = "1.9.31"','versionName = "1.9.32"',"name")
print('v1.9.32: Nearby Connections bilateral sync, per-person additive merge with safe conflicts')