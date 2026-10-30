"""Add verified direct APK installer (Android still asks for user consent).
Applied AFTER apply_v104.py, without touching version again.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def patch(p,old,new,name):
    s=p.read_text(encoding="utf-8")
    if s.count(old)!=1:raise RuntimeError("v104 updater "+name+": "+str(s.count(old)))
    p.write_text(s.replace(old,new,1),encoding="utf-8")

(base/"InAppUpdateInstaller.kt").write_text(
    Path("MediAgenda/v104_overrides/InAppUpdateInstaller.kt").read_text(
        encoding="utf-8"),encoding="utf-8")
manifest=root/"app/src/main/AndroidManifest.xml"
patch(manifest,
'''    <uses-permission android:name="android.permission.VIBRATE" />''',
'''    <uses-permission android:name="android.permission.VIBRATE" />
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />''',
"allow user-approved APK install")

main=base/"MainActivity.kt"
patch(main,'''    override fun onResume() {
        super.onResume()''',
'''    override fun onResume() {
        super.onResume()
        InAppUpdateInstaller.resumeIfAllowed(this)''',"resume pending system installer after permission")

checker=base/"SaudePraticaUpdateChecker.kt"
patch(checker,
'''        val download:String="",
        val details:String=""''',
'''        val download:String="",
        val details:String="",
        val digest:String=""''',"download digest field")
patch(checker,
'''                                var link=""
                                if(assets!=null){''',
'''                                var link=""
                                var checksum=""
                                if(assets!=null){''',"SHA response variable")
patch(checker,
'''                                            link=url
                                            break''',
'''                                            link=url
                                            checksum=asset.optString("digest")
                                            break''',"release asset SHA-256")
patch(checker,
'''                                        Answer("update",tag,link)''',
'''                                        Answer("update",tag,link,digest=checksum)''',"carry SHA")
patch(checker,
'''                .setPositiveButton("Descarregar atualização"){_,_->
                    try{
                        activity.startActivity(Intent(Intent.ACTION_VIEW,
                            Uri.parse(a.download)))
                    }catch(e:Exception){
                        MaterialAlertDialogBuilder(activity)
                            .setMessage("Não foi possível abrir o navegador.")
                            .setPositiveButton("OK",null).show()
                    }
                }''',
'''                .setPositiveButton("Atualizar agora"){_,_->
                    InAppUpdateInstaller.install(activity,a.download,a.digest)
                }''',"in-app verified installer")
print("In-app update downloader connected; still requires explicit Android confirmation")
