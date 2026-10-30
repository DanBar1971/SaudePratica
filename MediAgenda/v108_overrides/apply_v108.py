"""SaúdePrática 1.9.89: keep APK download in Downloads using Android DownloadManager.

Fix v1.9.87/88: the previous updater silently read a 153 MB APK in an
Activity-owned thread and wrote a private .part file, so it could lose the
result when the Activity changed; progress was not observable. The Android
system now owns and resumes the download, always stores a visible APK, and
verifies the hash/signature before user-confirmed installation.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
src=Path("MediAgenda/v108_overrides")
(base/"InAppUpdateInstaller.kt").write_text(
    (src/"InAppUpdateInstaller.kt").read_text(encoding="utf-8"),encoding="utf-8")

manifest=root/"app/src/main/AndroidManifest.xml"
s=manifest.read_text(encoding="utf-8")
anchor='''        <activity android:name=".UpdateInstallStatusActivity"'''
assert s.count(anchor)==1, "Installer status activity missing"
s=s.replace(anchor,'''        <activity android:name=".UpdateDownloadedActivity"
            android:exported="false" android:excludeFromRecents="true"
            android:theme="@style/Theme.MediAgenda" />
        <receiver android:name=".UpdateDownloadReceiver"
            android:exported="false">
            <intent-filter>
                <action android:name="android.intent.action.DOWNLOAD_COMPLETE"/>
            </intent-filter>
        </receiver>
'''+anchor,1)
manifest.write_text(s,encoding="utf-8")

gradle=root/"app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert s.count("versionCode = 98")==1 and s.count('versionName = "1.9.88"')==1
gradle.write_text(s.replace("versionCode = 98","versionCode = 99",1)
    .replace('versionName = "1.9.88"','versionName = "1.9.89"',1),encoding="utf-8")
print("v1.9.89: persistent DownloadManager, visible Downloads APK, SHA256 and Android signer checks")
