from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
java=root/"app/src/main/java/com/mediagenda/app"
for name,target in (
    ("ClinicalLabParser.kt",java/"labs/ClinicalLabParser.kt"),
    ("ClinicalLabStore.kt",java/"labs/ClinicalLabStore.kt"),
    ("ClinicalLabsActivity.kt",java/"ClinicalLabsActivity.kt"),
):
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(Path("MediAgenda/v38_overrides",name).read_text(encoding="utf-8"),
                      encoding="utf-8")

manifest=root/"app/src/main/AndroidManifest.xml"
s=manifest.read_text(encoding="utf-8")
needle='''        <activity android:name=".HealthRecordsActivity" android:exported="false" />'''
assert s.count(needle)==1,"missing profile report activity anchor"
s=s.replace(needle,needle+'''
        <activity android:name=".ClinicalLabsActivity" android:exported="false" />''',1)
manifest.write_text(s,encoding="utf-8")

# Original PDF is saved in the private folder and can be securely opened
# by another app through an explicit read-granted FileProvider URI.
res=root/"app/src/main/res/xml/saudepratica_document_paths.xml"
xml=res.read_text(encoding="utf-8")
assert "</paths>" in xml,"missing document FileProvider XML"
if 'name="clinical_labs"' not in xml:
    xml=xml.replace("</paths>",'''    <files-path name="clinical_labs"
        path="saudepratica_labs/" />
    <cache-path name="clinical_lab_camera"
        path="clinical_lab_camera/" />
</paths>''')
res.write_text(xml,encoding="utf-8")

main=java/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
def change(old,new,label):
    global s
    if s.count(old)!=1:
        raise RuntimeError("v1.9.19 missing or ambiguous "+label+": "+str(s.count(old)))
    s=s.replace(old,new,1)

change('''            DashboardModule("📂", "Documentos", "PDFs e imagens") { showDocuments() },''',
'''            DashboardModule("📂", "Documentos", "PDFs e imagens") { showDocuments() },
            DashboardModule("🧪", "Análises Clínicas", "Relatórios PDF, OCR e resultados") {
                startActivity(Intent(this,ClinicalLabsActivity::class.java)
                    .putExtra(ClinicalLabsActivity.EXTRA_PROFILE_ID,activeProfileId))
            },''',"dashboard clinical lab module")

change('''        val address = input("Morada", extendedProfileDraft?.get("address")
            ?: prefs.getString("address", "").orEmpty())
        val healthUnit''',
'''        val address = input("Morada", extendedProfileDraft?.get("address")
            ?: prefs.getString("address", "").orEmpty())
        val postalCode = input("Código postal (0000-000)", extendedProfileDraft?.get("postal_code")
            ?: prefs.getString("postal_code", "").orEmpty())
        val healthUnit''',"profile postal field")

change('''            ccValidity, address, healthUnit).forEach { box.addView(it.container) }''',
'''            ccValidity, address, postalCode, healthUnit).forEach { box.addView(it.container) }''',"postal immediately after address")

change('''                "address" to address.edit.text.toString().trim(),
                "health_unit"''',
'''                "address" to address.edit.text.toString().trim(),
                "postal_code" to postalCode.edit.text.toString().trim(),
                "health_unit"''',"postal in unsaved draft for image navigation")

change('''            val socialSecurity = niss.edit.text.toString().filter(Char::isDigit)''',
'''            val post=postalCode.edit.text.toString().trim()
            if(post.isNotBlank()&&!post.matches(Regex("""\\d{4}-\\d{3}"""))){
                postalCode.edit.error="Usa o formato 0000-000."
                return@setOnClickListener
            }
            val socialSecurity = niss.edit.text.toString().filter(Char::isDigit)''',
"Portuguese postal validation")

change('''                .putString("address", address.edit.text.toString().trim())
                .putString("health_unit"''',
'''                .putString("address", address.edit.text.toString().trim())
                .putString("postal_code", post)
                .putString("health_unit"''',
"postal save")

needle='''        box.addView(secondaryButton("⚙ Definições de notificações do Android"){'''
change(needle,'''        box.addView(noteBox("📤 Comunicações WhatsApp e email",
            "A partilha de consultas é manual. A SaúdePrática prepara a mensagem; "+
            "o envio só acontece após confirmares na aplicação de mensagens. "+
            "O envio automático não está configurado."))
        box.addView(secondaryButton("📤 Preparar mensagem para WhatsApp ou email"){
            val appointments=repo.loadAppointments()
                .filter{!it.done}
                .sortedWith(compareBy({it.date},{it.time}))
            if(appointments.isEmpty()){
                showError("Não há marcações por concluir neste perfil.")
            }else{
                MaterialAlertDialogBuilder(this)
                    .setTitle("Escolher marcação para partilhar")
                    .setItems(appointments.map{
                        it.date+" "+it.time+" · "+it.activity.ifBlank{it.department}
                    }.toTypedArray()){_,position->
                        shareAppointment(appointments[position])
                    }.setNegativeButton("Cancelar",null).show()
            }
        })
        box.addView(secondaryButton("⚙ Definições de notificações do Android"){''',
"discoverable communications within notifications")

main.write_text(s,encoding="utf-8")

gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in g
assert 'versionCode = 28' in g and 'versionName = "1.9.18"' in g
gradle.write_text(g.replace('versionCode = 28','versionCode = 29',1)
             .replace('versionName = "1.9.18"','versionName = "1.9.19"',1),
             encoding="utf-8")
print("SaúdePrática v1.9.19: postal code, on-device multi-page clinical lab OCR, and discoverable manual WhatsApp/email messages.")
