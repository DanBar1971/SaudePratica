package com.mediagenda.app.ocr

data class OcrAppointment(
    val date: String = "", val time: String = "", val department: String = "",
    val activity: String = "", val resource: String = "", val location: String = "",
    val type: String = "consulta", val raw: String = ""
)

object AppointmentOcrParser {
    private val isoDate = Regex("""\b(20\d{2})[-/.](\d{2})[-/.](\d{2})\b""")
    private val ptDate = Regex("""\b(\d{2})[-/.](\d{2})[-/.](20\d{2})\b""")
    private val timeRegex = Regex("""\b([01]?\d|2[0-3])[:h.]([0-5]\d)\b""")

    fun parse(text: String): OcrAppointment {
        val clean = text.replace('\u00A0', ' ')
        val lines = clean.lines().map { it.trim().replace(Regex("""\s+"""), " ") }.filter { it.isNotBlank() }

        val date = findDate(clean)
        val time = findTime(clean, date)

        val upper = clean.uppercase()
        val isCruzVermelha = upper.contains("HOSPITAL CRUZ VERMELHA") || upper.contains("MARCAÇÃO DE ACTO") || upper.contains("MARCACAO DE ACTO")
        val rmActs = extractRmActs(lines)
        val activity = if (rmActs.isNotEmpty()) rmActs.joinToString("; ") else findGenericActivity(lines)

        val department = when {
            upper.contains("RESSONÂNCIA MAGNÉTICA") || upper.contains("RESSONANCIA MAGNETICA") -> "Ressonância Magnética"
            upper.contains("MCDT CARDIOLOGIA") -> "MCDT Cardiologia"
            upper.contains("PATOLOGIA CLÍNICA") || upper.contains("PATOLOGIA CLINICA") -> "Patologia Clínica"
            upper.contains("HOSPITAL DIA") && upper.contains("HEMATO") -> "Hospital Dia - HematoOncologia"
            else -> lines.firstOrNull { l ->
                val u=l.uppercase()
                u.contains("CONS. MÉD") || u.contains("CONS. MED") || u.contains("CONS. ENF") ||
                    u.contains("MCDT") || u.contains("PATOLOGIA") || u.contains("HOSPITAL DIA")
            }.orEmpty()
        }

        var resource = extractResource(lines)
        val location = when {
            isCruzVermelha -> "Hospital Cruz Vermelha"
            else -> lines.firstOrNull { l ->
                val u=l.uppercase()
                u.contains("PAV ") || u.contains("HOSP.") || u == "INTERNAMENTO" || u.contains("HOSPITAL DIA ADULTOS")
            }.orEmpty()
        }
        if (isCruzVermelha && resource.contains("Hospital Cruz Vermelha", true)) resource = ""

        val type = when {
            upper.contains("ACTO EXAME") || upper.contains("ATO EXAME") || rmActs.isNotEmpty() ||
                activity.uppercase().contains("ECOCARDIOGRAMA") || activity.uppercase().contains("ECG") ||
                activity.uppercase().contains("RESSON") || activity.uppercase().startsWith("RM ") -> "exame"
            activity.uppercase().contains("COLHEITA") -> "colheita"
            listOf("PEMBROLIZUMAB","QUIMIOTERAP","RADIOTERAP","BRAQUITERAP").any { activity.uppercase().contains(it) } -> "tratamento"
            department.uppercase().contains("ENFERM") -> "enfermagem"
            else -> "consulta"
        }

        return OcrAppointment(date,time,department,activity,resource,location,type,text)
    }

    private fun findDate(text: String): String {
        isoDate.find(text)?.let { return "${it.groupValues[1]}-${it.groupValues[2]}-${it.groupValues[3]}" }
        ptDate.find(text)?.let { return "${it.groupValues[3]}-${it.groupValues[2]}-${it.groupValues[1]}" }
        return ""
    }

    private fun findTime(text: String, date: String): String {
        if (date.isNotBlank()) {
            val variants = listOf(date, date.split('-').reversed().joinToString("/"))
            for (v in variants) {
                val i = text.indexOf(v)
                if (i >= 0) {
                    val window = text.substring(i, minOf(text.length, i + 100))
                    timeRegex.find(window)?.let {
                        return it.groupValues[1].padStart(2,'0') + ":" + it.groupValues[2]
                    }
                }
            }
        }
        return timeRegex.find(text)?.let { it.groupValues[1].padStart(2,'0') + ":" + it.groupValues[2] }.orEmpty()
    }

    private fun extractRmActs(lines: List<String>): List<String> {
        val joined = lines.joinToString("\n")
        val exact = Regex("""(?i)\bRM\s+(Card[ií]aca\s+Funcional|Suplemento\s+De\s+Contraste|Card[ií]aca\s+Morfol[oó]gica)\s*;?""")
            .findAll(joined)
            .map { "RM ${it.groupValues[1]}".replace(Regex("""\s+"""), " ") }
            .toList()
        if (exact.isNotEmpty()) return exact.distinct()

        return lines.filter { l ->
            val u=l.uppercase()
            u.startsWith("RM ") || u.contains("CARDÍACA FUNCIONAL") || u.contains("CARDIACA FUNCIONAL") ||
                u.contains("SUPLEMENTO DE CONTRASTE") || u.contains("CARDÍACA MORFOLÓGICA") || u.contains("CARDIACA MORFOLOGICA")
        }.map { it.trim().trimEnd(';') }.distinct().take(6)
    }

    private fun findGenericActivity(lines: List<String>): String {
        val keys = listOf(
            "PEMBROLIZUMAB","BRAQUITERAP","QUIMIOTERAP","RADIOTERAP","ECOCARDIOGRAMA",
            "ECG SIMPLES","COLHEITA","SUBSEQUENTE","PRIMEIRA","RESSONÂNCIA","RESSONANCIA"
        )
        return lines.firstOrNull { line -> keys.any { line.uppercase().contains(it) } }.orEmpty()
    }

    private fun extractResource(lines: List<String>): String {
        val idx = lines.indexOfFirst {
            it.contains("Recurso Executante", true) || it.contains("Médico Prescritor", true) || it.contains("Medico Prescritor", true)
        }
        if (idx >= 0) {
            lines.drop(idx + 1).take(5).firstOrNull { candidate ->
                val u=candidate.uppercase()
                candidate.length in 4..60 && !u.contains("DATA") && !u.contains("HORA") &&
                    !u.contains("ACTO") && !u.contains("ATO") && !isoDate.containsMatchIn(candidate)
            }?.let { return it }
        }
        return ""
    }
}
