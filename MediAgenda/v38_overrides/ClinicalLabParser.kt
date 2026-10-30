package com.mediagenda.app.labs

import kotlin.math.abs

/** Words with normalized visual coordinates from on-device ML Kit OCR. */
data class LabWord(val text:String,val x:Float,val y:Float,val height:Float)
data class LabValue(
    val section:String,val parameter:String,val result:String,
    val unit:String,val reference:String,val previous:String,val page:Int
)

/**
 * Conservative column-aware extractor for Portuguese lab tables.
 * The unmodified OCR text is also archived so rows that cannot be
 * confidently separated are never thrown away.
 */
object ClinicalLabParser {
    private val number=Regex("""^[-+]?[<>≤≥]?\s*\d{1,5}(?:[.,]\d{1,5})?(?:\s*[%])?$""")
    private val forbidden=Regex("""(?i)(RESULTADO|UNIDADES|VALORES DE REFER|RESULTADOS ANTERIORES|OBSERVA|PÁG\.|PAGINA|COLHEITA|LABORAT|HEMOGRAMA|QUIMICA CLINICA GERAL|CLINICO|PROFISSIONAIS|METODO|NOTA:)""")
    private val sections=listOf("HEMATOLOGIA","QUÍMICA CLÍNICA","QUIMICA CLINICA",
        "IMUNOLOGIA","BIOQUÍMICA","BIOQUIMICA","URINA","MICROBIOLOGIA",
        "HORMONAS","ENDOCRINOLOGIA","COAGULAÇÃO","COAGULACAO","SEROLOGIA")
    private fun cell(words:List<LabWord>)=words.sortedBy{it.x}
        .joinToString(" "){it.text.trim()}.replace(Regex("""\s+""")," ").trim()

    fun extract(words:List<LabWord>,page:Int,previousSection:String=""):Pair<List<LabValue>,String> {
        if(words.isEmpty())return emptyList<LabValue>() to previousSection
        // Threshold is proportional to the actual OCR font height, not pixels
        // of the original camera photo.
        val heights=words.map{it.height}.filter{it>1f}.sorted()
        val median=heights.getOrElse(heights.size/2){18f}.coerceIn(9f,52f)
        val rows=mutableListOf<MutableList<LabWord>>()
        for(word in words.sortedBy{it.y}){
            val nearest=rows.lastOrNull()?.takeIf{
                abs(it.map{w->w.y}.average()-word.y)<median*0.72f
            }
            if(nearest!=null)nearest.add(word) else rows.add(mutableListOf(word))
        }
        val data=mutableListOf<LabValue>()
        var section=previousSection
        for(row in rows){
            val all=cell(row)
            if(all.isBlank())continue
            val upper=all.uppercase()
            sections.firstOrNull{upper.contains(it)}?.let{section=it}
            if(forbidden.containsMatchIn(all) || all.length<4)continue
            val label=cell(row.filter{it.x<0.355f})
            val value=cell(row.filter{it.x>=0.355f&&it.x<0.485f})
            val unit=cell(row.filter{it.x>=0.485f&&it.x<0.64f})
            val reference=cell(row.filter{it.x>=0.64f&&it.x<0.865f})
            val previous=cell(row.filter{it.x>=0.865f})
            val found=value.replace(" ","").take(50)
            if(label.length<3||label.none(Char::isLetter)||
                !Regex("""[0-9]""").containsMatchIn(found)||
                !Regex("""^[<>≤≥]?\s*[-+]?\d""").containsMatchIn(found))continue
            val cleaned=label.trim(' ',':','·','-').take(120)
            if(cleaned.isBlank()||cleaned.any{it=='@'}||forbidden.containsMatchIn(cleaned))continue
            data.add(LabValue(section,cleaned,found,unit.take(60),
                reference.take(100),previous.take(80),page))
        }
        return data.distinctBy{it.parameter.lowercase() to it.page} to section
    }
}
