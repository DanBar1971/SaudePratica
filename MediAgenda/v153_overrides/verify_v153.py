#!/usr/bin/env python3
"""Android v1.9.133 regression and isolation checks after v153 overlay."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
src=root/"src/main/java/com/mediagenda/app"
main=(src/"MainActivity.kt").read_text(encoding="utf-8")
manifest=(root/"src/main/AndroidManifest.xml").read_text(encoding="utf-8")
gradle=(root/"build.gradle.kts").read_text(encoding="utf-8")
cleanup=(src/"LegacyAssistantCleanup.java").read_text(encoding="utf-8")
assert "versionCode = 143" in gradle and 'versionName = "1.9.133"' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert "AgentAssistantActivity" not in main+manifest
assert "agentDraftLauncher" not in main
assert "fromAgent" not in main
assert (src/"SmartHelpActivity.kt").is_file()
assert 'startActivity(Intent(this,SmartHelpActivity::class.java))' in main
assert '"Ajuda tradicional"' in main
assert "LegacyAssistantCleanup.run(applicationContext)" in main
for p in ("AgentAssistantActivity.kt","SmallOfflineModel.kt","SystemModelDownload.kt","OnlineAiClient.kt"):
    assert not (src/p).exists(),p
assert not (root/"src/main/cpp/saude_llm.cpp").exists()
assert "genai-prompt" not in gradle
assert "externalNativeBuild" not in gradle
assert "saude_llm" not in gradle
# Keep the Gemini nutrition API, ML Kit OCR and profile-aware data models.
assert 'implementation("com.google.mlkit:text-recognition:16.0.1")' in gradle
assert (src/"MealAiActivity.kt").is_file()
assert (src/"sync/NearbySyncActivity.kt").is_file()
assert (src/"sync/NearbySyncStore.kt").is_file()
assert (src/"WindowsLanPairActivity.java").is_file()
assert 'android:name=".WindowsLanPairActivity"' in manifest
assert 'startActivity(Intent(this,WindowsLanPairActivity::class.java))' in main
for p in ("data/FamilyBackupStore.kt","data/PortableWindowsBackup.kt",
          "notifications/NotificationScheduler.kt","data/WellnessStore.kt"):
    assert (src/p).is_file(),p
for key in ('"Qwen3-0.6B-Q4_K_S.gguf"','"saudepratica_ia_model_download"',
            '"saudepratica_online_ai"','"saude_online_ai_mode"',
            '"saudepratica_online_ai_token_v1"'):
    assert key in cleanup,key
assert 'getFilesDir(), "ia-local"' in cleanup
assert 'getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)' in cleanup
for forbidden in ('FamilyBackupStore','PortableWindowsBackup','DataRepository',
                  'ProfileStore','deleteDatabase','getFilesDir().delete',
                  'getSharedPreferences("mediagenda_ui", Context.MODE_PRIVATE)\n                    .edit().clear()'):
    assert forbidden not in cleanup,forbidden
print("PASS 1.9.133: generative Assistants removed, legacy Help restored and old model cleanup scoped safely.")
print("PASS 1.9.133: Nearby/Wi-Fi Windows pairing, nutrition, profiles, backups and alarms retained.")
