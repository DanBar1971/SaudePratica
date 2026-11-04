#!/usr/bin/env python3
"""No release if opt-in, native engine, checksum or patient-safety gates regress."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

app = Path("build-src/MediAgenda_Android_v1/app")
src = app / "src/main/java/com/mediagenda/app"
gradle = (app / "build.gradle.kts").read_text(encoding="utf-8")
manifest = (app / "src/main/AndroidManifest.xml").read_text(encoding="utf-8")
agent = (src / "AgentAssistantActivity.kt").read_text(encoding="utf-8")
runtime = (src / "SmallOfflineModel.kt").read_text(encoding="utf-8")
cpp = (app / "src/main/cpp/saude_llm.cpp").read_text(encoding="utf-8")
cmake = (app / "src/main/cpp/CMakeLists.txt").read_text(encoding="utf-8")

assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert 'versionCode = 140' in gradle and 'versionName = "1.9.130"' in gradle
assert 'ndkVersion = "27.2.12479018"' in gradle
assert 'arm64-v8a' in gradle and 'x86_64' in gradle
assert 'src/main/cpp/CMakeLists.txt' in gradle and 'BUILD_SHARED_LIBS=OFF' in gradle

# Explicit two-step consent: no automatic download during app launch.
assert 'fun download(' in runtime and 'fun activate(' in runtime
assert 'fun remove(' in runtime and 'fun ask(' in runtime
assert 'downloaded() && hash(model) == MODEL_SHA256' in runtime
assert 'MODEL_SHA256' in runtime and re.search(r'"[0-9a-f]{64}"', runtime)
assert 'filesDir' in runtime and 'FileOutputStream(part)' in runtime
assert 'setPositiveButton("Descarregar 383 MB")' in agent
assert 'setPositiveButton("Instalar e ativar")' in agent
assert 'setNegativeButton("Agora não",null)' in agent
assert 'onProgress={ percent ->' in agent
assert 'smallReady -> generateSmall(value)' in agent
assert 'smallModel.ask(question)' in agent
assert 'saude_background' in agent and 'WindowInsetsCompat.Type.ime()' in agent

for forbidden in (
    'repo.saveMedications',
    'repo.saveAppointments',
    'NotificationScheduler',
    'MedicationAlarmService',
    'SharedPreferences.putString("clinical"',
):
    assert forbidden not in runtime and forbidden not in cpp

assert 'llama_model_load_from_file' in cpp
assert 'llama_process' in cpp
assert 'llama_sampler_sample' in cpp
assert 'Java_com_mediagenda_app_SmallOfflineModel_nativeLoadModel' in cpp
assert 'Java_com_mediagenda_app_SmallOfflineModel_nativeGenerate' in cpp
assert 'Java_com_mediagenda_app_SmallOfflineModel_nativeUnloadModel' in cpp
assert 'add_subdirectory' in cmake and 'target_link_libraries' in cmake
assert 'llama.cpp' in cmake

assert 'AgentAssistantActivity' in manifest and 'android:exported="false"' in manifest
ET.fromstring(manifest)
assert 'profileId!=activeProfileId' in (src/"MainActivity.kt").read_text(encoding="utf-8")
print("PASS: Qwen3 offline optional download/activation, checksum, native runtime and clinical safety.")
