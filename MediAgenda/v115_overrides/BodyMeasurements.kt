package com.mediagenda.app.data

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant

/** A manual weight is never sent to a third party and belongs to exactly one patient. */
class BodyMeasurements(private val context:Context,private val profile:String){
    private val prefs=context.getSharedPreferences("saudepratica_body_$profile",Context.MODE_PRIVATE)
    init{ require(profile=="legacy" || Regex("[a-fA-F0-9-]{36}").matches(profile)) }
    fun heightCm():Double {
        val own=prefs.getFloat("height_cm",0f).toDouble()
        if(own>0.0)return own
        // Use height already stored in this patient's profile.
        val raw=context.getSharedPreferences(ProfileStore(context).preferencesFor(profile),
            Context.MODE_PRIVATE).getString("height_cm","").orEmpty()
        return raw.replace(',','.').toDoubleOrNull()?.takeIf{it in 90.0..230.0}?:0.0
    }
    fun setHeight(cm:Double){require(cm in 90.0..230.0);check(prefs.edit().putFloat("height_cm",cm.toFloat()).commit())}
    fun addWeight(kg:Double){
        require(kg in 20.0..350.0){"Indica um peso entre 20 e 350 kg."}
        val list=JSONArray(prefs.getString("weights","[]"))
        list.put(JSONObject().put("at",System.currentTimeMillis()).put("kg",kg))
        check(prefs.edit().putString("weights",list.toString()).commit())
    }
    fun recent(max:Int=30):List<Pair<Long,Double>>{
        val list=runCatching{JSONArray(prefs.getString("weights","[]"))}.getOrDefault(JSONArray())
        return (0 until list.length()).mapNotNull{i->
            val x=list.optJSONObject(i)?:return@mapNotNull null
            val at=x.optLong("at",0L);val kg=x.optDouble("kg",Double.NaN)
            if(at>0L && kg.isFinite() && kg in 20.0..350.0)at to kg else null
        }.sortedByDescending{it.first}.take(max.coerceIn(1,60))
    }
    /** Adult screening only. Neither BMI nor this app diagnoses health or fitness. */
    fun adultBmi(kg:Double,height:Double=heightCm()):Double?{
        if(kg !in 20.0..350.0 || height !in 90.0..230.0)return null
        return kg/((height/100.0)*(height/100.0))
    }
    fun adultBmiLabel(bmi:Double):String=when{
        bmi<18.5->"Abaixo do intervalo de referência para adultos"
        bmi<25.0->"Dentro do intervalo de referência para adultos"
        bmi<30.0->"Acima do intervalo de referência para adultos"
        else->"IMC elevado face ao intervalo de referência para adultos"
    }
}