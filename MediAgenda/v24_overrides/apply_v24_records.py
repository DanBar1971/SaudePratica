from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
app=root/"app/src/main/java/com/mediagenda/app"
main=app/"MainActivity.kt"
manifest=root/"app/src/main/AndroidManifest.xml"
gradle=root/"app/build.gradle.kts"

(app/"data/PersonalHealthStore.kt").write_text(
    Path("MediAgenda/v24_overrides/PersonalHealthStore.kt").read_text(encoding="utf-8"),encoding="utf-8")
(app/"HealthRecordsActivity.kt").write_text(
    Path("MediAgenda/v24_overrides/HealthRecordsActivity.kt").read_text(encoding="utf-8"),encoding="utf-8")

s=main.read_text(encoding="utf-8")
def edit(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.5 records missing "+label+": "+old[:130])
 s=s.replace(old,new,1)

edit('''import com.mediagenda.app.data.ProfileStore''',
'''import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.data.PersonalHealthStore''',"store import")

edit('''    private fun showMedication() {''',
'''    private fun healthRecords(kind: String) {
        startActivity(Intent(this, HealthRecordsActivity::class.java)
            .putExtra(HealthRecordsActivity.EXTRA_PROFILE_ID, activeProfileId)
            .putExtra(HealthRecordsActivity.EXTRA_CATEGORY, kind))
    }

    private fun showMedication() {''', "records launcher")

edit('''            DashboardModule("👓", "Óculos", "Graduação e receita") { openWellness("glasses") },
            DashboardModule("✚", "Farmácias", "Perto de mim e serviço") { showPharmacies() },''',
'''            DashboardModule("👓", "Óculos", "Graduação e receita") { openWellness("glasses") },
            DashboardModule("🩺", "Sintomas", "Diário e efeitos secundários") { healthRecords("symptoms") },
            DashboardModule("📊", "Medições", "Tensão, glicemia e mais") { healthRecords("measurements") },
            DashboardModule("💉", "Vacinas", "Histórico de vacinação") { healthRecords("vaccines") },
            DashboardModule("🆘", "Emergência", "Alergias e contactos") { healthRecords("emergency") },
            DashboardModule("✚", "Farmácias", "Perto de mim e serviço") { showPharmacies() },''',
"dashboard health tiles")

edit('''        box.addView(infoCard("ℹ️", "Acerca", "SaúdePrática — versão e autor") {
            showAboutSaudePratica()
        })
''','',"remove old About early")

edit('''        box.addView(infoCard("▦", "Exportar para Excel", "Gera CSV UTF-8 com separador ';' para abrir no Excel.") {
            showExportCsvDialog()
        })''',
'''        box.addView(infoCard("▦", "Exportar para Excel", "Gera CSV UTF-8 com separador ';' para abrir no Excel.") {
            showExportCsvDialog()
        })
        box.addView(infoCard("ℹ️", "Acerca", "SaúdePrática — versão, autor e contacto") {
            showAboutSaudePratica()
        })''', "About must be final, after Excel")

edit('''        box.addView(infoCard("🥗", "Alimentação e Regime", "Guardar as indicações de alimentação durante tratamentos") {
            openWellness("diet")
        })''',
'''        box.addView(infoCard("🥗", "Alimentação e Regime", "Guardar as indicações de alimentação durante tratamentos") {
            openWellness("diet")
        })
        box.addView(infoCard("🩺", "Diário de Sintomas", "Registar sintomas e possíveis efeitos secundários") {
            healthRecords("symptoms")
        })
        box.addView(infoCard("📊", "Medições de Saúde", "Tensão arterial, glicemia, peso, temperatura, saturação") {
            healthRecords("measurements")
        })
        box.addView(infoCard("💉", "Calendário de Vacinas", "Guardar as vacinas e próximas doses") {
            healthRecords("vaccines")
        })
        box.addView(infoCard("🆘", "Ficha de Emergência", "Contactos e alergias por utilizador") {
            healthRecords("emergency")
        })
        box.addView(infoCard("✅", "Tomas confirmadas", "Histórico das tomas registadas manualmente") {
            healthRecords("intakes")
        })''', "new More options")

main.write_text(s,encoding="utf-8")

m=manifest.read_text(encoding="utf-8")
anchor='''        <activity android:name=".WellnessActivity" android:exported="false" />'''
if anchor not in m:raise RuntimeError("Missing Wellness activity in manifest")
m=m.replace(anchor,anchor+'''
        <activity android:name=".HealthRecordsActivity" android:exported="false" />''',1)
manifest.write_text(m,encoding="utf-8")

g=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in g
assert 'versionCode = 14' in g and 'versionName = "1.9.4"' in g
g=g.replace('versionCode = 14','versionCode = 15',1)
g=g.replace('versionName = "1.9.4"','versionName = "1.9.5"',1)
gradle.write_text(g,encoding="utf-8")
print("v1.9.5: new medical record modules, About last, stable identity retained.")
