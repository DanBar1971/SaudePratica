from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
app=root/"app/src/main"
source=app/"java/com/mediagenda/app"
for original,destination in [
    ("AppPinStore.kt",source/"data/AppPinStore.kt"),
    ("AppPinActivity.kt",source/"AppPinActivity.kt"),
    ("SaudePraticaApplication.kt",source/"SaudePraticaApplication.kt"),
]:
    destination.write_text(
        Path("MediAgenda/v31_overrides",original).read_text(encoding="utf-8"),
        encoding="utf-8")

splash=source/"SplashActivity.kt"
s=splash.read_text(encoding="utf-8")
old='''import android.app.Activity'''
new='''import android.app.Activity
import com.mediagenda.app.data.AppPinStore'''
assert old in s, "Splash activity import missing"
s=s.replace(old,new,1)
old='''            startActivity(Intent(this, MainActivity::class.java))
            finish()'''
new='''            val pinEnabled=AppPinStore(this).enabled()
            val destination=if(pinEnabled)AppPinActivity::class.java else MainActivity::class.java
            startActivity(Intent(this,destination).apply {
                if(pinEnabled)putExtra(AppPinActivity.FROM_SPLASH,true)
            })
            finish()'''
assert old in s, "Splash launch missing"
s=s.replace(old,new,1)
splash.write_text(s,encoding="utf-8")

manifest=app/"AndroidManifest.xml"
s=manifest.read_text(encoding="utf-8")
old='<application android:allowBackup="true"'
assert s.count(old)==1, "Manifest application element missing"
s=s.replace(old,'<application android:name=".SaudePraticaApplication" android:allowBackup="true"',1)
old='<activity android:name=".MainActivity" android:exported="false" />'
assert s.count(old)==1, "Manifest MainActivity missing"
s=s.replace(old,old+'''
        <activity android:name=".AppPinActivity" android:exported="false" />''',1)
manifest.write_text(s,encoding="utf-8")

main=source/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
old='''import com.mediagenda.app.data.ProfileStore'''
assert old in s
s=s.replace(old,old+'''
import com.mediagenda.app.data.AppPinStore''',1)
old='''        box.addView(infoCard("◐", "Aspeto da aplicação", "Escolha entre automático, claro e escuro.") {
            showThemeDialog()
        })'''
new=old+'''
        box.addView(infoCard("🔒", "PIN de acesso",
            if(AppPinStore(this).enabled())"Ativado · PIN de 4 dígitos"
            else "Desativado · a aplicação abre sem pedir PIN") {
            startActivity(Intent(this,AppPinActivity::class.java)
                .putExtra(AppPinActivity.MODE,AppPinActivity.SETTINGS))
        })'''
assert s.count(old)==1, "Mais theme field missing"
s=s.replace(old,new,1)
main.write_text(s,encoding="utf-8")

gradle=root/"app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in s
assert 'versionCode = 21' in s and 'versionName = "1.9.11"' in s
s=s.replace('versionCode = 21','versionCode = 22',1)
s=s.replace('versionName = "1.9.11"','versionName = "1.9.12"',1)
gradle.write_text(s,encoding="utf-8")
print("v1.9.12 ready: optional app PIN (off by default), settings, app launch gate, field-reading improvements, same application id.")
