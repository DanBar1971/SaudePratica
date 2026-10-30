from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
main=base/"MainActivity.kt"
manifest=root/"app/src/main/AndroidManifest.xml"
gradle=root/"app/build.gradle.kts"
def patch(path,old,new,label):
    content=path.read_text(encoding="utf-8")
    count=content.count(old)
    if count!=1:
        raise RuntimeError(f"SaúdePrática v1.9.33 {label}: expected 1 occurrence, found {count}")
    path.write_text(content.replace(old,new,1),encoding="utf-8")

patch(main,
    '"Medições","Vacinas","Emergência","Farmácias","SNS 24",',
    '"Medições","Vacinas","Emergência","Farmácias","SNS 24","IPO Lisboa",',
    "dashboard module labels")
patch(main,
    '''            DashboardModule("🏥", "SNS 24", "Aplicação oficial de saúde") { openSns24() },''',
    '''            DashboardModule("🏥", "SNS 24", "Aplicação oficial de saúde") { openSns24() },
            DashboardModule("🏨", "IPO Lisboa", "Abrir aplicação IPO Lisboa") { openIpoLisboa() },''',
    "dashboard card next to SNS24")
patch(main,'    private fun openSns24() {',
    '''    private fun openIpoLisboa() {
        val ipoPackage = "com.seamlink.gatewaybox.ipolisboa"
        val launch = packageManager.getLaunchIntentForPackage(ipoPackage)
        if (launch != null) {
            runCatching { startActivity(launch) }.onSuccess { return }
        }
        MaterialAlertDialogBuilder(this)
            .setTitle("IPO Lisboa")
            .setMessage("A aplicação IPO Lisboa não está disponível neste telemóvel. Queres abrir a página oficial na Google Play?")
            .setPositiveButton("Abrir Google Play") { _, _ ->
                val store = Intent(Intent.ACTION_VIEW,
                    Uri.parse("market://details?id=$ipoPackage"))
                runCatching { startActivity(store) }.onFailure {
                    openUrl("https://play.google.com/store/apps/details?id=$ipoPackage")
                }
            }
            .setNegativeButton("Cancelar", null)
            .show()
    }

    private fun openSns24() {''',
    "independent IPO Lisboa launcher")
patch(manifest,
    '<queries><package android:name="pt.minsaude.spms.ces" /></queries>',
    '''<queries>
        <package android:name="pt.minsaude.spms.ces" />
        <package android:name="com.seamlink.gatewaybox.ipolisboa" />
    </queries>''',
    "visible packages")
patch(gradle,"versionCode = 42","versionCode = 43","version code")
patch(gradle,'versionName = "1.9.32"','versionName = "1.9.33"',"version name")
print("SaúdePrática v1.9.33: IPO Lisboa shortcut added next to SNS24.")
