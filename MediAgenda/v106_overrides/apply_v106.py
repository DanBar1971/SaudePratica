"""SaúdePrática v1.9.87: update-install regression fix for Android / HyperOS.

The v1.9.85+ installer safely verifies the public release SHA-256 and signing
certificate but sends a private cache content:// URI to an ACTION_VIEW handler.
Some Android/HyperOS package parsers reject this with "problem parsing package".
Stream the already verified APK to Android PackageInstaller.Session instead,
always requiring user approval. Do not touch medicine, alarms, media or profiles.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
src=Path("MediAgenda/v106_overrides")

def edit(file,old,new,label):
    s=file.read_text(encoding="utf-8")
    found=s.count(old)
    if found!=1:raise RuntimeError(f"v106 {label}: expected one anchor, got {found}")
    file.write_text(s.replace(old,new,1),encoding="utf-8")

(base/"SessionApkUpdater.kt").write_text(
    (src/"SessionApkUpdater.kt").read_text(encoding="utf-8"),encoding="utf-8")

installer=base/"InAppUpdateInstaller.kt"
edit(installer,
'''        val uri=FileProvider.getUriForFile(activity,
            activity.packageName+".fileprovider",apk)
        runCatching{
            activity.startActivity(Intent(Intent.ACTION_VIEW).apply{
                setDataAndType(uri,"application/vnd.android.package-archive")
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            })
        }.onFailure{message(activity,
            "Não foi possível abrir o instalador do Android: "+it.message)}''',
'''        // The validated APK is streamed as bytes to PackageInstaller.
        // Never delegate a private FileProvider URI to manufacturer parsers.
        SessionApkUpdater.install(activity,apk)''',
"replace FileProvider ACTION_VIEW with PackageInstaller session")

manifest=root/"app/src/main/AndroidManifest.xml"
edit(manifest,
'''        <activity android:name=".HealthRecordsActivity" android:exported="false" />''',
'''        <activity android:name=".UpdateInstallStatusActivity"
            android:exported="false" android:excludeFromRecents="true"
            android:theme="@style/Theme.MediAgenda" />
        <activity android:name=".HealthRecordsActivity" android:exported="false" />''',
"register Android user-confirmation status screen")

gradle=root/"app/build.gradle.kts"
edit(gradle,"versionCode = 96","versionCode = 97","versionCode")
edit(gradle,'versionName = "1.9.86"','versionName = "1.9.87"',"versionName")

print("v1.9.87: verified GitHub APK installs via PackageInstaller.Session + Android user approval")
