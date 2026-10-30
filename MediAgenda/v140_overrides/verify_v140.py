#!/usr/bin/env python3
"""Build-time static acceptance checks for v1.9.120 (not a phone test)."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
main=(src/"MainActivity.kt").read_text()
glucose=(src/"DiabetesActivity.kt").read_text()
links=(src/"ImportantShortcutsActivity.kt").read_text()
smart=(src/"SmartHelpActivity.kt").read_text()
help=(src/"SupportHelpActivity.kt").read_text()
gradle=(app/"build.gradle.kts").read_text()
manifest=app/"src/main/AndroidManifest.xml"

assert 'versionCode = 130' in gradle and 'versionName = "1.9.120"' in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert "DashboardModule(" in main and '"Diabetes"' in main
assert '"SNS 24", "Aplicação oficial de saúde"' not in main
assert '"IPO Lisboa", "Abrir aplicação IPO Lisboa"' not in main
assert "DiabetesActivity.EXTRA_PROFILE_ID,activeProfileId" in main
assert "ImportantShortcutsActivity::class.java" in main
assert "https://danbar1971.github.io/SaudePratica/" in main
assert "DiabetesActivity" in manifest.read_text()
assert "ImportantShortcutsActivity" in manifest.read_text()
ET.parse(manifest)
assert "QUERY_ALL_PACKAGES" not in manifest.read_text()
for pkg in ("pt.minsaude.spms.ces","com.seamlink.gatewaybox.ipolisboa"):
    assert pkg in links,pkg
for term in ("CATEGORY_LAUNCHER","queryIntentActivities","https","Intent.ACTION_MAIN"):
    assert term in links,term
for term in ('"profile_id"','SHA-256','JSONArray','hba1c','glucose','mg/dL','mmol/L','"manual"'):
    assert term in glucose,term
for term in ("Como registar a glicemia?","Como criar um atalho de aplicação?",
             "O catálogo português PortFIR ainda está em integração"):
    assert term in smart,term
assert "Diabetes · Diário por perfil" in help
assert "Atalhos Importantes" in help
# Do not edit scheduling/caregiver alarm paths or relocate PIN/lockscreen.
assert "NotificationScheduler" in main
# Staged MVP deliberately excludes insulin dosing or fake sensor capture.
assert "insulinDoseCalculator" not in glucose
assert "Camera" not in glucose
print("v140 static checks passed (not equivalent to Android compilation/device testing)")
