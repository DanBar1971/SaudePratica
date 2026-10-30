package com.mediagenda.app

import android.app.Activity
import android.app.PendingIntent
import android.content.Intent
import android.content.pm.PackageInstaller
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import java.io.File
import java.io.FileInputStream

/**
 * APK installer that never delegates a private FileProvider URL to a
 * manufacturer package parser. The system PackageInstaller receives the bytes
 * via a session and presents its own required approval to the user.
 *
 * InAppUpdateInstaller has already checked the public GitHub SHA-256, the app's
 * package name, a higher versionCode, and the original Android certificate.
 */
internal object SessionApkUpdater {
    @Volatile private var writing=false

    fun install(activity:Activity,apk:File) {
        if(writing){
            Toast.makeText(activity,"Preparação da atualização em curso…",
                Toast.LENGTH_LONG).show()
            return
        }
        writing=true
        Toast.makeText(activity,"A preparar o instalador Android…",
            Toast.LENGTH_LONG).show()
        Thread {
            val result=runCatching {
                require(apk.isFile && apk.length() in 1L..(260L*1024*1024)){
                    "A APK já não está disponível ou está incompleta."
                }
                val installer=activity.packageManager.packageInstaller
                val params=PackageInstaller.SessionParams(
                    PackageInstaller.SessionParams.MODE_FULL_INSTALL).apply {
                    setAppPackageName(activity.packageName)
                    setSize(apk.length())
                    if(Build.VERSION.SDK_INT>=31)
                        setRequireUserAction(PackageInstaller.SessionParams.USER_ACTION_REQUIRED)
                }
                val id=installer.createSession(params)
                var committed=false
                try {
                    installer.openSession(id).use { session ->
                        session.openWrite("base.apk",0,apk.length()).use { output ->
                            FileInputStream(apk).use{input->
                                input.copyTo(output,64*1024)
                            }
                            session.fsync(output)
                        }
                        // The callback must be mutable on targetSdk 35 so
                        // Android can populate EXTRA_STATUS and EXTRA_INTENT.
                        val statusIntent=Intent(activity,UpdateInstallStatusActivity::class.java)
                            .apply {
                                action="com.mediagenda.app.UPDATE_INSTALL_STATUS"
                                data=Uri.parse("saudepratica://install-session/$id")
                                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            }
                        val callback=PendingIntent.getActivity(
                            activity,id,statusIntent,
                            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE)
                        session.commit(callback.intentSender)
                        committed=true
                    }
                } finally {
                    if(!committed)runCatching{installer.abandonSession(id)}
                }
            }
            activity.runOnUiThread {
                writing=false
                if(activity.isFinishing || activity.isDestroyed)return@runOnUiThread
                result.onFailure { exception ->
                    MaterialAlertDialogBuilder(activity)
                        .setTitle("Não foi possível instalar a atualização")
                        .setMessage("O instalador Android não conseguiu preparar o pacote: "+
                            (exception.message?:"erro desconhecido")+
                            "\n\nA APK original também está disponível no GitHub.")
                        .setNegativeButton("Fechar",null)
                        .setPositiveButton("Abrir GitHub"){_,_->
                            activity.startActivity(Intent(Intent.ACTION_VIEW,
                                Uri.parse("https://github.com/DanBar1971/AndroidAppDev/releases/latest")))
                        }.show()
                }
            }
        }.start()
    }
}

/** User-visible Android installation confirmation; no silent installations. */
class UpdateInstallStatusActivity:Activity() {
    override fun onCreate(savedInstanceState:Bundle?) {
        super.onCreate(savedInstanceState)
        val status=intent.getIntExtra(PackageInstaller.EXTRA_STATUS,
            PackageInstaller.STATUS_FAILURE)
        if(status==PackageInstaller.STATUS_PENDING_USER_ACTION) {
            val approval:Intent?=if(Build.VERSION.SDK_INT>=33)
                intent.getParcelableExtra(Intent.EXTRA_INTENT,Intent::class.java)
            else {
                @Suppress("DEPRECATION")
                intent.getParcelableExtra(Intent.EXTRA_INTENT)
            }
            if(approval==null){
                showError("O Android não devolveu o pedido de autorização.")
                return
            }
            try {
                startActivity(approval)
                finish()
            } catch (e:Exception) {
                showError("O instalador Android recusou abrir: "+
                    (e.message?:"erro desconhecido"))
            }
            return
        }
        if(status==PackageInstaller.STATUS_SUCCESS){
            Toast.makeText(this,"Atualização instalada.",Toast.LENGTH_LONG).show()
            finish()
            return
        }
        val message=intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE)
            .orEmpty().take(500)
        showError("Falha da instalação Android ($status)."+
            if(message.isBlank())"" else "\n$message")
    }

    private fun showError(message:String) {
        if(isFinishing){finish();return}
        MaterialAlertDialogBuilder(this)
            .setTitle("Atualização não instalada")
            .setMessage(message+
                "\n\nPodes instalar manualmente a APK da Release oficial.")
            .setNegativeButton("Fechar"){_,_->finish()}
            .setPositiveButton("Ver GitHub"){_,_->
                startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(
                    "https://github.com/DanBar1971/AndroidAppDev/releases/latest")))
                finish()
            }.setOnCancelListener{finish()}.show()
    }
}
