from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/notifications")
p=root/"NotificationScheduler.kt";s=p.read_text(encoding="utf-8")
def edit(old,new,label):
 global s
 if old not in s:raise RuntimeError("Cycle alarms: missing "+label)
 s=s.replace(old,new,1)
edit("import com.mediagenda.app.data.WellnessStore","import com.mediagenda.app.data.WellnessStore\nimport com.mediagenda.app.data.CycleStore","CycleStore import")
edit('''            scheduleNextWater(profile.id)
        }
    }''','''            scheduleNextWater(profile.id)
            scheduleNextPill(profile.id)
        }
    }''',"all-profile scheduling")
edit('''    private fun scheduleNextMedication(m: Medication, profileId: String, profileName: String, multiple: Boolean) {''',
'''    fun scheduleNextPill(profileId:String) {
        if(ProfileStore(context).all().none{it.id==profileId})return
        val store=CycleStore(context,profileId)
        if(!store.alerts||store.pillPattern=="off")return
        val now=LocalDateTime.now(zone)
        val next=(0..366).asSequence()
            .map{now.toLocalDate().plusDays(it.toLong())}
            .filter{store.pillDay(it)}
            .map{LocalDateTime.of(it,store.pillTime)}
            .firstOrNull{it.isAfter(now.plusSeconds(2))}?:return
        schedule("pill|"+profileId,next,"💊 Pílula contracetiva",
            "Lembrete para a toma programada. Confirma a toma manualmente na SaúdePrática.",
            profileId=profileId,kind="pill")
    }

    private fun scheduleNextMedication(m: Medication, profileId: String, profileName: String, multiple: Boolean) {''',
"chained pill alert")
p.write_text(s,encoding="utf-8")
p=root/"NotificationReceiver.kt";s=p.read_text(encoding="utf-8")
old='''            if (intent.getStringExtra("reminder_kind") == "water") {
                runCatching {
                    NotificationScheduler(context).scheduleNextWater(
                        intent.getStringExtra("profile_id") ?: "legacy"
                    )
                }
            }'''
new=old+'''
            if (intent.getStringExtra("reminder_kind") == "pill") {
                runCatching {
                    NotificationScheduler(context).scheduleNextPill(
                        intent.getStringExtra("profile_id") ?: "legacy"
                    )
                }
            }'''
if old not in s:raise RuntimeError("Cycle alarms: receiver chain anchor missing")
p.write_text(s.replace(old,new,1),encoding="utf-8")
print("Optional contraceptive pill reminders scheduled for every profile and automatically rearmed.")
