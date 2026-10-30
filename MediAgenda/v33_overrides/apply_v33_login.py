from pathlib import Path

pin=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/AppPinActivity.kt")
s=pin.read_text(encoding="utf-8")
def change(old,new,label):
    global s
    assert old in s,"v1.9.14 PIN: "+label
    s=s.replace(old,new,1)

change('''import android.graphics.Color''',
'''import android.graphics.Color
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.LayerDrawable
import android.view.KeyEvent
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputMethodManager
import androidx.core.content.ContextCompat''',
"PIN wallpaper and keyboard imports")

change('''        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            gravity=Gravity.CENTER
            setPadding(dp(18),dp(12),dp(18),dp(12))
            setBackgroundColor(if(dark)Color.rgb(5,22,32)else Color.rgb(246,249,250))
        }''',
'''        // The same artwork used on the dashboard makes the PIN entry
        // screen feel like the app's first screen, not an external login.
        val art=ContextCompat.getDrawable(this,R.drawable.saude_background)
        if(art is BitmapDrawable)art.gravity=Gravity.FILL
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            gravity=Gravity.CENTER
            setPadding(dp(18),dp(12),dp(18),dp(12))
            background=if(art!=null)LayerDrawable(arrayOf(
                art,
                ColorDrawable(if(dark)Color.argb(112,2,16,27)
                    else Color.argb(155,246,250,251))
            )) else ColorDrawable(
                if(dark)Color.rgb(5,22,32)else Color.rgb(246,249,250))
        }''',
"login wallpaper")

change('''        add(box,action(if(current)"Confirmar" else "Entrar"){
            val seconds=pin.blockedSeconds()''',
'''        val submit=action(if(current)"Confirmar" else "Entrar"){
            val seconds=pin.blockedSeconds()''',
"submit button ref")
change('''        })
        add(box,action("Esqueci-me do PIN"){recover()})
        add(box,action(if(current)"Cancelar" else "Sair"){''',
'''        }
        add(box,submit)
        // The keyboard's Done/Enter key unlocks without another tap.
        input.imeOptions=EditorInfo.IME_ACTION_DONE
        input.setOnEditorActionListener { _,actionId,event->
            val enter=actionId==EditorInfo.IME_ACTION_DONE ||
                (event?.keyCode==KeyEvent.KEYCODE_ENTER && event.action==KeyEvent.ACTION_UP)
            if(enter){submit.performClick();true}else false
        }
        // Focus and show the numeric keyboard as soon as PIN login appears.
        window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE or
            WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        input.requestFocus()
        input.post {
            if(!isFinishing && input.isAttachedToWindow){
                input.requestFocus()
                (getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager)
                    .showSoftInput(input,InputMethodManager.SHOW_IMPLICIT)
            }
        }
        add(box,action("Esqueci-me do PIN"){recover()})
        add(box,action(if(current)"Cancelar" else "Sair"){''',
"enter-to-unlock & autofocus")

pin.write_text(s,encoding="utf-8")
print("PIN entry now uses SaúdePrática wallpaper, automatic numeric keyboard focus, Done/Enter submission, masked digits retained.")
