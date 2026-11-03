#!/usr/bin/env python3
"""Release gates: no online medical data, optional downloads, original identity."""
from pathlib import Path
import xml.etree.ElementTree as ET
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
agent=(src/"AgentAssistantActivity.kt").read_text()
download=(src/"SystemModelDownload.kt").read_text()
client=(src/"OnlineAiClient.kt").read_text()
gradle=(app/"build.gradle.kts").read_text()
manifest=(app/"src/main/AndroidManifest.xml").read_text()

assert 'versionName = "1.9.131"' in gradle
assert 'versionCode = 141' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert "android.permission.INTERNET" in manifest
ET.fromstring(manifest)
assert 'AgentAssistantActivity' in manifest and 'android:exported="false"' in manifest

# The official native profile authorization and no-direct-write invariant.
main=(src/"MainActivity.kt").read_text()
assert "agentDraftLauncher" in main and "profileId!=activeProfileId" in main
for forbidden in ("repo.saveMedications","repo.saveAppointments",
                  "NotificationScheduler","MedicationAlarmService"):
    assert forbidden not in agent,forbidden
    assert forbidden not in client,forbidden

assert 'DownloadManager' in download
assert 'getSharedPreferences' in download
assert "COLUMN_BYTES_DOWNLOADED_SO_FAR" in download
assert "COLUMN_TOTAL_SIZE_BYTES" in download
assert "STATUS_PAUSED" in download
assert "COLUMN_REASON" in download
assert "setDestinationInExternalFilesDir" in download
assert "sha256" in download.lower()
assert "SHA256" in download and "MODEL" not in download
assert 'VISIBLE_NOTIFY_COMPLETED' in download
assert 'PAUSED_WAITING_FOR_NETWORK' in download
assert 'SystemModelDownload.Phase.DOWNLOADED' in agent
assert 'downloadPanel.visibility' in agent
assert 'downloadLabel.text' in agent
assert 'downloadProgress.progress' in agent
assert 'override fun onStart()' in agent and 'override fun onStop()' in agent

assert "AndroidKeyStore" in client and "AES/GCM/NoPadding" in client
assert ".workers.dev" in client and "/v1/ask" in client
assert 'put("question",q)' in client
assert "profileId" not in client
assert "medication" not in client.lower()
assert "Bearer $secret" in client
assert 'setPositiveButton("Guardar e utilizar")' in agent
assert 'onlineSelected && onlineClient.isConfigured() -> generateOnline(value)' in agent
assert 'onlineClient.ask(question)' in agent
assert 'onlineClient.disconnect()' in agent
assert 'Ajuda tradicional' in (src/"SmartHelpActivity.kt").read_text()

assert "smallModel.ask(question)" in agent
assert 'manageSmallModel()' in agent
assert "downloadProgress" in agent
assert 'saude_background' in agent
print("PASS Android 1.9.131: optional online/local modes, Keystore, DownloadManager, original profile/alarm invariants")
