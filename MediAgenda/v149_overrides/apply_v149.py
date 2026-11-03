#!/usr/bin/env python3
"""Android 1.9.129: profile-scoped assistant and optional true on-device Gemini Nano.

Runs after v147; no medication/appointment records are written by AI.
The native MainActivity editors remain the only place to confirm and save.
"""
from pathlib import Path
from shutil import copyfile

app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
patch=Path("MediAgenda/v149_overrides")

def replace(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    count=s.count(old)
    if count!=1:
        raise AssertionError(f"{label}: expected exactly one anchor; found {count}")
    path.write_text(s.replace(old,new,1),encoding="utf-8")

copyfile(patch/"AgentAssistantActivity.kt",src/"AgentAssistantActivity.kt")

main=src/"MainActivity.kt"
anchor="    private val newProfileWizard=registerForActivityResult("
insert="""    // An agent may only return a draft to the already unlocked MainActivity.
    // No model has direct access to saveMedications/saveAppointments.
    private val agentDraftLauncher=registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()){result->
        val data=result.data
        if(result.resultCode==Activity.RESULT_OK && data!=null){
            val profileId=data.getStringExtra(AgentAssistantActivity.EXTRA_PROFILE_ID).orEmpty()
            // Ignore a stale result if the caregiver has switched patient.
            if(profileId.isBlank() || profileId!=activeProfileId ||
               profiles.all().none{it.id==profileId}){
                showError("O perfil mudou. A ficha não foi aberta.")
            }else when(data.getStringExtra(AgentAssistantActivity.EXTRA_ACTION)){
                AgentAssistantActivity.ACTION_MEDICATION -> {
                    val name=data.getStringExtra(AgentAssistantActivity.EXTRA_NAME)
                        .orEmpty().take(100)
                    val dose=data.getStringExtra(AgentAssistantActivity.EXTRA_DOSE)
                        .orEmpty().take(50)
                    // No persistence until user presses Guardar on the real form.
                    editMedication(null,Medication(medication=name,dose=dose))
                }
                AgentAssistantActivity.ACTION_APPOINTMENT -> {
                    val date=data.getStringExtra(AgentAssistantActivity.EXTRA_DATE)
                        .orEmpty().take(10)
                    val time=data.getStringExtra(AgentAssistantActivity.EXTRA_TIME)
                        .orEmpty().take(5)
                    val activity=data.getStringExtra(AgentAssistantActivity.EXTRA_ACTIVITY)
                        .orEmpty().take(150)
                    editAppointment(null,Appointment(date=date,time=time,activity=activity),true)
                }
                else -> showError("Pedido de assistente desconhecido. Nenhum dado alterado.")
            }
        }
    }
"""
replace(main,anchor,insert+anchor,"native pending draft activity result")
replace(main,'''            startActivity(Intent(this,SmartHelpActivity::class.java))''',
'''            agentDraftLauncher.launch(Intent(this,AgentAssistantActivity::class.java)
                .putExtra(AgentAssistantActivity.EXTRA_PROFILE_ID,activeProfileId))''',
"replace help launch with internal profile-scoped agent")
replace(main,
'''        box.addView(infoCard("✨", "Assistente de ajuda offline",
            "Faz perguntas sobre medicamentos, tomas, consultas e sincronização") {''',
'''        box.addView(infoCard("✨", "Assistente IA SaúdePrática",
            "Consultas e medicação do perfil, fichas guiadas e IA local quando disponível") {''',
"replace assistant entry")
# Differentiate an agent draft from a photo OCR result in the native form.
replace(main,
'''    private fun editAppointment(existing: Appointment?, fromOcr: Appointment? = null) {''',
'''    private fun editAppointment(existing: Appointment?, fromOcr: Appointment? = null,
        fromAgent:Boolean=false) {''',
"editor option")
replace(main,
'''        if (fromOcr != null) box.addView(noteBox("Confirme os dados lidos", "A fotografia é apenas uma ajuda. Confirme data, hora e local antes de guardar."))''',
'''        if(fromAgent)box.addView(noteBox("Rascunho do assistente",
            "Revê a data, a hora, o local e os lembretes antes de guardar."))
        else if(fromOcr != null)box.addView(noteBox("Confirme os dados lidos",
            "A fotografia é apenas uma ajuda. Confirme data, hora e local antes de guardar."))''',
"native editor draft warning")

manifest=app/"src/main/AndroidManifest.xml"
replace(manifest,"    </application>",
'''        <activity android:name=".AgentAssistantActivity" android:exported="false" />
    </application>''',"manifest non-exported agent")
gradle=app/"build.gradle.kts"
replace(gradle,
'''    implementation("com.google.mlkit:text-recognition:16.0.1")''',
'''    // Gemini Nano: entirely on-device when AICore and the model are available.
    // No API key or paid backend. Older phones retain native guided actions.
    implementation("com.google.mlkit:genai-prompt:1.0.0-beta4")
    implementation("com.google.mlkit:text-recognition:16.0.1")''',
"optional Nano inference")
# Current ML Kit GenAI metadata requires Kotlin 2.3.x, while the older
# SaúdePrática build root still pins Kotlin 2.0.21.
buildRoot=app.parent/"build.gradle.kts"
replace(buildRoot,'version "2.0.21"','version "2.3.21"',"GenAI Kotlin metadata compatibility")
replace(gradle,'versionCode = 137','versionCode = 139',"versionCode")
replace(gradle,'versionName = "1.9.127"','versionName = "1.9.129"',"versionName")
print("Android v1.9.129: assistant with Nano optional, native profile-scoped read tools, drafts only.")
