"""SaúdePrática v1.9.83 — Gemini direct multimodal + encrypted BYO auth key.

This patch extends v1.9.82 without removing its central proxy, offline mode,
photos, history or medical profile separation. The key is NOT bundled in the APK.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
source=Path("MediAgenda/v101_overrides")
meal=base/"MealAiActivity.kt"
s=meal.read_text(encoding="utf-8")
def replace(old,new,label):
    global s
    count=s.count(old)
    if count!=1:raise RuntimeError(f"v1.9.83 {label}: expected one anchor, found {count}")
    s=s.replace(old,new,1)

replace(
 'p.addView(button("✨ Analisar refeição com Gemini (online)") { analyzeWithGemini() })',
 'p.addView(button("✨ Analisar refeição com Gemini (online)") { analyzeWithGemini() })\n'
 '            p.addView(button("🔑 Configurar / testar Gemini no telemóvel") { configurarGemini() })',
 "Gemini key settings button")
replace(
 'val answer=runCatching{MealGeminiClient.analyze(jpeg)}',
 'val answer=runCatching{MealGeminiDirect.analyze(this@MealAiActivity,jpeg)}',
 "Gemini local-first with remote fallback")

anchor='    private fun analyzeWithGemini(){'
new_method=r'''    /** Owner-only one-time setup, encrypted per device and never sent in a backup. */
    private fun configurarGemini(){
        val field=android.widget.EditText(this).apply {
            hint=if(PrivateGeminiKey.configured(this@MealAiActivity))
                "Chave já guardada; cola outra para substituir"
            else "Cola a chave API Google Gemini"
            inputType=android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
            setSingleLine(true)
            setPadding(dp(12),dp(16),dp(12),dp(16))
        }
        val panel=LinearLayout(this).apply {
            orientation=LinearLayout.VERTICAL
            setPadding(dp(12),dp(8),dp(12),dp(8))
            addView(label("A chave é cifrada pelo Android Keystore e fica apenas " +
                "neste telemóvel. Não é incluída nos backups, na sincronização familiar " +
                "ou na APK. Cada fotografia só é enviada ao Google após autorização.",13f))
            addView(field)
        }
        MaterialAlertDialogBuilder(this)
            .setTitle("Gemini · Configuração privada")
            .setView(ScrollView(this).apply{addView(panel)})
            .setNegativeButton("Cancelar",null)
            .setNeutralButton("Eliminar chave"){_,_->
                runCatching{PrivateGeminiKey.delete(this)}
                    .onSuccess{Toast.makeText(this,"Chave Gemini eliminada neste telemóvel.",
                        Toast.LENGTH_LONG).show()}
                    .onFailure{alert("Falha ao eliminar a chave: "+it.message)}
            }
            .setPositiveButton("Guardar e testar"){_,_->
                try{
                    val typed=field.text.toString().trim()
                    if(typed.isNotBlank())PrivateGeminiKey.save(this,typed)
                    val key=PrivateGeminiKey.read(this)
                        ?:error("Cola primeiro a chave Gemini API.")
                    Thread{
                        val result=runCatching{MealGeminiDirect.test(key)}
                        runOnUiThread{
                            if(isFinishing||isDestroyed)return@runOnUiThread
                            result.onSuccess{ok->
                                alert(if(ok)"Gemini ligado! Já podes analisar refeições " +
                                    "pela fotografia." else "O Gemini não confirmou a ligação.")
                            }.onFailure{
                                alert("Chave guardada, mas o teste falhou: " +
                                    (it.message?:"erro de ligação") +
                                    ". Confirma a chave, o acesso ao modelo e a quota.")
                            }
                        }
                    }.start()
                }catch(e:Exception){alert(e.message?:"Não foi possível guardar a chave.")}
            }.show()
    }

'''
if s.count(anchor)!=1:raise RuntimeError("Gemini setup insertion point missing")
s=s.replace(anchor,new_method+anchor,1)
meal.write_text(s,encoding="utf-8")
(base/"MealGeminiDirect.kt").write_text(
    (source/"MealGeminiDirect.kt").read_text(encoding="utf-8"),encoding="utf-8")

build=root/"app/build.gradle.kts"
s=build.read_text(encoding="utf-8")
if s.count("versionCode = 92")!=1 or s.count('versionName = "1.9.82"')!=1:
    raise RuntimeError("Unexpected base version: v1.9.82 required")
s=s.replace("versionCode = 92","versionCode = 93",1)
s=s.replace('versionName = "1.9.82"','versionName = "1.9.83"',1)
build.write_text(s,encoding="utf-8")
print("v1.9.83: Gemini vision, encrypted key, local/central fallback, history intact")
