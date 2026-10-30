from pathlib import Path
file = Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt")
text = file.read_text(encoding="utf-8")
start = text.index("    private fun showDataTools() {")
end = text.index("    private fun screenHeader(", start)
section = text[start:end]
first = '        box.addView(infoCard("📂", "Documentos Digitais",'
last = '        box.addView(infoCard("🏥", "Abrir SNS 24",'
assert section.count(first) == 1 and section.count(last) == 1, "Unexpected Mais structure"
section = section[:section.index(first)] + section[section.index(last):]
assert section.index('"Acerca"') > section.index('"Exportar para Excel"')
text = text[:start] + section + text[end:]
anchor = '            DashboardModule("💊", "Medicação", "Tomas e avisos") { showMedication() },'
assert text.count(anchor) == 1
text = text.replace(anchor, anchor + '\n            DashboardModule("✅", "Tomas", "Histórico confirmado") { healthRecords("intakes") },', 1)
file.write_text(text, encoding="utf-8")
print("No duplicate modules in Mais, intake history available on dashboard, About stays last.")
