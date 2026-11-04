package com.mediagenda.app

import android.content.Context
import android.os.Handler
import android.os.Looper
import java.io.Closeable
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Optional GGUF inference entirely on the Android device (no cloud or API key).
 * This class never reads or writes profiles, clinical records or alarms.
 * Native actions, patient isolation and draft approval remain in MainActivity.
 */
internal class SmallOfflineModel(private val context: Context) : Closeable {
    companion object {
        const val TITLE = "Qwen3 0.6B (IA local leve)"
        const val SIZE = "383 MB"
        private const val FILE = "Qwen3-0.6B-Q4_K_S.gguf"
        private const val MODEL_URL =
            "https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/resolve/50968a4468ef4233ed78cd7c3de230dd1d61a56b/Qwen3-0.6B-Q4_K_S.gguf"
        private const val MODEL_SHA256 =
            "3e5495288a45c7891d32afeb4e7a1ed58a9a22fab83f8903b561204a89aae363"
        private const val MAX_BYTES = 450_000_000L
        private const val MIN_BYTES = 350_000_000L
        private const val REQUIRED_FREE_BYTES = 600_000_000L
        private val linked by lazy {
            try { System.loadLibrary("saude_llm"); true }
            catch (_: UnsatisfiedLinkError) { false }
            catch (_: SecurityException) { false }
        }
    }

    private val worker = Executors.newSingleThreadExecutor { task ->
        Thread(task, "SaudePratica-IA-Offline").apply { isDaemon = true }
    }
    private val main = Handler(Looper.getMainLooper())
    private val stopped = AtomicBoolean(false)
    private var modelLoaded = false
    private val folder get() = File(context.filesDir, "ia-local")
    private val model get() = File(folder, FILE)
    private external fun nativeLoadModel(path: String): Boolean
    private external fun nativeGenerate(question: String, maxTokens: Int): String
    private external fun nativeUnloadModel()

    fun runtimeSupported(): Boolean =
        linked && android.os.Build.SUPPORTED_64_BIT_ABIS.isNotEmpty()

    fun downloaded(): Boolean = model.isFile &&
        model.length() in MIN_BYTES..MAX_BYTES

    private fun hash(path: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        path.inputStream().buffered().use { input ->
            val bytes = ByteArray(65536)
            while (true) {
                val n = input.read(bytes)
                if (n < 0) break
                digest.update(bytes, 0, n)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it.toInt() and 255) }
    }

    private fun deliver(cb: (Result<Unit>) -> Unit, value: Result<Unit>) {
        if (!stopped.get()) main.post { if (!stopped.get()) cb(value) }
    }

    /** Call ONLY after a user confirmed the 383 MB download in native UI. */
    fun download(onProgress: (Int) -> Unit, onFinished: (Result<Unit>) -> Unit) {
        if (stopped.get()) return
        worker.execute {
            val outcome = runCatching {
                check(folder.isDirectory || folder.mkdirs()) { "Sem acesso à pasta da IA." }
                check(folder.usableSpace >= REQUIRED_FREE_BYTES) {
                    "Espaço insuficiente. Liberta pelo menos 600 MB."
                }
                // A previously downloaded model is never trusted merely by its size.
                if (downloaded() && hash(model) == MODEL_SHA256) return@runCatching
                val part = File(folder, "$FILE.part")
                part.delete()
                try {
                    val conn = URL(MODEL_URL).openConnection() as HttpURLConnection
                    try {
                        conn.connectTimeout = 25_000
                        conn.readTimeout = 45_000
                        conn.instanceFollowRedirects = true
                        conn.setRequestProperty("Accept", "application/octet-stream")
                        check(conn.responseCode == HttpURLConnection.HTTP_OK) {
                            "O servidor do modelo respondeu: HTTP ${conn.responseCode}"
                        }
                        val length = conn.contentLengthLong
                        check(length == -1L || length in MIN_BYTES..MAX_BYTES) {
                            "Tamanho inesperado do modelo."
                        }
                        val md = MessageDigest.getInstance("SHA-256")
                        var written = 0L
                        conn.inputStream.use { input ->
                            FileOutputStream(part).use { output ->
                                val bytes = ByteArray(65536)
                                var lastProgress = -1
                                while (true) {
                                    check(!stopped.get()) { "Transferência interrompida." }
                                    val n = input.read(bytes)
                                    if (n < 0) break
                                    written += n
                                    check(written <= MAX_BYTES) { "Ficheiro demasiado grande." }
                                    md.update(bytes, 0, n)
                                    output.write(bytes, 0, n)
                                    val percent = (written * 100L / 383_000_000L).toInt().coerceIn(0, 99)
                                    if (percent != lastProgress) {
                                        lastProgress = percent
                                        main.post { if (!stopped.get()) onProgress(percent) }
                                    }
                                }
                                output.fd.sync()
                            }
                        }
                        check(written in MIN_BYTES..MAX_BYTES) { "Modelo descarregado incompleto." }
                        val actual = md.digest().joinToString("") { "%02x".format(it.toInt() and 255) }
                        check(actual == MODEL_SHA256) { "Modelo inválido: a soma SHA-256 não coincide." }
                        if (model.exists()) check(model.delete()) { "Não foi possível substituir a cópia antiga." }
                        check(part.renameTo(model)) { "Não foi possível instalar o modelo." }
                    } finally {
                        conn.disconnect()
                    }
                } finally { part.delete() }
            }
            deliver(onFinished, outcome)
        }
    }

    /** Explicit second stage after a verified download; never run on main thread. */
    fun activate(onFinished: (Result<Unit>) -> Unit) {
        if (stopped.get()) return
        worker.execute {
            val outcome = runCatching {
                check(runtimeSupported()) {
                    "O motor de IA para este processador não está disponível."
                }
                check(downloaded() && hash(model) == MODEL_SHA256) {
                    "Modelo não instalado ou corrompido. Volta a descarregar."
                }
                if (!modelLoaded) {
                    check(nativeLoadModel(model.absolutePath)) {
                        "O telemóvel não conseguiu abrir o modelo. Pode faltar memória."
                    }
                    modelLoaded = true
                }
            }
            deliver(onFinished, outcome)
        }
    }

    fun ready() = modelLoaded && !stopped.get()

    fun ask(question: String, onFinished: (Result<String>) -> Unit) {
        if (stopped.get()) return
        worker.execute {
            val outcome = runCatching {
                check(modelLoaded) { "É necessário ativar primeiro a IA local." }
                check(question.isNotBlank()) { "Escreve a tua pergunta." }
                // Only user's own question. Never append medication, diagnoses or profile data.
                val answer = nativeGenerate(question.take(800), 160).trim()
                check(answer.isNotBlank()) { "O modelo não produziu uma resposta." }
                answer.take(2200)
            }
            if (!stopped.get()) main.post {
                if (!stopped.get()) onFinished(outcome)
            }
        }
    }

    fun remove(onFinished: (Result<Unit>) -> Unit) {
        if (stopped.get()) return
        worker.execute {
            val outcome = runCatching {
                if (modelLoaded) { nativeUnloadModel(); modelLoaded = false }
                if (model.exists()) check(model.delete()) { "Não foi possível remover o modelo." }
            }
            deliver(onFinished, outcome)
        }
    }

    override fun close() {
        if (stopped.compareAndSet(false, true)) {
            worker.execute {
                if (modelLoaded && linked) { nativeUnloadModel(); modelLoaded = false }
            }
            worker.shutdown()
        }
    }
}
