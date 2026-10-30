"""Fase C invariant gate: source and branding; real device verification remains mandatory."""
from pathlib import Path
p=Path("build-src/MediAgenda_Android_v1")
src=p/"app/src/main/java/com/mediagenda/app"
meal=(src/"MealAiActivity.kt").read_text(encoding="utf-8")
gemini=(src/"MealGeminiDirect.kt").read_text(encoding="utf-8")
barcode=(src/"MealBarcodeService.kt").read_text(encoding="utf-8")
history=(src/"MealNutritionHistory.kt").read_text(encoding="utf-8")
gradle=(p/"app/build.gradle.kts").read_text(encoding="utf-8")
for required in ("GmsBarcodeScanning.getClient","lookupBarcode(","MealBarcodeService.lookup",
    "MealNutritionHistory.summary","MealDiary(this,profileId).add(entry,photo)",
    "fun photoFile(entry:JSONObject)","fun attachPhoto(id:String,jpeg:ByteArray)",
    "correctGemini(","MealGeminiDirect.correct","protein_g","carbs_g","fat_g",
    '.put("barcode",result?.optString("barcode"'):
    assert required in meal, "missing nutrition function "+required
assert 'fun correct(c:Context,jpeg:ByteArray,original:JSONObject,feedback:String)' in gemini
assert "PrivateGeminiKey.read(c)" in gemini and "responseMimeType" in gemini
assert "https://world.openfoodfacts.org/api/v3/product/" in barcode
assert 'setRequestProperty("User-Agent"' in barcode
assert "profile" not in barcode.lower().replace("profile or medical records","")
assert "fun summary(items:JSONArray,days:Int)" in history
assert any("versionCode = "+str(v) in gradle for v in (103,104,105,106,107,108)) and any('versionName = "'+v+'"' in gradle for v in ("1.9.93","1.9.94","1.9.95","1.9.96","1.9.97","1.9.98"))
assert 'play-services-code-scanner:16.1.0' in gradle
for n in ("saude_icon.png","saude_splash.png","saude_background.png"):
    f=p/"app/src/main/res/drawable-nodpi"/n
    assert f.is_file() and f.stat().st_size > 1024, "missing official "+n
print("Fase C: nutrition+barcode+correction+photo history+branding: OK")
