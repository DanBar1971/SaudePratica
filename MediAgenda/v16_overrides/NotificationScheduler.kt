package com.mediagenda.app.notifications

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.model.Appointment
import com.mediagenda.app.model.Medication
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.LocalTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/** Keeps one upcoming medication alarm per medicine and chains the next one
 * when that notification is delivered. No arbitrary 30-day scheduling cutoff.
 */
class NotificationScheduler(private val context: Context) {
    private val prefs = context.getSharedPreferences("alarm_registry", Context.MODE_PRIVATE)
    private val alarmManager = context.getSystemService(AlarmManager::class.java)
    private val zone = ZoneId.systemDefault()

    fun scheduleAll(meds: List<Medication>, appointments: List<Appointment>) {
        cancelRegistered()
        meds.forEach { scheduleNextMedication(it) }
        appointments.forEach { scheduleAppointment(it) }
    }

    fun scheduleNextMedicationById(medicationId: String) {
        val med = runCatching { DataRepository(context).loadMedications() }
            .getOrNull()?.firstOrNull { it.id == medicationId } ?: return
        scheduleNextMedication(med)
    }

    private fun scheduleNextMedication(m: Medication) {
        val reminder = when {
            Regex("""^\d{2}:\d{2}$""").matches(m.reminderTime) -> m.reminderTime
            Regex("""^\d{2}:\d{2}$""").matches(m.time) -> m.time
            else -> return
        }
        val t = runCatching { LocalTime.parse(reminder) }.getOrNull() ?: return
        val now = LocalDateTime.now(zone)
        val start = runCatching { LocalDate.parse(m.repeatStart) }.getOrNull()
        val until = runCatching { LocalDate.parse(m.repeatUntil) }.getOrNull()
        val mode = m.repeatMode.ifBlank { if (m.schedule.values.any { it.isNotEmpty() }) "dates" else "daily" }
        val dateSet = m.schedule.flatMap { (month, days) ->
            days.mapNotNull { day ->
                runCatching { LocalDate.parse("$month-${day.toString().padStart(2, '0')}") }.getOrNull()
            }
        }.toSet()
        val next = (0..366).asSequence()
            .map { now.toLocalDate().plusDays(it.toLong()) }
            .filter { start == null || !it.isBefore(start) }
            .filter { until == null || !it.isAfter(until) }
            .filter { d ->
                when (mode) {
                    "daily" -> true
                    "weekly" -> m.repeatWeekdays.contains(d.dayOfWeek.value - 1)
                    "range" -> start != null && until != null
                    "dates" -> dateSet.contains(d)
                    else -> dateSet.contains(d)
                }
            }
            .map { LocalDateTime.of(it, t) }
            .firstOrNull { it.isAfter(now.plusSeconds(2)) } ?: return

        val dose = if (m.dose.isBlank()) "" else " — ${m.dose}"
        val indication = if (m.indication.isBlank()) "" else " — ${m.indication}"
        schedule(
            "med|${m.id}", next, "💊 ${m.medication}",
            "Hora da medicação$dose$indication", m.id
        )
    }

    private fun scheduleAppointment(a: Appointment) {
        if (a.done || a.date.isBlank() || a.time.isBlank()) return
        expandOccurrences(a).forEach { event ->
            a.remindersMinutes.distinct().forEach { mins ->
                val alarmDt = event.minusMinutes(mins.toLong())
                val whenText = when (mins) {
                    1440 -> "amanhã"
                    120 -> "daqui a 2 horas"
                    else -> "daqui a $mins minutos"
                }
                schedule(
                    "agenda|${a.id}|$event|$mins", alarmDt,
                    "📅 ${a.activity.ifBlank { a.department }}",
                    "$whenText: ${event.format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm"))}" +
                        if (a.location.isBlank()) "" else " — ${a.location}"
                )
            }
        }
    }

    private fun expandOccurrences(a: Appointment): List<LocalDateTime> {
        val startDate = runCatching { LocalDate.parse(a.date) }.getOrNull() ?: return emptyList()
        val t = runCatching { LocalTime.parse(a.time) }.getOrNull() ?: return emptyList()
        if (a.recurrence.mode == "none" || a.recurrence.mode.isBlank()) {
            return listOf(LocalDateTime.of(startDate, t))
        }
        val until = runCatching { LocalDate.parse(a.recurrence.until) }.getOrNull() ?: startDate
        val result = mutableListOf<LocalDateTime>()
        var d = startDate
        while (!d.isAfter(until)) {
            val weekday = d.dayOfWeek.value - 1
            val ok = when (a.recurrence.mode) {
                "weekdays" -> weekday in 0..4
                "weekly" -> if (a.recurrence.weekdays.isEmpty()) {
                    d.dayOfWeek == startDate.dayOfWeek
                } else {
                    a.recurrence.weekdays.contains(weekday)
                }
                else -> d == startDate
            }
            if (ok) result += LocalDateTime.of(d, t)
            d = d.plusDays(1)
        }
        return result
    }

    private fun schedule(
        key: String,
        dt: LocalDateTime,
        title: String,
        body: String,
        medicationId: String? = null
    ) {
        val millis = dt.atZone(zone).toInstant().toEpochMilli()
        if (millis <= System.currentTimeMillis()) return
        val requestCode = key.hashCode()
        val intent = Intent(context, NotificationReceiver::class.java).apply {
            action = "com.mediagenda.app.REMINDER"
            putExtra("title", title)
            putExtra("body", body)
            putExtra("notification_id", requestCode)
            if (medicationId != null) putExtra("medication_id", medicationId)
        }
        val pi = PendingIntent.getBroadcast(
            context, requestCode, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !alarmManager.canScheduleExactAlarms()) {
            // Android may delay alarms in this fallback: show option to grant exact alarm access.
            alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, millis, pi)
        } else {
            alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, millis, pi)
        }
        val ids = prefs.getStringSet("ids", emptySet()).orEmpty().toMutableSet()
        ids += requestCode.toString()
        prefs.edit().putStringSet("ids", ids).apply()
    }

    private fun cancelRegistered() {
        prefs.getStringSet("ids", emptySet()).orEmpty().forEach { s ->
            val code = s.toIntOrNull() ?: return@forEach
            val intent = Intent(context, NotificationReceiver::class.java).apply {
                action = "com.mediagenda.app.REMINDER"
            }
            val pi = PendingIntent.getBroadcast(
                context, code, intent,
                PendingIntent.FLAG_NO_CREATE or PendingIntent.FLAG_IMMUTABLE
            )
            if (pi != null) alarmManager.cancel(pi)
        }
        prefs.edit().remove("ids").apply()
    }
}
