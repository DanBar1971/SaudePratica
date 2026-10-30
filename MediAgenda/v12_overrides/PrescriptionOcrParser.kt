package com.mediagenda.app.ocr

import com.mediagenda.app.model.Medication
import java.time.LocalDate

object PrescriptionOcrParser {
    private val longNumber = Regex("""(?<!\d)\d{12,24}(?!\d)""")
    private val accessRegex = Regex("""(?i)c[oó]digo\s+de\s+acesso(?:\s+e\s+dispensa)?\s*[:\-]*\s*\*?\s*(\d{4,10})""")
    private val optionRegex = Regex("""(?i)c[oó]digo\s+de\s+op[cç][aã]o\s*[:\-]*\s*\*?\s*(\d{3,10})""")
    private val isoDateRegex = Regex("""\b(20\d{2})[-/.](\d{2})[-/.](\d{2})\b""")
    private val ptDateRegex = Regex("""\b(\d{2})[-/.](\d{2})[-/.](20\d{2})\b""")
    private val medLine = Regex(
        """^\s*\d*\s*([\p{L}][\p{L}\s+\-/]+?),\s*([0-9]+(?:[.,][0-9]+)?\s*(?:mg|mcg|µg|g|ml|mL|UI|%))\b(.*)$""",
        RegexOption.IGNORE_CASE
    )

    fun parse(text: String, scannedCode: String = ""): Medication {
        val clean = text.replace('\u00A0', ' ')
        val lines = clean.lines().map { it.trim().replace(Regex("""\s+"""), " ") }.filter { it.isNotBlank() }

        val allCodes = (scannedCode + "\n" + clean)
        val prescriptionNumber = findPrescriptionNumber(clean, scannedCode)
        val access = accessRegex.find(clean)?.groupValues?.getOrNull(1).orEmpty()
        val option = optionRegex.find(clean)?.groupValues?.getOrNull(1).orEmpty()

        var name = ""
        var dose = ""
        var medIndex = -1
        for ((i, line) in lines.withIndex()) {
            val m = medLine.find(line) ?: continue
            val candidate = m.groupValues[1].trim().removePrefix("1 ").trim()
            if (candidate.contains("DCI /", ignoreCase = true)) continue
            name = candidate
            dose = m.groupValues[2].trim().replace(',', '.')
            medIndex = i
            break
        }

        if (name.isBlank()) {
            val likely = lines.withIndex().firstOrNull { (_, line) ->
                val u = line.uppercase()
                (u.contains(" MG") || u.contains(" MCG") || u.contains(" ML") || u.contains(" UI")) &&
                    !u.contains("ENCARG") && !u.contains("TELEFONE") && !u.contains("PREÇO")
            }
            if (likely != null) {
                medIndex = likely.index
                val cleaned = likely.value.replace(Regex("""^\d+\s+"""), "")
                val parts = cleaned.split(',')
                if (parts.isNotEmpty()) name = parts[0].trim()
                dose = Regex("""([0-9]+(?:[.,][0-9]+)?\s*(?:mg|mcg|µg|g|ml|mL|UI|%))""", RegexOption.IGNORE_CASE)
                    .find(likely.value)?.value.orEmpty().replace(',', '.')
            }
        }

        val posologyCandidates = if (medIndex >= 0) lines.drop(medIndex + 1).take(8) else lines
        val posology = posologyCandidates.firstOrNull { line ->
            val u = line.uppercase()
            listOf("24/24", "12/12", "8/8", "JEJUM", "DEITAR", "DURANTE", "COMPRIMIDO", "CÁPSULA", "CAPSULA", "SOS", " CP", "1 CP").any { u.contains(it) }
        }.orEmpty()

        val allDates = extractDates(clean)
        val prescriptionDate = findPrescriptionDate(clean, allDates)
        val validUntil = findValidity(lines, allDates, prescriptionDate)
        val timeHint = when {
            posology.contains("jejum", true) -> "Jejum"
            posology.contains("deitar", true) -> "Deitar"
            posology.contains("jantar", true) -> "Jantar"
            posology.contains("pequeno", true) -> "P. Alm."
            else -> ""
        }

        return Medication(
            medication = name,
            dose = dose,
            indication = posology,
            time = timeHint,
            prescriptionCode = prescriptionNumber,
            prescriptionDate = prescriptionDate,
            dispenseCode = access,
            optionCode = option,
            validUntil = validUntil,
            sourceBarcode = allCodes.lines().map { it.trim() }.filter { it.isNotBlank() }.distinct().joinToString(" | ").take(500)
        )
    }

    private fun findPrescriptionNumber(text: String, scannedCode: String): String {
        val scannedNumeric = longNumber.findAll(scannedCode).map { it.value }.firstOrNull { it.length >= 16 }
        if (!scannedNumeric.isNullOrBlank()) return scannedNumeric

        val normalized = text.replace("*", " ")
        val nearTitle = Regex("""(?is)(?:guia\s+de\s+tratamento\s+da\s+)?prescri[cç][aã]o\s+n[.ºo°]*\s*[:\- ]*([0-9\s]{12,30})""")
            .find(normalized)?.groupValues?.getOrNull(1)?.filter { it.isDigit() }
        if (!nearTitle.isNullOrBlank() && nearTitle.length in 12..24) return nearTitle

        linesAround(normalized, "prescri").forEach { line ->
            val digits = line.filter { it.isDigit() }
            if (digits.length in 16..24) return digits
        }

        return longNumber.findAll(normalized).map { it.value }.firstOrNull { it.length >= 16 }.orEmpty()
    }

    private fun findPrescriptionDate(text: String, dates: List<String>): String {
        val direct = Regex("""(?i)\bdata\s*[:\-]\s*(20\d{2}[-/.]\d{2}[-/.]\d{2}|\d{2}[-/.]\d{2}[-/.]20\d{2})""")
            .find(text)?.groupValues?.getOrNull(1)
        normalizeDate(direct)?.let { return it }
        return dates.minOrNull().orEmpty()
    }

    private fun findValidity(lines: List<String>, dates: List<String>, prescriptionDate: String): String {
        val validityIndex = lines.indexOfFirst { it.contains("validade", true) }
        if (validityIndex >= 0) {
            lines.drop(validityIndex).take(14).forEach { line ->
                extractDates(line).firstOrNull { it != prescriptionDate }?.let { return it }
            }
        }
        return dates.filter { it != prescriptionDate }.maxOrNull().orEmpty()
    }

    private fun extractDates(text: String): List<String> {
        val out = mutableListOf<String>()
        isoDateRegex.findAll(text).forEach { m -> out += "${m.groupValues[1]}-${m.groupValues[2]}-${m.groupValues[3]}" }
        ptDateRegex.findAll(text).forEach { m -> out += "${m.groupValues[3]}-${m.groupValues[2]}-${m.groupValues[1]}" }
        return out.filter { runCatching { LocalDate.parse(it) }.isSuccess }.distinct().sorted()
    }

    private fun normalizeDate(raw: String?): String? {
        if (raw.isNullOrBlank()) return null
        isoDateRegex.find(raw)?.let { return "${it.groupValues[1]}-${it.groupValues[2]}-${it.groupValues[3]}" }
        ptDateRegex.find(raw)?.let { return "${it.groupValues[3]}-${it.groupValues[2]}-${it.groupValues[1]}" }
        return null
    }

    private fun linesAround(text: String, token: String): List<String> {
        val lines = text.lines().map { it.trim() }
        val i = lines.indexOfFirst { it.contains(token, true) }
        if (i < 0) return lines.take(8)
        return lines.subList(i, minOf(lines.size, i + 5))
    }
}
