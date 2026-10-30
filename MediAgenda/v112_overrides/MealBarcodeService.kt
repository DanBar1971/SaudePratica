package com.mediagenda.app

import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * SaúdePrática native Kotlin adapter for the Open Food Facts product database.
 * Inspired by SnapCal (ghostwan/food-calories, MIT stated in README) and OFF.
 *
 * Product records are © Open Food Facts contributors; database ODbL 1.0.
 * Only the barcode is sent to Open Food Facts. No profile or medical records.
 * Prices, allergy safety and exact calories are never inferred from barcode.
 */
internal object MealBarcodeService {
    private val codeFormat=Regex("[0-9]{8,14}")

    fun lookup(raw:String):JSONObject {
        val barcode=raw.trim()
        require(codeFormat.matches(barcode)) {
            "Indica um código de barras EAN/UPC válido (8 a 14 algarismos)."
        }
        // OFF API v3 current version. Do not send identity or private health data.
        val endpoint="https://world.openfoodfacts.org/api/v3/product/$barcode" +
            "?fields=code,product_name,product_name_pt,brands,nutriments," +
            "serving_size,nutriscore_grade,nova_group"
        val connection=(URL(endpoint).openConnection() as HttpURLConnection).apply{
            requestMethod="GET"
            connectTimeout=12000
            readTimeout=12000
            instanceFollowRedirects=false
            setRequestProperty("Accept","application/json")
            setRequestProperty("User-Agent",
                "SaudePratica/1.9.93 (https://github.com/DanBar1971/AndroidAppDev)")
        }
        return try {
            val status=connection.responseCode
            if(status==404)error("Produto não encontrado no Open Food Facts.")
            require(status==200) { "Open Food Facts indisponível (HTTP $status)." }
            val text=connection.inputStream.bufferedReader(Charsets.UTF_8).use {
                it.readText().take(240_000)
            }
            parse(barcode,JSONObject(text))
        } finally { connection.disconnect() }
    }

    internal fun parse(code:String,body:JSONObject):JSONObject {
        val item=body.optJSONObject("product")
            ?:error("Não foram encontrados dados deste produto.")
        val name=item.optString("product_name_pt").trim()
            .ifBlank {item.optString("product_name").trim()}
            .take(140)
        require(name.isNotBlank()) {
            "Produto sem designação. Introduz manualmente os alimentos."
        }
        val nutr=item.optJSONObject("nutriments")
            ?:error("Produto sem tabela nutricional. Introduz os valores manualmente.")
        fun per100(key:String):Double {
            val v=nutr.optDouble(key+"_100g",Double.NaN)
            return if(v.isFinite()&&v in 0.0..1000.0)v else 0.0
        }
        val kcal=nutr.optDouble("energy-kcal_100g",Double.NaN).let {
            if(it.isFinite() && it in 0.0..1000.0)it
            else nutr.optDouble("energy_100g",Double.NaN).let { joule ->
                if(joule.isFinite()&&joule in 0.0..4184.0)joule/4.184
                else Double.NaN
            }
        }
        require(kcal.isFinite() && kcal>=0.0) {
            "Produto sem energia por 100 g. Introduz os valores manualmente."
        }
        val brand=item.optString("brands").trim().take(80)
        val label=if(brand.isBlank())name else "$name · $brand"
        val food=JSONObject().put("name",label)
            .put("grams",100).put("kcal",kcal)
            .put("protein_g",per100("proteins"))
            .put("carbs_g",per100("carbohydrates"))
            .put("fat_g",per100("fat"))
        return JSONObject().put("foods",JSONArray().put(food))
            .put("total_kcal",kcal)
            .put("protein_g",per100("proteins"))
            .put("carbs_g",per100("carbohydrates"))
            .put("fat_g",per100("fat"))
            .put("barcode",code)
            .put("source","Open Food Facts")
            .put("uncertainty_note",
                "Open Food Facts · valores por 100 g (não pela embalagem toda). " +
                "Confirma os gramas consumidos. Dados dos colaboradores · ODbL 1.0.")
    }
}
