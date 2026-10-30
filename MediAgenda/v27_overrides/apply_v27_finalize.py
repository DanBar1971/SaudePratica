from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
app=root/"app/src/main"
wellness=app/"java/com/mediagenda/app/WellnessActivity.kt"
s=wellness.read_text(encoding="utf-8")
for old,new in [
    ('"👓 Graduação dos óculos"','"👓 Saúde Visual"'),
    ('"🥗 Plano alimentar / regime"','"🥗 Nutrição e Regime"'),
    ('heading("👓", "Graduação dos óculos", "Receita óptica guardada localmente")',
     'heading("👓", "Saúde Visual", "Receita óptica guardada localmente")'),
    ('heading("🥗", "Alimentação e regime", "Indicações de um profissional de saúde")',
     'heading("🥗", "Nutrição e Regime", "Indicações de um profissional de saúde")')
]:
    if old not in s:raise RuntimeError("Wellness heading not found: "+old)
    s=s.replace(old,new,1)
wellness.write_text(s,encoding="utf-8")

manifest=app/"AndroidManifest.xml"
m=manifest.read_text(encoding="utf-8")
needle='''        <activity android:name=".MonthlyCalendarActivity" android:exported="false" />'''
assert needle in m
m=m.replace(needle,needle+'''
        <activity android:name=".ProfileMediaActivity" android:exported="false" />''',1)

# Identity-card photos are intentionally excluded from automatic Android
# backup and device-to-device transfer; they are not part of exported JSON.
assert 'android:allowBackup="true"' in m
m=m.replace('android:allowBackup="true"',
    'android:allowBackup="true" android:fullBackupContent="@xml/saude_backup_rules" android:dataExtractionRules="@xml/saude_data_extraction_rules"',1)
manifest.write_text(m,encoding="utf-8")

xml=app/"res/xml"
xml.mkdir(parents=True,exist_ok=True)
(xml/"saude_backup_rules.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<full-backup-content>
    <exclude domain="file" path="saudepratica_identity/" />
</full-backup-content>
''',encoding="utf-8")
(xml/"saude_data_extraction_rules.xml").write_text('''<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules>
    <cloud-backup>
        <exclude domain="file" path="saudepratica_identity/" />
    </cloud-backup>
    <device-transfer>
        <exclude domain="file" path="saudepratica_identity/" />
    </device-transfer>
</data-extraction-rules>
''',encoding="utf-8")

gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in g, "Do not change app id"
assert 'versionCode = 17' in g and 'versionName = "1.9.7"' in g
gradle.write_text(g.replace('versionCode = 17','versionCode = 18',1)
    .replace('versionName = "1.9.7"','versionName = "1.9.8"',1),encoding="utf-8")
print("SaúdePrática v1.9.8: consistent new module names, declared private photo screen, no CC cloud backup.")
