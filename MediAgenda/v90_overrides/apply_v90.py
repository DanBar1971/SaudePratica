"""SaúdePrática v1.9.72: explicit full-screen permission and lock-screen notification diagnostics."""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def change(p,old,new,why):
 s=p.read_text()
 if s.count(old)!=1:raise RuntimeError(f"v90 {why}: expected 1, got {s.count(old)}")
 p.write_text(s.replace(old,new,1))
main=base/"MainActivity.kt"
change(main,'''    private fun testRealMedicationAlarm(){
        if(Build.VERSION.SDK_INT>=33 &&''','''    private fun testRealMedicationAlarm(){
        if(Build.VERSION.SDK_INT>=34 &&
            !getSystemService(android.app.NotificationManager::class.java)
                .canUseFullScreenIntent()){
            MaterialAlertDialogBuilder(this)
                .setTitle("Ativar ecrã completo com o telemóvel bloqueado")
                .setMessage("O Android/HyperOS não autorizou a SaúdePrática a "+
                    "abrir alarmes por cima do ecrã bloqueado. Ativa a permissão "+
                    "'Alarmes em ecrã completo' para a SaúdePrática. "+
                    "O som e a voz continuam a funcionar mesmo sem esta permissão.")
                .setPositiveButton("Abrir permissões"){_,_->
                    runCatching{startActivity(Intent(
                        android.provider.Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT,
                        android.net.Uri.parse("package:"+packageName)))}
                        .onFailure{Toast.makeText(this,
                            "Abre Definições → Aplicações → Acesso especial → "+
                            "Alarmes em ecrã completo",Toast.LENGTH_LONG).show()}
                }.setNegativeButton("Cancelar",null).show()
            return
        }
        if(Build.VERSION.SDK_INT>=33 &&''',"test permission")
# Preserve the Android alarm activity over the keyguard, even if another
# activity in the same task is already visible behind the lock screen.
alarm=base/"notifications/MedicationAlarmService.kt"
change(alarm,'''        setShowWhenLocked(true)
        setTurnScreenOn(true)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)''','''        setShowWhenLocked(true)
        setTurnScreenOn(true)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON or
            WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED or
            WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON or
            WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD)
        // Do not request device credentials or mark a dose taken automatically.''',"keyguard window")
receiver=base/"notifications/NotificationReceiver.kt"
change(receiver,'''                val full=PendingIntent.getActivity(context,alarmId,open,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)''','''                val full=PendingIntent.getActivity(context,alarmId,open,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                if(android.os.Build.VERSION.SDK_INT>=34 &&
                    !manager.canUseFullScreenIntent()){
                    android.util.Log.w("SaudePraticaAlarm",
                        "Full-screen intent not granted: HyperOS will show "+
                        "lock-screen notification until user grants special access")
                }''',"receiver diagnostic")
# Separate permission path from notification channel settings. Channel importance
# is user-controlled and cannot be elevated by APK update.
change(main,'''                box.addView(secondaryButton("🔔 Autorizar alarmes em ecrã completo"){
                    startActivity(Intent(android.provider.Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT,
                        android.net.Uri.parse("package:"+packageName)))
                })''','''                box.addView(secondaryButton("🔔 Autorizar alarmes em ecrã completo"){
                    runCatching{startActivity(Intent(
                        android.provider.Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT,
                        android.net.Uri.parse("package:"+packageName)))}
                        .onFailure{Toast.makeText(this,
                            "Abre as permissões especiais da SaúdePrática.",
                            Toast.LENGTH_LONG).show()}
                })''',"settings robust")
gradle=root/"app/build.gradle.kts"
change(gradle,"versionCode = 81","versionCode = 82","versionCode")
change(gradle,'versionName = "1.9.71"','versionName = "1.9.72"',"versionName")
print("v1.9.72: full-screen permission check and keyguard activity")
