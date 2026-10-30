package com.mediagenda.app

import android.app.Activity
import android.app.DownloadManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.Settings
import android.widget.ProgressBar
import androidx.core.app.NotificationCompat
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import java.io.File
import java.io.FileOutputStream
import java.security.MessageDigest

/**
 * v1.9.89 - System DownloadManager handles long GitHub downloads even when
 * the app is closed. The actual APK remains in the user's Downloads folder.
 * Only a user request can start installation. Verify SHA256, package name,
 * versionCode and original installed signing certificate before installing.
 */
internal object InAppUpdateInstaller {
    private const val PREF = "saudepratica_download_manager_update_v2"
    private const val CHANNEL = "saudepratica_update_ready_v2"
    private const val MAX_BYTES = 260L * 1024L * 1024L
    private val TRUSTED = Regex(
        "^https://github[.]com/DanBar1971/AndroidAppDev/releases/download/(v[0-9]+[.][0-9]+[.][0-9]+)/SaudePratica[.]apk$")
    private val HEX = Regex("^[a-fA-F0-9]{64}$")
    private fun prefs(c: Context) = c.getSharedPreferences(PREF, Context.MODE_PRIVATE)
    private fun manager(c: Context) = c.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager

    private fun queryStatus(c: Context, id: Long): Pair<Int, String> {
        val cursor = manager(c).query(DownloadManager.Query().setFilterById(id))
        cursor.use {
            if (!it.moveToFirst()) return -1 to "Transferência não encontrada."
            val status = it.getInt(it.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS))
            val reason = it.getInt(it.getColumnIndexOrThrow(DownloadManager.COLUMN_REASON))
            val done = it.getLong(it.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR))
            val total = it.getLong(it.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES))
            val detail = if (total > 0L) "${(done * 100L / total).coerceIn(0, 100)}%"
                         else "${done / (1024L * 1024L)} MB recebidos"
            return status to if (status == DownloadManager.STATUS_FAILED)
                "A transferência falhou (código Android $reason)." else detail
        }
    }

    fun install(activity: Activity, url: String, digest: String) {
        val match = TRUSTED.matchEntire(url)
        val hash = digest.removePrefix("sha256:").lowercase()
        if (match == null || !HEX.matches(hash)) {
            alert(activity, "A Release não fornece uma ligação ou SHA-256 verificável.")
            return
        }
        val store = prefs(activity)
        val previous = store.getLong("download_id", -1L)
        if (previous > 0L) {
            val (status, detail) = runCatching { queryStatus(activity, previous) }
                .getOrDefault(-1 to "Estado indisponível")
            if (store.getString("digest", null) == hash && 
                status == DownloadManager.STATUS_SUCCESSFUL) {
                MaterialAlertDialogBuilder(activity)
                    .setTitle("Atualização já descarregada")
                    .setMessage("A APK está na pasta Downloads. Verificar e instalar agora?")
                    .setNegativeButton("Mais tarde", null)
                    .setPositiveButton("Instalar") { _, _ -> finishInstallation(activity) }
                    .show()
                return
            }
            if (status == DownloadManager.STATUS_RUNNING ||
                status == DownloadManager.STATUS_PENDING ||
                status == DownloadManager.STATUS_PAUSED) {
                MaterialAlertDialogBuilder(activity)
                    .setTitle("Transferência em curso")
                    .setMessage("O Android continua a descarregar a APK: $detail."+
                        "\nPodes sair da aplicação e consultar o progresso nas notificações.")
                    .setNegativeButton("Fechar", null)
                    .setPositiveButton("Ver transferências") { _, _ -> openDownloads(activity) }
                    .show()
                return
            }
        }
        val version = match.groupValues[1]
        try {
            val filename = "SaudePratica-$version-${System.currentTimeMillis()}.apk"
            val req = DownloadManager.Request(Uri.parse(url))
                .setTitle("SaúdePrática $version")
                .setDescription("Download seguro para a pasta Downloads")
                .setMimeType("application/vnd.android.package-archive")
                .setAllowedOverMetered(true)
                .setAllowedOverRoaming(false)
                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, filename)
            val id = manager(activity).enqueue(req)
            if (!store.edit().putLong("download_id", id).putString("digest", hash)
                    .putString("release_url", url).putString("filename", filename)
                    .remove("alerted_id").commit()) {
                manager(activity).remove(id)
                error("Não foi possível guardar os dados da transferência.")
            }
            MaterialAlertDialogBuilder(activity)
                .setTitle("Download iniciado")
                .setMessage("O Android está a descarregar a APK para Ficheiros → Downloads."+
                    "\n\nO progresso aparece nas notificações. A transferência continua "+
                    "mesmo que feches a SaúdePrática. Quando terminar, toca na "+
                    "notificação de instalação para confirmar a atualização.")
                .setNegativeButton("Fechar", null)
                .setPositiveButton("Ver transferências") { _, _ -> openDownloads(activity) }
                .show()
        } catch (e: Exception) {
            alert(activity, "Não foi possível iniciar a transferência: "+
                (e.message ?: e.javaClass.simpleName))
        }
    }

    fun resumeIfAllowed(activity: Activity) {
        val store = prefs(activity)
        if (store.getBoolean("awaiting_install_permission", false) &&
            (Build.VERSION.SDK_INT < 26 ||
             activity.packageManager.canRequestPackageInstalls())) {
            store.edit().remove("awaiting_install_permission").apply()
            finishInstallation(activity)
            return
        }
        val id = store.getLong("download_id", -1L)
        if (id <= 0L || store.getLong("alerted_id", -1L) == id) return
        val status = runCatching { queryStatus(activity, id).first }.getOrDefault(-1)
        if (status == DownloadManager.STATUS_SUCCESSFUL) {
            store.edit().putLong("alerted_id", id).apply()
            MaterialAlertDialogBuilder(activity)
                .setTitle("APK da SaúdePrática descarregada")
                .setMessage("A APK já está disponível em Ficheiros → Downloads."+
                    "\nQueres verificar a assinatura e instalar a atualização?")
                .setNegativeButton("Mais tarde", null)
                .setPositiveButton("Verificar e instalar") { _, _ -> finishInstallation(activity) }
                .show()
        } else if (status == DownloadManager.STATUS_FAILED) {
            store.edit().putLong("alerted_id", id).apply()
            alert(activity, "O Android não conseguiu descarregar a atualização."+
                "\nVolta a Verificar atualizações para repetir, "+
                "ou usa o navegador para descarregar do GitHub.")
        }
    }

    fun completed(context: Context, id: Long) {
        if (prefs(context).getLong("download_id", -1L) != id) return
        val status = runCatching { queryStatus(context, id).first }.getOrDefault(-1)
        val notificationManager = context.getSystemService(NotificationManager::class.java)
        notificationManager.createNotificationChannel(NotificationChannel(
            CHANNEL, "Atualizações SaúdePrática", NotificationManager.IMPORTANCE_DEFAULT))
        val ready = status == DownloadManager.STATUS_SUCCESSFUL
        val click = Intent(context, UpdateDownloadedActivity::class.java).apply {
            action = "com.mediagenda.app.OPEN_DOWNLOADED_UPDATE"
            data = Uri.parse("saudepratica://download/$id")
        }
        val pi = PendingIntent.getActivity(context, id.hashCode(), click,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val n = NotificationCompat.Builder(context, CHANNEL)
            .setSmallIcon(android.R.drawable.stat_sys_download_done)
            .setContentTitle(if (ready) "SaúdePrática: APK descarregada"
                else "SaúdePrática: download falhou")
            .setContentText(if (ready) "Toca para verificar e instalar a atualização"
                else "Abre SaúdePrática e volta a verificar atualizações")
            .setAutoCancel(true)
            .setContentIntent(pi)
            .build()
        notificationManager.notify(198901, n)
    }

    fun finishInstallation(activity: Activity) {
        if (Build.VERSION.SDK_INT >= 26 &&
            !activity.packageManager.canRequestPackageInstalls()) {
            MaterialAlertDialogBuilder(activity)
                .setTitle("Autorizar a instalação desta fonte")
                .setMessage("Para instalar a APK, o Android precisa de autorização para "+
                    "atualizações fornecidas pela SaúdePrática. "+
                    "A instalação continuará a exigir a tua confirmação.")
                .setNegativeButton("Cancelar", null)
                .setPositiveButton("Abrir definições") { _, _ ->
                    prefs(activity).edit()
                        .putBoolean("awaiting_install_permission", true).apply()
                    activity.startActivity(Intent(
                        Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:"+activity.packageName)))
                }.show()
            return
        }
        val id = prefs(activity).getLong("download_id", -1L)
        if (id <= 0L) {
            alert(activity, "Não existe uma APK descarregada por esta aplicação.")
            return
        }
        val progress = ProgressBar(activity).apply {
            isIndeterminate = true
            setPadding(40, 26, 40, 26)
        }
        val dialog = MaterialAlertDialogBuilder(activity)
            .setTitle("A verificar a APK")
            .setMessage("A confirmar o SHA-256, a versão e o certificado Android…")
            .setView(progress)
            .setCancelable(false).create()
        dialog.show()
        Thread {
            val result = runCatching {
                val status = queryStatus(activity, id).first
                require(status == DownloadManager.STATUS_SUCCESSFUL) {
                    "A transferência ainda não terminou."
                }
                val output = File(File(activity.cacheDir, "updates"),
                    "SaudePratica-verified.apk")
                require(output.parentFile!!.isDirectory ||
                    output.parentFile!!.mkdirs()) { "Sem acesso à pasta de atualização." }
                val temp = File(output.parentFile, "SaudePratica-verifying.apk")
                val expected = prefs(activity).getString("digest", null).orEmpty()
                require(HEX.matches(expected)) { "Falta o SHA-256 da Release." }
                temp.delete()
                try {
                    val sha = MessageDigest.getInstance("SHA-256")
                    var total = 0L
                    manager(activity).openDownloadedFile(id).use { fd ->
                        java.io.FileInputStream(fd.fileDescriptor).use { input ->
                            FileOutputStream(temp).use { dest ->
                                val buffer = ByteArray(65536)
                                while (true) {
                                    val n = input.read(buffer)
                                    if (n == -1) break
                                    total += n
                                    require(total <= MAX_BYTES) { "APK demasiado grande." }
                                    sha.update(buffer, 0, n)
                                    dest.write(buffer, 0, n)
                                }
                                dest.fd.sync()
                            }
                        }
                    }
                    require(total > 0L) { "APK vazia." }
                    val actual = sha.digest().joinToString("") {
                        "%02x".format(it.toInt() and 255)
                    }
                    require(actual.equals(expected, true)) {
                        "A APK não corresponde à assinatura SHA-256 publicada no GitHub."
                    }
                    validatePackage(activity, temp)
                    output.delete()
                    check(temp.renameTo(output)) { "Falhou a preparação da APK." }
                    output
                } finally { temp.delete() }
            }
            activity.runOnUiThread {
                dialog.dismiss()
                if (activity.isFinishing || activity.isDestroyed) return@runOnUiThread
                result.onSuccess { apk -> SessionApkUpdater.install(activity, apk) }
                    .onFailure { error ->
                        alert(activity, "Falhou a validação: "+
                            (error.message ?: error.javaClass.simpleName)+
                            "\nA APK continua disponível na pasta Downloads "+
                            "para diagnóstico ou instalação manual.")
                    }
            }
        }.start()
    }

    @Suppress("DEPRECATION")
    private fun validatePackage(activity: Activity, apk: File) {
        val pm = activity.packageManager
        val flag = if (Build.VERSION.SDK_INT >= 28)
            PackageManager.GET_SIGNING_CERTIFICATES else PackageManager.GET_SIGNATURES
        val candidate = pm.getPackageArchiveInfo(apk.absolutePath, flag)
            ?: error("APK não reconhecida pelo Android.")
        require(candidate.packageName == activity.packageName) {
            "A APK pertence a outra aplicação."
        }
        val installed = pm.getPackageInfo(activity.packageName, flag)
        val nextVersion = if (Build.VERSION.SDK_INT >= 28) candidate.longVersionCode
                          else candidate.versionCode.toLong()
        val installedVersion = if (Build.VERSION.SDK_INT >= 28) installed.longVersionCode
                               else installed.versionCode.toLong()
        require(nextVersion > installedVersion) { "Esta APK não é mais recente." }
        val candidateCerts = if (Build.VERSION.SDK_INT >= 28)
            candidate.signingInfo?.apkContentsSigners else candidate.signatures
        val installedCerts = if (Build.VERSION.SDK_INT >= 28)
            installed.signingInfo?.apkContentsSigners else installed.signatures
        require(!candidateCerts.isNullOrEmpty() && !installedCerts.isNullOrEmpty() &&
            candidateCerts.size == installedCerts.size &&
            candidateCerts.all { c ->
                installedCerts.any { it.toByteArray().contentEquals(c.toByteArray()) }
            }) { "Certificado Android diferente da aplicação instalada." }
    }

    private fun openDownloads(activity: Activity) {
        try { activity.startActivity(Intent(DownloadManager.ACTION_VIEW_DOWNLOADS)) }
        catch (_: Exception) { alert(activity, "Abre Ficheiros → Downloads.") }
    }
    private fun alert(activity: Activity, msg: String) {
        if (!activity.isFinishing && !activity.isDestroyed)
            MaterialAlertDialogBuilder(activity)
                .setTitle("Atualização SaúdePrática")
                .setMessage(msg).setPositiveButton("OK", null).show()
    }
}

class UpdateDownloadReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == DownloadManager.ACTION_DOWNLOAD_COMPLETE)
            InAppUpdateInstaller.completed(context,
                intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1L))
    }
}

class UpdateDownloadedActivity : Activity() {
    override fun onResume() {
        super.onResume()
        InAppUpdateInstaller.resumeIfAllowed(this)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        MaterialAlertDialogBuilder(this)
            .setTitle("Instalar a nova SaúdePrática")
            .setMessage("O Android descarregou a APK para a pasta Downloads."+
                "\nQueres verificar o ficheiro e iniciar a instalação?")
            .setNegativeButton("Mais tarde") { _, _ -> finish() }
            .setPositiveButton("Verificar e instalar") { _, _ ->
                InAppUpdateInstaller.finishInstallation(this)
            }
            .setOnCancelListener { finish() }.show()
    }
}
