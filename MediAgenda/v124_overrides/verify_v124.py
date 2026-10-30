#!/usr/bin/env python3
"""Regression gate: profile row must remain visible, selectable and separate."""
from pathlib import Path
root=Path('build-src/MediAgenda_Android_v1/app')
s=(root/'src/main/java/com/mediagenda/app/MainActivity.kt').read_text(encoding='utf-8')
assert 'val cardContent=LinearLayout(this).apply{' in s
assert 'cardContent.addView(row,LinearLayout.LayoutParams(' in s
assert 'row.setOnClickListener{ activateProfile(profile) }' in s
assert 'cardContent.addView(deviceButton,LinearLayout.LayoutParams(' in s
assert 'card.addView(cardContent,android.widget.FrameLayout.LayoutParams(' in s
assert 'card.addView(deviceButton)' not in s
assert 'card.addView(row)\n            val ownerOfAlarms' not in s
assert 'val doseCount=runCatching{' in s and 'val agendaCount=runCatching{' in s
assert 'text=profile.name+(if(isCaregiver)' in s
assert 'val avatar=userAvatar(profile.id,160)' in s
assert 'card.setOnClickListener{activateProfile(profile)}' in s
assert 'DeviceAlarmRouting\n                .explicit(this)==profile.id' in s
assert '📱 Associar alarmes a este telemóvel' in s
assert '💊 NÃO TEM CAIXA · Só lamelas / blisters' in s
assert 'if(activity is com.mediagenda.app.notifications.MedicationAlarmActivity)return' in (root/'src/main/java/com/mediagenda/app/SaudePraticaApplication.kt').read_text(encoding='utf-8')
g=(root/'build.gradle.kts').read_text(encoding='utf-8')
assert 'versionCode = 114' in g and 'versionName = "1.9.104"' in g
print('PASS v1.9.104 selector: original avatar/name, independent tap, profile badges, no overlay; lockscreen alarm PIN fix retained.')

# Full-screen profile wizard must respect system navigation and IME insets.
wizard=(root/'src/main/java/com/mediagenda/app/ProfileWizardActivity.kt').read_text(encoding='utf-8')
for required in ['WindowCompat.setDecorFitsSystemWindows(window,false)',
                 'ViewCompat.setOnApplyWindowInsetsListener(root)',
                 'WindowInsetsCompat.Type.systemBars()',
                 'WindowInsetsCompat.Type.ime()',
                 'maxOf(system.bottom,keyboard.bottom)+dp(18)',
                 'ViewCompat.requestApplyInsets(root)',
                 'root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))',
                 'root.addView(bottom)']:
    assert required in wizard, required
print('PASS v1.9.104 profile wizard safe area: buttons above navigation bar and keyboard')
