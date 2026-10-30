package com.mediagenda.app

import android.app.Activity
import android.app.Application
import android.content.Intent
import android.os.Bundle
import com.mediagenda.app.data.AppPinStore

/** Closes the PIN session when the application leaves the foreground. */
class SaudePraticaApplication:Application(), Application.ActivityLifecycleCallbacks {
    private var started=0

    override fun onCreate() {
        super.onCreate()
        registerActivityLifecycleCallbacks(this)
    }
    override fun onActivityCreated(activity:Activity,state:Bundle?){}
    override fun onActivityStarted(activity:Activity) { started++ }
    override fun onActivityResumed(activity:Activity) {
        if(activity is AppPinActivity || activity is SplashActivity)return
        if(AppPinStore(activity).enabled() &&
            !AppPinSession.unlocked && !AppPinSession.gateRequested) {
            AppPinSession.gateRequested=true
            activity.startActivity(Intent(activity,AppPinActivity::class.java)
                .putExtra(AppPinActivity.FROM_SPLASH,false))
        }
    }
    override fun onActivityPaused(activity:Activity){}
    override fun onActivityStopped(activity:Activity) {
        started=(started-1).coerceAtLeast(0)
        if(started==0){
            AppPinSession.unlocked=false
            AppPinSession.gateRequested=false
        }
    }
    override fun onActivitySaveInstanceState(activity:Activity,state:Bundle){}
    override fun onActivityDestroyed(activity:Activity){}
}

object AppPinSession {
    @Volatile var unlocked=false
    @Volatile var gateRequested=false
}
