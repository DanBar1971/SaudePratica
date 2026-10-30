from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1')
base=root/'app/src/main/java/com/mediagenda/app'
src=Path('MediAgenda/v70_overrides')

def patch(target, old, new, label):
    s=target.read_text(encoding='utf-8')
    n=s.count(old)
    if n != 1: raise RuntimeError(f'v1.9.52 {label}: expected one anchor, got {n}')
    target.write_text(s.replace(old,new,1),encoding='utf-8')

(base/'ActivityHealthConnect.kt').write_text((src/'ActivityHealthConnect.kt').read_text(encoding='utf-8'),encoding='utf-8')
main=base/'MainActivity.kt'
patch(main,'''        box.addView(infoCard("🔔", "Notificações",
            "Testar avisos de agendamentos e alarmes de medicação") {''', '''        box.addView(infoCard("❤️", "Health Connect · permissões e associação",
            "Autorizar dados de atividade, gerir acessos e escolher o perfil") {
            startActivity(Intent(this,ActivityHealthConnect::class.java)
                .putExtra(ActivityHealthConnect.EXTRA_PROFILE_ID,activeProfileId)
                .putExtra(ActivityHealthConnect.EXTRA_SETTINGS,true))
        })
        box.addView(infoCard("🔔", "Notificações",
            "Testar avisos de agendamentos e alarmes de medicação") {''', 'menu Mais')
manifest=root/'app/src/main/AndroidManifest.xml'
patch(manifest,'''    <uses-permission android:name="android.permission.health.READ_ACTIVE_CALORIES_BURNED" />''', '''    <uses-permission android:name="android.permission.health.READ_ACTIVE_CALORIES_BURNED" />
    <!-- Extra read-only data types, individually optional in Mais -->
    <uses-permission android:name="android.permission.health.READ_HEART_RATE" />
    <uses-permission android:name="android.permission.health.READ_TOTAL_CALORIES_BURNED" />''', 'extra read permissions')
privacy=base/'HealthPermissionsRationaleActivity.kt'
patch(privacy, '''"Dados solicitados: passos, distância, calorias ativas e duração do sono. " +
                "A SaúdePrática pede apenas acesso de leitura, sujeito à tua autorização." to 16f,''', '''"Dados solicitados: passos, distância, calorias ativas e duração do sono. " +
                "Podes também autorizar, separadamente, ritmo cardíaco e energia total. " +
                "A SaúdePrática pede apenas acesso de leitura, sujeito à tua autorização." to 16f,''', 'privacy rationale')
gradle=root/'app/build.gradle.kts'
patch(gradle,'versionCode = 61','versionCode = 62','version code')
patch(gradle,'versionName = "1.9.51"','versionName = "1.9.52"','version name')
print('v1.9.52: Health Connect permissions in Mais, optional heart-rate and total kcal, weekly charts and kcal unit correction')