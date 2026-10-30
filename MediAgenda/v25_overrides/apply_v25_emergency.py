from pathlib import Path
source=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
f=source/"data/PersonalHealthStore.kt"
s=f.read_text(encoding="utf-8")
old='''        val permitted = setOf("contact_name", "contact_phone", "second_contact", "allergies",
            "conditions", "notes", "blood_group")'''
new='''        val permitted = setOf("contact_name", "contact_phone", "second_contact", "allergies",
            "conditions", "chronic_conditions", "notes", "blood_group")'''
assert old in s, "Emergency fields whitelist anchor missing"
f.write_text(s.replace(old,new,1),encoding="utf-8")

f=source/"HealthRecordsActivity.kt";s=f.read_text(encoding="utf-8")
def edit(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.6 emergency missing "+label)
 s=s.replace(old,new,1)
edit('''            "allergies" to "Alergias conhecidas",
            "conditions" to "Informações médicas relevantes",''',
'''            "allergies" to "Alergias conhecidas",
            "chronic_conditions" to "Doenças crónicas",
            "conditions" to "Informações médicas relevantes",''',
"chronic condition field")

edit('''        val fields=entries.map{(key,caption,initial)->
            box.addView(label(caption,13f,true,Color.rgb(15,100,95)))''',
'''        val fields=entries.map{(key,caption,initial)->
            box.addView(label(caption,13f,true,
                if(dark)Color.rgb(128,238,225) else Color.rgb(3,105,99)))''',
"dialog accessible captions")

edit('''                setText(initial);textSize=15f;setTextColor(Color.rgb(20,40,51))
                setSingleLine(key !in setOf("details","notes","allergies","conditions"))
                box.addView(this)''',
'''                setText(initial);textSize=15f
                setTextColor(if(dark)Color.rgb(244,249,251) else Color.rgb(19,38,51))
                setHintTextColor(if(dark)Color.rgb(185,199,207) else Color.rgb(90,108,119))
                backgroundTintList=ColorStateList.valueOf(
                    if(dark)Color.rgb(116,219,207) else Color.rgb(4,120,111))
                setSingleLine(key !in setOf("details","notes","allergies",
                    "chronic_conditions","conditions"))
                box.addView(this)''',
"form text and input contrast")

edit('''        heads.addView(label("$icon  $title",25f,true))''',
'''        heads.addView(label("$icon  $title",if(category=="emergency")21f else 24f,true))''',
"long emergency header sizing")
f.write_text(s,encoding="utf-8")
print("v1.9.6: chronic conditions and legible dark/light emergency+health record forms.")
