package com.mediagenda.app.ocr

import java.text.Normalizer
import java.util.Locale

/**
 * Portuguese Citizen Card filiation parser. OCR values are only suggestions:
 * the user must confirm each parent name before it is stored in their profile.
 */
object CitizenCardParentage {
    data class Names(val father:String?, val mother:String?)

    private fun fold(value:String):String=Normalizer.normalize(
        value.uppercase(Locale.ROOT),Normalizer.Form.NFD
    ).replace(Regex("""\p{Mn}+"""),"")
        .replace(Regex("""\s+""")," ").trim()

    private val header=Regex("""(?i)\b(?:FILI[AÃAÇC]{1,5}O|FILIACAO|PARENTS?|PARENTES)\b(?:\s*[/|:]\s*(?:PARENTS?|PARENTES))?\s*[:\-–—]?\s*""")
    private val boundary=Regex("""(?i)(?:IDENTIFICA(?:Ç|C)[AÃA]O\s+FISCAL|FISCAL\s*(?:NO|N[.º°])|SEGURAN(?:Ç|C)A\s+SOCIAL|UTENTE\s+DE\s+SA(?:Ú|U)DE|TAX\s*NO\b|SOCIAL\s+SECURITY|HEALTH\s+NO\b)""")
    private val separator=Regex("""\s*[•·●*|¦]\s*|\s+[–—-]\s+""")
    private val motherLead=Regex("""\b(?:MARIA|ANA|ISABEL|TERESA|LUISA|LUIZA|HELENA|JOANA|CATARINA|CARLA|ROSA|FATIMA|FÁTIMA|LAURA|SOFIA|SUSANA|PAULA|ELSA|LURDES|MARLENE|FERNANDA|SARA)\b""")
    private val extraneous=Regex("""(?i)(?:CART[AÃA]O\s+DE\s+CIDAD[AÃA]O|PORTUGAL|CITIZEN\s+CARD|DOCUMENT\s+NO|NACIONALIDADE|PARENTS?|FILIA(?:Ç|C)[AÃA]O|DADOS|ASSINATURA|NUMERO|N[.º°]\s*DOC)""")

    private fun clean(source:String):String=source
        .replace(Regex("""[\t\u00a0]+""")," ")
        .replace(Regex("""\s+""")," ").trim()
        .trim(' ','*','•','·','|','-','–','—','/',':').trim()

    private fun reasonable(candidate:String?):Boolean{
        if(candidate.isNullOrBlank())return false
        val text=fold(candidate)
        if(text.length !in 8..105 || text.any(Char::isDigit))return false
        if(text.split(" ").count{it.length>=2}<2)return false
        if(extraneous.containsMatchIn(text))return false
        return text.all{it.isLetter() || it in " '-."}
    }

    private fun withoutHeading(source:String):String{
        var value=source.trim()
        repeat(3){
            val found=header.find(value)
            if(found!=null && found.range.first<=6)
                value=value.substring(found.range.last+1).trim()
        }
        return clean(value)
    }

    fun parse(raw:String):Names{
        val rows=raw.lines().map(String::trim).filter(String::isNotEmpty)
        if(rows.isEmpty())return Names(null,null)
        val position=rows.indexOfFirst {
            val normalized=fold(it)
            normalized.contains("FILIAC") || normalized.contains("FILIAÇ") ||
                normalized.contains("PARENTS")
        }
        // Do not reinterpret the holder's name or MRZ as parent names.
        if(position<0)return Names(null,null)
        val first=withoutHeading(rows[position])
        val area=buildList{
            if(first.isNotBlank())add(first)
            for(i in position+1 until rows.size){
                val row=rows[i]
                if(boundary.containsMatchIn(fold(row)) ||
                    fold(row).startsWith("I<PRT") ||
                    fold(row).startsWith("PORTUGAL") ||
                    Regex("""\b\d{8,11}\b""").containsMatchIn(row))break
                if(row.any(Char::isLetter))add(withoutHeading(row))
                if(size>=4)break
            }
        }.filter(String::isNotBlank)
        if(area.isEmpty())return Names(null,null)
        val joined=area.joinToString(" ")
        // Real cards print father * mother; OCR may output •, ·, | or a dash.
        val division=separator.find(joined)
        if(division!=null){
            val father=clean(joined.substring(0,division.range.first))
            val mother=clean(joined.substring(division.range.last+1))
            return Names(father.takeIf(::reasonable),mother.takeIf(::reasonable))
        }
        // When ML Kit drops the tiny separator, split before an obvious
        // second Portuguese given name. These remain user-reviewed proposals.
        val normalized=fold(joined)
        val nameStart=motherLead.findAll(normalized).firstOrNull {
            val a=normalized.substring(0,it.range.first)
            val b=normalized.substring(it.range.first)
            a.trim().split(" ").count{word->word.length>=2}>=2 &&
                b.trim().split(" ").count{word->word.length>=2}>=2
        }
        if(nameStart!=null){
            val father=clean(joined.substring(0,nameStart.range.first))
            val mother=clean(joined.substring(nameStart.range.first))
            return Names(father.takeIf(::reasonable),mother.takeIf(::reasonable))
        }
        if(area.size>=2 && reasonable(area[0]) &&
            reasonable(area.drop(1).joinToString(" "))){
            return Names(clean(area[0]),clean(area.drop(1).joinToString(" ")))
        }
        return Names(null,null)
    }
}
