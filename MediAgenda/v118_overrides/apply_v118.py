"""SaúdePrática v1.9.99: replace overloaded preview Gemini models with
stable photo-capable Flash-Lite variants, classify quota vs server availability,
keep identity, UI/photo diary, A-E alarms and all branding unchanged.
"""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
client=base/'MealGeminiDirect.kt'
s=client.read_text(encoding='utf-8')
a='    private class RetryableGeminiException(message:String):Exception(message)'
b='    private fun normalize(response:JSONObject):JSONObject{'
assert s.count(a)==1 and s.count(b)==1, 'Gemini implementation anchor changed'
old=s[s.index(a):s.index(b,s.index(a))]
new=Path('MediAgenda/v118_overrides/gemini_stable.kt.txt').read_text(encoding='utf-8')
assert new.count('private fun call(')==1 and new.count('private fun sendOnce(')==1
s=s.replace(old,new,1)
# Propagate the resolved model to the user-visible review, without logging keys.
anchor='''            .put("provider","gemini")'''
assert s.count(anchor)==1
s=s.replace(anchor,'''            .put("provider","gemini")
            .put("model_used",response.optString("model_used",""))''',1)
client.write_text(s,encoding='utf-8')
activity=base/'MealAiActivity.kt'
t=activity.read_text(encoding='utf-8')
def replace(old,new):
    global t
    assert t.count(old)==1, (old[:60],t.count(old))
    t=t.replace(old,new,1)
replace('''                alert(if(ok)"Gemini ligado! Já podes analisar refeições " +
                                    "pela fotografia." else "O Gemini não confirmou a ligação.")''',
        '''                alert(if(ok)"Gemini ligado! Teste concluído num modelo estável " +
                                    "(Flash-Lite). Já podes analisar fotografias." 
                                    else "O Gemini não confirmou a ligação.")''')
replace('''                                alert("Chave guardada, mas o teste falhou: " +
                                    (it.message?:"erro de ligação") +
                                    ". Confirma a chave, o acesso ao modelo e a quota.")''',
        '''                                alert("Chave guardada. Não foi possível concluir o teste: " +
                                    (it.message?:"erro de ligação") +
                                    ". Um erro HTTP 429 ou 503 não significa que a chave seja inválida.")''')
replace('''            msg.contains("503") || msg.contains("indisponível",true) ->''',
        '''            msg.contains("429") ->
                    "Limites ou quota Gemini atingidos (HTTP 429). " +
                    "Consulta o teu projeto e as quotas por modelo no Google AI Studio. " +
                    "Não precisas de substituir a chave; a foto continua disponível."
            msg.contains("503") || msg.contains("indisponível",true) ->''')
replace('''                                        "Confirma a chave e o modelo, ou usa o modo manual.")''',
        '''                                        "Consulta as quotas no Google AI Studio, ou usa o modo manual.")''')
activity.write_text(t,encoding='utf-8')
gradle=root/'app/build.gradle.kts'
g=gradle.read_text(encoding='utf-8')
assert g.count('versionCode = 108')==1 and g.count('versionName = "1.9.98"')==1
g=g.replace('versionCode = 108','versionCode = 109',1).replace(
    'versionName = "1.9.98"','versionName = "1.9.99"',1)
gradle.write_text(g,encoding='utf-8')
print('SaúdePrática v1.9.99: stable Gemini models, 429/503 diagnostics, unchanged photos/alarms')
