from pathlib import Path
root = Path('build-src/MediAgenda_Android_v1')
base = root/'app/src/main/java/com/mediagenda/app'
source = Path('MediAgenda/v69_overrides')

def change(path, old, new, label):
    data = path.read_text(encoding='utf-8')
    found = data.count(old)
    if found != 1:
        raise RuntimeError(f'v1.9.51 {label}: expected one anchor; got {found}')
    path.write_text(data.replace(old,new,1),encoding='utf-8')

for name in ('ActivityHealthConnect.kt','HealthPermissionsRationaleActivity.kt'):
    (base/name).write_text((source/name).read_text(encoding='utf-8'),encoding='utf-8')

main = base/'MainActivity.kt'
change(main,
    '            DashboardModule("💧", "Beber água", "Hidratação") { openWellness("water") },',
    '''            DashboardModule("💧", "Beber água", "Hidratação") { openWellness("water") },
            DashboardModule("🚶", "Atividade e Saúde", "Passos, sono e energia") {
                startActivity(Intent(this, ActivityHealthConnect::class.java)
                    .putExtra(ActivityHealthConnect.EXTRA_PROFILE_ID, activeProfileId))
            },''','dashboard module')

wellness=base/'WellnessActivity.kt'
change(wellness,'import android.content.res.ColorStateList',
    'import android.content.Intent\nimport android.content.res.ColorStateList',
    'wellness Intent import')
change(wellness,
    '        card(content, "💧 Hidratação", "Registar copos de água e configurar lembretes opcionais.",',
    '''        card(content, "🚶 Atividade e Saúde", "Passos, sono, distância e calorias do Health Connect.",
            "Abrir Atividade e Saúde") {
                startActivity(Intent(this, ActivityHealthConnect::class.java)
                    .putExtra(ActivityHealthConnect.EXTRA_PROFILE_ID, profileId))
        }
        card(content, "💧 Hidratação", "Registar copos de água e configurar lembretes opcionais.",''','wellness menu')

manifest=root/'app/src/main/AndroidManifest.xml'
change(manifest, '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />',
    '''    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <!-- Read only, opt-in: Android 14+ Health Connect; no background data access -->
    <uses-permission android:name="android.permission.health.READ_STEPS" />
    <uses-permission android:name="android.permission.health.READ_SLEEP" />
    <uses-permission android:name="android.permission.health.READ_DISTANCE" />
    <uses-permission android:name="android.permission.health.READ_ACTIVE_CALORIES_BURNED" />''',
    'read only health permissions')
change(manifest, '        <activity android:name=".WellnessActivity" android:exported="false" />',
    '''        <activity android:name=".WellnessActivity" android:exported="false" />
        <activity android:name=".ActivityHealthConnect" android:exported="false" />
        <activity android:name=".HealthPermissionsRationaleActivity" android:exported="false" />
        <activity-alias android:name=".HealthPermissionUsageActivity"
            android:exported="true"
            android:targetActivity=".HealthPermissionsRationaleActivity"
            android:permission="android.permission.START_VIEW_PERMISSION_USAGE">
            <intent-filter>
                <action android:name="android.intent.action.VIEW_PERMISSION_USAGE" />
                <category android:name="android.intent.category.HEALTH_PERMISSIONS" />
            </intent-filter>
        </activity-alias>''',
    'health screens and Android privacy rationale')

gradle=root/'app/build.gradle.kts'
change(gradle,'versionCode = 60','versionCode = 61','version code')
change(gradle,'versionName = "1.9.50"','versionName = "1.9.51"','version name')
print('SaúdePrática v1.9.51: Health Connect read-only opt-in, linked profile, steps, sleep, distance, active calories and weekly steps')