package com.mediagenda.app

import org.json.JSONArray
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.util.Locale

/** Profile-private historical summary, adapted from SnapCal history patterns.
 * The diary is read-only and records from other profiles are never queried.
 */
internal object MealNutritionHistory {
    fun summary(items:JSONArray,days:Int):String {
        require(days in 1..365)
        val now=LocalDate.now()
        var count=0
        var calories=0.0
        var protein=0.0
        var carbs=0.0
        var fat=0.0
        val dates=mutableSetOf<LocalDate>()
        for(i in 0 until items.length()){
            val row=items.optJSONObject(i)?:continue
            val timestamp=row.optLong("at",0L)
            if(timestamp<=0)continue
            val day=Instant.ofEpochMilli(timestamp)
                .atZone(ZoneId.systemDefault()).toLocalDate()
            if(day.isAfter(now)||day.isBefore(now.minusDays((days-1).toLong())))continue
            count++
            dates.add(day)
            fun safe(field:String):Double{
                val v=row.optDouble(field,0.0)
                return if(v.isFinite())v.coerceIn(0.0,10000.0) else 0.0
            }
            calories+=safe("kcal")
            protein+=safe("protein_g")
            carbs+=safe("carbs_g")
            fat+=safe("fat_g")
        }
        if(count==0)return "Sem refeições guardadas nos últimos "+days+" dias."
        return String.format(Locale("pt","PT"),
            "%d refeições · %.0f kcal registadas nos últimos %d dias.\n"+
            "Média de registos: %.0f kcal/dia (inclui dias sem registos).\n"+
            "Proteínas: %.0f g · Hidratos: %.0f g · Gorduras: %.0f g.\n"+
            "%d dias com registos. Dias sem registo não significam jejum.",
            count,calories,days,calories/days,protein,carbs,fat,dates.size)
    }
}
