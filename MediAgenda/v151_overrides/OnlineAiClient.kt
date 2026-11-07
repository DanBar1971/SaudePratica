package com.mediagenda.app

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import org.json.JSONObject
import java.io.Closeable
import java.net.URL
import java.security.KeyStore
import java.util.concurrent.Executors
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.net.ssl.HttpsURLConnection

/**
 * Optional ONLINE inference. No clinical database access here, no records,
 * profiles, names or medication lists are marshalled into the request.
 * A user explicitly selects online mode and only typed text is transmitted.
 *
 * The provider token is entered on the user's device and protected by
 * Android Keystore AES-GCM; it is NEVER shipped in the APK or GitHub.
 */
internal class OnlineAiClient(private val app: Context) : Closeable {
    companion object {
        private const val KEY_ALIAS = "saudepratica_online_ai_token_v1"
        private const val PREFS = "saudepratica_online_ai"
        private const val ENDPOINT = "endpoint"
        private const val CREDENTIAL = "credential"
    }
    private val prefs = app.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    private val ui = Handler(Looper.getMainLooper())
    private val worker = Executors.newSingleThreadExecutor { task ->
        Thread(task, "SaudePratica-IA-Online").apply { isDaemon = true }
    }
    @Volatile private var closed = false

    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore")
        store.load(null)
        val saved = store.getKey(KEY_ALIAS, null) as? SecretKey
        if(saved != null) return saved
        val gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        gen.init(KeyGenParameterSpec.Builder(
            KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        ).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
         .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
         .setKeySize(256)
         .build())
        return gen.generateKey()
    }

    private fun encrypt(value: String): String {
        val cipher=Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val bytes=cipher.doFinal(value.toByteArray(Charsets.UTF_8))
        return Base64.encodeToString(cipher.iv + bytes, Base64.NO_WRAP)
    }

    private fun decrypt(value: String): String {
        val bytes=Base64.decode(value, Base64.NO_WRAP)
        require(bytes.size > 28) { "Credencial guardada incompleta." }
        val cipher=Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE,key(),GCMParameterSpec(128,bytes.copyOfRange(0,12)))
        return String(cipher.doFinal(bytes.copyOfRange(12,bytes.size)),Charsets.UTF_8)
    }

    fun isConfigured(): Boolean =
        !prefs.getString(ENDPOINT,null).isNullOrEmpty() &&
        !prefs.getString(CREDENTIAL,null).isNullOrEmpty()

    fun endpoint(): String = prefs.getString(ENDPOINT,"").orEmpty()

    fun configure(endpointRaw:String, accessToken:String) {
        val address=URL(endpointRaw.trim())
        require(address.protocol == "https" && address.port == -1) {
            "O endereço do serviço tem de utilizar HTTPS, sem portas especiais."
        }
        require(address.host.lowercase().endsWith(".workers.dev") &&
                address.host.length > ".workers.dev".length &&
                address.path == "/v1/ask" &&
                address.query == null && address.ref == null &&
                address.userInfo == null) {
            "Introduz o URL completo do teu serviço Cloudflare Workers: https://...workers.dev/v1/ask"
        }
        require(accessToken.matches(Regex("[A-Za-z0-9_-]{24,128}"))) {
            "O código de acesso deve ter entre 24 e 128 letras, números, _ ou -."
        }
        val protected=encrypt(accessToken)
        require(prefs.edit().putString(ENDPOINT,address.toString())
            .putString(CREDENTIAL,protected).commit()) {
            "Não foi possível guardar a configuração neste dispositivo."
        }
    }

    fun disconnect() {
        prefs.edit().remove(ENDPOINT).remove(CREDENTIAL).apply()
    }

    /** No profile identifiers, log or health-record context is attached. */
    fun ask(question:String, onDone:(Result<String>)->Unit) {
        if(closed)return
        worker.execute {
            val result = runCatching {
                require(isConfigured()) { "IA Online ainda não configurada." }
                val q=question.trim()
                require(q.length in 2..700) {
                    "A pergunta deve conter entre 2 e 700 caracteres."
                }
                val secret=decrypt(prefs.getString(CREDENTIAL,"").orEmpty())
                val url=URL(endpoint())
                val connection=url.openConnection() as HttpsURLConnection
                try {
                    connection.requestMethod="POST"
                    connection.connectTimeout=15_000
                    connection.readTimeout=35_000
                    connection.doOutput=true
                    connection.instanceFollowRedirects=false
                    connection.setRequestProperty("Content-Type","application/json; charset=utf-8")
                    connection.setRequestProperty("Accept","application/json")
                    connection.setRequestProperty("Authorization","Bearer $secret")
                    connection.setRequestProperty("Cache-Control","no-store")
                    val payload=JSONObject().put("question",q).toString().toByteArray(Charsets.UTF_8)
                    require(payload.size <= 2048) { "Pergunta demasiado longa." }
                    connection.outputStream.use { it.write(payload) }
                    val responseCode=connection.responseCode
                    if(responseCode != 200){
                        throw IllegalStateException(when(responseCode){
                            401,403 -> "Código do serviço online incorreto ou expirado."
                            429 -> "O limite de utilização foi atingido. Tenta mais tarde."
                            503 -> "Serviço de IA temporariamente indisponível ou sem quota."
                            else -> "O serviço online respondeu com erro HTTP $responseCode."
                        })
                    }
                    val data=connection.inputStream.bufferedReader(Charsets.UTF_8).use{
                        it.readText().take(10000)
                    }
                    val answer=JSONObject(data).optString("answer").trim()
                    check(answer.isNotBlank()) { "O serviço não devolveu uma resposta." }
                    answer.take(2200)
                } finally { connection.disconnect() }
            }
            if(!closed)ui.post{if(!closed)onDone(result)}
        }
    }

    override fun close() {
        closed=true
        worker.shutdownNow()
    }
}
