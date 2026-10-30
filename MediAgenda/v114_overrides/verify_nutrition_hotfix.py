"""Validate UX, Gemini auth and previous behavior without embedding any secrets."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
b=root/"app/src/main/java/com/mediagenda/app"
meal=(b/"MealAiActivity.kt").read_text(encoding="utf-8")
gemini=(b/"MealGeminiDirect.kt").read_text(encoding="utf-8")
wellness=(b/"WellnessActivity.kt").read_text(encoding="utf-8")
gradle=(root/"app/build.gradle.kts").read_text(encoding="utf-8")
assert "🔑 Configurar API Gemini" in meal
assert 'panel("Inteligência artificial · Gemini"' in meal
assert meal.index('p.addView(button("📷 Fotografar refeição")') < meal.index("if(photo!=null)") < meal.index('val tools=panel("Outras formas de registar"')
assert "photo=mem.toByteArray();lastGeminiResult=null;draw()" in meal
assert "photo=mem.toByteArray();draw();detectOffline()" not in meal
assert "photo=mem.toByteArray();draw();detectOffline()" not in meal
assert "Gemini por configurar" in meal and "configurarGemini()" in meal
assert 'https://aistudio.google.com/apikey' in meal
assert "val waiting=MaterialAlertDialogBuilder(this)" in meal
assert "waiting.dismiss()" in meal and "onFailure{error->" in meal
assert "minOf(items.length(),12)" in meal
assert 'val key=PrivateGeminiKey.read(c)?:error(' in gemini
assert "?:return MealGeminiClient.analyze(jpeg)" not in gemini
assert 'gemini-3.8-flash:generateContent' in gemini
assert "fun configured(c:Context)=read(c)!=null" in gemini
assert 'card(content,"Plano alimentar (opcional)"' in wellness
assert 'private fun openDietPlan()' in wellness
assert 'store.saveText(values)' in wellness
assert any("versionCode = "+str(v) in gradle for v in (105,106,107,108)) and any('versionName = "'+v+'"' in gradle for v in ("1.9.95","1.9.96","1.9.97","1.9.98"))
for image in ["saude_icon.png","saude_splash.png","saude_background.png"]:
    art=root/"app/src/main/res/drawable-nodpi"/image
    assert art.is_file() and art.stat().st_size>1024,image
print("Nutrition hotfix v1.9.95: Gemini visible, no silent fallback, plan optional, artwork preserved")
