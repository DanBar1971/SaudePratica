from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
source=root/"app/src/main/java/com/mediagenda/app"
parentage=source/"ocr/CitizenCardParentage.kt"
parentage.write_text(
    Path("MediAgenda/v35_overrides/CitizenCardParentage.kt").read_text(encoding="utf-8"),
    encoding="utf-8")

parser=source/"ocr/ProfileCitizenCardOcr.kt"
s=parser.read_text(encoding="utf-8")
old='''        val numbers=groupedBackNumbers(back)
        add("nif","NIF",numbers.first)'''
new='''        // More robust second pass for parentage on Portuguese CC backs:
        // accepts a bullet, a dash, a line wrap and an omitted separator.
        // Unlike earlier code it handles an entire OCR line after FILIAÇÃO.
        val parentage=CitizenCardParentage.parse(backText)
        parentage.father?.let {
            list["father_name"]=Proposed("father_name","Nome do pai",it)
        }
        parentage.mother?.let {
            list["mother_name"]=Proposed("mother_name","Nome da mãe",it)
        }
        val numbers=groupedBackNumbers(back)
        add("nif","NIF",numbers.first)'''
assert s.count(old)==1, "Missing parser insertion anchor"
parser.write_text(s.replace(old,new,1),encoding="utf-8")

gallery=source/"ProfileMediaActivity.kt"
s=gallery.read_text(encoding="utf-8")
old='''                    val x=if(side=="cc_back")0.12f else 0.26f
                    val y=if(side=="cc_back")0.13f else 0.48f
                    val width=if(side=="cc_back")0.82f else 0.53f
                    val height=if(side=="cc_back")0.31f else 0.32f'''
new='''                    // Back: crop tightly around FILIAÇÃO and BOTH lines
                    // of parent names, excluding the logo and number row.
                    // This helps ML Kit retain short dot/bullet separators.
                    val x=if(side=="cc_back")0.18f else 0.26f
                    val y=if(side=="cc_back")0.20f else 0.48f
                    val width=if(side=="cc_back")0.78f else 0.53f
                    val height=if(side=="cc_back")0.25f else 0.32f'''
assert s.count(old)==1, "Missing OCR cropping anchor"
gallery.write_text(s.replace(old,new,1),encoding="utf-8")

main=source/"MainActivity.kt"
s=main.read_text(encoding="utf-8")
old='''        box.addView(noteBox("Dados do perfil", "O NIF e o número de utente são opcionais. O Cartão de Cidadão é lido localmente e a fotografia é eliminada após o OCR. Confirme os números antes de guardar."))
'''
assert s.count(old)==1, "Missing outdated Dados do perfil note card"
main.write_text(s.replace(old,"",1),encoding="utf-8")

gradle=root/"app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in s
assert 'versionCode = 25' in s and 'versionName = "1.9.15"' in s
gradle.write_text(
    s.replace('versionCode = 25','versionCode = 26',1)
     .replace('versionName = "1.9.15"','versionName = "1.9.16"',1),
    encoding="utf-8")
print("v1.9.16: multiline parent names OCR, refined card back region; remove outdated Dados do perfil note, same application ID.")
