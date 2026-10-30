"""v1.9.86: restore full-screen medical alarm on locked/dark screen.

Android keyguard is not the same thing as a running app task. A foreground
app task behind the lockscreen must NEVER suppress the full-screen intent.
Android 14+ still requires the user's explicit FSI permission.
"""
from pathlib import Path
base=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
p=base/"notifications/MedicationAlarmService.kt"
s=p.read_text(encoding="utf-8")
old='''        val foreground=runCatching {
            val manager=getSystemService(ActivityManager::class.java)
            manager.appTasks.any{ task->
                task.taskInfo.isRunning && task.taskInfo.topActivity?.packageName==packageName
            }
        }.getOrDefault(false)
        val channelId=if(foreground)QUIET_CHANNEL else CHANNEL'''
new='''        // A background Activity may still be the appTasks.topActivity when
        // Android's KEYGUARD is showing. Treat that as LOCKED, not foreground.
        val locked=runCatching{
            getSystemService(android.app.KeyguardManager::class.java).isKeyguardLocked
        }.getOrDefault(false)
        val interactive=runCatching{
            getSystemService(android.os.PowerManager::class.java).isInteractive
        }.getOrDefault(true)
        val foreground=if(locked||!interactive)false else runCatching {
            val manager=getSystemService(ActivityManager::class.java)
            manager.appTasks.any{ task->
                task.taskInfo.isRunning && task.taskInfo.topActivity?.packageName==packageName
            }
        }.getOrDefault(false)
        val channelId=if(foreground)QUIET_CHANNEL else CHANNEL
        if(locked||!interactive){
            val enabled=runCatching{
                if(android.os.Build.VERSION.SDK_INT>=34)
                    getSystemService(NotificationManager::class.java)
                        .canUseFullScreenIntent()
                else true
            }.getOrDefault(false)
            android.util.Log.i("SaudePraticaAlarm",
                "lockscreen FSI: locked=$locked interactive=$interactive enabled=$enabled")
        }'''
if s.count(old)!=1:raise RuntimeError("Expected foreground selection in v1.9.85 "+str(s.count(old)))
p.write_text(s.replace(old,new,1),encoding="utf-8")
print("Lockscreen alarms always request HIGH channel + fullscreen PendingIntent")
