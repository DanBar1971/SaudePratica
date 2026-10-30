package com.mediagenda.app

import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.widget.Toast
import androidx.core.content.FileProvider
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest

/**
 * A user-triggered, in-app GitHub APK download. No silently installed updates.
 * Validates the published SHA-256 and exact installed signing certificate
 * before asking Android's system installer to update this package.
 */
internal object InAppUpdateInstaller {
    private const val PREFIX=
        "https://github.com/DanBar1971/AndroidAppDev/releases/download/"
    private const val MAX_BYTES=260L*1024*1024
    private val regex=Regex("^[a-fA-F0-9]{64}$")
    @Volatile private var busy=false
    private fun target(a:Activity)=File(File(a.cacheDir,"updates"),"SaudePratica-update.apk")
    private fun pref(a:Activity)=a.getSharedPreferences(
        "saudepratica_update_install_v1",Activity.MODE_PRIVATE)

    fun install(activity:Activity,url:String,digest:String){
        if(busy)return
        val hash=digest.removePrefix("sha256:")
        if(!url.startsWith(PREFIX)||!url.endsWith("/SaudePratica.apk")||
            !regex.matches(hash)){
            message(activity,"A Release não tem uma APK ou assinatura digital verificável.")
            return
        }
        busy=true
        Toast.makeText(activity,"A descarregar a atualização na SaúdePrática…",
            Toast.LENGTH_LONG).show()
        Thread {
            val result=runCatching{
                val out=target(activity)
                require(out.parentFile!!.isDirectory||out.parentFile!!.mkdirs())
                val staging=File(out.parentFile,"SaudePratica-update.part")
                staging.delete()
                try {
                    val conn=URL(url).openConnection() as HttpURLConnection
                    conn.connectTimeout=15000;conn.readTimeout=45000
                    conn.instanceFollowRedirects=true
                    conn.setRequestProperty("User-Agent","SaudePratica-Android-Update")
                    try{
                        require(conn.responseCode==200){"Download indisponível (HTTP "+conn.responseCode+")."}
                        require(conn.url.protocol=="https"){"A ligação não é segura."}
                        val size=conn.contentLengthLong
                        require(size in 1..MAX_BYTES){"A APK não tem um tamanho válido."}
                        val sha=MessageDigest.getInstance("SHA-256")
                        var read=0L
                        conn.inputStream.use{input->
                            staging.outputStream().use{output->
                                val bytes=ByteArray(64*1024)
                                while(true){
                                    val n=input.read(bytes)
                                    if(n<0)break
                                    read+=n
                                    require(read<=MAX_BYTES){"Ficheiro maior do que o permitido."}
                                    sha.update(bytes,0,n);output.write(bytes,0,n)
                                }
                            }
                        }
                        require(read==size){"Download incompleto."}
                        val actual=sha.digest().joinToString(""){
                            "%02x".format(it.toInt() and 0xff)
                        }
                        require(actual.equals(hash,true)){"SHA-256 da APK diferente do GitHub."}
                        validatePackage(activity,staging)
                        out.delete()
                        check(staging.renameTo(out)){"Não foi possível preparar a APK."}
                        pref(activity).edit().putBoolean("ready",true).commit()
                    }finally{conn.disconnect()}
                }finally{staging.delete()}
            }
            activity.runOnUiThread {
                busy=false
                if(activity.isFinishing||activity.isDestroyed)return@runOnUiThread
                result.onSuccess { showInstaller(activity) }
                    .onFailure { message(activity,
                        "Não foi possível preparar a atualização: "+
                        (it.message?:"erro desconhecido")) }
            }
        }.start()
    }

    @Suppress("DEPRECATION")
    private fun validatePackage(activity:Activity,apk:File){
        val pm=activity.packageManager
        val flag=if(Build.VERSION.SDK_INT>=28)PackageManager.GET_SIGNING_CERTIFICATES
                 else PackageManager.GET_SIGNATURES
        val candidate=pm.getPackageArchiveInfo(apk.absolutePath,flag)
            ?:error("APK inválida.")
        require(candidate.packageName==activity.packageName){
            "A APK pertence a outra aplicação."
        }
        val installed=pm.getPackageInfo(activity.packageName,flag)
        val newVersion=if(Build.VERSION.SDK_INT>=28)candidate.longVersionCode
            else candidate.versionCode.toLong()
        val oldVersion=if(Build.VERSION.SDK_INT>=28)installed.longVersionCode
            else installed.versionCode.toLong()
        require(newVersion>oldVersion){"A versão descarregada não é mais recente."}
        val newSignatures=if(Build.VERSION.SDK_INT>=28)
            candidate.signingInfo?.apkContentsSigners else candidate.signatures
        val original=if(Build.VERSION.SDK_INT>=28)
            installed.signingInfo?.apkContentsSigners else installed.signatures
        require(!newSignatures.isNullOrEmpty()&&!original.isNullOrEmpty() &&
            newSignatures.size==original.size &&
            newSignatures.all{candidateSigner->
                original.any{it.toByteArray().contentEquals(candidateSigner.toByteArray())}
            }){"Certificado Android diferente do original."}
    }

    fun resumeIfAllowed(activity:Activity){
        if(pref(activity).getBoolean("ready",false) &&
            (Build.VERSION.SDK_INT<26||
                activity.packageManager.canRequestPackageInstalls())){
            // Only continue when the user previously requested this download.
            pref(activity).edit().putBoolean("ready",false).apply()
            showInstaller(activity)
        }
    }

    private fun showInstaller(activity:Activity){
        val apk=target(activity)
        if(!apk.isFile)return
        if(Build.VERSION.SDK_INT>=26 &&
            !activity.packageManager.canRequestPackageInstalls()){
            MaterialAlertDialogBuilder(activity)
                .setTitle("Autorizar instalação de atualizações")
                .setMessage("Para atualizar diretamente, autoriza a SaúdePrática " +
                    "a instalar aplicações desta fonte. O Android continuará " +
                    "a pedir a confirmação da instalação.")
                .setNegativeButton("Cancelar"){_,_->
                    pref(activity).edit().putBoolean("ready",false).apply()
                }
                .setPositiveButton("Abrir definições"){_,_->
                    activity.startActivity(Intent(
                        Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:"+activity.packageName)))
                }.show()
            return
        }
        pref(activity).edit().putBoolean("ready",false).apply()
        val uri=FileProvider.getUriForFile(activity,
            activity.packageName+".fileprovider",apk)
        runCatching{
            activity.startActivity(Intent(Intent.ACTION_VIEW).apply{
                setDataAndType(uri,"application/vnd.android.package-archive")
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            })
        }.onFailure{message(activity,
            "Não foi possível abrir o instalador do Android: "+it.message)}
    }
    private fun message(activity:Activity,text:String){
        MaterialAlertDialogBuilder(activity)
            .setTitle("Atualização SaúdePrática")
            .setMessage(text).setPositiveButton("OK",null).show()
    }
}
