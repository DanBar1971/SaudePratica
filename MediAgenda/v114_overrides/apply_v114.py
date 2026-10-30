"""SaúdePrática 1.9.95: reliable Gemini flow, simplified nutrition and compact diet-plan access.
Applied after v113; no migration, artwork, alarm or database modifications.
"""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'

def update(relative, changes):
    path=base/relative
    s=path.read_text(encoding='utf-8')
    for label, old, new in changes:
        count=s.count(old)
        if count!=1: raise RuntimeError(f'v114 {relative} {label}: anchors={count}')
        s=s.replace(old,new,1)
    path.write_text(s,encoding='utf-8')

path=base/'MealAiActivity.kt'
s=path.read_text(encoding='utf-8')
start='    private fun draw() {\n'
end='    private fun scanBarcode(){\n'
assert s.count(start)==1 and s.count(end)==1
new_draw='''    private fun draw() {
        body.removeAllViews()
        val current=ProfileStore(this).all().firstOrNull{it.id==profileId}
        body.addView(label("🍽️ Refeições",25f,true))
        body.addView(label((current?.name?:"Perfil atual")+
            " · Fotografar, reconhecer e guardar o que comeste.",14f).apply{
            setTextColor(secondary)
        })
        val p=panel("Nova refeição","Escolhe uma fotografia. Com Gemini, revês todos os alimentos e as porções antes de guardar.")
        p.addView(button("📷 Fotografar refeição") { capture() })
        p.addView(button("🖼️ Escolher fotografia do telemóvel") {
            gallery.launch(arrayOf("image/jpeg","image/png","image/webp"))
        })
        if(photo!=null){
            val jpeg=photo!!
            p.addView(ImageView(this).apply{
                scaleType=ImageView.ScaleType.FIT_CENTER
                adjustViewBounds=true
                setImageBitmap(BitmapFactory.decodeByteArray(jpeg,0,jpeg.size))
                contentDescription="Fotografia da refeição ainda não guardada"
            },LinearLayout.LayoutParams(-1,dp(230)))
            p.addView(button("✨ Analisar esta refeição com Gemini") {analyzeWithGemini()})
            p.addView(button("✎ Identificar alimentos manualmente") {
                chooseFoods(emptySet(),true)
            })
            p.addView(button("✕ Retirar fotografia") {photo=null;draw()})
        } else {
            p.addView(label("Após escolher a fotografia aparece aqui o botão Analisar com Gemini.",13f))
        }
        val configured=PrivateGeminiKey.read(this)!=null
        val setup=panel("Inteligência artificial · Gemini",
            if(configured)"✓ Chave Gemini guardada neste telemóvel. Podes testá-la ou substituí-la."
            else "Por configurar. Para reconhecer refeições completas, precisas de uma chave Gemini pessoal.")
        setup.addView(button(if(configured)"⚙ Testar ou alterar Gemini" else
            "🔑 Configurar API Gemini") {configurarGemini()})
        val tools=panel("Outras formas de registar",
            "Sem fotografia também podes procurar alimentos ou usar o código de barras.")
        tools.addView(button("🥗 Escolher alimentos e calcular calorias"){
            chooseFoods(emptySet(),photo!=null)
        })
        tools.addView(button("▦ Ler código de barras") {scanBarcode()})
        tools.addView(button("⌨ Escrever código de barras") {manualBarcode()})
        tools.addView(button("✎ Registar manualmente") {editAndSave(null)})
        if(photo!=null){
            tools.addView(button("⋯ Reconhecimento offline experimental"){
                MaterialAlertDialogBuilder(this)
                    .setTitle("Reconhecimento offline limitado")
                    .setMessage("O modelo local identifica no máximo um prato e não reconhece "+
                        "refeições completas com sopa, arroz, carne e sobremesa. "+
                        "Para vários alimentos usa Gemini ou escolhe os ingredientes manualmente.")
                    .setNegativeButton("Cancelar",null)
                    .setPositiveButton("Experimentar"){_,_->detectOffline()}.show()
            })
        }
        showHistory()
        val diary=MealDiary(this,profileId).list()
        if(diary.length()>0){
            val recent=panel("Resumo nutricional","Apenas refeições registadas, não o consumo total real.")
            recent.addView(label("7 dias: "+MealNutritionHistory.summary(diary,7),13f))
            recent.addView(label("30 dias: "+MealNutritionHistory.summary(diary,30),13f))
        }
    }
'''
s=s[:s.index(start)]+new_draw+s[s.index(end):]
s=s.replace('    private var busy = false\n','    private var busy = false\n',1)
assert 'photo=mem.toByteArray();draw();detectOffline()' in s
s=s.replace('photo=mem.toByteArray();draw();detectOffline()','photo=mem.toByteArray();draw()',1)
# Setup link and readback in existing settings dialog, preserve original encrypted Keystore.
needle='''            addView(field)
        }
        MaterialAlertDialogBuilder(this)
            .setTitle("Gemini · Configuração privada")'''
assert s.count(needle)==1
s=s.replace(needle,'''            addView(field)
            addView(button("🔗 Obter chave Gemini no Google AI Studio") {
                startActivity(Intent(Intent.ACTION_VIEW,
                    Uri.parse("https://aistudio.google.com/apikey")))
            })
            addView(label("Se ainda tens uma chave antiga, cria uma nova chave de autorização (auth key). " +
                "A utilização do Gemini pode estar sujeita a limites ou custos.",13f))
        }
        MaterialAlertDialogBuilder(this)
            .setTitle("Gemini · Configuração privada")''',1)
# Ensure config status updates regardless test outcome.
needle='''                    if(typed.isNotBlank())PrivateGeminiKey.save(this,typed)
                    val key=PrivateGeminiKey.read(this)'''
assert s.count(needle)==1
s=s.replace(needle,'''                    if(typed.isNotBlank())PrivateGeminiKey.save(this,typed)
                    draw()
                    val key=PrivateGeminiKey.read(this)''',1)
# Better UX for analyze -- key check before prompting, no unsupported proxy route.
start='    private fun analyzeWithGemini(){\n'
end='    private fun correctGemini(original:JSONObject){\n'
assert s.count(start)==1 and s.count(end)==1
new_analyze='''    /** Never pretend a request succeeded. Show a persistent progress dialogue
     * until either the selected Gemini API replies or gives an actionable error.
     */
    private fun analyzeWithGemini(){
        val jpeg=photo ?: return alert("Fotografa ou escolhe primeiro uma refeição.")
        if(busy)return
        if(PrivateGeminiKey.read(this).isNullOrBlank()){
            MaterialAlertDialogBuilder(this).setTitle("Gemini por configurar")
                .setMessage("Para analisar uma refeição completa, configura a tua chave Gemini. "+
                    "Encontras a chave no Google AI Studio. Também podes escolher os alimentos manualmente.")
                .setNegativeButton("Modo manual"){_,_->chooseFoods(emptySet(),true)}
                .setPositiveButton("Configurar Gemini"){_,_->configurarGemini()}.show()
            return
        }
        MaterialAlertDialogBuilder(this).setTitle("Analisar fotografia com Gemini?")
            .setMessage("Apenas a fotografia escolhida será enviada ao Google Gemini. "+
                "Não são enviados o perfil nem os dados de saúde. "+
                "As calorias e gramagens são estimativas que deves rever.")
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Analisar"){_,_->
                busy=true
                val indicator=android.widget.ProgressBar(this)
                val box=LinearLayout(this).apply{gravity=Gravity.CENTER
                    setPadding(dp(16),dp(20),dp(16),dp(18));addView(indicator)
                }
                val waiting=MaterialAlertDialogBuilder(this)
                    .setTitle("A analisar a refeição…")
                    .setMessage("A enviar a fotografia e a identificar os alimentos. "+
                        "O resultado aparecerá para confirmação.")
                    .setView(box).setCancelable(false).create()
                waiting.show()
                Thread{
                    val answer=runCatching{
                        MealGeminiDirect.analyze(this@MealAiActivity,jpeg)
                    }
                    runOnUiThread{
                        busy=false
                        waiting.dismiss()
                        if(isFinishing||isDestroyed)return@runOnUiThread
                        answer.onSuccess{reviewGeminiFoods(it)}
                            .onFailure{error->
                                MaterialAlertDialogBuilder(this)
                                    .setTitle("Não foi possível analisar com Gemini")
                                    .setMessage((error.message?:"Erro de ligação")+
                                        "\\n\\nA fotografia continua disponível. "+
                                        "Confirma a chave e o modelo, ou usa o modo manual.")
                                    .setNegativeButton("Modo manual"){_,_->
                                        chooseFoods(emptySet(),true)
                                    }.setPositiveButton("Configurar Gemini"){_,_->
                                        configurarGemini()
                                    }.show()
                            }
                    }
                }.start()
            }.show()
    }

'''
s=s[:s.index(start)]+new_analyze+s[s.index(end):]
# Make diary easier to scan; delete remains available in detail dialog.
assert 'minOf(items.length(),40)' in s
s=s.replace('minOf(items.length(),40)','minOf(items.length(),12)',1)
a=s.index('            p.addView(button("🗑 Eliminar refeição de "+whenDate){')
b=s.index('        }\n    }\n    private fun showMealDetails(',a)
s=s[:a]+s[b:]
path.write_text(s,encoding='utf-8')

# Gemini: explicit one-device auth key; updated stable multimodal model;
# visible permission/limit errors; no silent disabled proxy fallback.
update('MealGeminiDirect.kt',[
    ('valid-key-status','fun configured(c:Context)=file(c).isFile',
        'fun configured(c:Context)=read(c)!=null'),
    ('explicit key',
        'val key=PrivateGeminiKey.read(c)?:return MealGeminiClient.analyze(jpeg)',
        'val key=PrivateGeminiKey.read(c)?:error("Configura uma chave Gemini em Nutrição > Configurar API Gemini.")'),
    ('model',
        'private const val ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"',
        'private const val ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"'),
    ('improved auth error',
        '400,401,403->"Chave API ou permissões Gemini recusadas (HTTP "+status+")."',
        '400,401,403->"Gemini recusou a chave (HTTP "+status+"). Cria uma auth key no Google AI Studio e verifica o acesso ao modelo."'),
    ('improved model error',
        '404->"Modelo Gemini não disponível (404)."',
        '404->"Modelo Gemini não disponível para esta chave (404). Verifica o projeto Google AI Studio."'),
    ('timeout error',
        '429->"Limite de chamadas Gemini atingido (429)."',
        '429->"Limite ou quota Gemini atingidos (429). Confirma limites e faturação no Google AI Studio."'),
    ('strict test response',
        'return (call(key,body).optJSONArray("candidates")?.length()?:0)>0',
        'return call(key,body).optJSONArray("candidates")?.optJSONObject(0)\n            ?.optJSONObject("content")?.optJSONArray("parts")?.length()?.let{it>0}?:false')
])

# Diet plan: keep stored professional instructions, hide verbose fields until requested.
path=base/'WellnessActivity.kt'
w=path.read_text(encoding='utf-8')
start='        val items = listOf(\n            "diet_name" to "Nome do plano",'
assert w.count(start)==1
w=w.replace(start,'''        card(content,"Plano alimentar (opcional)",
            "Consulta ou edita as orientações de um nutricionista ou médico, apenas se tiveres um plano.",
            "Ver / editar plano alimentar") { openDietPlan() }
    }

    /** Existing stored prescriptions are untouched; this modal is optional. */
    private fun openDietPlan() {
        val items = listOf(
            "diet_name" to "Nome do plano",''',1)
old='''        card(content, "Plano alimentar pessoal", summary, "✎ Guardar ou alterar plano") {
            dataDialog("Plano alimentar do tratamento", listOf('''
assert w.count(old)==1
w=w.replace(old,'''        val note=ScrollView(this).apply{addView(TextView(this@WellnessActivity).apply{
            text=summary
            textSize=15f
            setTextColor(modalText)
            setPadding(dp(14),dp(10),dp(14),dp(10))
        })}
        MaterialAlertDialogBuilder(this).setTitle("Plano alimentar (opcional)")
            .setView(note).setNegativeButton("Fechar",null)
            .setPositiveButton("Editar"){_,_->
            dataDialog("Plano alimentar do tratamento", listOf(''',1)
old='''            )) { values ->
                store.saveText(values)
                showDiet()
            }
        }
        line(content,
            "A aplicação regista as orientações que recebeste. Não cria dietas clínicas nem altera restrições prescritas. Antes de mudar a alimentação durante um tratamento, confirma com a tua equipa de saúde.",
            12f, false, muted, 13)
    }
}'''
assert w.count(old)==1
w=w.replace(old,'''            )) { values ->
                store.saveText(values)
                showDiet()
            }
        }.show()
    }
}''',1)
path.write_text(w,encoding='utf-8')

build=root/'app/build.gradle.kts'
b=build.read_text(encoding='utf-8')
assert b.count('versionCode = 104')==1 and b.count('versionName = "1.9.94"')==1
build.write_text(b.replace('versionCode = 104','versionCode = 105',1)
    .replace('versionName = "1.9.94"','versionName = "1.9.95"',1),encoding='utf-8')
print('v1.9.95 nutrition UX: key always visible, no silent proxy, progress/errors, optional plan, history compact')