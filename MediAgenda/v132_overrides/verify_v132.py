#!/usr/bin/env python3
"""Fail-closed assertions for the health tips feature; no clinical data changes."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
base=root/"src/main/java/com/mediagenda/app"
tips=(base/"HealthTipsManager.kt").read_text()
screen=(base/"HealthTipsActivity.kt").read_text()
main=(base/"MainActivity.kt").read_text()
manifest=(root/"src/main/AndroidManifest.xml").read_text()
gradle=(root/"build.gradle.kts").read_text()
for token in ("danbar1971.github.io/SaudePratica/info_saude/informacoes.json",
              "action_url","last_popup","seen_","minimum_days_between_shows",
              "getSystemService(Context.KEYGUARD_SERVICE)","hasWindowFocus()",
              "applicationContext","frequency_days","loadDataWithBaseURL",
              "activity.startActivity(Intent(Intent.ACTION_VIEW,uri))"):
    assert token in tips,token
for token in ("Histórico de informações","Dicas e Informações",
              "HealthTipsManager.history(this)","Outras dicas disponíveis",
              "setFrequency","saude_background"):
    assert token in screen,token
assert main.count("HealthTipsManager.maybeShow(this)")==1
assert main.count("startActivity(Intent(this,HealthTipsActivity::class.java))")==1
assert "com.mediagenda.app.HealthTipsActivity" in manifest
assert 'versionName = "1.9.112"' in gradle
assert "versionCode = 122" in gradle
assert 'applicationId = "com.mediagenda.app.stable"' in gradle
assert "synchronize" not in tips.lower()
assert "ProfileStore" not in tips
print("v1.9.112 audited: remote catalog, local-only archive, safe layout and original app identity")
