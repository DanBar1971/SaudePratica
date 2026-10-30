from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")
src = root/"app/src/main/java/com/mediagenda/app"
main = src/"MainActivity.kt"
manifest = root/"app/src/main/AndroidManifest.xml"
gradle = root/"app/build.gradle.kts"

(src/"DocumentsActivity.kt").write_text(
    Path("MediAgenda/v22_overrides/DocumentsActivity.kt").read_text(encoding="utf-8"),
    encoding="utf-8")
(src/"data/HealthDocumentStore.kt").write_text(
    Path("MediAgenda/v22_overrides/HealthDocumentStore.kt").read_text(encoding="utf-8"),
    encoding="utf-8")

def sub(s, old, new, label):
    if old not in s:
        raise RuntimeError("SaúdePrática 1.9.3 missing "+label+": "+old[:120])
    return s.replace(old, new, 1)

s = main.read_text(encoding="utf-8")
s = sub(s, "import java.time.LocalDate",
'''import java.time.LocalTime
import java.time.LocalDateTime
import java.time.LocalDate''', "date/time imports")

s = sub(s, '''        val items = repo.loadMedications()

        content.addView(sectionRow''',
'''        val allItems = repo.loadMedications()
        val sorting = getSharedPreferences("saudepratica_med_sort", MODE_PRIVATE)
            .getString(activeProfileId, "name")
        val items = if (sorting == "date") allItems.sortedWith(
            compareBy<Medication> { nextMedicationTime(it) ?: LocalDateTime.MAX }
                .thenBy { it.medication.lowercase(Locale("pt", "PT")) }
        ) else allItems.sortedBy { it.medication.lowercase(Locale("pt", "PT")) }

        content.addView(sectionRow''', "medication sort")

s = sub(s, '''        if (items.isEmpty()) {
            content.addView(emptyState("Ainda não há medicação"''',
'''        val sortRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(dp(3), 0, 0, dp(7))
        }
        sortRow.addView(TextView(this).apply {
            text = "Ordenar: "
            textSize = 12f
            setTextColor(muted)
        })
        sortRow.addView(secondaryButton(if (sorting == "date") "📅 Data / hora ▾" else "A–Z Nome ▾") {
            MaterialAlertDialogBuilder(this)
                .setTitle("Ordenar medicamentos")
                .setSingleChoiceItems(arrayOf("Nome (A–Z)", "Próxima data e hora"),
                    if (sorting == "date") 1 else 0) { dialog, selected ->
                    getSharedPreferences("saudepratica_med_sort", MODE_PRIVATE)
                        .edit().putString(activeProfileId, if (selected == 0) "name" else "date").apply()
                    dialog.dismiss()
                    showMedication()
                }.setNegativeButton("Cancelar", null).show()
        })
        content.addView(sortRow)

        if (items.isEmpty()) {
            content.addView(emptyState("Ainda não há medicação"''', "sort UI")

s = sub(s, '''    private fun showAgenda() {''',
'''    private fun nextMedicationTime(med: Medication): LocalDateTime? {
        val time = runCatching {
            LocalTime.parse(med.reminderTime.ifBlank { med.time })
        }.getOrNull() ?: return null
        val today = LocalDateTime.now()
        val start = runCatching { LocalDate.parse(med.repeatStart) }.getOrNull()
        val until = runCatching { LocalDate.parse(med.repeatUntil) }.getOrNull()
        val specialDays = med.schedule.flatMap { (month, days) ->
            days.mapNotNull { d ->
                runCatching { LocalDate.parse("$month-"+d.toString().padStart(2,'0')) }.getOrNull()
            }
        }.toSet()
        val mode = med.repeatMode.ifBlank { if (specialDays.isEmpty()) "daily" else "dates" }
        return (0..366).asSequence()
            .map { today.toLocalDate().plusDays(it.toLong()) }
            .filter { start == null || !it.isBefore(start) }
            .filter { until == null || !it.isAfter(until) }
            .filter { date ->
                when (mode) {
                    "daily" -> true
                    "weekly" -> med.repeatWeekdays.contains(date.dayOfWeek.value - 1)
                    "range" -> start != null && until != null
                    else -> specialDays.contains(date)
                }
            }
            .map { LocalDateTime.of(it, time) }
            .firstOrNull { it.isAfter(today) }
    }

    private fun showAgenda() {''', "next medication datetime")

s = sub(s, '''    private fun showPharmacies() {''',
'''    private fun showDocuments() {
        startActivity(Intent(this, DocumentsActivity::class.java)
            .putExtra(DocumentsActivity.EXTRA_PROFILE_ID, activeProfileId))
    }

    private fun showPharmacies() {''', "documents launch")

s = sub(s, '''        box.addView(infoCard("ℹ️", "Acerca",''',
'''        box.addView(infoCard("📂", "Documentos Digitais",
            "Atestados, vacinas, justificações, PDFs e imagens guardados por utilizador") {
            showDocuments()
        })
        box.addView(infoCard("ℹ️", "Acerca",''', "documents in Mais")

s = sub(s, '''            Triple("📅", "Agenda") { showAgenda() },
            Triple("✚", "Farmácias") { showPharmacies() },''',
'''            Triple("📅", "Agenda") { showAgenda() },
            Triple("📂", "Docs") { showDocuments() },
            Triple("✚", "Farmácias") { showPharmacies() },''', "bottom tab Docs")

s = sub(s, '''        renderBottomNav(2)
    }

    private fun activateProfile(''',
'''        renderBottomNav(3)
    }

    private fun activateProfile(''', "pharmacy tab")
s = sub(s, '''        renderBottomNav(3)
    }

    private fun screenHeader(''',
'''        renderBottomNav(4)
    }

    private fun screenHeader(''', "More tab")
main.write_text(s, encoding="utf-8")

m = manifest.read_text(encoding="utf-8")
m = sub(m, '        <receiver android:name=".notifications.NotificationReceiver"',
'''        <activity android:name=".DocumentsActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.SEND" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:mimeType="application/pdf" />
                <data android:mimeType="image/*" />
            </intent-filter>
        </activity>
        <provider android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.documents"
            android:exported="false" android:grantUriPermissions="true">
            <meta-data android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/saudepratica_document_paths" />
        </provider>
        <receiver android:name=".notifications.NotificationReceiver"''', "share target provider")
manifest.write_text(m, encoding="utf-8")

path = root/"app/src/main/res/xml/saudepratica_document_paths.xml"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text('''<?xml version="1.0" encoding="utf-8"?>
<paths xmlns:android="http://schemas.android.com/apk/res/android">
    <files-path name="stored_documents" path="saudepratica_documents/" />
    <cache-path name="scanned_documents" path="saudepratica_document_scans/" />
</paths>
''', encoding="utf-8")

g = gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in g
assert 'versionCode = 12' in g and 'versionName = "1.9.2"' in g
g = g.replace('versionCode = 12', 'versionCode = 13', 1)
g = g.replace('versionName = "1.9.2"', 'versionName = "1.9.3"', 1)
gradle.write_text(g, encoding="utf-8")
print("SaúdePrática v1.9.3: documents storage and UI, medication sort.")
