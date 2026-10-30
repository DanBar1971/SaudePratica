"""Fase D: ensure original PDF/images and profile-safe offline clinic catalogue."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
read=lambda rel:(base/rel).read_text(encoding="utf-8")
vault=read("data/HealthDocumentStore.kt")
main=read("MainActivity.kt")
documents=read("DocumentsActivity.kt")
clinics=read("HealthcareCatalog.kt")
labs=read("ClinicalLabsActivity.kt")
work=read("WorkMedicineActivity.kt")
manifest=(root/"app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
gradle=(root/"app/build.gradle.kts").read_text(encoding="utf-8")
for key in ("fun archiveIfMissing(uri: Uri", "val incomingMime=mime(uri).first",
            "document.mimeType != incomingMime", "sha256(input)",
            "fun archivePdfIfMissing", "android.util.AtomicFile(index)",
            "fun contentUri(document: HealthDocument)"):
    assert key in vault,"Document vault missing "+key
assert "HealthDocumentStore(this,activeProfileId)" in main
assert "store.archiveIfMissing(uri,store.suggestedName(uri))" in main
assert "processImportedHealthImage(uri, purpose)" in main
assert "archiveIfMissing(uri,name)" in labs
assert "archiveIfMissing(uri,title)" in work
assert "Intent.ACTION_SEND_MULTIPLE" in documents
assert "archiveSharedBatch(multiple)" in documents
assert 'android.intent.action.SEND_MULTIPLE' in manifest
assert "fun search(context:Context,query:String)" in clinics
assert "fun remember(context:Context,name:String" in clinics
assert "searchHealthcareFacility(onSelected)" in main
assert "HealthcareCatalog.facilities(this,district,municipality)" in main
assert "HealthcareCatalog.remember(this,name,district,municipality)" in main
assert any("versionCode = "+str(v) in gradle for v in (104,105,106,107,108)) and any('versionName = "'+v+'"' in gradle for v in ("1.9.94","1.9.95","1.9.96","1.9.97","1.9.98"))
assert 'android:icon="@drawable/saude_icon"' in manifest
for img in ("saude_icon.png","saude_splash.png","saude_background.png"):
    f=root/"app/src/main/res/drawable-nodpi"/img
    assert f.is_file() and f.stat().st_size>1024,img
print("Fase D validated: original PDF/IMG, OCR sources, clinics, identity and branding")
