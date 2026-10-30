package com.mediagenda.app.work

import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale

/**
 * Offline catalogue of the MCG portal's exam groups. Never infers a medical
 * diagnosis or declares a patient fit for work from OCR text alone.
 */
object WorkplaceClassifier {
    const val COMPLETED="completed"
    const val SCHEDULED="scheduled"
    const val CLINICAL="clinical"
    const val ARCHIVE="archive"
    const val OTHER="other"
    val types=listOf(COMPLETED,SCHEDULED,CLINICAL,ARCHIVE,OTHER)

    fun group(path:String):String {
        val p=path.lowercase(Locale.ROOT)
            .replace('á','a').replace('é','e').replace('í','i')
            .replace('ó','o').replace('ã','a').replace('ç','c')
        return when {
            p.contains("exames marcados")->SCHEDULED
            p.contains("exames efectuados")||p.contains("exames efetuados")->COMPLETED
            p.contains("relatorios clinicos")->CLINICAL
            p.contains("arquivos exames")||p.contains("arquivo de exames")->ARCHIVE
            p.contains("credencial")->SCHEDULED
            p.contains("aconselhamento")->CLINICAL
            p.substringAfterLast('/').matches(Regex("""fa(?:\s*\(\d+\))?\.pdf"""))->COMPLETED
            else->OTHER
        }
    }
    fun type(path:String,ocrText:String=""):String{
        val name=path.lowercase(Locale.ROOT)
        val content=ocrText.lowercase(Locale.ROOT)
        return when {
            name.contains("credencial")||content.contains("credencial")->"Convocatória / credencial"
            name.substringAfterLast('/').matches(Regex("""fa(?:\s*\(\d+\))?\.pdf"""))||
                content.contains("ficha de aptid")->"Ficha de aptidão"
            name.contains("aconselhamento")||content.contains("carta de aconselhamento")->
                "Carta de aconselhamento"
            content.contains("audiometr")||content.contains("speech audiometry")->
                "Audiometria"
            content.contains("electrocardiogr")||content.contains("eletrocardiogr")||
                content.contains("ecg")||name.contains("electro")->
                "Eletrocardiograma"
            content.contains("hemograma")||content.contains("bioquímica")||
                content.contains("bioquimica")||content.contains("análise resultado")->
                "Análises clínicas"
            else->"Exame complementar / documento"
        }
    }
    fun title(path:String,type:String):String{
        val plain=path.substringAfterLast('/').substringBeforeLast('.')
            .replace(Regex("""\s*\(\d+\)$"""),"").trim()
        return when {
            plain.startsWith("fa",true) && plain.length<=4->"Ficha de aptidão"
            plain.startsWith("Aconselhamento",true)->"Carta de aconselhamento"
            plain.startsWith("Credencial",true)->"Credencial de exame"
            plain.matches(Regex("""\d{8}_\d{6}"""))->type
            else->plain.take(105).ifBlank{type}
        }
    }
    fun date(filename:String,ocrText:String=""):String{
        // Explicit date from a document (when present) has preference over
        // a timestamp in a camera filename.
        val text=ocrText.take(6500)
        for(pattern in listOf(
            Regex("""\b(\d{2})[/-](\d{2})[/-](\d{4})\b"""),
            Regex("""\b(\d{4})-(\d{2})-(\d{2})\b""")
        )){
            val m=pattern.find(text)?:continue
            val groups=m.groupValues
            val v=if(groups[1].length==4)
                "${groups[1]}-${groups[2]}-${groups[3]}"
            else "${groups[3]}-${groups[2]}-${groups[1]}"
            if(runCatching{LocalDate.parse(v)}.isSuccess)return v
        }
        Regex("""(?:^|[^\d])(\d{2})(\d{2})(20\d{2})(?:_|[^\d]|$)""")
            .find(filename)?.let{
                val v="${it.groupValues[3]}-${it.groupValues[2]}-${it.groupValues[1]}"
                if(runCatching{LocalDate.parse(v)}.isSuccess)return v
            }
        return ""
    }
}
