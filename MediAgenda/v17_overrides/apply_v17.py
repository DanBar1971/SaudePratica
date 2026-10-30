from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")
src = root / "app/src/main/java/com/mediagenda/app/MainActivity.kt"
s = src.read_text(encoding="utf-8")

def exact(old, new):
    global s
    if old not in s:
        raise RuntimeError("v1.7 UI patch target not found: " + repr(old[:160]))
    s = s.replace(old, new, 1)

# These two prominent cards previously occupied more than half of each screen.
# Move both actions into the existing '+ Add' selection, freeing the entire list.
start = s.index("        content.addView(summaryCard(\n            icon = \"📦\",", s.index("    private fun showMedication()"))
end = s.index('        content.addView(sectionRow("Medicamentos"', start)
s = s[:start] + s[end:]

start = s.index("        content.addView(summaryCard(\n            icon = \"📷\",", s.index("    private fun showAgenda()"))
end = s.index("        val items = repo.loadAppointments()", start)
s = s[:start] + s[end:]

exact('''        content.addView(sectionRow("Medicamentos", "${items.size} registados") {
            editMedication(null)
        })''',
'''        content.addView(sectionRow("Medicamentos", "${items.size} registados") {
            showMedicationAddOptions()
        })''')

exact('''        content.addView(sectionRow("Próximas marcações", "${items.size} no total") {
            editAppointment(null)
        })''',
'''        content.addView(sectionRow("Marcações", "${items.size} no total") {
            showAppointmentAddOptions()
        })''')

exact('''            text = "+ Manual"''', '''            text = "+ Adicionar"''')

needle = '''    private fun showPharmacies() {'''
extra = '''    private fun showMedicationAddOptions() {
        MaterialAlertDialogBuilder(this)
            .setTitle("Adicionar medicação")
            .setItems(arrayOf(
                "📦 Fotografar caixa de medicamento",
                "🔎 Ler guia de tratamento",
                "✍️ Introduzir manualmente"
            )) { _, choice ->
                when (choice) {
                    0 -> captureMedicationBoxPhoto()
                    1 -> startPrescriptionScan()
                    else -> editMedication(null)
                }
            }
            .setNegativeButton("Cancelar", null).show()
    }

    private fun showAppointmentAddOptions() {
        MaterialAlertDialogBuilder(this)
            .setTitle("Adicionar marcação")
            .setItems(arrayOf(
                "📷 Fotografar folha de marcações",
                "✍️ Introduzir manualmente"
            )) { _, choice ->
                when (choice) {
                    0 -> captureAppointmentPhoto()
                    else -> editAppointment(null)
                }
            }
            .setNegativeButton("Cancelar", null).show()
    }

'''
exact(needle, extra+needle)

# Keep empty lists compact, too: the +Adicionar menu is the single entry point.
exact('''"Fotografe uma caixa, leia uma guia ou adicione manualmente."''',
      '''"Toque em + Adicionar para fotografar uma caixa, ler uma guia ou inserir manualmente."''')
exact('''"Fotografe uma folha de marcações ou adicione uma consulta."''',
      '''"Toque em + Adicionar para fotografar uma folha ou inserir uma marcação."''')

exact(
    'import com.mediagenda.app.ocr.MultiAppointmentOcrParser\n',
    'import com.mediagenda.app.ocr.MultiAppointmentOcrParser\nimport com.mediagenda.app.ocr.IpoTableParser\n'
)

# For IPO, use 2D positions exclusively. The original text-order parser grouped
# columns as if they were sequential rows and mistakenly imported the print date.
needle = '''                val rows = MultiAppointmentOcrParser.parseMany(vision.text, locations)
                    .map { p -> Appointment('''
replacement = '''                val isIpo = vision.text.contains("PRÓXIMAS MARCAÇÕES", true) ||
                    vision.text.contains("PROXIMAS MARCACOES", true) ||
                    vision.text.contains("IPO LISBOA", true) ||
                    vision.text.contains("INSTITUTO PORTUGUÊS", true) ||
                    vision.text.contains("INSTITUTO PORTUGUES", true) ||
                    vision.text.contains("PAV RADIOTERAP", true)
                val recognized = if (isIpo)
                    IpoTableParser.parse(locations)
                else
                    MultiAppointmentOcrParser.parseMany(vision.text, locations)
                val rows = recognized.map { p -> Appointment('''
exact(needle,replacement)

# Avoid adding a single bad row automatically for a multi-entry IPO sheet.
exact('''                } else if (rows.size == 1) {
                    editAppointment(null, rows.first())
                } else {
                    confirmImportedAppointments(rows)
                }''',
'''                } else if (isIpo) {
                    confirmImportedAppointments(rows)
                } else if (rows.size == 1) {
                    editAppointment(null, rows.first())
                } else {
                    confirmImportedAppointments(rows)
                }''')

# Android MaterialAlertDialog shows either a message or its list, not both in
# a reliable small-screen layout. The message obscured the actual multi-choice
# entries. Show a proper scrollable list without the long paragraph.
old = '''            .setMessage("Confirme cada data, hora e descrição. Desmarque os resultados incorretos. As entradas já existentes não serão duplicadas. Pode editar cada ficha na Agenda depois de importar.")
            .setMultiChoiceItems(labels, selections)'''
new = '''            .setMultiChoiceItems(labels, selections)'''
exact(old,new)

# Do not preselect rows that have no clinical meaning.
exact('''            c.activity.isNotBlank() && appointmentMatchKey(c) !in already''',
      '''            c.activity.isNotBlank() && c.department.isNotBlank() &&
                appointmentMatchKey(c) !in already''')

src.write_text(s, encoding="utf-8")

# Increment version; retain stable package ID for lossless install on v1.6.
gradle = root / "app/build.gradle.kts"
s = gradle.read_text(encoding="utf-8")
if 'applicationId = "com.mediagenda.app.stable"' not in s:
    raise RuntimeError("Stable application identifier missing")
if 'versionCode = 7' not in s or 'versionName = "1.6.0"' not in s:
    raise RuntimeError("Unexpected base app version")
s = s.replace('versionCode = 7','versionCode = 8')
s = s.replace('versionName = "1.6.0"', 'versionName = "1.7.0"')
gradle.write_text(s, encoding="utf-8")
print("MediAgenda v1.7: compact add menus, IPO table coordinate parsing, visible review list.")
