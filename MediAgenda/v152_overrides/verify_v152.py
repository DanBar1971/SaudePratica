#!/usr/bin/env python3
"""Static safety checks after applying Android 1.9.132 overlay."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
src=root/"src/main/java/com/mediagenda/app"
text=lambda p:p.read_text(encoding="utf-8")
agent=text(src/"AgentAssistantActivity.kt")
lan=text(src/"WindowsLanPairActivity.java")
manifest=text(root/"src/main/AndroidManifest.xml")
main=text(src/"MainActivity.kt")
gradle=text(root/"build.gradle.kts")
assert 'versionCode = 142' in gradle
assert 'versionName = "1.9.132"' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
for token in ('thinkingPulse','thinkingHandler','A gerar resposta','setThinking(true,"IA local leve")',
              'setThinking(true,"Gemini Nano")','setThinking(true,"IA Online")',
              'sendButton.isEnabled=!active','setTextColor(if(dark)Color.WHITE',
              'backgroundTintList=android.content.res.ColorStateList.valueOf'):
    assert token in agent,token
assert 'class WindowsLanPairActivity' in lan
assert 'package com.mediagenda.app;' in lan
for token in ('_saudepratica-sync._tcp.','SP_DISCOVER_1:','SP_FOUND_1:',
              'sp-pair-test-0','/v1/status','/v1/request','/v1/result?id=',
              'new AlertDialog.Builder(this)','setPositiveButton("Autorizar"'):
    assert token in lan,token
for forbidden in ('DataRepository','ProfileStore','loadMedications','loadAppointments',
                  'PortableWindowsBackup','/v1/data','/v1/clinical','getSharedPreferences'):
    assert forbidden not in lan,forbidden
assert 'android:name=".WindowsLanPairActivity"' in manifest
assert 'android:exported="false"' in manifest
assert 'android.permission.CHANGE_WIFI_MULTICAST_STATE' in manifest
assert 'android.permission.ACCESS_WIFI_STATE' in manifest
assert 'Ligação Windows · Wi-Fi (teste)' in main
assert 'startActivity(Intent(this,WindowsLanPairActivity::class.java))' in main
assert (src/"sync/NearbySyncActivity.kt").exists()
assert (src/"notifications/NotificationScheduler.kt").exists()
assert (src/"data/FamilyBackupStore.kt").exists()
print("Android 1.9.132 safety assertions passed: assist UI, local Windows handshake, no clinical transfer.")
