#!/usr/bin/env python3
"""Android 1.9.132: assistant UX and embedded Windows LAN discovery-only pairing.

Apply after v151. This changes no clinical files, alarms, records or update URL.
The embedded Windows LAN screen is explicitly discovery/consent ONLY: no health data.
"""
from pathlib import Path
from shutil import copyfile

app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
over=Path("MediAgenda/v152_overrides")
agent=src/"AgentAssistantActivity.kt"
s=agent.read_text(encoding="utf-8")

def change(old,new,label):
    global s
    n=s.count(old)
    if n!=1: raise AssertionError(f"{label}: expected 1 anchor; got {n}")
    s=s.replace(old,new,1)

change("    private var busy = false",'''    private var busy = false
    private var thinkingMode="IA local"
    private var thinkingStep=0
    private lateinit var thinkingRow:LinearLayout
    private lateinit var thinkingLabel:TextView
    private lateinit var sendButton:MaterialButton
    private val thinkingHandler=android.os.Handler(android.os.Looper.getMainLooper())
    private val thinkingPulse=object:Runnable {
        override fun run(){
            if(!busy || !this@AgentAssistantActivity::thinkingLabel.isInitialized
                || isFinishing || isDestroyed)return
            thinkingStep=(thinkingStep+1)%3
            thinkingLabel.text="A gerar resposta"+ ".".repeat(thinkingStep+1)+
                "  ·  "+thinkingMode
            thinkingHandler.postDelayed(this,700L)
        }
    }
    private fun setThinking(active:Boolean,channel:String="IA local"){
        busy=active
        thinkingMode=channel
        runOnUiThread {
            if(isFinishing || isDestroyed)return@runOnUiThread
            thinkingHandler.removeCallbacks(thinkingPulse)
            if(this::thinkingRow.isInitialized){
                thinkingRow.visibility=if(active)View.VISIBLE else View.GONE
                if(active){
                    thinkingStep=0
                    thinkingLabel.text="A gerar resposta…  ·  "+channel
                    thinkingHandler.postDelayed(thinkingPulse,700L)
                }
            }
            if(this::sendButton.isInitialized)sendButton.isEnabled=!active
        }
    }''',"thinking state")

change('''        outer.addView(status)
        // Persistent download status, fixed under title; never hidden in chat.''','''        outer.addView(status)
        // Explicit and animated local/online processing indication. Uses an
        // indeterminate system spinner; never guesses a completion percentage.
        thinkingRow=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(12),dp(9),dp(12),dp(9))
            background=rounded(if(dark)Color.argb(232,27,47,57)
                else Color.argb(232,255,255,255))
            visibility=View.GONE
        }
        val indicator=android.widget.ProgressBar(this).apply{
            isIndeterminate=true
            indeterminateTintList=android.content.res.ColorStateList.valueOf(
                if(dark)Color.rgb(93,225,207) else Color.rgb(7,105,99))
        }
        thinkingRow.addView(indicator,LinearLayout.LayoutParams(dp(27),dp(27)).apply{
            rightMargin=dp(12)
        })
        thinkingLabel=TextView(this).apply{
            text="A gerar resposta…"
            textSize=14f
            setTextColor(fg)
            setTypeface(typeface,android.graphics.Typeface.BOLD)
        }
        thinkingRow.addView(thinkingLabel,LinearLayout.LayoutParams(0,-2,1f))
        outer.addView(thinkingRow,LinearLayout.LayoutParams(-1,-2).apply{
            bottomMargin=dp(7)
        })
        // Persistent download status, fixed under title; never hidden in chat.''',
"thinking progress row")

change('''        outer.addView(shortcuts)
        val composer=LinearLayout(this).apply''','''        // Same visual language as Backup, Segurança and the other modules:
        // dark translucent cards, readable contrast and consistent spacing.
        for(i in 0 until shortcuts.childCount){
            val row=shortcuts.getChildAt(i) as? LinearLayout ?: continue
            row.setPadding(0,dp(3),0,dp(3))
            for(j in 0 until row.childCount){
                val item=row.getChildAt(j) as? MaterialButton ?: continue
                val params=item.layoutParams as? LinearLayout.LayoutParams ?: continue
                params.marginStart=dp(3)
                params.marginEnd=dp(3)
                item.layoutParams=params
            }
        }
        outer.addView(shortcuts)
        val composer=LinearLayout(this).apply''',"shortcut card spacing")

change('''        composer.addView(button("➤"){
            val value=input.text.toString().trim()
            if(value.isNotEmpty()){input.text.clear();ask(value)}
        },LinearLayout.LayoutParams(dp(62),dp(54)))''','''        sendButton=button("➤"){
            val value=input.text.toString().trim()
            if(value.isNotEmpty() && !busy){input.text.clear();ask(value)}
        }
        sendButton.contentDescription="Enviar pergunta"
        composer.addView(sendButton,LinearLayout.LayoutParams(dp(62),dp(54)))''',
"send button busy guard")

change('''        text=label;isAllCaps=false;textSize=12f;minHeight=dp(44)
        cornerRadius=dp(14)
        setPadding(dp(8),dp(6),dp(8),dp(6))
        setOnClickListener{action()}''','''        text=label;isAllCaps=false;textSize=13f;minHeight=dp(44)
        cornerRadius=dp(16)
        insetTop=0;insetBottom=0
        setPadding(dp(9),dp(6),dp(9),dp(6))
        backgroundTintList=android.content.res.ColorStateList.valueOf(
            if(dark)Color.argb(238,28,48,60) else Color.argb(238,255,255,255))
        setTextColor(if(dark)Color.WHITE else Color.rgb(19,55,67))
        strokeWidth=dp(1)
        strokeColor=android.content.res.ColorStateList.valueOf(
            if(dark)Color.argb(155,89,162,174) else Color.argb(130,8,115,116))
        setOnClickListener{action()}''',"branded accessible button style")

change('''    private fun ask(value:String){
        bubble(true,value)''','''    private fun ask(value:String){
        if(busy){input.setText(value);return}
        bubble(true,value)''',"no silent discarded question")

# Only generation functions change busy indicator; no new inference or data flow.
def replace_in_method(first,last,channel):
    global s
    begin=s.index(first)
    end=s.index(last,begin)
    part=s[begin:end]
    assert part.count("busy=true")==1,(channel,"start",part.count("busy=true"))
    assert part.count("busy=false")==1,(channel,"stop",part.count("busy=false"))
    part=part.replace("busy=true",f'setThinking(true,"{channel}")',1)
    part=part.replace("busy=false","setThinking(false)",1)
    s=s[:begin]+part+s[end:]

replace_in_method("    private fun generateOnline(question:String){",
                  "    private fun generateSmall(question:String)", "IA Online")
replace_in_method("    private fun generateSmall(question:String)",
                  "    private fun manageLocalModel()", "IA local leve")
replace_in_method("    private fun generateLocal(question:String)",
                  "    override fun onDestroy()", "Gemini Nano")

change('''        updateHandler.removeCallbacks(downloadMonitor)
        modelDownload.close()''','''        thinkingHandler.removeCallbacks(thinkingPulse)
        updateHandler.removeCallbacks(downloadMonitor)
        modelDownload.close()''',"clean up thinking animation")

agent.write_text(s,encoding="utf-8")

# Same discovery, pair request and manual consent protocol as Windows 0.8.12.
# The screen stays internal, and the server is stopped at onDestroy().
copyfile(over/"WindowsLanPairActivity.java",src/"WindowsLanPairActivity.java")
main=src/"MainActivity.kt"
m=main.read_text(encoding="utf-8")
anchor='''        box.addView(infoCard("🔐", "Backup .spbackup · Família",'''
assert m.count(anchor)==1,("backup menu location",m.count(anchor))
m=m.replace(anchor,'''        box.addView(infoCard("💻", "Ligação Windows · Wi-Fi (teste)",
            "Detetar o telemóvel no PC e autorizar o código; ainda sem transferência clínica") {
            startActivity(Intent(this,WindowsLanPairActivity::class.java))
        })
'''+anchor,1)
main.write_text(m,encoding="utf-8")

manifest=app/"src/main/AndroidManifest.xml"
x=manifest.read_text(encoding="utf-8")
assert x.count("    </application>")==1
for perm in ("android.permission.ACCESS_WIFI_STATE",
             "android.permission.CHANGE_WIFI_MULTICAST_STATE"):
    if perm not in x:
        assert "    <application" in x
        x=x.replace("    <application",
            f'    <uses-permission android:name="{perm}"/>\n    <application',1)
x=x.replace("    </application>",'''        <activity android:name=".WindowsLanPairActivity"
            android:exported="false" />
    </application>''',1)
manifest.write_text(x,encoding="utf-8")

gradle=app/"build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert g.count("versionCode = 141")==1
assert g.count('versionName = "1.9.131"')==1
g=g.replace("versionCode = 141","versionCode = 142",1)
g=g.replace('versionName = "1.9.131"','versionName = "1.9.132"',1)
gradle.write_text(g,encoding="utf-8")
print("Android v1.9.132: animated thinking, branded buttons, Windows LAN consent inside main app. No clinical sync.")
