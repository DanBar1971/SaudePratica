"""SaúdePrática v1.9.98 — genuine nutrition review screen, no modal clipping.
Apply after v116. Patient/profile and photo serialization are unchanged.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
meal=base/"MealAiActivity.kt"
s=meal.read_text(encoding="utf-8")

def replace(old,new,label):
    global s
    n=s.count(old)
    if n!=1:raise RuntimeError("v117 "+label+" anchors="+str(n))
    s=s.replace(old,new,1)

start="    private fun reviewGeminiFoods(response:JSONObject){"
end="    private fun matchedFood(name:String):FoodReference.Food? {"
assert s.count(start)==1 and s.count(end)==1
a=s.index(start);b=s.index(end,a)
new=Path("MediAgenda/v117_overrides/review_ui.kt.txt").read_text(encoding="utf-8")
assert new.count("private fun reviewGeminiFoods(")==1
s=s[:a]+new+s[b:]
replace("    private var busy = false",
        "    private var busy = false\n    private var lastGeminiResult:JSONObject?=null",
        "cache last successful Gemini analysis")
replace('            p.addView(button("✨ Analisar esta refeição com Gemini") {analyzeWithGemini()})',
        '''            lastGeminiResult?.let{cached->
                p.addView(button("✓ Rever resultado já reconhecido (sem Internet)") {
                    reviewGeminiFoods(cached)
                })
            }
            p.addView(button("✨ Analisar esta refeição com Gemini") {analyzeWithGemini()})''',
        "access last good AI result")
replace("photo=mem.toByteArray();draw()",
    "photo=mem.toByteArray();lastGeminiResult=null;draw()",
    "clear cache when photograph changes")
# Tell the user why a retry failed: DNS vs service temporarily unavailable,
# rather than suggesting replacing a working key.
old='''    private fun analyzeWithGemini(){'''
helper='''    private fun explainMealGeminiError(error:Throwable):String{
        val msg=error.message.orEmpty()
        return when {
            error is java.net.UnknownHostException ||
                msg.contains("Unable to resolve host",true) ->
                    "Não foi possível resolver o endereço do Google Gemini (DNS). "+
                    "Verifica a Internet, DNS privado e bloqueadores de rede. "+
                    "Experimenta Wi-Fi ou dados móveis. Não precisas de mudar a chave API."
            msg.contains("503") || msg.contains("indisponível",true) ->
                    "O serviço Gemini respondeu com indisponibilidade temporária "+
                    "(HTTP 503). A chave pode estar correta. Tenta novamente mais tarde."
            msg.contains("timeout",true) || error is java.net.SocketTimeoutException ->
                    "A ligação ao Gemini ultrapassou o tempo de espera. "+
                    "Verifica a rede e experimenta novamente."
            else -> msg.ifBlank{"Não foi possível estabelecer ligação com o Gemini."}
        }
    }

    private fun analyzeWithGemini(){'''
replace(old,helper,"actionable Gemini errors")
replace('''.setMessage((error.message?:"Erro de ligação")+''',
        '''.setMessage(explainMealGeminiError(error)+''',
        "classify error in popup")
meal.write_text(s,encoding="utf-8")
gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 107")==1 and g.count('versionName = "1.9.97"')==1
g=g.replace("versionCode = 107","versionCode = 108",1).replace(
    'versionName = "1.9.97"','versionName = "1.9.98"',1)
gradle.write_text(g,encoding="utf-8")
print("1.9.98 UI: visible labels, grouped ingredient cards, one sticky Save, AI cache, DNS errors")
