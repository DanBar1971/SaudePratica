from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
folder=base/'i18n';folder.mkdir(parents=True,exist_ok=True)
src=Path('MediAgenda/v54_overrides')
(folder/'AppLanguage.kt').write_bytes((src/'AppLanguage.kt').read_bytes())
(base/'SupportHelpActivity.kt').write_bytes((src/'SupportHelpActivity.kt').read_bytes())
res=root/'app/src/main/res/drawable-nodpi';res.mkdir(parents=True,exist_ok=True)
for tag in ('home','med','calendar','docs','sync','support'):
    (res/f'guide_{tag}.png').write_bytes((src/f'guide_{tag}.png').read_bytes())

def patch(path,old,new,label):
    content=path.read_text(encoding='utf-8')
    count=content.count(old)
    if count!=1: raise RuntimeError(f'SaúdePrática v1.9.35 {label}: expected one anchor, found {count}')
    path.write_text(content.replace(old,new,1),encoding='utf-8')

application=base/'SaudePraticaApplication.kt'
patch(application,'import com.mediagenda.app.data.AppPinStore',
    'import com.mediagenda.app.data.AppPinStore\nimport com.mediagenda.app.i18n.AppLanguage',
    'language import')
patch(application,'    override fun onActivityResumed(activity:Activity) {',
    '''    override fun onActivityResumed(activity:Activity) {
        AppLanguage.attach(activity)''','attach translations to screens')

main=base/'MainActivity.kt'
patch(main,'import com.mediagenda.app.data.AppPinStore',
    'import com.mediagenda.app.data.AppPinStore\nimport com.mediagenda.app.i18n.AppLanguage',
    'main i18n import')
patch(main,
'''        box.addView(infoCard("🔒", "PIN de acesso",''',
'''        box.addView(infoCard("🌐", "Idiomas",
            "Escolher idioma da aplicação · " + AppLanguage.chosenName(this)) {
            val names=AppLanguage.names.toTypedArray()
            val selected=AppLanguage.codes.indexOf(AppLanguage.code(this))
            MaterialAlertDialogBuilder(this)
                .setTitle("🌐 Idiomas")
                .setSingleChoiceItems(names,selected){dialog,which->
                    dialog.dismiss()
                    val next=AppLanguage.codes[which]
                    if(next!=AppLanguage.code(this)){
                        AppLanguage.choose(this,next)
                        // A fresh screen rebuilds all visual labels using the
                        // chosen language; medicine and profile data stay intact.
                        recreate()
                    }
                }
                .setNegativeButton("Cancelar",null).show()
        })
        box.addView(infoCard("🔒", "PIN de acesso",''',
        'language menu item')
patch(main,
'''        box.addView(infoCard("ℹ️", "Acerca", "SaúdePrática — versão, autor e contacto") {''',
'''        box.addView(infoCard("📖", "Ajuda", "Como usar a SaúdePrática, passo a passo") {
            startActivity(Intent(this,SupportHelpActivity::class.java)
                .putExtra(SupportHelpActivity.MODE,SupportHelpActivity.HELP))
        })
        box.addView(infoCard("✉", "Contactar suporte",
            "Pedir ajuda, sugerir melhorias ou comunicar erros") {
            startActivity(Intent(this,SupportHelpActivity::class.java)
                .putExtra(SupportHelpActivity.MODE,SupportHelpActivity.CONTACT))
        })
        box.addView(infoCard("🍺", "Apoiar o autor 🍺",
            "Oferecer uma cerveja via PayPal (opcional)") {
            MaterialAlertDialogBuilder(this)
                .setTitle("🍺 Apoiar o autor")
                .setMessage("Se gostas da SaúdePrática, podes oferecer uma "+
                    "cerveja ao autor. É totalmente opcional e não altera "+
                    "as funcionalidades da aplicação. O PayPal abre fora da app.")
                .setPositiveButton("Abrir PayPal"){_,_->
                    runCatching{
                        startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(
                            SupportHelpActivity.PAYPAL_URL)))
                    }.onFailure { showError("Não foi possível abrir o PayPal.") }
                }
                .setNegativeButton("Cancelar",null).show()
        })
        box.addView(infoCard("ℹ️", "Acerca", "SaúdePrática — versão, autor e contacto") {''',
        'help support and donation menu items')

manifest=root/'app/src/main/AndroidManifest.xml'
patch(manifest,
    '        <activity android:name=".MainActivity" android:exported="false" />',
    '''        <activity android:name=".MainActivity" android:exported="false" />
        <activity android:name=".SupportHelpActivity" android:exported="false" />''',
    'help/support Activity')
gradle=root/'app/build.gradle.kts'
patch(gradle,'versionCode = 44','versionCode = 45','versionCode')
patch(gradle,'versionName = "1.9.34"','versionName = "1.9.35"','versionName')
print('v1.9.35: multilingual UI selector, contact support, illustrated guide and voluntary PayPal author support')