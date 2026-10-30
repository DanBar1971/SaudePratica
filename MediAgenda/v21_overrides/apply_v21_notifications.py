from pathlib import Path
src=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/notifications")
def sub(s,a,b):
 if a not in s: raise RuntimeError("v1.9.2 notifications missing "+a[:100])
 return s.replace(a,b,1)
f=src/"NotificationScheduler.kt";s=f.read_text(encoding="utf-8")
s=sub(s,'import com.mediagenda.app.data.DataRepository','import com.mediagenda.app.data.DataRepository\nimport com.mediagenda.app.data.ProfileStore')
s=sub(s,'''    fun scheduleAll(meds: List<Medication>, appointments: List<Appointment>) {
        cancelRegistered()
        meds.forEach { scheduleNextMedication(it) }
        appointments.forEach { scheduleAppointment(it) }
    }

    fun scheduleNextMedicationById(medicationId: String) {
        val med = runCatching { DataRepository(context).loadMedications() }
            .getOrNull()?.firstOrNull { it.id == medicationId } ?: return
        scheduleNextMedication(med)
    }

    private fun scheduleNextMedication(m: Medication) {''','''    fun scheduleAllProfiles() {
        cancelRegistered()
        val profiles = ProfileStore(context).all()
        profiles.forEach { profile ->
            val data = runCatching {
                val repository = DataRepository(context, profile.id)
                repository.loadMedications() to repository.loadAppointments()
            }.getOrNull() ?: return@forEach
            data.first.forEach { scheduleNextMedication(it, profile.id, profile.name, profiles.size > 1) }
            data.second.forEach { scheduleAppointment(it, profile.id, profile.name, profiles.size > 1) }
        }
    }

    fun scheduleNextMedicationById(medicationId: String, profileId: String = "legacy") {
        val profile = ProfileStore(context).all().firstOrNull { it.id == profileId } ?: return
        val med = runCatching { DataRepository(context, profileId).loadMedications() }
            .getOrNull()?.firstOrNull { it.id == medicationId } ?: return
        scheduleNextMedication(med, profileId, profile.name, ProfileStore(context).all().size > 1)
    }

    private fun scheduleNextMedication(m: Medication, profileId: String, profileName: String, multiple: Boolean) {''')
s=sub(s,'''        schedule(
            "med|${m.id}", next, "💊 ${m.medication}",
            "Hora da medicação$dose$indication", m.id
        )''','''        schedule(
            "med|$profileId|${m.id}", next,
            "💊 " + (if (multiple) "$profileName: " else "") + m.medication,
            "Hora da medicação$dose$indication", m.id, profileId
        )''')
s=sub(s,'    private fun scheduleAppointment(a: Appointment) {','    private fun scheduleAppointment(a: Appointment, profileId: String, profileName: String, multiple: Boolean) {')
s=sub(s,'''                    "agenda|${a.id}|$event|$mins", alarmDt,
                    "📅 ${a.activity.ifBlank { a.department }}",
                    "$whenText: ${event.format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm"))}" +
                        if (a.location.isBlank()) "" else " — ${a.location}"
''','''                    "agenda|$profileId|${a.id}|$event|$mins", alarmDt,
                    "📅 " + (if (multiple) "$profileName: " else "") + a.activity.ifBlank { a.department },
                    "$whenText: ${event.format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm"))}" +
                        (if (a.location.isBlank()) "" else " — ${a.location}"),
                    profileId = profileId
''')
s=sub(s,'        medicationId: String? = null\n    ) {','        medicationId: String? = null,\n        profileId: String = "legacy"\n    ) {')
s=sub(s,'            putExtra("notification_id", requestCode)','            putExtra("notification_id", requestCode)\n            putExtra("profile_id", profileId)')
f.write_text(s,encoding="utf-8")
f=src/"NotificationReceiver.kt";s=f.read_text(encoding="utf-8")
s=sub(s,'NotificationScheduler(context).scheduleNextMedicationById(medicationId)','NotificationScheduler(context).scheduleNextMedicationById(\n                        medicationId, intent.getStringExtra("profile_id") ?: "legacy"\n                    )')
f.write_text(s,encoding="utf-8")
f=src/"BootReceiver.kt";s=f.read_text(encoding="utf-8")
s=sub(s,'        val repo = DataRepository(context)\n        repo.ensureFiles()\n        NotificationScheduler(context).scheduleAll(repo.loadMedications(), repo.loadAppointments())','        NotificationScheduler(context).scheduleAllProfiles()')
f.write_text(s,encoding="utf-8")
print("Multi-profile alerts scheduled across all profiles.")
