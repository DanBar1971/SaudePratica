from pathlib import Path
ROOT=Path('build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app')
def update(name,old,new):
 p=ROOT/name;s=p.read_text(encoding='utf-8');n=s.count(old)
 assert n==1,(name,old[:80],n)
 p.write_text(s.replace(old,new,1),encoding='utf-8')
update('notifications/NotificationScheduler.kt','        if (a.done) return','        if (a.done || a.cancelled) return')
update('MonthlyCalendarActivity.kt','            if(a.done)content.addView(label("Concluído",12f,c=teal))',
       '            if(a.cancelled)content.addView(label("Cancelada",12f,c=muted))\n            else if(a.done)content.addView(label("Concluído",12f,c=teal))')
update('ProfileWizardActivity.kt','    private val bg=Color.rgb(5,28,37)', '''    private val bg=Color.rgb(5,28,37)
    private val wizardLight:Boolean get(){
        val selected=getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
            .getString("theme_mode","system")
        return selected=="light" || (selected=="system" &&
            (resources.configuration.uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK)
                !=android.content.res.Configuration.UI_MODE_NIGHT_YES)
    }
    private val wizardInk:Int get()=if(wizardLight)Color.rgb(23,46,58)else Color.WHITE
    private val wizardMuted:Int get()=if(wizardLight)Color.rgb(83,105,116)else Color.rgb(170,201,211)''')
update('ProfileWizardActivity.kt','            setTextColor(Color.WHITE);setTypeface(typeface,Typeface.BOLD)',
       '            setTextColor(wizardInk);setTypeface(typeface,Typeface.BOLD)')
update('ProfileWizardActivity.kt','        this.text=text;textSize=size;setTextColor(Color.WHITE)',
       '        this.text=AppLanguage.t(this@ProfileWizardActivity,text);textSize=size;setTextColor(wizardInk)')
update('ProfileWizardActivity.kt','        text=title;isAllCaps=false;textSize=14f;minHeight=dp(52)',
       '        text=AppLanguage.t(this@ProfileWizardActivity,title);isAllCaps=false;textSize=14f;minHeight=dp(52)')
update('ProfileWizardActivity.kt','            setText(value);textSize=16f;setTextColor(Color.WHITE)',
       '            setText(value);textSize=16f;setTextColor(wizardInk)')
update('ProfileWizardActivity.kt','    private fun hint(text:String){body.addView(label(text,13f).apply{setTextColor(Color.rgb(170,201,211))})}',
       '    private fun hint(text:String){body.addView(label(text,13f).apply{setTextColor(wizardMuted)})}')
update('ProfileWizardActivity.kt','            setTextColor(Color.WHITE);buttonTintList=ColorStateList.valueOf(teal)',
       '            setTextColor(wizardInk);buttonTintList=ColorStateList.valueOf(teal)')
update('ProfileWizardActivity.kt','progress=TextView(this).apply{textSize=13f;setTextColor(Color.rgb(113,227,206))}',
       'progress=TextView(this).apply{textSize=13f;setTextColor(if(wizardLight)Color.rgb(6,112,101) else Color.rgb(113,227,206))}')
update('MainActivity.kt','''        box.addView(ccThumbs)

        val name = input("Nome do perfil (nome curto)", draft?.first ?: profileName())''', '''        box.addView(ccThumbs)
        val overviewPrefs=getSharedPreferences(profiles.preferencesFor(activeProfileId),MODE_PRIVATE)
        box.addView(noteBox("📋 Resumo do perfil",
            overviewPrefs.getString("full_name","").orEmpty().ifBlank{profileName()}+" · "+
            overviewPrefs.getString("birth_date","").orEmpty().ifBlank{"Data de nascimento por preencher"}+"\\n"+
            overviewPrefs.getString("health_unit","").orEmpty().ifBlank{"Sem unidade de saúde preferencial"}))

        val name = input("Nome do perfil (nome curto)", draft?.first ?: profileName())''')
print('v126 extra: notification skip, monthly status, wizard contrast, profile summary.')