"""SaúdePrática 1.9.76: check published GitHub Releases and prompt safely for updates."""
from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"

def replace(path,old,new,label):
    content=path.read_text(encoding="utf-8")
    count=content.count(old)
    if count!=1:raise RuntimeError(f"v94 {label}: anchor appears {count} times")
    path.write_text(content.replace(old,new,1),encoding="utf-8")

updater = r'''package com.mediagenda.app

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * Anonymous, read-only GitHub Releases version check. No profile, medical data,
 * device ID or login is transmitted. Never installs an APK silently.
 *
 * Do not promote unverified Actions artifacts to application updates:
 * only a published, non-draft GitHub Release with the exact signed APK asset
 * named SaudePratica.apk may be offered.
 */
object SaudePraticaUpdateChecker {
    private const val API =
        "https://api.github.com/repos/DanBar1971/AndroidAppDev/releases/latest"
    private const val RELEASES =
        "https://github.com/DanBar1971/AndroidAppDev/releases"
    private const val ASSET_NAME="SaudePratica.apk"
    private const val PREFIX=
        "https://github.com/DanBar1971/AndroidAppDev/releases/download/"
    private const val EVERY=12L*60L*60L*1000L
    private val versionPattern=Regex("""^v?(\d+)\.(\d+)\.(\d+)$""")
    @Volatile private var busy=false

    private data class Answer(
        val status:String,
        val tag:String="",
        val download:String="",
        val details:String=""
    )

    private fun version(value:String):List<Int>? =
        versionPattern.matchEntire(value.trim())?.groupValues?.drop(1)
            ?.mapNotNull{it.toIntOrNull()}?.takeIf{it.size==3}

    private fun newer(release:String,current:String):Boolean {
        val a=version(release)?:return false
        val b=version(current)?:return false
        for(i in 0..2) {
            if(a[i]>b[i])return true
            if(a[i]<b[i])return false
        }
        return false
    }

    fun check(activity:AppCompatActivity,manual:Boolean=false) {
        val prefs=activity.getSharedPreferences("saudepratica_updates_v1",
            Context.MODE_PRIVATE)
        val now=System.currentTimeMillis()
        if(!manual && now-prefs.getLong("last_checked",0)<EVERY)return
        synchronized(this) {
            if(busy)return
            busy=true
        }
        if(!manual)prefs.edit().putLong("last_checked",now).apply()

        Thread({
            val answer=try{
                val conn=(URL(API).openConnection() as HttpURLConnection).apply{
                    requestMethod="GET"
                    connectTimeout=8000
                    readTimeout=8000
                    setRequestProperty("Accept","application/vnd.github+json")
                    setRequestProperty("User-Agent","SaudePratica-Android-UpdateCheck")
                    setRequestProperty("X-GitHub-Api-Version","2022-11-28")
                }
                try{
                    when(conn.responseCode){
                        200->{
                            val body=conn.inputStream.bufferedReader(Charsets.UTF_8)
                                .use{it.readText()}
                            val json=JSONObject(body)
                            if(json.optBoolean("draft")||json.optBoolean("prerelease")){
                                Answer("no_release")
                            }else{
                                val tag=json.optString("tag_name")
                                val assets=json.optJSONArray("assets")
                                var link=""
                                if(assets!=null){
                                    for(i in 0 until assets.length()){
                                        val asset=assets.optJSONObject(i)?:continue
                                        if(asset.optString("name")!=ASSET_NAME ||
                                            asset.optString("state")!="uploaded")continue
                                        val url=asset.optString("browser_download_url")
                                        if(url.startsWith(PREFIX) &&
                                            url.endsWith("/"+ASSET_NAME)) {
                                            link=url
                                            break
                                        }
                                    }
                                }
                                when{
                                    version(tag)==null->Answer("invalid_release")
                                    newer(tag,BuildConfig.VERSION_NAME) && link.isBlank()->
                                        Answer("no_apk",tag)
                                    newer(tag,BuildConfig.VERSION_NAME)->
                                        Answer("update",tag,link)
                                    else->Answer("current",tag)
                                }
                            }
                        }
                        404->Answer("no_release")
                        403->Answer("network",
                            details="O GitHub recusou temporariamente a consulta.")
                        else->Answer("network",
                            details="Resposta do GitHub: "+conn.responseCode)
                    }
                }finally{conn.disconnect()}
            }catch(e:Exception){
                Answer("network",details=e.localizedMessage.orEmpty())
            }
            activity.runOnUiThread {
                busy=false
                if(activity.isFinishing || activity.isDestroyed)return@runOnUiThread
                show(activity,answer,manual)
            }
        },"SaudePraticaUpdateCheck").start()
    }

    private fun show(activity:Activity,a:Answer,manual:Boolean) {
        val prefs=activity.getSharedPreferences("saudepratica_updates_v1",
            Context.MODE_PRIVATE)
        if(a.status=="update"){
            if(!manual && prefs.getString("prompted_tag",null)==a.tag)return
            prefs.edit().putString("prompted_tag",a.tag).apply()
            MaterialAlertDialogBuilder(activity)
                .setTitle("📲 SaúdePrática "+a.tag+" disponível")
                .setMessage("Tens a versão "+BuildConfig.VERSION_NAME+
                    " instalada. Há uma atualização assinada publicada no GitHub."+
                    "\n\nQueres descarregá-la? A instalação será confirmada pelo Android. "+
                    "Não desinstales a aplicação anterior, para manter os dados.")
                .setPositiveButton("Descarregar atualização"){_,_->
                    try{
                        activity.startActivity(Intent(Intent.ACTION_VIEW,
                            Uri.parse(a.download)))
                    }catch(e:Exception){
                        MaterialAlertDialogBuilder(activity)
                            .setMessage("Não foi possível abrir o navegador.")
                            .setPositiveButton("OK",null).show()
                    }
                }
                .setNegativeButton("Mais tarde",null)
                .show()
            return
        }
        if(!manual)return
        val detail=when(a.status){
            "current"->"Já tens a versão mais recente publicada no GitHub."+
                "\nVersão instalada: "+BuildConfig.VERSION_NAME
            "no_release"->"Ainda não existe uma versão publicada em "+
                "GitHub Releases (ou o repositório não é público). "+
                "Por isso o endereço de download apresentava erro 404. "+
                "O autor precisa de publicar a APK assinada numa Release."
            "no_apk"->"A versão "+a.tag+" existe, mas falta anexar o ficheiro "+
                "assinado "+ASSET_NAME+" à Release. Ainda não é possível atualizar."
            "invalid_release"->"A versão publicada no GitHub não usa uma "+
                "etiqueta reconhecida (ex.: v1.9.76)."
            else->"Não foi possível verificar as atualizações. "+
                "Confirma a ligação à internet e volta a tentar."+
                if(a.details.isNotBlank())"\n"+a.details else ""
        }
        MaterialAlertDialogBuilder(activity)
            .setTitle("Atualizações da SaúdePrática")
            .setMessage(detail)
            .setPositiveButton("OK",null)
            .setNeutralButton("Ver versões no GitHub"){_,_->
                runCatching{activity.startActivity(Intent(Intent.ACTION_VIEW,
                    Uri.parse(RELEASES)))}
            }
            .show()
    }
}
'''
(base/"SaudePraticaUpdateChecker.kt").write_text(updater,encoding="utf-8")

main=base/"MainActivity.kt"
replace(main,'''        // Fallback for camera apps that do not deliver a reliable ActivityResult.
        // If image bytes are really present, the same private capture is shown.''','''        // Check anonymous GitHub release metadata at most once every 12 hours.
        // Never interrupt medication scheduling or require permissions.
        if(::content.isInitialized && profiles.all().isNotEmpty())
            com.mediagenda.app.SaudePraticaUpdateChecker.check(this,false)
        // Fallback for camera apps that do not deliver a reliable ActivityResult.
        // If image bytes are really present, the same private capture is shown.''',"onResume scheduled checks")

replace(main,'''        box.addView(infoCard("ℹ️", "Acerca", "SaúdePrática — versão, autor e contacto") {
            showAboutSaudePratica()
        })''','''        box.addView(infoCard("📲", "Verificar atualizações",
            "Versão instalada "+BuildConfig.VERSION_NAME+
            " · procurar nova APK no GitHub") {
            com.mediagenda.app.SaudePraticaUpdateChecker.check(this,true)
        })
        box.addView(infoCard("ℹ️", "Acerca", "SaúdePrática — versão, autor e contacto") {
            showAboutSaudePratica()
        })''',"manual updates in options help")

help=base/"SupportHelpActivity.kt"
replace(help,'''        parent.addView(action(tr("✉ Contactar suporte","✉ Contact support","✉ Contacter le support",
            "✉ Support kontaktieren","✉ Contactar soporte")){''','''        val updateGuide=panel()
        updateGuide.addView(text(tr("📲 Atualizações da aplicação",
            "📲 Application updates","📲 Mises à jour","📲 App-Updates",
            "📲 Actualizaciones"),18f))
        updateGuide.addView(text(tr(
            "Em Opções → Ajuda e informações → Verificar atualizações podes consultar novas versões. A SaúdePrática também verifica automaticamente, sem enviar dados médicos. Se houver uma APK publicada no GitHub, abre o download e o Android pede confirmação para instalar. Sem versão publicada, o GitHub mostra 404. Não desinstales a app para atualizar.",
            "Options → Help and information → Check for updates. The app also checks automatically without sending medical data. A published GitHub APK opens in your browser; Android asks you to confirm installation. Without a published release the link returns 404. Do not uninstall before updating.",
            "Options → Aide et informations → Rechercher des mises à jour. La vérification automatique n'envoie pas de données médicales. Le téléchargement ouvre le navigateur et Android demande confirmation. Sans version publiée, le lien renvoie 404. Ne désinstallez pas l'application.",
            "Optionen → Hilfe und Informationen → Auf Updates prüfen. Die automatische Prüfung überträgt keine Gesundheitsdaten. Ein veröffentlichter Download öffnet den Browser; Android verlangt die Bestätigung. Ohne Release erscheint Fehler 404. Nicht deinstallieren.",
            "Opciones → Ayuda e información → Buscar actualizaciones. La búsqueda automática no envía datos médicos. La APK publicada se descarga mediante el navegador y Android solicita confirmación. Sin versión publicada aparece el error 404. No desinstales la aplicación."
        ),14f,muted))
        addCard(parent,updateGuide)
        parent.addView(action(tr("✉ Contactar suporte","✉ Contact support","✉ Contacter le support",
            "✉ Support kontaktieren","✉ Contactar soporte")){''',"multilingual help for updates")

gradle=root/"app/build.gradle.kts"
replace(gradle,'versionCode = 85','versionCode = 86',"versionCode")
replace(gradle,'versionName = "1.9.75"','versionName = "1.9.76"',"versionName")
print("SaúdePrática v1.9.76: opt-in and automatic GitHub Release update checks")
