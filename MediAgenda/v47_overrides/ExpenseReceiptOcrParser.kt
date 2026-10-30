package com.mediagenda.app.expenses

import java.time.LocalDate

/** OCR is a suggestion only: the user confirms every value before saving. */
data class ExpenseReceiptScan(
    val date: String = "",
    val category: String = "Outros",
    val merchant: String = "",
    val description: String = "",
    val receiptNumber: String = "",
    val supplierNif: String = "",
    val amount: String = "",
    val raw: String = ""
)

object ExpenseReceiptOcrParser {
    fun parse(raw:String): ExpenseReceiptScan {
        val lines=raw.lines().map{it.trim().replace(Regex("\\s+")," ")}
            .filter{it.isNotEmpty()}
        val joined=lines.joinToString("\n")
        val datePattern=Regex("""\b([0-3]?\d)[/.-]([01]?\d)[/.-](20\d{2})\b""")
        val date=datePattern.findAll(joined).mapNotNull{m->
            runCatching{
                LocalDate.of(m.groupValues[3].toInt(),
                    m.groupValues[2].toInt(),m.groupValues[1].toInt()).toString()
            }.getOrNull()
        }.firstOrNull().orEmpty()
        val nifPattern=Regex("""(?i)\b(?:NIF|NIPC|contribuinte)\s*[:#º.\-]?\s*(\d{9})\b""")
        val nif=lines.firstNotNullOfOrNull { line->
            if(Regex("""(?i)(cliente|adquirente|consumidor)""").containsMatchIn(line))
                null else nifPattern.find(line)?.groupValues?.get(1)
        }.orEmpty()
        val invoice=Regex("""(?i)\b(?:fatura(?:\s+simplificada)?|factura|FT|FS|FR|recibo)\s*(?:n[.º°o]*|#|:)?\s*([A-Z0-9][A-Z0-9/._-]{2,28})""")
            .find(joined)?.groupValues?.get(1).orEmpty()
        val euros=Regex("""(?:\d{1,3}(?:[. ]\d{3})*|\d+)[,.]\d{2}""")
        val totalLabels=Regex("""(?i)(total(?:\s+a\s+pagar)?|valor\s+a\s+pagar|montante\s+total|a\s+pagar|total\s+eur)""")
        val amount=lines.asReversed().firstNotNullOfOrNull{line->
            if(!totalLabels.containsMatchIn(line) ||
                Regex("""(?i)(subtotal|desconto|sem\s+iva|total\s+iva)""").containsMatchIn(line))
                null else euros.findAll(line).lastOrNull()?.value
        }.orEmpty().replace(" ","").let{
            if(it.count{c->c=='.'}>0 && it.contains(','))it.replace(".","")
            else it
        }
        val top=lines.take(12)
        val merchant=top.firstOrNull{
            it.length in 4..70 &&
            it.any(Char::isLetter) &&
            !Regex("""(?i)(fatura|factura|recibo|cliente|contribuinte|nif|nipc|data|telefone|tel:|página|page|original|duplicado|via\s+cliente|obrigado|www\.|http|@)""").containsMatchIn(it) &&
            it.count(Char::isDigit)<it.length/3
        }.orEmpty()
        val category=when {
            Regex("""(?i)farm[aá]cia|medicamento|farmac[eê]utico""").containsMatchIn(joined)->"Farmácia"
            Regex("""(?i)consulta|consult[oó]rio|cl[ií]nica""").containsMatchIn(joined)->"Consulta"
            Regex("""(?i)exame|laborat[oó]rio|an[aá]lise|radiografia|resson[aâ]ncia""").containsMatchIn(joined)->"Exame"
            Regex("""(?i)[oó]tica|[oó]culos|lentes""").containsMatchIn(joined)->"Óculos / Lentes"
            Regex("""(?i)seguro|adse|reembolso""").containsMatchIn(joined)->"Seguro / ADSE"
            else->"Outros"
        }
        return ExpenseReceiptScan(date,category,merchant,"",invoice,nif,amount,raw)
    }
}
