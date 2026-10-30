"""Fase C: concrete Kotlin integration, photo diary + Gemini correction + barcode.
SnapCal (MIT per README) supplied architectural patterns; Open Food Facts ODbL data.
"""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
src=Path('MediAgenda/v112_overrides')
meal=base/'MealAiActivity.kt'
s=meal.read_text(encoding='utf-8')
def once(a,b,label):
    global s
    n=s.count(a)
    if n!=1:raise RuntimeError(f'Fase C {label} anchor count {n}')
    s=s.replace(a,b,1)

once('import android.widget.Toast', '''import android.widget.Toast
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning
import com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions
import com.google.mlkit.vision.barcode.common.Barcode''', 'scanner imports')
once('        p.addView(button("✎ Registar refeição manualmente") { editAndSave(null) })', '''        p.addView(button("▦ Ler código de barras EAN/UPC") { scanBarcode() })
        p.addView(button("⌨ Inserir código manualmente") { manualBarcode() })
        p.addView(button("✎ Registar refeição manualmente") { editAndSave(null) })''', 'barcode buttons')
once('''        showHistory()
    }
    private fun capture()''','''        val diary=MealDiary(this,profileId).list()
        val stats=panel("Histórico nutricional do perfil", "Soma apenas as refeições guardadas.")
        stats.addView(label("Últimos 7 dias\\n"+MealNutritionHistory.summary(diary,7),13f))
        stats.addView(label("Últimos 30 dias\\n"+MealNutritionHistory.summary(diary,30),13f))
        showHistory()
    }
    private fun scanBarcode(){
        val config=GmsBarcodeScannerOptions.Builder()
            .setBarcodeFormats(Barcode.FORMAT_EAN_13,Barcode.FORMAT_EAN_8,
                Barcode.FORMAT_UPC_A,Barcode.FORMAT_UPC_E).build()
        GmsBarcodeScanning.getClient(this,config).startScan()
            .addOnSuccessListener{value->
                val code=value.rawValue.orEmpty()
                if(code.isNotBlank())lookupBarcode(code)
                else alert("Código não reconhecido. Experimenta novamente.")
            }.addOnFailureListener{e->
                alert("Não foi possível usar a câmara: "+(e.message?:"Erro")+
                    ". Podes inserir o código manualmente.")
            }
    }
    private fun manualBarcode(){
        val number=input("Código EAN/UPC (8 a 14 algarismos)","")
        number.inputType=android.text.InputType.TYPE_CLASS_NUMBER
        MaterialAlertDialogBuilder(this).setTitle("Consultar produto")
            .setView(number).setNegativeButton("Cancelar",null)
            .setPositiveButton("Procurar"){_,_->lookupBarcode(number.text.toString())}.show()
    }
    private fun lookupBarcode(raw:String){
        if(busy)return
        val code=raw.trim()
        if(!code.matches(Regex("[0-9]{8,14}"))){
            alert("Código inválido: indica 8 a 14 algarismos.");return
        }
        busy=true
        Thread{
            val lookup=runCatching{MealBarcodeService.lookup(code)}
            runOnUiThread{
                busy=false
                if(isFinishing||isDestroyed)return@runOnUiThread
                lookup.onSuccess{reviewBarcode(it)}
                    .onFailure{alert("Open Food Facts: "+(it.message?:"Produto indisponível")+
                        ". Podes registar manualmente.")}
            }
        }.start()
    }
    private fun reviewBarcode(result:JSONObject){
        val per100=result.optJSONArray("foods")?.optJSONObject(0)
            ?:return alert("Produto sem valores nutricionais.")
        val grams=input("Quantidade consumida (g)","100",true)
        val view=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(10),dp(16),dp(10))
            addView(label(per100.optString("name"),17f,true))
            addView(label("Open Food Facts · valores por 100 g. Confirma os gramas consumidos.",13f))
            addView(grams)
        }
        val dialog=MaterialAlertDialogBuilder(this).setTitle("Confirmar porção")
            .setView(view).setNegativeButton("Cancelar",null)
            .setPositiveButton("Rever e guardar",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener{
                val quantity=grams.text.toString().replace(',','.').toDoubleOrNull()
                if(quantity==null||quantity !in 1.0..2500.0){
                    grams.error="Confirma um peso entre 1 e 2500 g"
                    return@setOnClickListener
                }
                val factor=quantity/100.0
                val item=JSONObject(per100.toString()).put("grams",quantity)
                for(k in arrayOf("kcal","protein_g","carbs_g","fat_g"))
                    item.put(k,per100.optDouble(k,0.0)*factor)
                val data=JSONObject().put("foods",JSONArray().put(item))
                    .put("total_kcal",item.optDouble("kcal"))
                    .put("protein_g",item.optDouble("protein_g"))
                    .put("carbs_g",item.optDouble("carbs_g"))
                    .put("fat_g",item.optDouble("fat_g"))
                    .put("source","Open Food Facts")
                    .put("barcode",result.optString("barcode"))
                    .put("uncertainty_note",result.optString("uncertainty_note"))
                dialog.dismiss();editAndSave(data)
            }
    }
    private fun capture()''','barcode+summary')

start='    /** Each suggested ingredient, weight and calorie value is editable. */\n    private fun reviewGeminiFoods(response:JSONObject){'
end='    private fun matchedFood(name:String):FoodReference.Food? {'
assert s.count(start)==1 and s.count(end)==1
begin=s.index(start);stop=s.index(end,begin)
replacement='''    private fun correctGemini(original:JSONObject){
        val jpeg=photo?:return alert("Fotografia indisponível para correção.")
        if(!PrivateGeminiKey.configured(this)){
            alert("Configura a tua chave privada Gemini para corrigir com IA. " +
                "Podes editar os ingredientes manualmente.");return
        }
        val correction=input("Ex.: não é vaca, é lombo de porco; inclui esparregado","")
            .apply{setSingleLine(false);minLines=3}
        MaterialAlertDialogBuilder(this).setTitle("Corrigir análise multimodal")
            .setMessage("A mesma fotografia será enviada novamente ao Gemini com " +
                "a tua correção. Não são enviados perfis nem dados clínicos.")
            .setView(correction).setNegativeButton("Cancelar",null)
            .setPositiveButton("Enviar correção"){_,_->
                val hint=correction.text.toString().trim()
                if(hint.length !in 4..500){
                    alert("Escreve a correção (4 a 500 caracteres).");return@setPositiveButton
                }
                if(busy)return@setPositiveButton
                busy=true
                Thread{
                    val response=runCatching{
                        MealGeminiDirect.correct(this@MealAiActivity,jpeg,original,hint)
                    }
                    runOnUiThread{
                        busy=false
                        if(isFinishing||isDestroyed)return@runOnUiThread
                        response.onSuccess{reviewGeminiFoods(it)}
                            .onFailure{alert("Correção Gemini: "+(it.message?:"Erro")+
                                ". Podes corrigir manualmente.")}
                    }
                }.start()
            }.show()
    }
    /** Every image-detected ingredient, gram, kcal and macro can be adjusted. */
    private fun reviewGeminiFoods(response:JSONObject){
        val items=response.optJSONArray("foods")?:JSONArray()
        val holder=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL;setPadding(dp(14),dp(6),dp(14),dp(10))
        }
        holder.addView(label("Revê alimentos, gramas, kcal e macros. Ingredientes " +
            "invisíveis (óleo, sal, molhos) não podem ser medidos pela foto.",13f))
        val rows=mutableListOf<List<EditText>>()
        fun addRow(item:JSONObject){
            val group=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
            val name=input("Alimento",item.optString("name"))
            group.addView(name)
            val fields=arrayOf("grams","kcal","protein_g","carbs_g","fat_g")
            val labels=arrayOf("Gramas","kcal","Proteínas g","Hidratos g","Gordura g")
            val nums=fields.indices.map{idx->
                input(labels[idx],item.optDouble(fields[idx],0.0).toString(),true)
            }
            for(set in listOf(nums.take(2),nums.drop(2))){
                val line=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
                set.forEach{line.addView(it,LinearLayout.LayoutParams(0,-2,1f))}
                group.addView(line)
            }
            holder.addView(group);rows.add(listOf(name)+nums)
        }
        for(i in 0 until items.length())items.optJSONObject(i)?.let{addRow(it)}
        holder.addView(button("＋ Adicionar ingrediente"){
            addRow(JSONObject().put("name","").put("grams",100))
        })
        val dialog=MaterialAlertDialogBuilder(this).setTitle("Confirmar alimentos")
            .setView(ScrollView(this).apply{addView(holder)})
            .setNegativeButton("Cancelar",null)
            .setNeutralButton("✍ Corrigir com IA"){_,_->correctGemini(response)}
            .setPositiveButton("Recalcular",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener{
                try{
                    val foods=JSONArray();val sums=DoubleArray(4)
                    for(r in rows){
                        val foodName=r[0].text.toString().trim()
                        if(foodName.isBlank())continue
                        val nums=r.drop(1).map{
                            it.text.toString().trim().replace(',','.').toDoubleOrNull()
                                ?:Double.NaN
                        }
                        require(nums[0].isFinite()&&nums[0] in 1.0..2500.0&&
                            nums.drop(1).all{it.isFinite()&&it in 0.0..5000.0}){
                            "Confirma os números de "+foodName
                        }
                        val ingredient=JSONObject().put("name",foodName.take(100))
                            .put("grams",nums[0])
                        for((i,key) in arrayOf("kcal","protein_g","carbs_g","fat_g").withIndex()){
                            ingredient.put(key,nums[i+1]);sums[i]+=nums[i+1]
                        }
                        foods.put(ingredient)
                    }
                    require(foods.length()>0 && sums[0] in 1.0..10000.0){
                        "Confirma pelo menos um alimento e as calorias."
                    }
                    val data=JSONObject().put("foods",foods)
                        .put("total_kcal",sums[0])
                        .put("protein_g",sums[1]).put("carbs_g",sums[2])
                        .put("fat_g",sums[3])
                        .put("source","Gemini · revisto pelo utilizador")
                        .put("uncertainty_note",response.optString("uncertainty_note")+
                            " Pesos e valores confirmados pelo utilizador.")
                    dialog.dismiss();editAndSave(data)
                }catch(e:Exception){
                    Toast.makeText(this,e.message?:"Dados inválidos",Toast.LENGTH_LONG).show()
                }
            }
    }
'''
s=s[:begin]+replacement+s[stop:]
once('.put("note",note.text.toString().take(500)).put("estimated",result!=null)',
     '.put("note",note.text.toString().take(500)).put("estimated",result!=null)\n'
     '                    .put("source",result?.optString("source","manual") ?: "manual")\n'
     '                    .put("barcode",result?.optString("barcode","") ?: "")',
     'source metadata')
once(r'''            "\n\n${row.optString("note")}",14f))''',
r'''            "\nOrigem: "+row.optString("source","manual")+
            (if(row.optString("barcode").isBlank())"" else
                "\nEAN/UPC: "+row.optString("barcode"))+
            "\n\n${row.optString("note")}",14f))''',"show data origin")
meal.write_text(s,encoding='utf-8')

p=base/'MealGeminiDirect.kt'
g=p.read_text(encoding='utf-8')
anchor='internal object MealGeminiDirect{'
assert g.count(anchor)==1
p.write_text(g.replace(anchor,anchor+(src/'MealGeminiCorrection.kt.txt').read_text(encoding='utf-8'),1),encoding='utf-8')
for n in ('MealBarcodeService.kt','MealNutritionHistory.kt'):
    (base/n).write_text((src/n).read_text(encoding='utf-8'),encoding='utf-8')
gradle=root/'app/build.gradle.kts'
g=gradle.read_text(encoding='utf-8')
assert g.count('versionCode = 102')==1 and g.count('versionName = "1.9.92"')==1
assert 'play-services-code-scanner:16.1.0' in g
g=g.replace('versionCode = 102','versionCode = 103',1).replace('versionName = "1.9.92"','versionName = "1.9.93"',1)
gradle.write_text(g,encoding='utf-8')
print('Fase C 1.9.93 applied: barcode + correction + macros + historical photo diary')