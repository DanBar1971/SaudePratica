#!/usr/bin/env python3
"""v1.9.124 ONLY adds diagnostic/settings access. NEVER alter working alarm paths."""
from pathlib import Path
from shutil import copyfile
from hashlib import sha256

app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
over=Path("MediAgenda/v144_overrides")
protected=[
  "notifications/MedicationAlarmService.kt",
  "notifications/NotificationScheduler.kt",
  "notifications/NotificationReceiver.kt",
  "notifications/MedicationAlarmCoordinator.kt",
  "notifications/MedicationAlarmPreferences.kt",
  "notifications/IntakeActionReceiver.kt",
  "notifications/DeviceAlarmRouting.kt",
]
baseline={p:sha256((src/p).read_bytes()).hexdigest() for p in protected if (src/p).exists()}
assert len(baseline)>=5,"Existing medication alarm source files missing"
copyfile(over/"AlarmPermissionsActivity.kt",src/"AlarmPermissionsActivity.kt")

main=src/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
anchor='        box.addView(infoCard("🔔", "Notificações",'
card='''        box.addView(infoCard("🛡️", "Permissões e alarmes do telemóvel",
            "Verificar ecrã bloqueado, notificações, bateria e Redmi/MIUI") {
            startActivity(Intent(this,AlarmPermissionsActivity::class.java))
        })
'''
assert s.count(anchor)==1,("Options > Security & notifications card",s.count(anchor))
s=s.replace(anchor,card+anchor,1)
main.write_text(s,encoding="utf-8")

manifest=app/"src/main/AndroidManifest.xml"
m=manifest.read_text(encoding="utf-8")
assert m.count("</application>")==1
m=m.replace("</application>",'''        <activity android:name=".AlarmPermissionsActivity"
            android:exported="false" />
    </application>''',1)
manifest.write_text(m,encoding="utf-8")

# Explain the Redmi permissions in the existing multilingual offline Help.
helpfile=src/"SupportHelpActivity.kt"
h=helpfile.read_text(encoding="utf-8")
help_anchor="        val linksGuide=panel()"
assert h.count(help_anchor)==1,"Help anchor changed"
help_card='''        val alarmPermissionsGuide=panel()
        alarmPermissionsGuide.addView(text(tr(
            "🛡️ Permissões do Android · alarme sem ecrã",
            "🛡️ Android permissions · audible alarm without screen",
            "🛡️ Autorisations Android · alarme sans écran",
            "🛡️ Android-Berechtigungen · Alarm ohne Anzeige",
            "🛡️ Permisos Android · suena sin pantalla"),18f))
        alarmPermissionsGuide.addView(text(tr(
            "Se o alarme toca mas não mostra a ficha, abre Opções → Segurança e notificações → Permissões e alarmes do telemóvel. Verifica notificações, ecrã completo, canal de alarmes e bateria. Em Redmi/MIUI, confirma Mostrar no ecrã bloqueado, pop-ups em segundo plano e Início automático. Regressa a Notificações para testar o alarme sem registar uma toma.",
            "If the alarm sounds but its screen is missing, go to Options → Security and notifications → Phone permissions and alarms. Check full screen, notifications, alarm channel and battery. On Redmi/MIUI check Show on lock screen, background pop-ups and Autostart. Test from Notifications; no dose is recorded.",
            "Si l'alarme sonne sans écran, ouvrez Options → Sécurité et notifications → Autorisations et alarmes. Vérifiez le plein écran, les notifications, la batterie et, sur Redmi, l'écran verrouillé, les fenêtres contextuelles et le démarrage automatique.",
            "Wenn der Alarm klingelt, aber kein Bildschirm erscheint: Optionen → Sicherheit/Benachrichtigungen → Telefonberechtigungen. Vollbild, Sperrbildschirm, Benachrichtigungen, Akku und Redmi-Autostart prüfen.",
            "Si suena la alarma sin abrir la pantalla: Opciones → Seguridad y notificaciones → Permisos y alarmas. Comprueba pantalla completa, notificaciones, batería y, en Redmi, pantalla bloqueada, ventanas emergentes e inicio automático."),13f))
        addCard(parent,alarmPermissionsGuide)
'''
h=h.replace(help_anchor,help_card+help_anchor,1)
helpfile.write_text(h,encoding="utf-8")

gradle=app/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 133")==1,"Unexpected Android version code"
assert g.count('versionName = "1.9.123"')==1,"Unexpected Android version name"
g=g.replace("versionCode = 133","versionCode = 134",1)
g=g.replace('versionName = "1.9.123"','versionName = "1.9.124"',1)
gradle.write_text(g,encoding="utf-8")

for path,digest in baseline.items():
    assert sha256((src/path).read_bytes()).hexdigest()==digest,(
        "ALARM REGRESSION: forbidden modification to "+path)
print("v1.9.124: permissions panel only; all %d alarm source fingerprints unchanged."%len(baseline))
