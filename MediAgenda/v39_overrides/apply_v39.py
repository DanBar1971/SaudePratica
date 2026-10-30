from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
java=root/"app/src/main/java/com/mediagenda/app"
for filename,target in (
    ("WorkplaceClassifier.kt",java/"work/WorkplaceClassifier.kt"),
    ("WorkMedicineStore.kt",java/"work/WorkMedicineStore.kt"),
    ("WorkMedicineActivity.kt",java/"WorkMedicineActivity.kt"),
):
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(Path("MediAgenda/v39_overrides",filename)
        .read_text(encoding="utf-8"),encoding="utf-8")

manifest=root/"app/src/main/AndroidManifest.xml"
s=manifest.read_text(encoding="utf-8")
anchor='''        <activity android:name=".ClinicalLabsActivity" android:exported="false" />'''
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'''
        <activity android:name=".WorkMedicineActivity" android:exported="false" />''',1)
manifest.write_text(s,encoding="utf-8")

paths=root/"app/src/main/res/xml/saudepratica_document_paths.xml"
s=paths.read_text(encoding="utf-8")
assert '</paths>' in s
s=s.replace('</paths>','''    <files-path name="work_medicine_archive"
        path="saudepratica_workplace/" />
    <cache-path name="work_medicine_camera"
        path="work_med_camera/" />
</paths>''',1)
paths.write_text(s,encoding="utf-8")

main=java/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
needle='''            DashboardModule("🧪", "Análises Clínicas", "Relatórios PDF, OCR e resultados") {
                startActivity(Intent(this,ClinicalLabsActivity::class.java)
                    .putExtra(ClinicalLabsActivity.EXTRA_PROFILE_ID,activeProfileId))
            },'''
assert s.count(needle)==1
s=s.replace(needle,needle+'''
            DashboardModule("🏥", "Medicina do Trabalho", "Aptidão, exames e histórico MCG") {
                startActivity(Intent(this,WorkMedicineActivity::class.java)
                    .putExtra(WorkMedicineActivity.EXTRA_PROFILE_ID,activeProfileId))
            },''',1)
main.write_text(s,encoding="utf-8")

gradle=root/"app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in s
assert 'versionCode = 29' in s and 'versionName = "1.9.19"' in s
gradle.write_text(s.replace('versionCode = 29','versionCode = 30',1)
    .replace('versionName = "1.9.19"','versionName = "1.9.20"',1),encoding="utf-8")

print("v1.9.20 Medicina do Trabalho: card on home, private archive, MCG ZIP import, categories and OCR, future Agenda reminders. App identity unchanged.")
