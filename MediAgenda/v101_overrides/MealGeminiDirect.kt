package com.mediagenda.app

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * BYO Gemini API auth key: encrypted using Android Keystore, on this device only.
 * Stored under noBackupFilesDir so it cannot be uploaded in app backups or sync.
 * Never include the key in source, GitHub, the APK, requests to other domains or logs.
 */
internal object PrivateGeminiKey {
    private const val ALIAS="saudepratica_gemini_auth_v1"
    private fun file(c:Context)=File(c.noBackupFilesDir,"gemini-auth-v1.bin")
    private fun secret():SecretKey{
        val ks=KeyStore.getInstance("AndroidKeyStore").apply{load(null)}
        val old=ks.getKey(ALIAS,null) as? SecretKey
        if(old!=null)return old
        val gen=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore")
        gen.init(KeyGenParameterSpec.Builder(ALIAS,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256).build())
        return gen.generateKey()
    }
    fun configured(c:Context)=file(c).isFile
    fun save(c:Context,raw:String){
        val key=raw.trim()
        require(key.length in 12..500 && !key.contains('\n') && !key.contains('\r')){
            "A chave Gemini parece inválida."
        }
        val cipher=Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE,secret())
        val bytes=byteArrayOf(1)+cipher.iv+cipher.doFinal(key.toByteArray(Charsets.UTF_8))
        val temp=File(c.noBackupFilesDir,"gemini-auth-v1.tmp")
        temp.writeBytes(bytes)
        check(temp.renameTo(file(c))){"Não foi possível guardar a chave."}
    }
    fun read(c:Context):String?{
        val bytes=runCatching{file(c).readBytes()}.getOrNull()?:return null
        return runCatching{
            require(bytes.size in 30..4000 && bytes[0]==1.toByte())
            val cipher=Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE,secret(),
                GCMParameterSpec(128,bytes.copyOfRange(1,13)))
            String(cipher.doFinal(bytes.copyOfRange(13,bytes.size)),Charsets.UTF_8)
        }.getOrNull()?.takeIf{it.isNotBlank()}
    }
    fun delete(c:Context){
        file(c).delete()
        val ks=KeyStore.getInstance("AndroidKeyStore").apply{load(null)}
        if(ks.containsAlias(ALIAS))ks.deleteEntry(ALIAS)
    }
}

/**
 * Direct, opt-in Gemini vision request, preserving the v1.9.82 remote proxy as fallback.
 * Neither profile IDs nor medical records are transmitted: only the consented JPEG.
 */
internal object MealGeminiDirect{
    private const val ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
    private const val PROMPT = """
Analisa esta fotografia de uma refeição COMPLETA em português de Portugal.
Identifica separadamente apenas os alimentos visíveis: prato principal, arroz,
batata, esparregado, salada, sopa, sobremesa ou bebida, se existirem na imagem.
Nunca inventes ingredientes invisíveis; não assumas que há só um prato.
Estima gramas, kcal, proteínas, hidratos e gorduras de cada alimento.
Sinaliza a incerteza: óleo, molhos, quantidade e modo de confeção não são
medíveis a partir da fotografia. Retorna APENAS JSON com este formato:
{"foods":[{"name":"arroz cozido","grams":150,"kcal":195,
"protein_g":4,"carbs_g":42,"fat_g":0.5}],"total_kcal":195,
"uncertainty_note":"Pesos e calorias aproximados."}
Se não houver comida reconhecível, devolve foods=[] e explica o motivo.
As calorias são estimativas visuais, não medições clínicas.
"""
    fun analyze(c:Context,jpeg:ByteArray):JSONObject{
        require(jpeg.size in 500..2_500_000){"Fotografia inválida ou demasiado grande."}
        val key=PrivateGeminiKey.read(c)?:return MealGeminiClient.analyze(jpeg)
        val parts=JSONArray().put(JSONObject().put("text",PROMPT))
            .put(JSONObject().put("inlineData",JSONObject()
                .put("mimeType","image/jpeg")
                .put("data",Base64.encodeToString(jpeg,Base64.NO_WRAP))))
        val body=JSONObject()
            .put("contents",JSONArray().put(JSONObject().put("role","user").put("parts",parts)))
            .put("generationConfig",JSONObject().put("temperature",0.1)
                .put("responseMimeType","application/json").put("maxOutputTokens",2300))
        return normalize(call(key,body))
    }
    fun test(key:String):Boolean{
        val parts=JSONArray().put(JSONObject().put("text","Responde só OK."))
        val body=JSONObject().put("contents",JSONArray()
            .put(JSONObject().put("parts",parts)))
        return (call(key,body).optJSONArray("candidates")?.length()?:0)>0
    }
    private fun call(key:String,body:JSONObject):JSONObject{
        val c=URL(ENDPOINT).openConnection() as HttpURLConnection
        c.requestMethod="POST";c.doOutput=true;c.instanceFollowRedirects=false
        c.connectTimeout=12000;c.readTimeout=48000
        c.setRequestProperty("Content-Type","application/json; charset=utf-8")
        c.setRequestProperty("Accept","application/json")
        c.setRequestProperty("Cache-Control","no-store")
        c.setRequestProperty("X-goog-api-key",key)
        return try{
            c.outputStream.use{it.write(body.toString().toByteArray(Charsets.UTF_8))}
            val status=c.responseCode
            if(status !in 200..299)error(when(status){
                400,401,403->"Chave API ou permissões Gemini recusadas (HTTP "+status+")."
                404->"Modelo Gemini não disponível (404)."
                429->"Limite de chamadas Gemini atingido (429)."
                else->"Gemini indisponível (HTTP "+status+")."
            })
            val response=c.inputStream.bufferedReader(Charsets.UTF_8).use{
                it.readText().take(120000)
            }
            JSONObject(response)
        }finally{c.disconnect()}
    }
    private fun normalize(response:JSONObject):JSONObject{
        val parts=response.optJSONArray("candidates")?.optJSONObject(0)
            ?.optJSONObject("content")?.optJSONArray("parts")
            ?:error("Gemini não devolveu alimentos.")
        val text=buildString{
            for(i in 0 until parts.length())append(parts.optJSONObject(i)?.optString("text").orEmpty())
        }.trim().removePrefix("```json").removePrefix("```").removeSuffix("```").trim()
        val parsed=runCatching{JSONObject(text)}.getOrElse{
            error("Resposta Gemini ilegível; tenta outra fotografia.")
        }
        val items=parsed.optJSONArray("foods")?:JSONArray()
        require(items.length() in 1..18){"Não foram reconhecidos alimentos. Podes usar o modo manual."}
        val foods=JSONArray()
        var kcalTotal=0.0
        for(i in 0 until items.length()){
            val item=items.optJSONObject(i)?:continue
            val name=item.optString("name").trim().take(90)
            val grams=item.optDouble("grams",Double.NaN)
            val kcal=item.optDouble("kcal",Double.NaN)
            if(name.isBlank()||!grams.isFinite()||grams !in 1.0..2500.0||
                !kcal.isFinite()||kcal !in 0.0..5000.0)continue
            val clean=JSONObject().put("name",name).put("grams",grams).put("kcal",kcal)
            for(k in arrayOf("protein_g","carbs_g","fat_g")){
                val v=item.optDouble(k,0.0)
                clean.put(k,if(v.isFinite()&&v in 0.0..1000.0)v else 0.0)
            }
            foods.put(clean);kcalTotal+=kcal
        }
        require(foods.length()>0&&kcalTotal in 1.0..10000.0){
            "Sem calorias utilizáveis. Confirma os alimentos manualmente."
        }
        return JSONObject().put("foods",foods).put("total_kcal",kcalTotal)
            .put("uncertainty_note",parsed.optString("uncertainty_note")
                .take(300).ifBlank{"Porções e calorias estimadas visualmente."})
            .put("provider","gemini")
    }
}
