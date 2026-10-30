package com.mediagenda.app.ocr

import java.time.LocalDate
import kotlin.math.abs
import kotlin.math.max

/**
 * IPO appointment tables: read date anchors by 2D position, then associate
 * department, clinical act, resource and location using the same physical row.
 *
 * Unlike reading TextRecognition.text in order (normally grouped by column),
 * this prevents assigning all the dates to the first department or using the
 * printing date as a medical appointment.
 */
object IpoTableParser {
    private val dateTime = Regex(
        """(?<!\d)(\d{2}[/.-]\d{2}[/.-]20\d{2}|20\d{2}[/.-]\d{2}[/.-]\d{2})\s+(?:às\s+)?([01]?\d|2[0-3])[:h.]([0-5]\d)\b""",
        RegexOption.IGNORE_CASE
    )
    private val dateOnly = Regex("""(?<!\d)(\d{2}[/.-]\d{2}[/.-]20\d{2}|20\d{2}[/.-]\d{2}[/.-]\d{2})(?!\d)""")
    private val timeOnly = Regex("""\b([01]?\d|2[0-3])[:h.]([0-5]\d)\b""")
    private val spaces = Regex("""\s+""")
    private val medical = listOf(
        "CONS", "COLHEITA", "MCDT", "CARDIO", "HEMATO", "ONCO",
        "PATOLOGIA", "RADIO", "BRAQUI", "PEMBROLIZUMAB", "ECOCARDIO",
        "ELECTRO", "ECG", "HOSPITAL DIA", "RM ", "RESSON", "QUIMIO",
        "ENFERMAGEM", "TRATAMENTO", "MEDICAS"
    )

    private data class Anchor(val item: LocatedOcrLine, val date: String, val time: String)
    private fun cx(v: LocatedOcrLine) = (v.left + v.right) / 2
    private fun cy(v: LocatedOcrLine) = (v.top + v.bottom) / 2
    private fun median(xs: List<Int>): Int = xs.sorted()[xs.size / 2]
    private fun norm(text: String): String = text.trim().replace(spaces," ")
    private fun date(s: String): String {
        val v = s.replace('.', '/').replace('-', '/')
        val x = v.split('/')
        if (x.size != 3) return ""
        val iso = if (x[0].length == 4) {
            x[0] + "-" + x[1] + "-" + x[2]
        } else {
            x[2] + "-" + x[1] + "-" + x[0]
        }
        return if (runCatching { LocalDate.parse(iso) }.isSuccess) iso else ""
    }
    private fun pair(line: String): Pair<String,String>? {
        val m = dateTime.find(line) ?: return null
        val d = date(m.groupValues[1])
        if (d.isBlank()) return null
        return d to (m.groupValues[2].padStart(2,'0') + ":" + m.groupValues[3])
    }
    private fun printRelated(text: String): Boolean {
        val u = text.uppercase()
        return u.contains("DATA DE IMPRESS") || u.contains("IMPRESSÃO") ||
            u.contains("IMPRESSAO") || u.contains("DATA DE EMISS")
    }
    private fun isMedical(s: String): Boolean {
        val u = s.uppercase()
        return medical.any { u.contains(it) }
    }

    /** For a normal single-appointment sheet let the existing parser work. */
    fun parse(lines: List<LocatedOcrLine>): List<OcrAppointment> {
        if (lines.size < 8) return emptyList()
        val clean = lines.map { it.copy(text=norm(it.text)) }
            .filter { it.text.isNotBlank() }
        val anchors = clean.mapNotNull { l ->
            val p = pair(l.text) ?: return@mapNotNull null
            if (printRelated(l.text)) return@mapNotNull null
            Anchor(l,p.first,p.second)
        }
        if (anchors.size < 2) return emptyList()

        // A compact column of date+time anchors forms the table.
        // Printed-at timestamps elsewhere on the page are spatial outliers.
        val xSpread = anchors.maxOf { cx(it.item) } - anchors.minOf { cx(it.item) }
        val ySpread = anchors.maxOf { cy(it.item) } - anchors.minOf { cy(it.item) }
        val rowsAlongY = ySpread >= xSpread
        fun row(v: LocatedOcrLine): Int = if (rowsAlongY) cy(v) else cx(v)
        fun col(v: LocatedOcrLine): Int = if (rowsAlongY) cx(v) else cy(v)

        val rowCoordinates = anchors.map { row(it.item) }
        val colCoordinates = anchors.map { col(it.item) }
        val colMedian = median(colCoordinates)
        val allMin = clean.minOf { col(it) }
        val allMax = clean.maxOf { col(it) }
        val allowable = max(40, (allMax - allMin) / 13)
        val aligned = anchors.filter { abs(col(it.item) - colMedian) <= allowable }
            .sortedBy { row(it.item) }
        if (aligned.size < 2) return emptyList()

        // Table bounds: exclude header, printed date, footer.
        val first = aligned.first()
        val last = aligned.last()
        val gaps = aligned.zipWithNext { a,b -> abs(row(b.item)-row(a.item)) }
            .filter { it > 0 }.sorted()
        val rowGap = if (gaps.isEmpty()) 36 else median(gaps)
        val rowMin = row(first.item) - max(25,rowGap/2)
        val rowMax = row(last.item) + max(25,rowGap/2)
        val relevant = clean.filter { row(it) in rowMin..rowMax }

        // The date/time cell is an edge of the table. Choose the side
        // containing most text as the direction to the remaining 3 columns.
        val toRight = relevant.count { col(it) > colMedian + allowable/2 }
        val toLeft = relevant.count { col(it) < colMedian - allowable/2 }
        val sign = if (toRight >= toLeft) 1 else -1
        fun distance(v: LocatedOcrLine): Int = sign*(col(v)-colMedian)

        // Use detected header labels as column centres whenever possible.
        fun heading(vararg words: String): Int? {
            val h = clean.firstOrNull { item ->
                val u = item.text.uppercase()
                words.any { u.contains(it) }
            } ?: return null
            return distance(h)
        }
        val deptHead = heading("DEPARTAMENTO", "ATIVIDADE")
        val resourceHead = heading("RECURSO PRINCIPAL", "MÉDICO PRESCRITOR", "MEDICO PRESCRITOR")
        val locationHead = heading("LOCAL")
        val maxDist = relevant.map { distance(it) }.filter { it > 0 }.maxOrNull() ?: return emptyList()
        if (maxDist < allowable) return emptyList()

        val deptCenter = deptHead?.takeIf { it > 0 } ?: maxDist * 32 / 100
        val resourceCenter = resourceHead?.takeIf { it > deptCenter } ?: maxDist * 66 / 100
        val locationCenter = locationHead?.takeIf { it > resourceCenter } ?: maxDist * 94 / 100
        val boundaryA = max(allowable/2,(deptCenter + resourceCenter)/2)
        val boundaryB = (resourceCenter + locationCenter)/2

        val output = mutableListOf<OcrAppointment>()
        val seen = mutableSetOf<String>()
        aligned.forEachIndexed { idx, anchor ->
            val r = row(anchor.item)
            val before = if (idx == 0) rowMin else
                (row(aligned[idx-1].item)+r)/2
            val after = if (idx == aligned.lastIndex) rowMax else
                (row(aligned[idx+1].item)+r)/2

            val sameRow = relevant.filter { line ->
                row(line) >= before && row(line) < after &&
                    distance(line) > allowable/3 &&
                    !printRelated(line.text) &&
                    !dateTime.containsMatchIn(line.text)
            }.sortedBy { row(it) }

            val dept = mutableListOf<String>()
            val resource = mutableListOf<String>()
            val place = mutableListOf<String>()
            sameRow.forEach { l ->
                val v = distance(l)
                val target = if (v < boundaryA) dept else if (v < boundaryB) resource else place
                val str = norm(l.text)
                if (str.isNotBlank() && target.none { it == str }) target += str
            }

            // Rows without medical information are not safe to import.
            val rowText = (dept + resource + place).joinToString(" ")
            if (!isMedical(rowText)) return@forEachIndexed

            // Department/activity are normally two stacked lines in the IPO column.
            val fieldDept = dept.firstOrNull().orEmpty()
            val fieldActivity = when {
                dept.size >= 2 -> dept.drop(1).joinToString(" ").take(140)
                dept.isNotEmpty() -> dept.first()
                else -> resource.firstOrNull().orEmpty()
            }
            val fieldResource = resource.joinToString(" ").take(110)
            val fieldPlace = place.joinToString(" ").take(110)
            val all = (fieldDept+" "+fieldActivity+" "+fieldResource).uppercase()
            val type = when {
                all.contains("PEMBROLIZUMAB") || all.contains("QUIMIO") ||
                    all.contains("RADIO") || all.contains("BRAQUI") -> "tratamento"
                all.contains("COLHEITA") -> "colheita"
                all.contains("ECOCARDIO") || all.contains("ECG") ||
                    all.contains("ELECTROCARDIO") || all.contains("MCDT") -> "exame"
                else -> "consulta"
            }
            val key = anchor.date + "|" + anchor.time + "|" + fieldActivity.lowercase()
            if (seen.add(key)) {
                output += OcrAppointment(
                    date=anchor.date,time=anchor.time,department=fieldDept,
                    activity=fieldActivity,resource=fieldResource,
                    location=fieldPlace,type=type,
                    raw=(anchor.item.text + "\n" + dept.joinToString("\n") +
                        "\n" + resource.joinToString("\n") + "\n" + place.joinToString("\n")).trim()
                )
            }
        }
        return output.sortedWith(compareBy<OcrAppointment>{it.date}.thenBy{it.time}.thenBy{it.activity})
    }
}
