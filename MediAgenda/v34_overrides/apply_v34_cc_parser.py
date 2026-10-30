from pathlib import Path

ocr=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/ocr/ProfileCitizenCardOcr.kt")
s=ocr.read_text(encoding="utf-8")
def change(old,new,label):
    global s
    if old not in s:raise RuntimeError("v1.9.15 OCR: "+label)
    s=s.replace(old,new,1)

old='''        if(first!=null){
            val id=first.substring(5,14)
            if(checkDigit(id)==first[14])fields["cc_number"]=id.trimEnd('<')
        }'''
new='''        if(first!=null){
            // On this Portuguese layout, the ICAO line normally reads
            // I<PRT + 8 ID digits + civil check digit + optional <
            // + three alphanumeric suffix characters.
            // The previous nine-character checksum check rejected this
            // layout, so correctly read card numbers disappeared.
            val digits=first.substring(5,13)
            val check=first.getOrNull(13)
            val suffix=Regex("""^<?([A-Z0-9]{3})""")
                .find(first.substring(14))?.groupValues?.get(1)
            if(digits.all(Char::isDigit) && check?.isDigit()==true &&
                suffix!=null && suffix.any{it!='<'}) {
                fields["cc_number"]="$digits $check $suffix"
            }
        }'''
change(old,new,"MRZ document number format")

old='''        add("cc_number","Número do CC",printedCc ?: frontCc ?: mrz["cc_number"])'''
new='''        // Some OCR engines insert spaces between ZX9 suffix characters.
        val splitCc=Regex("""(?<!\\d)(\\d{8})\\s*(\\d)\\s*([A-Z]\\s*[A-Z0-9]\\s*[A-Z0-9])(?![A-Z0-9])""")
            .find(canonical(frontText))?.let {
                it.groupValues[1]+" "+it.groupValues[2]+" "+
                    it.groupValues[3].replace(" ","")
            }
        add("cc_number","Número do CC",
            printedCc ?: frontCc ?: splitCc ?: mrz["cc_number"])'''
change(old,new,"CC front split characters")

start=s.index('''        val filiationIndex=back.indexOfFirst''')
end=s.index('''        val numbers=groupedBackNumbers(back)''',start)
newParents='''        val filiationIndex=back.indexOfFirst{ row ->
            val n=canonical(row)
            n.contains("FILIACAO") || n.contains("FILIAC") ||
                n.contains("PARENTS") || n.contains("PARENT")
        }
        val numberHeader=back.indexOfFirst{ row ->
            val n=canonical(row)
            n.contains("IDENTIFICACAO FISCAL") || n.contains("SEGURANCA SOCIAL") ||
                n.contains("UTENTE DE SAUDE") ||
                (n.contains("FISCAL")&&n.contains("SOCIAL"))
        }
        // Restrict the parent names to the zone before the number row.
        // The cropped OCR pass intentionally adds a FILIACAO header and
        // an IDENTIFICACAO FISCAL footer to make this boundary reliable.
        val areaStart=if(filiationIndex>=0)filiationIndex+1
            else if(numberHeader>0)(numberHeader-3).coerceAtLeast(0)
            else -1
        val areaEnd=if(numberHeader>=0)numberHeader else back.size
        val lines=if(areaStart>=0 && areaEnd>areaStart)
            back.subList(areaStart,areaEnd).take(4)
        else emptyList()
        fun cleanParent(text:String)=text
            .replace(Regex("""(?i)(FILIACAO|PARENTS|NOME DO PAI|NOME DA MAE)\\s*[:/]*"""),"")
            .replace(Regex("""\\s+""")," ").trim()
        fun parentName(value:String)=
            value.length in 6..110 && value.count(Char::isLetter)>=6 &&
            value.none(Char::isDigit) &&
            listOf("CARTAO","PORTUGAL","IDENTIFICACAO","NACIONALIDADE",
                "NOME DO","FISCAL","SEGURANCA","UTENTE")
                .none{canonical(value).contains(it)}
        var father=cleanParent(nextValue(back,listOf("NOME DO PAI","FATHER NAME","PAI:")))
        var mother=cleanParent(nextValue(back,listOf("NOME DA MAE","MOTHER NAME","MAE:")))
        val delimit=Regex("""\\s*[•·*|]\\s*""")
        val marker=lines.indexOfFirst{delimit.containsMatchIn(it)}
        if(marker>=0){
            val raw=delimit.split(lines[marker],limit=2)
            if(raw.size==2){
                val one=cleanParent(raw[0])
                val otherLines=lines.drop(marker+1)
                    .takeWhile{it.any(Char::isLetter)&&it.none(Char::isDigit)}
                    .take(2).joinToString(" ")
                val two=cleanParent((raw[1]+" "+otherLines).trim())
                if(parentName(one))father=one
                if(parentName(two))mother=two
            }
        }else if(lines.size>=2){
            // Two separate OCR rows with no visible bullet.
            val firstParent=cleanParent(lines[0])
            val secondParent=cleanParent(lines.drop(1).take(2).joinToString(" "))
            if(parentName(firstParent)&&parentName(secondParent)){
                father=firstParent;mother=secondParent
            }
        }
        if(parentName(father))add("father_name","Nome do pai",father)
        if(parentName(mother))add("mother_name","Nome da mãe",mother)
'''
s=s[:start]+newParents+s[end:]
ocr.write_text(s,encoding="utf-8")
print("Portuguese CC OCR: correct MRZ number layout, split suffix recognition and multiline parent extraction.")
