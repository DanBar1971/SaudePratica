"""SaúdePrática 1.9.98: no clipped action buttons, real meal persistence."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
meal=(base/"MealAiActivity.kt").read_text(encoding="utf-8")
gradle=(root/"app/build.gradle.kts").read_text(encoding="utf-8")
for required in [
    "private fun reviewGeminiFoods(response:JSONObject)",
    "lastGeminiResult=JSONObject(response.toString())",
    "Rever resultado já reconhecido (sem Internet)",
    "Guardar refeição no diário",
    "Total estimado:",
    "Nutrientes ▾",
    "Quantidade (g)",
    "Calorias (kcal)",
    "Proteínas (g)",
    "Hidratos de carbono (g)",
    "Gorduras (g)",
    "dialog.window?.apply",
    "MATCH_PARENT",
    "SOFT_INPUT_ADJUST_RESIZE",
    "MealDiary(this,profileId).add(record,photo)",
    "lastGeminiResult=null",
    "explainMealGeminiError(error)",
    "Não foi possível resolver o endereço do Google Gemini",
    "A chave pode estar correta",
]:
    assert required in meal, "Missing nutrition UX feature: "+required
assert '.setTitle("Confirmar alimentos")' not in meal, "Old cramped dialog still used"
assert "versionCode = 108" in gradle and 'versionName = "1.9.98"' in gradle
assert "com.mediagenda.app.stable" in (root/"app/build.gradle.kts").read_text()
for picture in ("saude_icon.png","saude_splash.png","saude_background.png"):
    p=root/"app/src/main/res/drawable-nodpi"/picture
    assert p.exists() and p.stat().st_size>1024,picture
print("1.9.98 review UX and original branding verified")
