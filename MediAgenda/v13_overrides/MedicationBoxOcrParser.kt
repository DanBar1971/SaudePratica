package com.mediagenda.app.ocr

import com.mediagenda.app.model.Medication
import java.text.Normalizer
import java.util.Locale

object MedicationBoxOcrParser {
    private val doseRegex = Regex(
        """(?i)\b(\d+(?:[.,]\d+)?)\s*(mg|mcg|µg|g|ml|mL|UI|%)\b"""
    )
    private val quantityRegex = Regex(
        """(?i)\b(\d{1,3})\s*(comprimidos?|c[aá]psulas?|saquetas?|ampolas?|unidades?)\b"""
    )
    private val codeRegex = Regex("""(?<!\d)\d{6,14}(?!\d)""")

    fun parse(text: String, barcodeValues: List<String> = emptyList(), photoUri: String = ""): Medication {
        val lines = text
            .replace('\u00A0', ' ')
            .lines()
            .map { it.trim().replace(Regex("""\s+"""), " ") }
            .filter { it.isNotBlank() }

        val candidate = findProductLine(lines)
        var name = candidate?.first.orEmpty()
        var dose = candidate?.second.orEmpty()

        if (name.isBlank() || dose.isBlank()) {
            val pair = findSplitNameAndDose(lines)
            if (name.isBlank()) name = pair?.first.orEmpty()
            if (dose.isBlank()) dose = pair?.second.orEmpty()
        }

        name = cleanName(name)

        val allCodes = barcodeValues
            .flatMap { raw -> codeRegex.findAll(raw).map { it.value }.toList().ifEmpty { listOf(raw.trim()) } }
            .filter { it.isNotBlank() }
            .distinct()

        val printedCode = if (allCodes.isNotEmpty()) allCodes.joinToString(" | ")
        else lines.flatMap { codeRegex.findAll(it).map { m -> m.value }.toList() }
            .firstOrNull { it.length in 6..14 }.orEmpty()

        return Medication(
            medication = name,
            dose = normalizeDose(dose),
            sourceBarcode = printedCode,
            images = if (photoUri.isBlank()) mutableListOf() else mutableListOf(photoUri)
        )
    }

    fun normalizedMedicationName(value: String): String {
        var s = Normalizer.normalize(value.lowercase(Locale.ROOT), Normalizer.Form.NFD)
            .replace(Regex("""\p{Mn}+"""), "")
            .replace(Regex("""[^a-z0-9 ]+"""), " ")
            .replace(Regex("""\s+"""), " ")
            .trim()

        val labWords = setOf(
            "generis", "labesfal", "alter", "teva", "sandoz", "mylan",
            "tolife", "bluepharma", "ratiopharm", "zentiva", "krka"
        )
        s = s.split(" ").filter { it !in labWords }.joinToString(" ").trim()
        return s
    }

    fun normalizedDose(value: String): String =
        value.lowercase(Locale.ROOT)
            .replace(",", ".")
            .replace("µg", "mcg")
            .replace(Regex("""\s+"""), "")
            .trim()

    private fun findProductLine(lines: List<String>): Pair<String, String>? {
        for (line in lines) {
            if (shouldIgnore(line)) continue
            val dm = doseRegex.find(line) ?: continue
            val before = line.substring(0, dm.range.first).trim(' ', '-', ':', ',', ';')
            if (before.length < 3) continue

            var name = before
                .replace(Regex("""(?i)^generis\s*[:\-]?\s*"""), "")
                .replace(Regex("""(?i)^medicamento\s*[:\-]?\s*"""), "")
                .trim()

            // Stickers sometimes include a leading lab name before the product.
            if (name.equals("generis", true)) continue
            if (name.any { it.isLetter() }) return name to dm.value
        }
        return null
    }

    private fun findSplitNameAndDose(lines: List<String>): Pair<String, String>? {
        for (i in lines.indices) {
            val dm = doseRegex.find(lines[i]) ?: continue
            if (!shouldIgnore(lines[i])) {
                val ownBefore = lines[i].substring(0, dm.range.first).trim()
                if (ownBefore.length >= 3 && ownBefore.any { it.isLetter() }) {
                    return cleanName(ownBefore) to dm.value
                }
            }

            for (back in 1..2) {
                val j = i - back
                if (j < 0) break
                val previous = lines[j]
                if (previous.length !in 3..70 || shouldIgnore(previous)) continue
                if (previous.any { it.isLetter() } && !quantityRegex.containsMatchIn(previous)) {
                    return cleanName(previous) to dm.value
                }
            }
        }

        val likely = lines.firstOrNull { line ->
            line.length in 3..60 && !shouldIgnore(line) &&
                line.any { it.isLetter() } &&
                !quantityRegex.containsMatchIn(line)
        }
        return likely?.let { cleanName(it) to "" }
    }

    private fun shouldIgnore(line: String): Boolean {
        val u = line.uppercase(Locale.ROOT)
        val ignore = listOf(
            "IVA INCLU", "TITULAR DA AUTORIZ", "INTRODUÇÃO NO MERCADO",
            "INTRODUCAO NO MERCADO", "SOCIEDADE", "PORTUGAL", "INFARMED",
            "REGISTO N", "RUA ", "COMPRIMIDOS MG", "GENERIS®", "GRÜNENTHAL",
            "GRUNENTHAL"
        )
        if (ignore.any { u.contains(it) }) return true
        if (u.matches(Regex("""^\d{4}[- ]\d{3}.*"""))) return true
        return false
    }

    private fun cleanName(raw: String): String {
        var s = raw
            .replace(Regex("""(?i)^generis\s*[:\-]?\s*"""), "")
            .replace(Regex("""(?i)^medicamento\s*[:\-]?\s*"""), "")
            .replace(Regex("""(?i)\bcomprimidos?\b.*$"""), "")
            .replace(Regex("""(?i)\bc[aá]psulas?\b.*$"""), "")
            .trim(' ', '-', ':', ',', ';')

        // Avoid returning only a manufacturer.
        if (s.equals("Generis", true) || s.equals("Grünenthal", true) || s.equals("Grunenthal", true)) return ""
        return s
    }

    private fun normalizeDose(raw: String): String {
        val m = doseRegex.find(raw) ?: return raw.trim()
        val number = m.groupValues[1].replace(',', '.')
        val unit = m.groupValues[2].replace("µg", "mcg")
        return "$number $unit"
    }
}
