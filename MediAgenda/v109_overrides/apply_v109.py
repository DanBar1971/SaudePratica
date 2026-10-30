"""SaúdePrática v1.9.90 — long-press 3s profile shortcut and reliable SOS 4s.

Phone SOS is deliberately armed only while finger stays on the SOS card, for
four seconds, and opens the emergency contact from the active patient's
profile. Single tap still opens the emergency card.
"""
from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
main=base/"MainActivity.kt"

def change(old,new,label):
    s=main.read_text(encoding="utf-8")
    n=s.count(old)
    if n!=1:raise RuntimeError(f"v109 {label}: expected 1 source anchor, found {n}")
    main.write_text(s.replace(old,new,1),encoding="utf-8")

# The profile chip is a compound view. Android's default long-click timeout
# (~0.5s) would NOT implement the user's requested 3 seconds. Use a handled
# touch sequence, including ACTION_CANCEL and optional short-tap navigation.
change(
'''            if (profiles.all().size>1){
                profileBadge.setOnClickListener{showProfileSelection()}
                profileBadge.contentDescription="Mudar perfil: $profile"
            }
            top.addView(profileBadge)''',
'''            profileBadge.contentDescription="Perfil $profile. "+
                "Toque para escolher outro perfil; manter premido "+
                "3 segundos para abrir a ficha deste perfil."
            profileBadge.isClickable=true
            profileBadge.setOnClickListener{
                if(profiles.all().size>1)showProfileSelection()
                else showProfileDialog(false)
            }
            profileBadge.setOnLongClickListener{
                showProfileDialog(false)
                true
            }
            val profileHoldHandler=android.os.Handler(
                android.os.Looper.getMainLooper())
            var profileTouchStartedAt=0L
            var profileHeld=false
            var profilePressed=false
            val profileHoldAction=Runnable{
                if(profilePressed && !profileHeld &&
                    android.os.SystemClock.uptimeMillis()-profileTouchStartedAt>=3000L){
                    profileHeld=true
                    profileBadge.performHapticFeedback(
                        android.view.HapticFeedbackConstants.LONG_PRESS)
                    showProfileDialog(false)
                }
            }
            profileBadge.setOnTouchListener{view,event->
                when(event.actionMasked){
                    android.view.MotionEvent.ACTION_DOWN->{
                        profileHoldHandler.removeCallbacks(profileHoldAction)
                        profileTouchStartedAt=android.os.SystemClock.uptimeMillis()
                        profileHeld=false;profilePressed=true
                        view.parent?.requestDisallowInterceptTouchEvent(true)
                        profileHoldHandler.postDelayed(profileHoldAction,3000L)
                        true
                    }
                    android.view.MotionEvent.ACTION_MOVE->{
                        val slop=android.view.ViewConfiguration.get(this).scaledTouchSlop
                        if(event.x < -slop || event.y < -slop ||
                            event.x > view.width+slop || event.y > view.height+slop){
                            profileHoldHandler.removeCallbacks(profileHoldAction)
                            profilePressed=false
                        }
                        true
                    }
                    android.view.MotionEvent.ACTION_UP->{
                        profileHoldHandler.removeCallbacks(profileHoldAction)
                        val shortTap=profilePressed && !profileHeld
                        profilePressed=false
                        view.parent?.requestDisallowInterceptTouchEvent(false)
                        if(shortTap)view.performClick()
                        true
                    }
                    android.view.MotionEvent.ACTION_CANCEL->{
                        profileHoldHandler.removeCallbacks(profileHoldAction)
                        profilePressed=false
                        view.parent?.requestDisallowInterceptTouchEvent(false)
                        true
                    }
                    else->false
                }
            }
            top.addView(profileBadge)''',
"profile 3 second hold")

# Existing SOS handler (v95) could be cancelled by parent ScrollView when a
# small amount of finger drift was detected. It had no visible hold feedback.
# SOS yellow while pressed, countdown every 100ms, and exact 4000ms timeout.
change(
'''                if(module.title=="Emergência"){
                    val handler=android.os.Handler(android.os.Looper.getMainLooper())
                    var down=false
                    var fired=false
                    val threshold=android.view.ViewConfiguration.get(this).scaledTouchSlop
                    val call=Runnable{
                        if(down && !fired){
                            fired=true
                            card.performHapticFeedback(
                                android.view.HapticFeedbackConstants.LONG_PRESS)
                            callSelectedEmergencyContact()
                        }
                    }
                    card.contentDescription="Emergência. Toque para abrir a ficha; "+
                        "mantenha premido quatro segundos para ligar ao contacto."
                    card.setOnTouchListener{_,event->
                        when(event.actionMasked){
                            android.view.MotionEvent.ACTION_DOWN->{
                                down=true;fired=false
                                handler.postDelayed(call,4000L)
                                true
                            }
                            android.view.MotionEvent.ACTION_MOVE->{
                                if(event.x < -threshold ||
                                    event.y < -threshold ||
                                    event.x > card.width+threshold ||
                                    event.y > card.height+threshold){
                                    down=false;handler.removeCallbacks(call)
                                }
                                true
                            }
                            android.view.MotionEvent.ACTION_UP->{
                                handler.removeCallbacks(call)
                                val click=down && !fired
                                down=false
                                if(click)card.performClick()
                                true
                            }
                            android.view.MotionEvent.ACTION_CANCEL->{
                                down=false;handler.removeCallbacks(call);true
                            }
                            else->false
                        }
                    }
                }''',
'''                if(module.title=="Emergência"){
                    val handler=android.os.Handler(android.os.Looper.getMainLooper())
                    var pressing=false
                    var fired=false
                    var startedAt=0L
                    val threshold=android.view.ViewConfiguration.get(this).scaledTouchSlop
                    val sosSubtitle=inside.getChildAt(inside.childCount-1)
                        as? TextView
                    val sosHeading=inside.getChildAt(inside.childCount-2)
                        as? TextView
                    val originalSubtitle=sosSubtitle?.text
                    val yellow=Color.rgb(255,213,61)
                    val black=Color.rgb(36,33,26)
                    val call=Runnable{
                        if(pressing && !fired &&
                            android.os.SystemClock.uptimeMillis()-startedAt>=4000L){
                            fired=true
                            card.performHapticFeedback(
                                android.view.HapticFeedbackConstants.LONG_PRESS)
                            callSelectedEmergencyContact()
                        }
                    }
                    val countdown=object:Runnable{
                        override fun run(){
                            if(!pressing || fired)return
                            val elapsed=android.os.SystemClock.uptimeMillis()-startedAt
                            val remaining=((4000L-elapsed).coerceAtLeast(0L)+999L)/1000L
                            sosSubtitle?.text="🟡 A preparar chamada · "+
                                remaining+" s"
                            if(elapsed>=4000L)call.run()
                            else handler.postDelayed(this,100L)
                        }
                    }
                    card.contentDescription="Emergência. Toque para abrir ficha. "+
                        "Mantenha 4 segundos para contactar o número guardado."
                    card.setOnTouchListener{view,event->
                        when(event.actionMasked){
                            android.view.MotionEvent.ACTION_DOWN->{
                                handler.removeCallbacks(call)
                                handler.removeCallbacks(countdown)
                                pressing=true;fired=false
                                startedAt=android.os.SystemClock.uptimeMillis()
                                card.setCardBackgroundColor(yellow)
                                sosSubtitle?.setTextColor(black)
                                sosHeading?.setTextColor(black)
                                sosSubtitle?.text="🟡 A preparar chamada · 4 s"
                                view.parent?.requestDisallowInterceptTouchEvent(true)
                                handler.postDelayed(call,4000L)
                                handler.postDelayed(countdown,100L)
                                true
                            }
                            android.view.MotionEvent.ACTION_MOVE->{
                                if(event.x < -threshold ||
                                   event.y < -threshold ||
                                   event.x > card.width+threshold ||
                                   event.y > card.height+threshold){
                                    pressing=false
                                    handler.removeCallbacks(call)
                                    handler.removeCallbacks(countdown)
                                    card.setCardBackgroundColor(surface)
                                    sosSubtitle?.text=originalSubtitle
                                    sosSubtitle?.setTextColor(muted)
                                    sosHeading?.setTextColor(mainTextColor)
                                }
                                true
                            }
                            android.view.MotionEvent.ACTION_UP,
                            android.view.MotionEvent.ACTION_CANCEL->{
                                handler.removeCallbacks(call)
                                handler.removeCallbacks(countdown)
                                val shortTap=pressing && !fired &&
                                    event.actionMasked==
                                        android.view.MotionEvent.ACTION_UP
                                pressing=false
                                view.parent?.requestDisallowInterceptTouchEvent(false)
                                card.setCardBackgroundColor(surface)
                                sosSubtitle?.text=originalSubtitle
                                sosSubtitle?.setTextColor(muted)
                                sosHeading?.setTextColor(mainTextColor)
                                if(shortTap)card.performClick()
                                true
                            }
                            else->false
                        }
                    }
                }''',
"SOS yellow and reliable four-second countdown")

build=root/"app/build.gradle.kts"
s=build.read_text(encoding="utf-8")
assert s.count("versionCode = 99")==1 and s.count('versionName = "1.9.89"')==1
build.write_text(s.replace("versionCode = 99","versionCode = 100",1)
    .replace('versionName = "1.9.89"','versionName = "1.9.90"',1),
    encoding="utf-8")
print("SaúdePrática v1.9.90: press profile 3s, SOS yellow + 4s countdown")
