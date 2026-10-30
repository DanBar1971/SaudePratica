package com.mediagenda.app

import android.app.Activity
import android.app.Dialog
import android.app.KeyguardManager
import android.content.Context
import android.content.Intent
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.util.Base64
import android.view.Gravity
import android.view.View
import android.view.Window
import android.view.WindowManager
import android.webkit.WebView
import android.widget.Button
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.concurrent.thread

/** Public, non-personal informational cards. Never uploads patients or statistics.
 * Catalog and already-seen cards are cached in private app storage.
 */
internal object HealthTipsManager {
    private const val CATALOG_URL =
        "https://danbar1971.github.io/SaudePratica/info_saude/informacoes.json"
    private const val RESOURCE_URL =
        "https://danbar1971.github.io/SaudePratica/info_saude/"
    private const val PREFS = "saudepratica_health_tips_v1"
    private const val MAX_SIZE = 2 * 1024 * 1024
    private const val DAY = 86400000L
    private val active = AtomicBoolean(false)
    private val main = Handler(Looper.getMainLooper())

    data class Tip(val id: String, val title: String, val image: String,
        val actionLabel: String, val actionUrl: String, val closeLabel: String,
        val minDays: Int, val enabled: Boolean) {
        fun toJson() = JSONObject().apply {
            put("id", id); put("title", title); put("image", image)
            put("action_label", actionLabel); put("action_url", actionUrl)
            put("close_label", closeLabel); put("minimum_days_between_shows", minDays)
            put("enabled", enabled)
        }
    }

    private fun folder(c: Context) = File(c.filesDir, "info_saude").apply { mkdirs() }
    private fun prefs(c: Context) = c.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    private fun imagePath(c: Context, tip: Tip): File {
        val ext = tip.image.substringAfterLast('.', "svg").lowercase()
        return File(folder(c), tip.id + "." + ext)
    }
    private fun safeTip(raw: JSONObject): Tip? {
        val id = raw.optString("id")
        val image = raw.optString("image")
        if(!id.matches(Regex("[a-zA-Z0-9_-]{1,50}"))) return null
        if(!image.matches(Regex("imagens/[a-zA-Z0-9_./-]{1,100}\\.(svg|png|jpg|jpeg|webp)")) ||
            image.contains("..")) return null
        val url=raw.optString("action_url")
        if(url.isNotBlank() && (Uri.parse(url).scheme!="https" ||
            Uri.parse(url).host.isNullOrBlank())) return null
        return Tip(id, raw.optString("title").take(150), image,
            raw.optString("action_label","Saber mais").take(55), url,
            raw.optString("close_label","OK").take(25),
            raw.optInt("minimum_days_between_shows", 3).coerceIn(1,365),
            raw.optBoolean("enabled",true))
    }
    private fun parse(json: String): List<Tip> {
        val root=JSONObject(json)
        if(root.optInt("schema_version")!=1) return emptyList()
        val list=root.optJSONArray("items") ?: return emptyList()
        val tips=mutableListOf<Tip>()
        for(i in 0 until minOf(list.length(),100))
            list.optJSONObject(i)?.let{safeTip(it)}?.let{tips.add(it)}
        return tips.distinctBy{it.id}
    }
    private fun retrieve(url: String): ByteArray {
        val connection=(URL(url).openConnection() as HttpURLConnection).apply {
            connectTimeout=7000; readTimeout=9000
            instanceFollowRedirects=false
            setRequestProperty("User-Agent","SaudePratica-HealthTips/1")
        }
        try {
            if(connection.responseCode!=200) error("HTTP "+connection.responseCode)
            val reported=connection.contentLength
            if(reported>MAX_SIZE) error("Ficheiro demasiado grande")
            connection.inputStream.use{stream->
                val result=java.io.ByteArrayOutputStream()
                val block=ByteArray(8192)
                while(true) {
                    val n=stream.read(block)
                    if(n<0)break
                    if(result.size()+n>MAX_SIZE) error("Limite de tamanho")
                    result.write(block,0,n)
                }
                return result.toByteArray()
            }
        } finally {connection.disconnect()}
    }
    private fun catalog(c: Context, force: Boolean): List<Tip> {
        val store=prefs(c)
        val local=File(folder(c),"informacoes.json")
        if(force || !local.exists() ||
            System.currentTimeMillis()-store.getLong("last_fetch",0L)>DAY) {
            runCatching {
                val data=retrieve(CATALOG_URL).toString(Charsets.UTF_8)
                require(parse(data).isNotEmpty()){"Catálogo vazio ou inválido"}
                val tmp=File(folder(c),"informacoes.tmp")
                tmp.writeText(data, Charsets.UTF_8)
                check(tmp.renameTo(local)){"Não foi possível guardar o catálogo"}
                store.edit().putLong("last_fetch",System.currentTimeMillis()).apply()
            }.onFailure{android.util.Log.w("SaudePraticaTips","Sem rede: usar catálogo local",it)}
        }
        return runCatching{parse(local.readText(Charsets.UTF_8))}.getOrDefault(emptyList())
    }
    private fun ensureImage(c: Context, tip: Tip): File? {
        val f=imagePath(c,tip)
        if(f.exists() && f.length() in 1..MAX_SIZE.toLong()) return f
        return runCatching {
            val data=retrieve(RESOURCE_URL+tip.image)
            require(data.isNotEmpty()){"Imagem vazia"}
            val tmp=File(folder(c),tip.id+".tmp")
            tmp.writeBytes(data)
            check(tmp.renameTo(f)){"Erro ao guardar imagem"}
            f
        }.getOrNull()
    }

    fun history(c: Context): List<Pair<Tip,Long>> {
        val p=prefs(c)
        return p.all.keys.asSequence().filter{it.startsWith("seen_")}.mapNotNull{key->
            val id=key.removePrefix("seen_")
            val raw=p.getString("saved_"+id,null) ?: return@mapNotNull null
            val tip=runCatching{safeTip(JSONObject(raw))}.getOrNull() ?: return@mapNotNull null
            tip to p.getLong(key,0)
        }.sortedByDescending{it.second}.take(100).toList()
    }

    fun frequency(c:Context)=prefs(c).getInt("frequency_days",3)
    fun setFrequency(c:Context,days:Int) {
        require(days in listOf(0,1,3,7))
        prefs(c).edit().putInt("frequency_days",days).apply()
    }

    /** Called only after PIN/login and profile data initialization. */
    fun maybeShow(activity: Activity) {
        if(frequency(activity)==0 || !active.compareAndSet(false,true))return
        val app=activity.applicationContext
        thread(name="health-tips-catalog",isDaemon=true) {
            try {
                val p=prefs(app)
                val now=System.currentTimeMillis()
                val last=p.getLong("last_popup",0)
                if(last>0 && now-last<frequency(app)*DAY)return@thread
                val choices=catalog(app,false).filter{it.enabled}.filter{tip->
                    val prior=p.getLong("seen_"+tip.id,0L)
                    prior==0L || now-prior>=tip.minDays*DAY
                }
                if(choices.isEmpty())return@thread
                // Prioritize new items; shuffle to prevent an editorial fixed order.
                val fresh=choices.filter{p.getLong("seen_"+it.id,0)==0L}
                val tip=(fresh.ifEmpty{choices}).random()
                val file=ensureImage(app,tip) ?: return@thread
                main.postDelayed({
                    try {
                        val locked=(activity.getSystemService(Context.KEYGUARD_SERVICE)
                            as KeyguardManager).isKeyguardLocked
                        if(!activity.isFinishing && !activity.isDestroyed &&
                            activity.hasWindowFocus() && !locked &&
                            frequency(activity)>0) {
                            show(activity,tip,file,true)
                        }
                    } finally {active.set(false)}
                },1200)
            } catch(t:Throwable) {
                android.util.Log.w("SaudePraticaTips","Não foi possível apresentar dica",t)
            } finally {
                // Keep lock until delayed UI callback, if one was posted.
                main.postDelayed({active.set(false)},3000)
            }
        }
    }
    private fun dp(c:Context,n:Int)=(n*c.resources.displayMetrics.density+0.5f).toInt()
    private fun button(c:Context,text:String,filled:Int):Button=Button(c).apply {
        this.text=text
        textSize=if(text.length>22)12f else 14f
        isAllCaps=false
        setTextColor(Color.WHITE)
        minHeight=dp(c,52)
        setPadding(dp(c,7),dp(c,3),dp(c,7),dp(c,3))
        background=GradientDrawable().apply {
            setColor(filled);cornerRadius=dp(c,14).toFloat()
        }
    }
    private fun imageView(c:Context,tip:Tip,file:File):View {
        if(file.extension.lowercase()=="svg") {
            return WebView(c).apply {
                settings.javaScriptEnabled=false
                settings.allowFileAccess=false
                settings.allowContentAccess=false
                setBackgroundColor(Color.TRANSPARENT)
                isVerticalScrollBarEnabled=false
                isHorizontalScrollBarEnabled=false
                val encoded=Base64.encodeToString(file.readBytes(),Base64.NO_WRAP)
                val html="<html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head>"+
                    "<body style='margin:0;display:flex;align-items:center;justify-content:center;"+
                    "width:100vw;height:100vh;overflow:hidden;background:transparent'>"+
                    "<img alt='Informação SaúdePrática' src='data:image/svg+xml;base64,"+
                    encoded+"' style='object-fit:contain;max-width:100%;max-height:100%;width:100%;height:100%'>"+
                    "</body></html>"
                loadDataWithBaseURL("https://danbar1971.github.io/",html,"text/html","UTF-8",null)
            }
        }
        return ImageView(c).apply {
            scaleType=ImageView.ScaleType.FIT_CENTER
            setImageBitmap(BitmapFactory.decodeFile(file.absolutePath))
            contentDescription=tip.title
            adjustViewBounds=true
        }
    }
    fun show(activity:Activity,tip:Tip,file:File,automatic:Boolean) {
        if(!file.exists() || activity.isFinishing || activity.isDestroyed)return
        val dialog=Dialog(activity)
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE)
        val content=LinearLayout(activity).apply {
            orientation=LinearLayout.VERTICAL
            setBackgroundColor(Color.rgb(250,247,242))
            setPadding(dp(activity,5),dp(activity,5),dp(activity,5),dp(activity,7))
        }
        val picture=FrameLayout(activity)
        picture.addView(imageView(activity,tip,file),FrameLayout.LayoutParams(-1,-1))
        content.addView(picture,LinearLayout.LayoutParams(-1,0,1f))
        val actions=LinearLayout(activity).apply {
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER
            setPadding(dp(activity,4),dp(activity,5),dp(activity,4),dp(activity,2))
        }
        if(tip.actionUrl.isNotBlank()) {
            val open=button(activity,tip.actionLabel,Color.rgb(15,124,115))
            actions.addView(open,LinearLayout.LayoutParams(0,dp(activity,55),1.45f).apply {
                rightMargin=dp(activity,5)
            })
            open.setOnClickListener {
                val uri=Uri.parse(tip.actionUrl)
                if(uri.scheme=="https") {
                    runCatching{activity.startActivity(Intent(Intent.ACTION_VIEW,uri))}
                        .onFailure{android.widget.Toast.makeText(activity,
                            "Não foi possível abrir a ligação.",android.widget.Toast.LENGTH_SHORT).show()}
                }
                dialog.dismiss()
            }
        }
        val ok=button(activity,tip.closeLabel,Color.rgb(31,50,72))
        actions.addView(ok,LinearLayout.LayoutParams(0,dp(activity,55),1f))
        ok.setOnClickListener {dialog.dismiss()}
        content.addView(actions,LinearLayout.LayoutParams(-1,-2))
        dialog.setContentView(content)
        dialog.window?.apply {
            setBackgroundDrawableResource(android.R.color.transparent)
            setLayout((activity.resources.displayMetrics.widthPixels*0.96).toInt(),
                (activity.resources.displayMetrics.heightPixels*0.89).toInt())
            addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND)
        }
        dialog.show()
        dialog.window?.setLayout((activity.resources.displayMetrics.widthPixels*0.96).toInt(),
            (activity.resources.displayMetrics.heightPixels*0.89).toInt())
        if(automatic) {
            val now=System.currentTimeMillis()
            prefs(activity).edit().putLong("seen_"+tip.id,now)
                .putLong("last_popup",now)
                .putString("saved_"+tip.id,tip.toJson().toString()).apply()
        }
    }
    fun cachedImage(c:Context,tip:Tip)=imagePath(c,tip).takeIf{it.exists()}
    fun refreshAndBrowse(activity:Activity,done:(List<Tip>)->Unit) {
        val app=activity.applicationContext
        thread(name="health-tips-manual",isDaemon=true) {
            val cards=runCatching{catalog(app,true)}.getOrDefault(emptyList())
            main.post{if(!activity.isFinishing && !activity.isDestroyed)done(cards)}
        }
    }
    fun openManual(activity:Activity,tip:Tip) {
        val f=cachedImage(activity,tip)
        if(f!=null) {show(activity,tip,f,false);return}
        thread(name="health-tips-image",isDaemon=true) {
            val downloaded=ensureImage(activity.applicationContext,tip)
            main.post {
                if(downloaded!=null && !activity.isFinishing && !activity.isDestroyed)
                    show(activity,tip,downloaded,false)
            }
        }
    }
}
