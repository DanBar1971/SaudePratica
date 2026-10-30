"""Fail-closed regression checks for Gemini quota/overload fix."""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
g=(base/'MealGeminiDirect.kt').read_text()
m=(base/'MealAiActivity.kt').read_text()
b=(root/'app/build.gradle.kts').read_text()
for k in ('"gemini-3.5-flash-lite"','"gemini-3.1-flash-lite"','"gemini-2.5-flash-lite"','429','503',
          'aistudio.google.com/rate-limit','model_used','X-goog-api-key'):
    assert k in g,k
assert 'listOf("gemini-3.8-flash","gemini-3.8-flash"' not in g
assert 'require(model=="gemini-3.8-flash"' not in g
assert 'Chave guardada. Não foi possível concluir o teste:' in m
assert 'Um erro HTTP 429 ou 503 não significa que a chave seja inválida' in m
assert 'MealDiary(this,profileId).add(record,photo)' in m
assert 'lastGeminiResult=JSONObject(response.toString())' in m
assert 'versionCode = 109' in b and 'versionName = "1.9.99"' in b
assert 'applicationId = "com.mediagenda.app.stable"' in b
for art in ('saude_icon.png','saude_splash.png','saude_background.png'):
    assert (root/'app/src/main/res/drawable-nodpi'/art).stat().st_size>1024
print('1.9.99 Gemini stable model fallback, quota diagnostics, photos and original identity OK')
