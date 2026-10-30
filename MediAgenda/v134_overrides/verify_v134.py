#!/usr/bin/env python3
"""SaúdePrática v1.9.114 non-destructive synchronization invariants."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
base=root/"src/main/java/com/mediagenda/app"
sync=(base/"sync/NearbySyncStore.kt").read_text(encoding="utf-8")
ui=(base/"sync/NearbySyncActivity.kt").read_text(encoding="utf-8")
main=(base/"MainActivity.kt").read_text(encoding="utf-8")
gradle=(root/"build.gradle.kts").read_text(encoding="utf-8")
assert 'fun export(profileId:String)' in sync
assert 'fun receive(bundle:File,targetProfileId:String)' in sync
assert 'kind","saudepratica-nearby-v2"' in sync
assert 'require(profiles.length()==1)' in sync
assert 'store.create(receivedName' not in sync
assert 'require(targetProfile.name.trim().equals(remoteName,ignoreCase=true))' in sync
assert 'sourceFull==destFull' in sync
assert 'semanticKey(name,item)' in sync
assert 'UUID.randomUUID().toString()' in sync
assert 'if(mode=="host")worker.execute' in ui
assert 'export(selectedProfileId)' in ui and 'receive(local,selectedProfileId)' in ui
assert 'saudepratica.sync.v2' in ui
assert 'hideLegalNames(row)' in main
assert 'deviceButton.text="✎ FICHA"' in main
assert 'versionCode = 124' in gradle and 'versionName = "1.9.114"' in gradle
print("v1.9.114 static safety gates OK: scoped sender/receiver, no auto-created patients.")
