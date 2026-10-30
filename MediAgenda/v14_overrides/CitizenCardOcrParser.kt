package com.mediagenda.app.ocr

/** Portuguese Citizen Card back: extracts ONLY NIF and SNS user number.
 * Never reads, stores or exports the image; extracted values require user confirmation.
 * Unlabelled numbers are intentionally ignored to avoid confusing NISS, CC and SNS.
 */
data class CitizenCardData(val nif: String = "", val snsNumber: String = "")

object CitizenCardOcrParser {
    private val numeric = Regex("""(?<!\d)\d[\d .-]{7,16}\d(?!\d)""")

    private fun canonical(text: String): String =
        java.text.Normalizer.normalize(text.uppercase(java.util.Locale.ROOT), java.text.Normalizer.Form.NFD)
            .replace(Regex("""\p{Mn}+"""), "")
            .replace(Regex("""[^A-Z0-9]+"""), " ")
            .trim()

    /** Check digit for the 9-digit Portuguese NIF. */
    fun validNif(value: String): Boolean {
        if (!value.matches(Regex("""\d{9}"""))) return false
        val sum = (0 until 8).sumOf { (value[it] - '0') * (9 - it) }
        val mod = sum % 11
        val check = if (mod < 2) 0 else 11 - mod
        return value.last() - '0' == check
    }

    private fun candidates(text: String): List<String> =
        numeric.findAll(text)
            .map { m -> m.value.filter { it.isDigit() } }
            .filter { it.length == 9 }
            .distinct()
            .toList()

    fun parse(text: String): CitizenCardData {
        val lines = text.lines()
            .map { it.trim().replace(Regex("""\s+"""), " ") }
            .filter { it.isNotBlank() }

        var nif = ""
        var sns = ""
        for (i in lines.indices) {
            val label = canonical(lines[i])
            val nifLabel = label == "NIF" ||
                label.contains("IDENTIFICACAO FISCAL") ||
                label.contains("NUMERO FISCAL") ||
                label.contains("N FISCAL")
            val snsLabel = label.contains("UTENTE DE SAUDE") ||
                label.contains("UTENTE SAUDE") ||
                label.contains("UTENTE DO SNS") ||
                label.contains("NUMERO DE UTENTE") ||
                label.contains("N UTENTE") ||
                label == "SNS"
            if (!nifLabel && !snsLabel) continue

            // Try same line first, then the two immediately following OCR lines.
            // Stop if another identification label starts, to avoid mixing NIF and SNS.
            val window = mutableListOf(lines[i])
            for (next in (i + 1)..minOf(i + 2, lines.lastIndex)) {
                val nextNormalized = canonical(lines[next])
                if (nextNormalized.contains("SEGURANCA SOCIAL") ||
                    nextNormalized.contains("IDENTIFICACAO FISCAL") ||
                    nextNormalized.contains("UTENTE DE SAUDE") ||
                    nextNormalized.contains("UTENTE SAUDE")) break
                window += lines[next]
            }
            val matches = window.flatMap { candidates(it) }
            if (nifLabel && nif.isBlank()) nif = matches.firstOrNull(::validNif).orEmpty()
            if (snsLabel && sns.isBlank()) sns = matches.firstOrNull().orEmpty()
        }
        return CitizenCardData(nif, sns)
    }
}
