#!/usr/bin/env python3
"""SaúdePrática v1.9.113: real photo, authentic UI and clickable embedded actions.
Apply after v132. Preserve application ID, signing and all clinical/user data.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app")
base=root/"src/main/java/com/mediagenda/app"
manager=base/"HealthTipsManager.kt"
s=manager.read_text(encoding="utf-8")

def one(old,new,label):
    global s
    n=s.count(old)
    assert n==1,(label,n)
    s=s.replace(old,new,1)

one('''import org.json.JSONObject''','''import org.json.JSONObject
import org.json.JSONArray''',"json bounds import")

one('''        val minDays: Int, val enabled: Boolean) {''',
'''        val minDays: Int, val enabled: Boolean,
        val embeddedActions: Boolean, val actionBounds: FloatArray?,
        val closeBounds: FloatArray?) {''',"persist embedded regions model")

one('''            put("enabled", enabled)
        }''',
'''            put("enabled", enabled)
            put("embedded_actions", embeddedActions)
            val coords=JSONObject()
            fun arr(bounds:FloatArray?):JSONArray {
                val a=JSONArray()
                bounds?.forEach{a.put(it.toDouble())}
                return a
            }
            if(actionBounds!=null)coords.put("action",arr(actionBounds))
            if(closeBounds!=null)coords.put("close",arr(closeBounds))
            put("embedded_action_regions", coords)
        }''',"serialize action hitboxes for offline history")

one('''    private fun safeTip(raw: JSONObject): Tip? {''',
'''    private fun bounds(raw:JSONObject,which:String):FloatArray? {
        val array=raw.optJSONObject("embedded_action_regions")
            ?.optJSONArray(which) ?: return null
        if(array.length()!=4)return null
        val b=FloatArray(4){array.optDouble(it,-1.0).toFloat()}
        if(b.any{it<0f || it>1f} || b[2]<=b[0] || b[3]<=b[1])return null
        return b
    }
    private fun safeTip(raw: JSONObject): Tip? {''',"validate normalized rectangles")

one('''            raw.optBoolean("enabled",true))''',
'''            raw.optBoolean("enabled",true),
            raw.optBoolean("embedded_actions",false),
            bounds(raw,"action"),bounds(raw,"close"))''',"read embedded action regions")

one('''        if(force || !local.exists() ||
            System.currentTimeMillis()-store.getLong("last_fetch",0L)>DAY) {''',
'''        if(force || !local.exists() || store.getInt("client_revision",0)<113 ||
            System.currentTimeMillis()-store.getLong("last_fetch",0L)>DAY) {''',"force fresh JSON once for users with previously cached vector")

one('''                store.edit().putLong("last_fetch",System.currentTimeMillis()).apply()''',
'''                store.edit().putLong("last_fetch",System.currentTimeMillis())
                    .putInt("client_revision",113).apply()''',"persist updated photo catalogue revision")

one('''    fun history(c: Context): List<Pair<Tip,Long>> {
        val p=prefs(c)''',
'''    fun history(c: Context): List<Pair<Tip,Long>> {
        val available=runCatching {parse(
            File(folder(c),"informacoes.json").readText(Charsets.UTF_8)
        ).associateBy{it.id}}.getOrDefault(emptyMap())
        val p=prefs(c)''',"archive inherits latest published item metadata")

one('''            val tip=runCatching{safeTip(JSONObject(raw))}.getOrNull() ?: return@mapNotNull null''',
'''            val tip=available[id] ?:
                runCatching{safeTip(JSONObject(raw))}.getOrNull() ?: return@mapNotNull null''',"update archive from catalog")

one('''        val actions=LinearLayout(activity).apply {''',
'''        if(tip.embeddedActions && file.extension.lowercase()!="svg") {
            // The real buttons are printed in the poster. Use transparent,
            // accessible Android hit areas above them, not a second button row.
            picture.post {
                if(!dialog.isShowing || picture.width<=0 || picture.height<=0)
                    return@post
                val options=BitmapFactory.Options().apply{inJustDecodeBounds=true}
                BitmapFactory.decodeFile(file.absolutePath,options)
                if(options.outWidth<=0 || options.outHeight<=0)return@post
                val ratio=options.outWidth.toFloat()/options.outHeight.toFloat()
                val displayWidth=minOf(picture.width.toFloat(),
                    picture.height*ratio)
                val displayHeight=displayWidth/ratio
                val originX=(picture.width-displayWidth)/2f
                val originY=(picture.height-displayHeight)/2f
                fun hit(rect:FloatArray?,description:String,action:()->Unit) {
                    if(rect==null)return
                    val w=(displayWidth*(rect[2]-rect[0])).toInt()
                    val h=(displayHeight*(rect[3]-rect[1])).toInt()
                    if(w<dp(activity,24) || h<dp(activity,24))return
                    val view=View(activity).apply {
                        contentDescription=description
                        isClickable=true
                        importantForAccessibility=View.IMPORTANT_FOR_ACCESSIBILITY_YES
                        setOnClickListener{action()}
                    }
                    picture.addView(view,FrameLayout.LayoutParams(w,h).apply {
                        leftMargin=(originX+displayWidth*rect[0]).toInt()
                        topMargin=(originY+displayHeight*rect[1]).toInt()
                    })
                }
                hit(tip.actionBounds,tip.actionLabel) {
                    val uri=Uri.parse(tip.actionUrl)
                    if(uri.scheme=="https" && !uri.host.isNullOrBlank()) {
                        runCatching{activity.startActivity(
                            Intent(Intent.ACTION_VIEW,uri))}
                            .onFailure{android.widget.Toast.makeText(activity,
                                "Não foi possível abrir a ligação.",
                                android.widget.Toast.LENGTH_SHORT).show()}
                    }
                    dialog.dismiss()
                }
                hit(tip.closeBounds,tip.closeLabel) {dialog.dismiss()}
            }
        } else {
        val actions=LinearLayout(activity).apply {''',"overlay native hitboxes aligned to contained image")

one('''        content.addView(actions,LinearLayout.LayoutParams(-1,-2))
        dialog.setContentView(content)''',
'''        content.addView(actions,LinearLayout.LayoutParams(-1,-2))
        }
        dialog.setContentView(content)''',"do not render duplicate native footer")

manager.write_text(s,encoding="utf-8")
gradle=root/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 122")==1 and g.count('versionName = "1.9.112"')==1
gradle.write_text(g.replace("versionCode = 122","versionCode = 123")
  .replace('versionName = "1.9.112"','versionName = "1.9.113"'),encoding="utf-8")
print("1.9.113: photoreal public poster, accurate on-phone app screenshot, active embedded buttons, no footer duplication.")
