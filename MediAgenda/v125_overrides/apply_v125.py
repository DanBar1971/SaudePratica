#!/usr/bin/env python3
"""SaúdePrática v1.9.105: clinical identifiers, official artwork and coffee.

No profile IDs, patient data, alarm schedule or signing identity are changed.
The clinical editor remains compatible with observations_by_unit as newline text.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
base=root/"src/main/java/com/mediagenda/app"

def replace_exact(path, old, new, label):
    src=path.read_text(encoding="utf-8")
    assert src.count(old)==1,(label,src.count(old))
    path.write_text(src.replace(old,new,1),encoding="utf-8")

# Each clinical number is an editable independent record, including multiple
# entries for a single hospital. Legacy unstructured lines are never discarded.
p=base/"WorkMedicineActivity.kt"
src=p.read_text(encoding="utf-8")
begin=src.index('        val clinicalCard=card("Números de observação e processo de tratamento",')
end=src.index('        val items=runCatching{store.all()}',begin)
new_ui=r'''        val clinicalEntries=obs.lines().map{it.trim()}.filter{it.isNotEmpty()}.toMutableList()
        val clinicalCard=card("Números de observação e processo de tratamento",
            "Vários registos por hospital ou clínica, exclusivos deste perfil. Podes adicionar, alterar ou eliminar cada número.")
        fun editClinicalRecord(position:Int?){
            val raw=position?.let{clinicalEntries.getOrNull(it)}.orEmpty()
            val hasUnit=raw.contains("|")
            val savedUnit=if(hasUnit)raw.substringBefore("|").trim() else ""
            val savedNumber=if(hasUnit)raw.substringAfter("|").trim() else raw
            val sheet=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL
                setPadding(dp(18),dp(8),dp(18),dp(8))
            }
            val hospital=field("Hospital ou clínica (opcional)",savedUnit)
            val number=field("Número de observação ou processo",savedNumber)
            sheet.addView(hospital);sheet.addView(number)
            MaterialAlertDialogBuilder(this)
                .setTitle(if(position==null)"Adicionar número clínico" else "Editar número clínico")
                .setMessage("O registo será guardado apenas no perfil atual.")
                .setView(sheet).setNegativeButton("Cancelar",null)
                .setPositiveButton("Guardar"){_,_->
                    val unit=hospital.text.toString().trim()
                        .replace("\n"," ").replace("|","/")
                    val value=number.text.toString().trim()
                        .replace("\n"," ").replace("|","/")
                    if(value.isBlank()){
                        message("Introduz um número de observação ou processo.")
                    }else{
                        val record=if(unit.isBlank())value else "$unit | $value"
                        val updated=clinicalEntries.toMutableList()
                        if(position==null)updated.add(record)else updated[position]=record
                        val encoded=updated.joinToString("\n")
                        if(encoded.length>8000){
                            message("Limite de registos clínicos atingido.")
                        }else if(clinicalPrefs.edit()
                            .putString("observations_by_unit",encoded).commit()){
                            redraw()
                        }else message("Não foi possível guardar o registo.")
                    }
                }.show()
        }
        if(clinicalEntries.isEmpty())clinicalCard.addView(text(
            "Ainda não há registos de números clínicos.",13f,false,muted))
        clinicalEntries.forEachIndexed{index,record->
            val formatted=if(record.contains("|")){
                val parts=record.split("|",limit=2)
                parts[0].trim()+" · "+parts[1].trim()
            }else "Registo existente · "+record
            clinicalCard.addView(text("${index+1}. $formatted",14f,true,teal))
            val controls=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
            controls.addView(button("✎ Editar"){editClinicalRecord(index)},
                LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
            controls.addView(button("Eliminar"){
                MaterialAlertDialogBuilder(this)
                    .setTitle("Eliminar este número clínico?")
                    .setMessage("Só este registo será removido do perfil atual.")
                    .setNegativeButton("Cancelar",null)
                    .setPositiveButton("Eliminar"){_,_->
                        val updated=clinicalEntries.toMutableList()
                        updated.removeAt(index)
                        if(clinicalPrefs.edit()
                            .putString("observations_by_unit",updated.joinToString("\n"))
                            .commit())redraw()
                        else message("Não foi possível eliminar o registo.")
                    }.show()
            },LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
            clinicalCard.addView(controls)
        }
        clinicalCard.addView(button("＋ Adicionar número de observação / processo"){
            editClinicalRecord(null)
        })
        if(old.isNotBlank())clinicalCard.addView(text(
            "Número antigo (preservado): $old",13f,false,muted))
        clinicalCard.addView(button("✎ Editar número antigo (opcional)"){
            val previous=field("N.º de observação antigo",old)
            MaterialAlertDialogBuilder(this)
                .setTitle("Número clínico antigo")
                .setMessage("Mantém o histórico original, sem alterar os outros registos.")
                .setView(previous).setNegativeButton("Cancelar",null)
                .setPositiveButton("Guardar"){_,_->
                    if(clinicalPrefs.edit().putString("observation_number",
                        previous.text.toString().trim().take(100)).commit())redraw()
                    else message("Não foi possível guardar o número antigo.")
                }.show()
        })
'''
src=src[:begin]+new_ui+src[end:]
p.write_text(src,encoding="utf-8")

# Keep original photographic background in dark and light modes.
artwork={
    "CareHomeActivity.kt":(
      '            setBackgroundColor(if(dark)Color.rgb(9,25,34) else Color.rgb(242,248,250))',
      "CareHomeActivity",
      "Color.rgb(9,25,34)",
      "Color.rgb(242,248,250)"
    ),
    "MonthlyCalendarActivity.kt":(
      '            setBackgroundColor(if(dark)Color.rgb(5,22,32)else Color.rgb(246,249,251))',
      "MonthlyCalendarActivity",
      "Color.rgb(5,22,32)",
      "Color.rgb(246,249,251)"
    )
}
for name,(old,klass,dark,light) in artwork.items():
    replacement=f'''            // Same official SaúdePrática backdrop as Situação Clínica.
            val official=androidx.core.content.ContextCompat.getDrawable(
                this@{klass},R.drawable.saude_background)?.mutate()
            if(official is android.graphics.drawable.BitmapDrawable)
                official.gravity=Gravity.FILL
            background=if(official!=null)android.graphics.drawable.LayerDrawable(
                arrayOf(official,android.graphics.drawable.ColorDrawable(
                    if(dark)Color.argb(105,0,12,20)
                    else Color.argb(215,245,249,250))))
                else android.graphics.drawable.ColorDrawable(if(dark){dark} else {light})'''
    replace_exact(base/name,old,replacement,"official backdrop "+name)

# Payment target unchanged; author-support copy and icon become coffee.
coffee_changed=0
for file in base.rglob("*.kt"):
    before=file.read_text(encoding="utf-8")
    if "PayPal" not in before and "Apoiar o autor" not in before:
        continue
    after=(before.replace("uma cerveja","um café")
        .replace("Uma cerveja","Um café")
        .replace("cerveja","café")
        .replace("Cerveja","Café")
        .replace("🍺","☕"))
    if after!=before:
        coffee_changed+=1
        file.write_text(after,encoding="utf-8")
assert coffee_changed>0,"PayPal coffee labels not found in application"

# Help must be updated when module interactions change.
helpfile=base/"SupportHelpActivity.kt"
help=helpfile.read_text(encoding="utf-8")
anchor="        val shortcutGuide=panel()"
assert help.count(anchor)==1,("help clinical guide anchor",help.count(anchor))
help=help.replace(anchor,'''        val numbersGuide=panel()
        numbersGuide.addView(text(tr(
            "🏥 Situação Clínica · Números",
            "🏥 Clinical records · Numbers",
            "🏥 Situation clinique · Numéros",
            "🏥 Klinische Daten · Nummern",
            "🏥 Situación clínica · Números"),18f))
        numbersGuide.addView(text(tr(
            "Abre Situação Clínica → Editar números clínicos. Adiciona vários registos, mesmo do mesmo hospital, e edita ou elimina cada um separadamente. O número antigo permanece guardado no perfil.",
            "Open Clinical records to add, edit or delete individual reference numbers. Older numbers remain saved to the patient profile.",
            "Ouvrez Situation clinique pour ajouter, modifier ou supprimer chaque numéro. Les anciennes références restent enregistrées.",
            "Öffne Klinische Daten, um Referenznummern einzeln hinzuzufügen, zu ändern oder zu löschen. Alte Nummern bleiben gespeichert.",
            "Abre Situación clínica para añadir, editar o eliminar cada número. Los números antiguos se conservan."),14f,muted))
        addCard(parent,numbersGuide)
'''+anchor,1)
helpfile.write_text(help,encoding="utf-8")

gradle=root/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count('versionCode = 114')==1 and g.count('versionName = "1.9.104"')==1
gradle.write_text(g.replace('versionCode = 114','versionCode = 115')
  .replace('versionName = "1.9.104"','versionName = "1.9.105"'),encoding="utf-8")
print("SaúdePrática 1.9.105: individual clinical records, original backgrounds and coffee.")
