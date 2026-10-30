package com.mediagenda.app.ocr

import java.text.Normalizer
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.ResolverStyle
import java.util.Locale

/** OCR proposals, never committed without the user's explicit confirmation. */
object ProfileCitizenCardOcr {
    data class Proposed(val key:String,val label:String,val value:String)
    private val dateRe=Regex("""(?<!\d)(\d{2})[./\- ](\d{2})[./\- ](\d{4})(?!\d)""")
    private val isoRe=Regex("""(?<!\d)(\d{4})[./\-](\d{2})[./\-](\d{2})(?!\d)""")
    private val numeric=Regex("""(?<!\d)\d[\d .-]{7,20}\d(?!\d)""")
    private val numberCC=Regex("""\b\d{8}[A-Z0-9]{1,4}\b""")

    private fun canonical(t:String):String =
        Normalizer.normalize(t.uppercase(Locale.ROOT),Normalizer.Form.NFD)
            .replace(Regex("""\p{Mn}+"""),"").replace(Regex("""\s+""")," ").trim()
    private fun rows(t:String)=t.lines().map{it.trim()}.filter{it.isNotBlank()}

    private fun nextValue(lines:List<String>,tags:List<String>):String {
        for(i in lines.indices){
            if(tags.none{canonical(lines[i]).contains(it)})continue
            val split=lines[i].split(":",limit=2)
            if(split.size==2&&split[1].isNotBlank())return split[1].trim()
            for(j in i+1..minOf(i+2,lines.lastIndex)){
                val n=canonical(lines[j])
                if(n.isBlank())continue
                if(n.startsWith("APELIDO")||n.startsWith("NOME(S)")||
                    n.startsWith("DATA DE ")||n.startsWith("NACIONALIDADE")||
                    n.startsWith("VALIDADE")||n.startsWith("SEXO")||
                    n.startsWith("IDENTIFICACAO")||n.startsWith("SEGURANCA SOCIAL"))
                    break
                return lines[j].trim()
            }
        }
        return ""
    }
    private fun readDate(value:String):String? {
        val match=dateRe.find(value)
        val iso=isoRe.find(value)
        val normalized=when{
            match!=null -> "${match.groupValues[1]}/${match.groupValues[2]}/${match.groupValues[3]}"
            iso!=null -> "${iso.groupValues[3]}/${iso.groupValues[2]}/${iso.groupValues[1]}"
            else->return null
        }
        return runCatching{
            LocalDate.parse(normalized,
                DateTimeFormatter.ofPattern("dd/MM/uuuu").withResolverStyle(ResolverStyle.STRICT))
            normalized
        }.getOrNull()
    }
    private fun labelledDate(lines:List<String>,tags:List<String>):String?{
        for(i in lines.indices){
            if(tags.none{canonical(lines[i]).contains(it)})continue
            for(j in i..minOf(i+2,lines.lastIndex))readDate(lines[j])?.let{return it}
        }
        return null
    }
    private fun labelledNumber(lines:List<String>,tags:List<String>,length:Int):String? {
        for(i in lines.indices){
            if(tags.none{canonical(lines[i]).contains(it)})continue
            for(j in i..minOf(i+2,lines.lastIndex)){
                if(j>i&&listOf("IDENTIFICACAO FISCAL","SEGURANCA SOCIAL",
                    "UTENTE DE SAUDE").any{canonical(lines[j]).contains(it)})break
                for(match in numeric.findAll(lines[j])){
                    val digits=match.value.filter(Char::isDigit)
                    if(digits.length==length)return digits
                }
            }
        }
        return null
    }

    // Read the ICAO TD1 machine-readable lines from the reverse side.
    // Numeric fields are accepted only when their official check digit matches.
    private fun checkDigit(input:String):Char {
        val weights=intArrayOf(7,3,1)
        val result=input.withIndex().sumOf { (i,ch) ->
            val value=when(ch){
                in '0'..'9'->ch-'0'
                in 'A'..'Z'->ch-'A'+10
                '<'->0
                else->return 'X'
            }
            value*weights[i%3]
        }
        return ('0'.code+result%10).toChar()
    }
    private fun dateFromMrz(part:String,birth:Boolean):String? {
        if(part.length!=6||!part.all(Char::isDigit))return null
        val current=LocalDate.now()
        val year=2000+part.take(2).toInt()
        val y=if(birth&&year>current.year)year-100 else year
        if(!birth&&(y<current.year-20||y>current.year+35))return null
        val parsed=runCatching {
            LocalDate.of(y,part.substring(2,4).toInt(),part.substring(4,6).toInt())
        }.getOrNull()?:return null
        if(birth&&(parsed.isAfter(current)||parsed.isBefore(current.minusYears(120))))return null
        return parsed.format(DateTimeFormatter.ofPattern("dd/MM/uuuu"))
    }
    private fun mrz(raw:String):Map<String,String> {
        val lines=rows(raw).map{ canonical(it).replace(Regex("""[^A-Z0-9<]"""),"") }
        val first=lines.firstOrNull{it.startsWith("I<PRT")&&it.length>=15}
        val second=lines.firstOrNull {
            it.length>=18&&it.take(6).all(Char::isDigit)&&it[7] in "MFX<"&&
                it.substring(8,14).all(Char::isDigit)
        }
        val third=lines.firstOrNull{it.length>=18 && it.contains("<<") &&
            !it.startsWith("I<PRT") && it.takeWhile{c->c!='<'}.all{c->c in 'A'..'Z'}}
        val fields=linkedMapOf<String,String>()
        if(first!=null){
            val id=first.substring(5,14)
            if(checkDigit(id)==first[14])fields["cc_number"]=id.trimEnd('<')
        }
        if(second!=null){
            val dob=second.substring(0,6)
            val expires=second.substring(8,14)
            if(checkDigit(dob)==second[6])
                dateFromMrz(dob,true)?.let{fields["birth_date"]=it}
            if(checkDigit(expires)==second[14])
                dateFromMrz(expires,false)?.let{fields["cc_valid_until"]=it}
            when(second[7]) {
                'F'->fields["gender"]="Feminino"
                'M'->fields["gender"]="Masculino"
            }
            if(second.substring(15,18)=="PRT")fields["nationality"]="Portuguesa"
        }
        if(third!=null){
            val names=third.split("<<",limit=2)
            if(names.size==2){
                val firstNames=names[1].replace('<',' ').trim()
                val lastNames=names[0].replace('<',' ').trim()
                if(firstNames.length>=3&&lastNames.length>=3)
                    fields["full_name"]=firstNames+" "+lastNames
            }
        }
        return fields
    }
    private fun groupedBackNumbers(lines:List<String>):Triple<String?,String?,String?> {
        val rowIndex=lines.indexOfFirst{
            val n=canonical(it)
            listOf("IDENTIFICACAO FISCAL","SEGURANCA SOCIAL","UTENTE DE SAUDE")
                .count { tag->n.contains(tag) } >= 2
        }
        if(rowIndex>=0){
            val next=lines.drop(rowIndex+1).take(4)
                .takeWhile{!canonical(it).startsWith("I<PRT")}.joinToString(" ")
            val m=Regex("""(?<!\d)(\d{9})\s+(\d{11})\s+(\d{9})(?!\d)""")
                .find(next)
            if(m!=null)return Triple(m.groupValues[1].takeIf(CitizenCardOcrParser::validNif),
                m.groupValues[2],m.groupValues[3])
        }
        val old=CitizenCardOcrParser.parse(lines.joinToString("\n"))
        return Triple(old.nif.takeIf(CitizenCardOcrParser::validNif),
            labelledNumber(lines,listOf("SEGURANCA SOCIAL","NISS"),11),
            old.snsNumber.takeIf{it.matches(Regex("""\d{9}"""))})
    }

    fun propose(frontText:String,backText:String):List<Proposed>{
        val front=rows(frontText)
        val back=rows(backText)
        val list=linkedMapOf<String,Proposed>()
        val mrz=mrz(backText)
        fun add(key:String,label:String,value:String?){
            if(!value.isNullOrBlank())list[key]=Proposed(key,label,value.trim())
        }
        fun plausibleName(s:String)=s.length in 2..90&&s.any(Char::isLetter)&&
            s.none(Char::isDigit)&&canonical(s) !in setOf(
                "NACIONALIDADE","NATIONALITY","SEXO","VALIDADE","PORTUGAL",
                "APELIDO(S)","SURNAME","NOME(S)","GIVEN NAME")
        val surname=nextValue(front,listOf("APELIDO(S)","APELIDOS","SURNAME"))
        val given=nextValue(front,listOf("NOME(S)","GIVEN NAME"))
        if(plausibleName(surname)&&plausibleName(given))
            add("full_name","Nome completo","$given $surname")
        else add("full_name","Nome completo",mrz["full_name"])
        add("birth_date","Data de nascimento",mrz["birth_date"] ?: labelledDate(front,listOf(
            "DATA DE NASCIMENTO","DATE OF BIRTH","NASCIMENTO")))
        add("cc_valid_until","Validade do CC",mrz["cc_valid_until"] ?: labelledDate(front,listOf(
            "VALIDADE","EXPIRY DATE")))
        val sex=canonical(nextValue(front,listOf("SEXO","SEX")))
        add("gender","Género",mrz["gender"] ?: when{
            sex=="F"||sex.startsWith("F ")||sex=="FEMININO"->"Feminino"
            sex=="M"||sex.startsWith("M ")||sex=="MASCULINO"->"Masculino"
            else->null
        })
        val cc=nextValue(front,listOf("DOCUMENTO","DOCUMENT NO","DOC. N"))
        val printedCc=Regex("""(?<!\d)(\d{8})\s*(\d)\s*([A-Z0-9]{3})(?![A-Z0-9])""")
            .find(canonical(cc))?.let {
                it.groupValues[1]+" "+it.groupValues[2]+" "+it.groupValues[3]
            }
        add("cc_number","Número do CC",printedCc ?: mrz["cc_number"])
        // The Portuguese card may show nationality, height and family lineage.
        // Extract only explicitly labelled values; never infer missing content.
        val nationality=canonical(nextValue(front,listOf("NACIONALIDADE","NATIONALITY")))
        add("nationality","Nacionalidade",mrz["nationality"] ?:
            if(Regex("""\bPRT\b""").containsMatchIn(nationality)||nationality=="PORTUGUESA")
                "Portuguesa" else null)
        val height=nextValue(front,listOf("ALTURA","HEIGHT"))
        val heightMatch=Regex("""\b([1-2])[.,]?(\d{2})\b""").find(height)
        val cm=heightMatch?.let {
            val number=it.groupValues[1].toInt()*100+it.groupValues[2].toInt()
            number.takeIf{h->h in 100..240}?.toString()
        }
        add("height_cm","Altura (cm)",cm)
        val birthPlace=nextValue(front+back,listOf("NATURALIDADE","LOCAL DE NASCIMENTO","PLACE OF BIRTH"))
        if(birthPlace.length in 3..100 && birthPlace.none(Char::isDigit))
            add("birth_place","Naturalidade",birthPlace)
        val father=nextValue(back,listOf("NOME DO PAI","FATHER NAME","PAI:"))
        val mother=nextValue(back,listOf("NOME DA MAE","MOTHER NAME","MAE:"))
        if(plausibleName(father)) add("father_name","Nome do pai",father)
        if(plausibleName(mother)) add("mother_name","Nome da mãe",mother)
        val numbers=groupedBackNumbers(back)
        add("nif","NIF",numbers.first)
        add("sns_number","Número de utente SNS",numbers.third)
        add("niss","NISS",numbers.second)
        return list.values.toList()
    }
}
