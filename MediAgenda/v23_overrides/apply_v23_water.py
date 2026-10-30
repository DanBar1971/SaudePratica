from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/notifications")
scheduler = root/"NotificationScheduler.kt"
receiver = root/"NotificationReceiver.kt"

def sub(s, old, new, label):
    if old not in s:
        raise RuntimeError(f"SaúdePrática 1.9.4 water missing {label}: {old[:120]}")
    return s.replace(old, new, 1)

s = scheduler.read_text(encoding="utf-8")
s = sub(s, "import com.mediagenda.app.data.ProfileStore",
    "import com.mediagenda.app.data.ProfileStore\nimport com.mediagenda.app.data.WellnessStore", "WellnessStore import")

s = sub(s,
    '''            data.second.forEach { scheduleAppointment(it, profile.id, profile.name, profiles.size > 1) }
        }
    }''',
    '''            data.second.forEach { scheduleAppointment(it, profile.id, profile.name, profiles.size > 1) }
            scheduleNextWater(profile.id)
        }
    }''', "schedule all profiles")

s = sub(s,
    '''    private fun scheduleNextMedication(m: Medication, profileId: String, profileName: String, multiple: Boolean) {''',
    '''    /** Exactly one future water reminder per profile. Each delivery
     * schedules the next one. No default alerts unless the user opts in.
     */
    fun scheduleNextWater(profileId: String) {
        if (ProfileStore(context).all().none { it.id == profileId }) return
        val prefs = WellnessStore(context, profileId)
        if (!prefs.waterEnabled) return
        val first = runCatching { LocalTime.parse(prefs.waterStart) }.getOrNull() ?: return
        val last = runCatching { LocalTime.parse(prefs.waterEnd) }.getOrNull() ?: return
        if (!last.isAfter(first)) return
        val interval = prefs.waterInterval
        val now = LocalDateTime.now(zone)
        val chosen = (0..2).asSequence()
            .flatMap { addDays ->
                val date = now.toLocalDate().plusDays(addDays.toLong())
                generateSequence(first) { current ->
                    val next = current.plusMinutes(interval.toLong())
                    if (next.isAfter(last) || !next.isAfter(current)) null else next
                }.map { LocalDateTime.of(date, it) }
            }
            .firstOrNull { it.isAfter(now.plusSeconds(2)) } ?: return
        schedule("water|$profileId", chosen, "💧 Beber água",
            "Lembrete de hidratação. Siga as orientações e restrições de líquidos do seu profissional de saúde.",
            profileId = profileId, kind = "water")
    }

    private fun scheduleNextMedication(m: Medication, profileId: String, profileName: String, multiple: Boolean) {''',
    "new water scheduling")

s = sub(s,
    '''        medicationId: String? = null,
        profileId: String = "legacy"
    ) {''',
    '''        medicationId: String? = null,
        profileId: String = "legacy",
        kind: String = "health"
    ) {''', "schedule kind argument")

s = sub(s,
    '''            putExtra("profile_id", profileId)''',
    '''            putExtra("profile_id", profileId)
            putExtra("reminder_kind", kind)''',
    "reminder kind intent")

scheduler.write_text(s,encoding="utf-8")

s = receiver.read_text(encoding="utf-8")
s = sub(s,
    '''            if (!medicationId.isNullOrBlank()) {
                runCatching {
                    NotificationScheduler(context).scheduleNextMedicationById(
                        medicationId, intent.getStringExtra("profile_id") ?: "legacy"
                    )
                }
            }
        }''',
    '''            if (!medicationId.isNullOrBlank()) {
                runCatching {
                    NotificationScheduler(context).scheduleNextMedicationById(
                        medicationId, intent.getStringExtra("profile_id") ?: "legacy"
                    )
                }
            }
            if (intent.getStringExtra("reminder_kind") == "water") {
                runCatching {
                    NotificationScheduler(context).scheduleNextWater(
                        intent.getStringExtra("profile_id") ?: "legacy"
                    )
                }
            }
        }''',
    "chain future water reminder")

receiver.write_text(s,encoding="utf-8")
print("SaúdePrática 1.9.4: optional profile-specific chained water reminders.")
