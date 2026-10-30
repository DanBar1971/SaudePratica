#!/usr/bin/env python3
"""SaúdePrática v1.9.112: public GitHub health tips, optional popup and local history.
Applied AFTER v131. Keeps original app identity, images, alarms, PIN, data and signing.
"""
from pathlib import Path
from shutil import copyfile

root=Path("build-src/MediAgenda_Android_v1/app")
base=root/"src/main/java/com/mediagenda/app"
source=Path("MediAgenda/v132_overrides")

def once(path, old, new, label):
    text=path.read_text(encoding="utf-8")
    count=text.count(old)
    if count!=1:raise AssertionError(f"{label}: expected 1 occurrence, found {count}")
    path.write_text(text.replace(old,new,1),encoding="utf-8")

for name in ("HealthTipsManager.kt","HealthTipsActivity.kt"):
    copyfile(source/name,base/name)

# Both automatic and manually opened tips must appear in the history.
manager=base/"HealthTipsManager.kt"
once(manager,
'''        if(automatic) {
            val now=System.currentTimeMillis()
            prefs(activity).edit().putLong("seen_"+tip.id,now)
                .putLong("last_popup",now)
                .putString("saved_"+tip.id,tip.toJson().toString()).apply()
        }''',
'''        val now=System.currentTimeMillis()
        val editor=prefs(activity).edit()
            .putLong("seen_"+tip.id,now)
            .putString("saved_"+tip.id,tip.toJson().toString())
        if(automatic)editor.putLong("last_popup",now)
        editor.apply()''',"keep both popup and manually read cards in archive")

# Entry is strictly post-login, never from an Android lockscreen alarm.
main=base/"MainActivity.kt"
once(main,
'        SaudePraticaUpdateChecker.checkAfterLogin(this)',
'''        SaudePraticaUpdateChecker.checkAfterLogin(this)
        HealthTipsManager.maybeShow(this)''',"launch after PIN/login")

# Add the module into existing Opções/Informações area; keep support card intact.
once(main,
'        box.addView(infoCard("☕", "Apoiar o autor ☕",',
'''        box.addView(infoCard("💡", "Dicas e Informações",
            "Consultar dicas anteriores e configurar os avisos") {
            startActivity(Intent(this,HealthTipsActivity::class.java))
        })
        box.addView(infoCard("☕", "Apoiar o autor ☕",''',"options menu entry")

manifest=root/"src/main/AndroidManifest.xml"
once(manifest,"    </application>",
'''        <activity
            android:name="com.mediagenda.app.HealthTipsActivity"
            android:exported="false" />
    </application>''',"register non-exported history activity")

gradle=root/"build.gradle.kts"
once(gradle,"versionCode = 121","versionCode = 122","version code")
once(gradle,'versionName = "1.9.111"','versionName = "1.9.112"',"version name")

print("v1.9.112: GitHub catalog, vertical tip, safe link, history and frequency; existing identity retained")
