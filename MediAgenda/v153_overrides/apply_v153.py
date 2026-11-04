#!/usr/bin/env python3
"""v1.9.133: remove the optional generative Assistant, restore classic Help.

This is a narrowly scoped upgrade after v1.9.132. It removes the on-device
Qwen/Nano inference and online Assistant, BUT preserves independent Nutrition,
the Gemini key used by other modules, all existing patient data, Nearby sync,
Windows Wi-Fi discovery/consent, alarms, backups, and app identity.
"""
import re
import shutil
from pathlib import Path

app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
base=Path("MediAgenda/v153_overrides")
main=src/"MainActivity.kt"
m=main.read_text(encoding="utf-8")

# Remove the activity-result agent/draft mechanism. Native form editors remain.
start=m.index("    // An agent may only return a draft to the already unlocked MainActivity.")
end=m.index("    private val newProfileWizard=registerForActivityResult(",start)
assert 1000 < end-start < 5000
m=m[:start]+m[end:]

old='''            agentDraftLauncher.launch(Intent(this,AgentAssistantActivity::class.java)
                .putExtra(AgentAssistantActivity.EXTRA_PROFILE_ID,activeProfileId))'''
assert m.count(old)==1,("assistant launch",m.count(old))
m=m.replace(old,'''            startActivity(Intent(this,SmartHelpActivity::class.java))''',1)

old='''        box.addView(infoCard("✨", "Assistente IA SaúdePrática",
            "Consultas e medicação do perfil, fichas guiadas e IA local quando disponível") {'''
assert m.count(old)==1,("help navigation",m.count(old))
m=m.replace(old,'''        box.addView(infoCard("📚", "Ajuda tradicional",
            "Perguntas e respostas úteis sobre medicação, consultas, tomas e sincronização") {''',1)

old='''    private fun editAppointment(existing: Appointment?, fromOcr: Appointment? = null,
        fromAgent:Boolean=false) {'''
assert m.count(old)==1,("old native appointment editor",m.count(old))
m=m.replace(old,'''    private fun editAppointment(existing: Appointment?, fromOcr: Appointment? = null) {''',1)
old='''        if(fromAgent)box.addView(noteBox("Rascunho do assistente",
            "Revê a data, a hora, o local e os lembretes antes de guardar."))
        else if(fromOcr != null)box.addView(noteBox("Confirme os dados lidos",
            "A fotografia é apenas uma ajuda. Confirme data, hora e local antes de guardar."))'''
assert m.count(old)==1,("agent draft caption",m.count(old))
m=m.replace(old,'''        if (fromOcr != null) box.addView(noteBox("Confirme os dados lidos",
            "A fotografia é apenas uma ajuda. Confirme data, hora e local antes de guardar."))''',1)

# Remove the downloaded private model automatically on first launch after
# updating. Run off the UI thread and NEVER clear Android app data.
oncreate=re.search(r'override\s+fun\s+onCreate\s*\(\s*savedInstanceState\s*:\s*Bundle\?\s*\)\s*\{',m)
assert oncreate, "MainActivity.onCreate not found"
supercall=re.search(r'super\.onCreate\s*\(\s*savedInstanceState\s*\)\s*',m[oncreate.end():oncreate.end()+5000])
assert supercall, "MainActivity super.onCreate not found near onCreate"
offset=oncreate.end()+supercall.end()
m=m[:offset]+'''        LegacyAssistantCleanup.run(applicationContext)
'''+m[offset:]
assert "AgentAssistantActivity" not in m
assert "agentDraftLauncher" not in m
assert 'startActivity(Intent(this,WindowsLanPairActivity::class.java))' in m
assert 'startActivity(Intent(this,SmartHelpActivity::class.java))' in m
main.write_text(m,encoding="utf-8")

shutil.copyfile(base/"LegacyAssistantCleanup.java",src/"LegacyAssistantCleanup.java")

manifest=app/"src/main/AndroidManifest.xml"
xml=manifest.read_text(encoding="utf-8")
node='''        <activity android:name=".AgentAssistantActivity" android:exported="false" />
'''
assert xml.count(node)==1,("agent activity node",xml.count(node))
xml=xml.replace(node,"",1)
assert 'android:name=".WindowsLanPairActivity"' in xml
manifest.write_text(xml,encoding="utf-8")

# Drop all optional standalone assistant pieces; keep legacy SmartHelp and
# independent ML Kit OCR/Gemini nutrition integrations.
for filename in ("AgentAssistantActivity.kt","SmallOfflineModel.kt",
                 "SystemModelDownload.kt","OnlineAiClient.kt"):
    file=src/filename
    assert file.is_file(),filename
    file.unlink()
assert (src/"SmartHelpActivity.kt").is_file()
assert (src/"WindowsLanPairActivity.java").is_file()

gradle=app/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
model_runtime="// Independent small-model runtime, CPU only. GGUF weights are NEVER shipped."
assert g.count(model_runtime)==1,"Native llama Gradle block not found"
g=g[:g.index(model_runtime)].rstrip()+"\n"
nano_dep='''    implementation("com.google.mlkit:genai-prompt:1.0.0-beta4")\n'''
assert g.count(nano_dep)==1
g=g.replace(nano_dep,"",1)
g=g.replace('''    // Gemini Nano: entirely on-device when AICore and the model are available.
    // No API key or paid backend. Older phones retain native guided actions.
''',"")
assert g.count("versionCode = 142")==1 and g.count('versionName = "1.9.132"')==1
g=g.replace("versionCode = 142","versionCode = 143",1)
g=g.replace('versionName = "1.9.132"','versionName = "1.9.133"',1)
assert 'implementation("com.google.mlkit:text-recognition:16.0.1")' in g
gradle.write_text(g,encoding="utf-8")

native=app/"src/main/cpp"
if native.exists():
    known={"CMakeLists.txt","saude_llm.cpp"}
    assert set(p.name for p in native.iterdir()).issubset(known), \
        "Unexpected native sources; refuse to remove unrelated code"
    shutil.rmtree(native)

# Required for consistency across all supported languages. Keep the existing
# offline traditional FAQ; new shortcuts only point to it.
helpfile=src/"SmartHelpActivity.kt"
helptext=helpfile.read_text(encoding="utf-8")
assert "Ajuda tradicional" in helptext
assert "SmartHelpActivity" in helptext

print("PASS Android 1.9.133: restored offline Help; removed Gemini Nano, Qwen, IA Online assistant and native engine.")
print("Nearby, Windows discovery, backup, medication, Nutrition, alarms and original Android ID preserved.")
