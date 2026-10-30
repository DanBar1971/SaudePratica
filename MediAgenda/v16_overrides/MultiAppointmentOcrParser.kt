package com.mediagenda.app.ocr

import java.time.LocalDate

/** Splits a full hospital appointment sheet into independently reviewable rows.
 * OCR text is usually sufficient; bounding boxes help when phone reading order
 * follows table columns rather than rows.
 */
data class LocatedOcrLine(
    val text: String,
    val left: Int,
    val top: Int,
    val right: Int,
    val bottom: Int
)

object MultiAppointmentOcrParser {
    private val marker = Regex(
        """(?<!\d)(\d{2}[-/.]\d{2}[-/.]\d{4}|20\d{2}[-/.]\d{2}[-/.]\d{2})\s+(?:às\s+)?([01]?\d|2[0-3])[:h.]([0-5]\d)\b""",
        RegexOption.IGNORE_CASE
    )

    fun parseMany(text: String, positionedLines: List<LocatedOcrLine> = emptyList()): List<OcrAppointment> {
        val normal = text.replace('\u00a0', ' ').replace(Regex("""\r\n?"""), "\n")
        val matches = marker.findAll(normal).toList()
        val segments = mutableListOf<OcrAppointment>()
        matches.forEachIndexed { i, m ->
            val nearby = normal.substring(maxOf(0, m.range.first - 45), m.range.first)
            // Do not mistake the sheet print date for a clinical appointment.
            if (nearby.contains(Regex("""(?i)(data\s+de\s+impress[aã]o|emitid[ao]|impresso)\s*:?\s*$"""))) {
                return@forEachIndexed
            }
            val end = if (i + 1 < matches.size) matches[i+1].range.first else normal.length
            val chunk = normal.substring(m.range.first, end).take(900)
            val parsed = AppointmentOcrParser.parse(chunk)
            if (isCalendarDate(parsed.date) && parsed.time.isNotBlank()) {
                segments += parsed.copy(raw = chunk.take(450))
            }
        }

        val geometric = parseByRows(positionedLines)

        // Prefer reading-order segments if their structure is consistent; use
        // geometric grouping if it detects more medically descriptive entries.
        val segmentCount = segments.count { looksClinical(it) }
        val geometricCount = geometric.count { looksClinical(it) }
        val selected = if (geometricCount > segmentCount && geometric.size >= 2) geometric else segments

        val out = mutableListOf<OcrAppointment>()
        val keys = mutableSetOf<String>()
        selected.forEach { item ->
            if (!isCalendarDate(item.date) || item.time.isBlank()) return@forEach
            val key = "${item.date}|${item.time}|${item.activity.trim().lowercase()}"
            if (keys.add(key)) out += item
        }

        if (out.isNotEmpty()) return out.sortedWith(compareBy<OcrAppointment> { it.date }.thenBy { it.time }.thenBy { it.activity })
        // Single appointment forms are still supported.
        val p = AppointmentOcrParser.parse(normal)
        return if (p.date.isNotBlank() && p.time.isNotBlank()) listOf(p) else emptyList()
    }

    private fun looksClinical(p: OcrAppointment): Boolean {
        val x = (p.activity + " " + p.department).uppercase()
        return listOf(
            "CONS.", "CONSULTA", "CARDIOLOG", "BRAQUITERAP", "RADIOTERAP",
            "QUIMIOTERAP", "PEMBROLIZUMAB", "COLHEITA", "ECOCARDIOGRAMA",
            "ECG", "HOSPITAL DIA", "RESSON", "RM ", "HEMATO", "ENDOCRIN"
        ).any { x.contains(it) }
    }

    private fun isCalendarDate(date: String): Boolean =
        runCatching { LocalDate.parse(date) }.isSuccess

    private fun parseByRows(lines: List<LocatedOcrLine>): List<OcrAppointment> {
        if (lines.size < 4) return emptyList()
        val anchors = lines.filter { marker.containsMatchIn(it.text) }
        if (anchors.size < 2) return emptyList()
        val midX = anchors.map { (it.left + it.right) / 2 }
        val midY = anchors.map { (it.top + it.bottom) / 2 }
        val xSpread = midX.maxOrNull()!! - midX.minOrNull()!!
        val ySpread = midY.maxOrNull()!! - midY.minOrNull()!!
        val horizontalRows = xSpread > ySpread * 1.4
        fun pos(l: LocatedOcrLine): Int = if (horizontalRows) (l.left+l.right)/2 else (l.top+l.bottom)/2

        val sorted = anchors.sortedBy(::pos)
        val result = mutableListOf<OcrAppointment>()
        sorted.forEachIndexed { idx, anchor ->
            val before = if (idx == 0) Int.MIN_VALUE else (pos(sorted[idx-1]) + pos(anchor)) / 2
            val after = if (idx == sorted.lastIndex) Int.MAX_VALUE else (pos(sorted[idx+1]) + pos(anchor)) / 2
            val grouped = lines.filter { line -> pos(line) > before && pos(line) <= after }
                .sortedWith(if (horizontalRows) compareBy({ it.top }, { it.left }) else compareBy({ it.left }, { it.top }))
                .map { it.text }
                .distinct()
            val section = anchor.text + "\n" + grouped.filter { it != anchor.text }.joinToString("\n")
            val parsed = AppointmentOcrParser.parse(section)
            if (isCalendarDate(parsed.date) && parsed.time.isNotBlank()) {
                result += parsed.copy(raw = section.take(450))
            }
        }
        return result
    }
}
