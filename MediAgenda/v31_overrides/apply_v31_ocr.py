from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
ocr=root/"app/src/main/java/com/mediagenda/app/ocr/ProfileCitizenCardOcr.kt"
s=ocr.read_text(encoding="utf-8")
def edit(old,new,label):
    global s
    if old not in s:raise RuntimeError("SaúdePrática v1.9.12 OCR missing "+label)
    s=s.replace(old,new,1)

# Some actual OCR readings split the header labels into columns but print
# their 9 / 11 / 9-digit values in one horizontal row.
edit('''        val old=CitizenCardOcrParser.parse(lines.joinToString("\\n"))
        return Triple(old.nif.takeIf(CitizenCardOcrParser::validNif),
            labelledNumber(lines,listOf("SEGURANCA SOCIAL","NISS"),11),
            old.snsNumber.takeIf{it.matches(Regex("""\\d{9}"""))})''',
'''        val old=CitizenCardOcrParser.parse(lines.joinToString("\\n"))
        // If the three numbers survive OCR but their pale headings do not,
        // use the unique NIF checksum and the unique 11-digit NISS, then
        // offer all three for user confirmation (never auto-save).
        val beforeMrz=lines.takeWhile { !canonical(it).startsWith("I<PRT") }
        val raw=beforeMrz.joinToString(" ")
        val chunks=Regex("""(?<![A-Z0-9])(?:\\d[ -]?){8,10}\\d(?![A-Z0-9])""")
            .findAll(canonical(raw)).map { it.value.filter(Char::isDigit) }
            .filter { it.length==9 || it.length==11 }.distinct().toList()
        val nine=chunks.filter { it.length==9 }
        val eleven=chunks.filter { it.length==11 }
        val validNifs=nine.filter(CitizenCardOcrParser::validNif)
        val nif=old.nif.takeIf(CitizenCardOcrParser::validNif)
            ?:validNifs.singleOrNull()
        val niss=labelledNumber(lines,listOf("SEGURANCA SOCIAL","NISS"),11)
            ?:eleven.singleOrNull()
        val sns=old.snsNumber.takeIf{it.matches(Regex("""\\d{9}"""))}
            ?:if(nine.size==2 && nif!=null)nine.singleOrNull{it!=nif}else null
        return Triple(nif,niss,sns)''',
"back 3-column fallback")

# OCR may split the label from the value, so scan the card front for its
# explicit 8-digit / check / 3-character visible document reference.
edit('''        add("cc_number","Número do CC",printedCc ?: mrz["cc_number"])''',
'''        val frontCc=Regex("""(?<!\\d)(\\d{8})\\s*(\\d)\\s*([A-Z0-9]{3})(?![A-Z0-9])""")
            .find(canonical(frontText))?.let {
                it.groupValues[1]+" "+it.groupValues[2]+" "+it.groupValues[3]
            }
        add("cc_number","Número do CC",printedCc ?: frontCc ?: mrz["cc_number"])''',
"visible CC reference")

edit('''        val heightMatch=Regex("""\\b([1-2])[.,]?(\\d{2})\\b""").find(height)''',
'''        val heightMatch=Regex("""\\b([1-2])[.,]?(\\d{2})\\b""").find(height)
            ?:Regex("""\\b([1-2])[.,](\\d{2})\\b""").find(canonical(frontText))''',
"height in combined row")

edit('''        val father=nextValue(back,listOf("NOME DO PAI","FATHER NAME","PAI:"))
        val mother=nextValue(back,listOf("NOME DA MAE","MOTHER NAME","MAE:"))
        if(plausibleName(father)) add("father_name","Nome do pai",father)
        if(plausibleName(mother)) add("mother_name","Nome da mãe",mother)''',
'''        val filiationIndex=back.indexOfFirst { row ->
            val n=canonical(row)
            n.contains("FILIACAO") || n.contains("PARENTS")
        }
        var father=nextValue(back,listOf("NOME DO PAI","FATHER NAME","PAI:"))
        var mother=nextValue(back,listOf("NOME DA MAE","MOTHER NAME","MAE:"))
        if(filiationIndex>=0 && (father.isBlank() || mother.isBlank())){
            val lines=back.drop(filiationIndex+1)
                .takeWhile{ row ->
                    val n=canonical(row)
                    !n.startsWith("I<PRT") &&
                    !n.contains("IDENTIFICACAO FISCAL") &&
                    !n.contains("SEGURANCA SOCIAL") &&
                    !n.contains("UTENTE DE SAUDE")
                }.take(3)
            val joined=lines.joinToString(" ").trim()
            val segments=joined.split(Regex("""\\s*[•·*]\\s*"""),limit=2)
            if(segments.size==2){
                if(father.isBlank())father=segments[0]
                if(mother.isBlank())mother=segments[1]
            }
        }
        if(plausibleName(father)) add("father_name","Nome do pai",father)
        if(plausibleName(mother)) add("mother_name","Nome da mãe",mother)''',
"parent names from reverse side with bullet separator")

ocr.write_text(s,encoding="utf-8")
print("CC OCR revised: visible document number, back IDs by length/checksum, height and parentage.")
