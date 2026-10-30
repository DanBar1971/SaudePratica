"""SaúdePrática 1.9.82 — Gemini central optional, explicit photo consent, per-item editable nutrition.

Keeps the fully offline flow and data isolation. No API keys in the app.
The Gemini button is available but only functional when the official public
config references an activated secure endpoint. It never silently falls back
to a fabricated calorie estimate.
"""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
source=Path('MediAgenda/v100_overrides')
meal=base/'MealAiActivity.kt'
s=meal.read_text(encoding='utf-8')

def replace(old,new,name):
    global s
    count=s.count(old)
    if count!=1:
        raise RuntimeError(f'v100 {name}: expected 1 anchor, got {count}')
    s=s.replace(old,new,1)

replace('''            p.addView(button("✨ Sugestões offline (apenas um prato)") { detectOffline() })''',
'''            p.addView(button("✨ Analisar refeição com Gemini (online)") { analyzeWithGemini() })
            p.addView(button("🥗 Modo manual offline / selecionar alimentos") {
                chooseFoods(emptySet(),true)
            })
            p.addView(button("✨ Sugestões offline (apenas um prato)") { detectOffline() })''',
    'Gemini + offline controls')

point='''    private fun matchedFood(name:String):FoodReference.Food? {'''
if s.count(point)!=1:raise RuntimeError('v100 Gemini insertion anchor')
methods=r'''    /** One explicit consent per remote analysis; photos otherwise remain private. */
    private fun analyzeWithGemini(){
        val jpeg=photo ?: return
        if(busy)return
        MaterialAlertDialogBuilder(this)
            .setTitle("Analisar com Gemini online?")
            .setMessage("Apenas esta fotografia será enviada ao serviço central SaúdePrática e " +
                "ao Google Gemini para sugerir alimentos e porções. Não serão enviados " +
                "o nome, perfil ou registos médicos. O resultado é uma estimativa e " +
                "pode estar errado. Também podes usar o modo manual offline.")
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Enviar fotografia"){_,_->
                busy=true
                Toast.makeText(this,"A analisar a refeição com Gemini…",Toast.LENGTH_LONG).show()
                Thread {
                    val answer=runCatching{MealGeminiClient.analyze(jpeg)}
                    runOnUiThread{
                        busy=false
                        if(isFinishing||isDestroyed)return@runOnUiThread
                        answer.onSuccess{reviewGeminiFoods(it)}
                            .onFailure{alert("Gemini: ${it.message ?: "Falha de ligação"} " +
                                "Podes usar o modo manual offline.")}
                    }
                }.start()
            }.show()
    }

    /** Each suggested ingredient, weight and calorie value is editable. */
    private fun reviewGeminiFoods(response:JSONObject){
        val entries=response.optJSONArray("foods")?:JSONArray()
        val layout=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL
            setPadding(dp(14),dp(6),dp(14),dp(8))}
        layout.addView(label("Revê cada alimento, gramas e kcal. Podes acrescentar " +
            "ingredientes que não aparecem na fotografia. As kcal são aproximadas.",13f))
        val rows=mutableListOf<Triple<EditText,EditText,EditText>>()
        fun addRow(name:String,grams:String,kcal:String){
            val group=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL
                setPadding(0,dp(5),0,dp(7))}
            val food=input("Alimento",name)
            val quantity=input("Gramas",grams,true)
            val energy=input("kcal estimadas",kcal,true)
            group.addView(food)
            val numbers=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
            numbers.addView(quantity,LinearLayout.LayoutParams(0,-2,1f))
            numbers.addView(energy,LinearLayout.LayoutParams(0,-2,1f))
            group.addView(numbers)
            layout.addView(group)
            rows.add(Triple(food,quantity,energy))
        }
        for(i in 0 until entries.length()){
            val item=entries.optJSONObject(i)?:continue
            addRow(item.optString("name"),"${item.optInt("grams")}",
                "${item.optInt("kcal")}")
        }
        layout.addView(button("＋ Acrescentar alimento") {addRow("","100","0")})
        val dialog=MaterialAlertDialogBuilder(this).setTitle("Rever alimentos · Gemini")
            .setView(ScrollView(this).apply{addView(layout)})
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Recalcular total",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener{
                try {
                    val foods=JSONArray()
                    var total=0.0
                    for((name,grams,kcal) in rows){
                        val n=name.text.toString().trim()
                        if(n.isBlank())continue
                        val g=grams.text.toString().replace(',','.').toDoubleOrNull()
                        val k=kcal.text.toString().replace(',','.').toDoubleOrNull()
                        require(g!=null && g in 1.0..2500.0 && k!=null && k in 0.0..5000.0){
                            "Confirma os gramas e kcal de $n"
                        }
                        foods.put(JSONObject().put("name",n.take(100))
                            .put("grams",g).put("kcal",k))
                        total+=k
                    }
                    require(foods.length()>0 && total in 1.0..10000.0){
                        "Adiciona pelo menos um alimento e confirma as calorias."
                    }
                    val draft=JSONObject().put("foods",foods).put("total_kcal",total)
                        .put("uncertainty_note","Estimativa Gemini revista: valores por alimento " +
                            "editáveis. Confirma óleo, molhos e confeção. Macronutrientes " +
                            "não foram recalculados após as alterações.")
                    dialog.dismiss()
                    editAndSave(draft)
                }catch(e:Exception){Toast.makeText(this,e.message?:"Dados inválidos",
                    Toast.LENGTH_LONG).show()}
            }
    }
'''
s=s.replace(point,methods+point,1)
# Keep explicit deletion; v99 history shows the delete action and deletes the attached photo.
# Avoid introducing any new permissive photo/share channels.
meal.write_text(s,encoding='utf-8')
(base/'MealGeminiClient.kt').write_text((source/'MealGeminiClient.kt').read_text(encoding='utf-8'),encoding='utf-8')

build=root/'app/build.gradle.kts'
b=build.read_text(encoding='utf-8')
assert b.count('versionCode = 91')==1
assert b.count('versionName = "1.9.81"')==1
b=b.replace('versionCode = 91','versionCode = 92',1)
b=b.replace('versionName = "1.9.81"','versionName = "1.9.82"',1)
build.write_text(b,encoding='utf-8')
print('v1.9.82: Gemini gateway (remote centrally activated) + editable foods + offline + photo/history/delete')