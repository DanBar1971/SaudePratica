from pathlib import Path
base=Path("build-src/MediAgenda_Android_v1")
root=base/"app/src/main/java/com/mediagenda/app"
(root/"data/CycleStore.kt").write_text(
    Path("MediAgenda/v26_overrides/CycleStore.kt").read_text(encoding="utf-8"),encoding="utf-8")
(root/"MonthlyCalendarActivity.kt").write_text(
    Path("MediAgenda/v26_overrides/MonthlyCalendarActivity.kt").read_text(encoding="utf-8"),encoding="utf-8")

main=root/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
def edit(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.7 calendar integration missing "+label)
 s=s.replace(old,new,1)
edit('''    private fun showHome() {''','''    private fun openCalendar(cycleMode:Boolean=false) {
        startActivity(Intent(this,MonthlyCalendarActivity::class.java)
            .putExtra(MonthlyCalendarActivity.PROFILE,activeProfileId)
            .putExtra(MonthlyCalendarActivity.MODE,if(cycleMode)"cycle" else "agenda"))
    }

    private fun showHome() {''',"calendar launcher")
edit('''            DashboardModule("📅", "Agenda", "Consultas e exames") { showAgenda() },''',
'''            DashboardModule("📅", "Agenda", "Consultas e exames") { showAgenda() },
            DashboardModule("🗓️", "Calendário", "Vista mensal e marcações") { openCalendar() },''',"month on home")
edit('''            DashboardModule("💧", "Beber água", "Hidratação") { openWellness("water") },''',
'''            DashboardModule("💧", "Beber água", "Hidratação") { openWellness("water") },
            DashboardModule("🌸", "Ciclo Menstrual", "Período e pílula") { openCalendar(true) },''',"menstrual tile")

main.write_text(s,encoding="utf-8")
manifest=base/"app/src/main/AndroidManifest.xml";text=manifest.read_text(encoding="utf-8")
needle='''        <activity android:name=".HealthRecordsActivity" android:exported="false" />'''
assert needle in text
text=text.replace(needle,needle+'''
        <activity android:name=".MonthlyCalendarActivity" android:exported="false" />''',1)
manifest.write_text(text,encoding="utf-8")
gradle=base/"app/build.gradle.kts";text=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in text
assert 'versionCode = 16' in text and 'versionName = "1.9.6"' in text
text=text.replace('versionCode = 16','versionCode = 17',1)
text=text.replace('versionName = "1.9.6"','versionName = "1.9.7"',1)
gradle.write_text(text,encoding="utf-8")
print("SaúdePrática v1.9.7 includes monthly appointment calendar, menstrual and pill calendar; Mais has no duplicated modules.")
