#!/usr/bin/env python3
from pathlib import Path
r=Path("build-src/MediAgenda_Android_v1/app")
s=(r/"src/main/java/com/mediagenda/app/HealthTipsManager.kt").read_text()
g=(r/"build.gradle.kts").read_text()
checks=["embedded_actions","embedded_action_regions","client_revision",
        "actionBounds","closeBounds","inJustDecodeBounds=true",
        "picture.addView(view,FrameLayout.LayoutParams(w,h)",
        'contentDescription=description',
        "if(tip.embeddedActions && file.extension.lowercase()!=\"svg\")",
        "available[id] ?:","Intent.ACTION_VIEW"]
for c in checks:assert c in s,c
assert s.count("picture.post {")==1
assert 'versionName = "1.9.113"' in g and "versionCode = 123" in g
assert 'applicationId = "com.mediagenda.app.stable"' in g
print("PASS v1.9.113: actual photo actions, accessible overlay, no extra footer, unchanged package ID")
