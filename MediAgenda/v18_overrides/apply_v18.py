from pathlib import Path
import base64

root = Path("build-src/MediAgenda_Android_v1")
main = root / "app/src/main/java/com/mediagenda/app/MainActivity.kt"
manifest = root / "app/src/main/AndroidManifest.xml"
gradle = root / "app/build.gradle.kts"
values = root / "app/src/main/res/values/themes.xml"
draw = root / "app/src/main/res/drawable-nodpi"
draw.mkdir(parents=True, exist_ok=True)

# Small *temporary* placeholder assets to compile the Android resource table.
# The exact user-approved SaúdePrática images replace the PNG entries in the
# resulting unsigned APK before APK v2/v3 signing (see local packaging).
placeholder = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVR4nGNk4BX/z8DAwMDEAAUAEFEBJ5x+qOAAAAAASUVORK5CYII="
)
for name in ("saude_splash", "saude_background", "saude_icon"):
    (draw / (name + ".png")).write_bytes(placeholder)

# Add the in-app branded backdrop, without covering cards/text.
s = main.read_text(encoding="utf-8")
old = '''        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(appBackground)
        }'''
new = '''        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            if (isDarkPalette) {
                val wallpaper = androidx.core.content.ContextCompat.getDrawable(
                    this@MainActivity, R.drawable.saude_background
                )
                if (wallpaper != null) {
                    if (wallpaper is android.graphics.drawable.BitmapDrawable) {
                        wallpaper.gravity = Gravity.FILL
                    }
                    background = android.graphics.drawable.LayerDrawable(
                        arrayOf(wallpaper, android.graphics.drawable.ColorDrawable(
                            Color.argb(105, 3, 14, 23)
                        ))
                    )
                } else {
                    setBackgroundColor(appBackground)
                }
            } else {
                setBackgroundColor(appBackground)
            }
        }'''
if old not in s: raise RuntimeError("MainActivity root styling anchor not found")
s = s.replace(old,new,1)
if 'text = "MediAgenda"' not in s: raise RuntimeError("Brand label anchor not found")
s = s.replace('text = "MediAgenda"', 'text = "SaúdePrática"', 1)
main.write_text(s,encoding="utf-8")

# New launcher splash. Open the existing MainActivity, preserving all stored data.
splash = root / "app/src/main/java/com/mediagenda/app/SplashActivity.kt"
splash.write_text("""package com.mediagenda.app

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.widget.ImageView

class SplashActivity : Activity() {
    private val handler = Handler(Looper.getMainLooper())
    private val openMain = Runnable {
        if (!isFinishing && !isDestroyed) {
            startActivity(Intent(this, MainActivity::class.java))
            finish()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        @Suppress("DEPRECATION")
        window.decorView.systemUiVisibility =
            View.SYSTEM_UI_FLAG_FULLSCREEN or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or
                View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY or
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or
                View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
        window.statusBarColor = Color.TRANSPARENT
        window.navigationBarColor = Color.TRANSPARENT
        val image = ImageView(this).apply {
            setImageResource(R.drawable.saude_splash)
            scaleType = ImageView.ScaleType.CENTER_CROP
            setBackgroundColor(Color.rgb(3, 17, 26))
        }
        setContentView(image)
        handler.postDelayed(openMain, 1150L)
    }

    override fun onDestroy() {
        handler.removeCallbacks(openMain)
        super.onDestroy()
    }
}
""",encoding="utf-8")

m = manifest.read_text(encoding="utf-8")
if 'android:icon="@drawable/ic_mediagenda"' not in m:
    raise RuntimeError("App icon resource anchor not found")
m = m.replace('android:icon="@drawable/ic_mediagenda"','android:icon="@drawable/saude_icon"',1)
if 'android:label="MediAgenda"' not in m: raise RuntimeError("App label anchor not found")
m = m.replace('android:label="MediAgenda"','android:label="SaúdePrática"',1)
old = '<activity android:name=".MainActivity" android:exported="true">'
new = '''<activity android:name=".MainActivity" android:exported="false" />
        <activity android:name=".SplashActivity" android:exported="true" android:theme="@style/Theme.SaudeSplash">'''
if old not in m: raise RuntimeError("Launcher MainActivity declaration not found")
m = m.replace(old,new,1)
manifest.write_text(m,encoding="utf-8")

v = values.read_text(encoding="utf-8")
anchor = '</resources>'
splash_style = '''    <style name="Theme.SaudeSplash" parent="Theme.Material3.DayNight.NoActionBar">
        <item name="android:windowFullscreen">true</item>
        <item name="android:windowActionModeOverlay">true</item>
        <item name="android:statusBarColor">@android:color/transparent</item>
        <item name="android:navigationBarColor">@android:color/transparent</item>
        <item name="android:windowBackground">@android:color/black</item>
    </style>
'''
if anchor not in v: raise RuntimeError("Theme XML footer not found")
v = v.replace(anchor,splash_style+anchor,1)
values.write_text(v,encoding="utf-8")

g = gradle.read_text(encoding="utf-8")
if 'applicationId = "com.mediagenda.app.stable"' not in g:
    raise RuntimeError("Stable Android ID changed, upgrade would erase data!")
if 'versionCode = 8' not in g or 'versionName = "1.7.0"' not in g:
    raise RuntimeError("Expected MediAgenda 1.7 base not present")
g = g.replace('versionCode = 8','versionCode = 9',1)
g = g.replace('versionName = "1.7.0"','versionName = "1.8.0"',1)
gradle.write_text(g,encoding="utf-8")

print("SaúdePrática v1.8: launcher icon, branded 1150ms splash, UI wallpaper, same data ID.")
