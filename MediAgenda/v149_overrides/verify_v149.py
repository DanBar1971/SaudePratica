#!/usr/bin/env python3
"""Static acceptance gates; compile and device tests still required."""
from pathlib import Path
import xml.etree.ElementTree as ET
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
main=(src/"MainActivity.kt").read_text(encoding="utf-8")
agent=(src/"AgentAssistantActivity.kt").read_text(encoding="utf-8")
gradle=(app/"build.gradle.kts").read_text(encoding="utf-8")
manifest=(app/"src/main/AndroidManifest.xml").read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert 'versionName = "1.9.129"' in gradle and 'versionCode = 139' in gradle
assert 'minSdk = 26' in gradle
assert 'genai-prompt:1.0.0-beta4' in gradle
assert 'AgentAssistantActivity.EXTRA_PROFILE_ID,activeProfileId' in main
assert 'profileId!=activeProfileId' in main
assert 'agentDraftLauncher' in main
assert 'editMedication(null,Medication(' in main
assert 'editAppointment(null,Appointment(' in main
assert 'Rascunho do assistente' in main
assert 'AgentAssistantActivity' in manifest and 'android:exported="false"' in manifest
ET.fromstring(manifest)
for term in ('DataRepository(this,profileId)','ProfileStore(this).all()',
    'model?.download()?.collect','FeatureStatus.AVAILABLE','generateContent(prompt)',
    'setResult(Activity.RESULT_OK,result)','!a.cancelled','AppointmentStatus.completed',
    'readMedication()', 'readAgenda()'):
    assert term in agent,term
for forbidden in ('repo.saveMedications','repo.saveAppointments','NotificationScheduler',
    'IntakeActionReceiver','MedicationAlarmService','Gemini API key'):
    assert forbidden not in agent,forbidden
assert 'SmartHelpActivity::class.java' in agent
print("PASS: 1.9.129 no AI clinical writes, original package/profile/alarm invariants.")
