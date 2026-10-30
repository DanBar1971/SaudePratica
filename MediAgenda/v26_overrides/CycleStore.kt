package com.mediagenda.app.data

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.time.LocalDate
import java.time.LocalTime
import java.time.temporal.ChronoUnit

data class PeriodEntry(val start: LocalDate, val end: LocalDate)

class CycleStore(context: Context, profileId: String) {
    init { require(profileId == "legacy" || profileId.matches(Regex("[0-9a-fA-F-]{36}"))) }
    private val prefs = context.getSharedPreferences("saudepratica_cycle_$profileId", Context.MODE_PRIVATE)
    private val folder = File(context.filesDir, "saudepratica_cycle/$profileId").apply { mkdirs() }
    private val periodFile = File(folder, "periods.json")

    fun periods(): List<PeriodEntry> = runCatching {
        val a=JSONArray(periodFile.readText())
        (0 until a.length()).map { n ->
            a.getJSONObject(n).let {
                PeriodEntry(LocalDate.parse(it.getString("start")),LocalDate.parse(it.getString("end")))
            }
        }.sortedByDescending { it.start }
    }.getOrDefault(emptyList())

    fun addPeriod(start: LocalDate, end: LocalDate) {
        require(!end.isBefore(start) && ChronoUnit.DAYS.between(start,end) <=14) { "Intervalo de datas inválido." }
        val current=periods()
        require(current.none { !end.isBefore(it.start) && !start.isAfter(it.end) }) { "Datas já registadas." }
        writePeriods(current+PeriodEntry(start,end))
    }
    fun removePeriod(start: LocalDate) = writePeriods(periods().filterNot { it.start==start })
    private fun writePeriods(items:List<PeriodEntry>){
        val a=JSONArray()
        items.forEach { a.put(JSONObject().put("start",it.start.toString()).put("end",it.end.toString())) }
        val af=android.util.AtomicFile(periodFile)
        val stream=af.startWrite()
        try { stream.write(a.toString().toByteArray());af.finishWrite(stream) }
        catch(e:Exception){af.failWrite(stream);throw e}
    }
    var cycleDays:Int
        get()=prefs.getInt("cycle_days",28)
        set(v){require(v in 21..45);prefs.edit().putInt("cycle_days",v).apply()}
    fun estimatedNext():LocalDate?{
        val latest=periods().firstOrNull()?.start?:return null
        var date=latest.plusDays(cycleDays.toLong())
        while(date.isBefore(LocalDate.now()) && date.isBefore(latest.plusYears(3)))date=date.plusDays(cycleDays.toLong())
        return date
    }
    var pillPattern:String
        get()=prefs.getString("pill_pattern","off")?:"off"
        set(v){require(v in setOf("off","daily","21_7","24_4"));prefs.edit().putString("pill_pattern",v).apply()}
    var pillStart:LocalDate
        get()=runCatching { LocalDate.parse(prefs.getString("pill_start","")) }.getOrDefault(LocalDate.now())
        set(v){prefs.edit().putString("pill_start",v.toString()).apply()}
    var pillTime:LocalTime
        get()=runCatching { LocalTime.parse(prefs.getString("pill_time","21:00")) }.getOrDefault(LocalTime.of(21,0))
        set(v){prefs.edit().putString("pill_time",v.toString()).apply()}
    var alerts:Boolean
        get()=prefs.getBoolean("pill_alerts",false)
        set(v){prefs.edit().putBoolean("pill_alerts",v).apply()}
    fun pillDay(day:LocalDate):Boolean{
        if(pillPattern=="off" || day.isBefore(pillStart))return false
        val n=ChronoUnit.DAYS.between(pillStart,day)%28
        return when(pillPattern){"daily"->true;"21_7"->n<21;"24_4"->n<24;else->false}
    }
    fun pillTaken(day:LocalDate)=prefs.getStringSet("pill_taken",emptySet()).orEmpty().contains(day.toString())
    fun setPillTaken(day:LocalDate, taken:Boolean){
        require(!day.isAfter(LocalDate.now())){"Não é possível confirmar uma data futura."}
        val values=prefs.getStringSet("pill_taken",emptySet()).orEmpty().toMutableSet()
        if(taken)values.add(day.toString())else values.remove(day.toString())
        check(prefs.edit().putStringSet("pill_taken",values).commit()){"Falha ao guardar."}
    }
}
