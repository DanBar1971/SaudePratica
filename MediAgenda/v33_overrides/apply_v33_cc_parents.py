from pathlib import Path

ocr=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/ocr/ProfileCitizenCardOcr.kt")
s=ocr.read_text(encoding="utf-8")
start=s.index("        val filiationIndex=back.indexOfFirst")
end=s.index("        val numbers=groupedBackNumbers(back)",start)
s=s[:start]+'''        // Old CC back layout: FILIAÇÃO / PARENTS, then the two parents
        // separated by a bullet or asterisk. The mother's name often
        // continues on a second OCR line. This is NOT a single-line field.
        val filiationIndex=back.indexOfFirst { row ->
            val n=canonical(row)
            n.contains("FILIACAO") || n.contains("FILIAC") || n.contains("PARENTS")
        }
        val numberHeader=back.indexOfFirst { row ->
            val n=canonical(row)
            n.contains("IDENTIFICACAO FISCAL") || n.contains("SEGURANCA SOCIAL") ||
                n.contains("UTENTE DE SAUDE") ||
                (n.contains("FISCAL") && n.contains("SOCIAL"))
        }
        val candidates=when {
            filiationIndex>=0 -> back.drop(filiationIndex+1)
            numberHeader>1 -> back.take(numberHeader).takeLast(4)
            else -> emptyList()
        }.takeWhile { row ->
            val n=canonical(row)
            !n.startsWith("I<PRT") && !n.contains("IDENTIFICACAO FISCAL") &&
                !n.contains("SEGURANCA SOCIAL") && !n.contains("UTENTE DE SAUDE") &&
                !n.contains("HEALTH NO")
        }.take(4)
        fun cleanParent(value:String):String=
            value.trim().replace(Regex("""\s+""")," ")
                .replace(Regex("""(?i)^(PAI|MAE|FATHER|MOTHER)\s*[:.]\s*"""),"")
                .trim()
        var father=nextValue(back,listOf("NOME DO PAI","FATHER NAME","PAI:"))
        var mother=nextValue(back,listOf("NOME DA MAE","MOTHER NAME","MAE:"))
        val divider=Regex("""\s*[•·*|]\s*""")
        val pivot=candidates.indexOfFirst { row ->
            divider.containsMatchIn(row) && row.any(Char::isLetter)
        }
        if(pivot>=0) {
            val pieces=divider.split(candidates[pivot],limit=2)
            if(pieces.size==2) {
                val parentOne=cleanParent(pieces[0])
                val motherBase=cleanParent(pieces[1])
                val follow=candidates.drop(pivot+1)
                    .takeWhile { it.none(Char::isDigit) && !divider.containsMatchIn(it) }
                    .take(2).joinToString(" ")
                val parentTwo=cleanParent((motherBase+" "+follow).trim())
                if(plausibleName(parentOne))father=parentOne
                if(plausibleName(parentTwo))mother=parentTwo
            }
        } else if(candidates.size>=2) {
            // Two separate labelled lines are also possible.
            val one=cleanParent(candidates[0])
            val two=cleanParent(candidates.drop(1).joinToString(" "))
            if(plausibleName(one) && plausibleName(two)){
                father=one
                mother=two
            }
        }
        if(plausibleName(father)) add("father_name","Nome do pai",father)
        if(plausibleName(mother)) add("mother_name","Nome da mãe",mother)
''' +s[end:]
ocr.write_text(s,encoding="utf-8")
print("CC back OCR: parentage parsed from two sides of bullet, including wrapped mother name.")
