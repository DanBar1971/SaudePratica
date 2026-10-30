package com.mediagenda.app

import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URI
import java.net.URL

/**
 * Gemini photographs are sent ONLY after explicit consent in MealAiActivity.
 * No secret, user account, medical profile or API key is bundled in the APK.
 * Service selection is controlled by public project config and can be disabled remotely.
 */
internal object MealGeminiClient {
    private const val CONFIG =
        "https://raw.githubusercontent.com/DanBar1971/AndroidAppDev/master/MediAgenda/cloud/meal-ai-config.json"

    fun analyze(jpeg: ByteArray): JSONObject {
        require(jpeg.size in 500..2_500_000) { "Fotografia demasiado grande ou inválida." }
        val configuration = getJson(CONFIG, 7_000)
        if (!configuration.optBoolean("enabled", false) ||
            configuration.optString("provider") != "gemini") {
            error("O serviço online Gemini ainda não foi ativado pelo responsável da SaúdePrática. " +
                "Podes registar a refeição manualmente, sem Internet.")
        }
        val endpoint = configuration.optString("endpoint").trim()
        val uri = URI(endpoint)
        require(uri.scheme == "https" && uri.userInfo == null && uri.fragment == null &&
            uri.port == -1 && uri.host?.endsWith(".workers.dev") == true &&
            uri.path == "/analyze") { "O endereço do serviço de IA é inválido." }
        val body = JSONObject()
            .put("image_mime", "image/jpeg")
            .put("image_base64", Base64.encodeToString(jpeg, Base64.NO_WRAP))
            .put("language", "pt-PT")
        val conn = (URL(endpoint).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 10_000
            readTimeout = 45_000
            instanceFollowRedirects = false
            doOutput = true
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("Accept", "application/json")
            setRequestProperty("Cache-Control", "no-store")
        }
        val answer = try {
            conn.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            val status = conn.responseCode
            val stream = if (status in 200..299) conn.inputStream else conn.errorStream
            val result = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText().take(40_000) }.orEmpty()
            if (status !in 200..299) {
                val message = runCatching { JSONObject(result).optString("error") }.getOrNull()
                    .orEmpty().take(180)
                error(message.ifBlank { "Serviço online indisponível (HTTP $status)." })
            }
            JSONObject(result)
        } finally {
            conn.disconnect()
        }
        val foods = answer.optJSONArray("foods") ?: error("A IA não devolveu alimentos.")
        require(foods.length() in 1..18) {
            "A análise não identificou alimentos suficientes. Tenta modo manual."
        }
        val clean = JSONArray()
        var calories = 0.0
        for (i in 0 until foods.length()) {
            val f = foods.optJSONObject(i) ?: continue
            val name = f.optString("name").trim().take(90)
            val grams = f.optDouble("grams", Double.NaN)
            val kcal = f.optDouble("kcal", Double.NaN)
            if (name.isBlank() || !grams.isFinite() || grams !in 1.0..2500.0 ||
                !kcal.isFinite() || kcal !in 0.0..5000.0) continue
            val item = JSONObject().put("name",name).put("grams", grams).put("kcal", kcal)
            for (key in arrayOf("protein_g", "carbs_g", "fat_g")) {
                val n = f.optDouble(key, 0.0)
                item.put(key, if (n.isFinite() && n in 0.0..1000.0) n else 0.0)
            }
            clean.put(item)
            calories += kcal
        }
        require(clean.length() > 0 && calories in 1.0..10000.0) {
            "A IA não conseguiu calcular uma estimativa utilizável. Usa o modo manual."
        }
        val note = answer.optString("uncertainty_note").take(350)
        return JSONObject().put("foods", clean).put("total_kcal", calories)
            .put("uncertainty_note", (note + " Porções estimadas por Gemini: confirma os alimentos, molhos e pesos.").trim())
            .put("provider", "gemini")
    }

    private fun getJson(address: String, timeoutMs: Int): JSONObject {
        val conn = (URL(address).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"; connectTimeout = timeoutMs; readTimeout = timeoutMs
            instanceFollowRedirects = false
            setRequestProperty("Accept", "application/json")
        }
        return try {
            require(conn.responseCode == 200) { "Configuração de IA indisponível." }
            val text = conn.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText().take(15_000) }
            JSONObject(text)
        } finally { conn.disconnect() }
    }
}