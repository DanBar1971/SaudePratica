#!/usr/bin/env python3
"""SaúdePrática Android 1.9.134: persist Health Connect reads in profile backups.

Apply *after* v153 to the reconstructed 1.9.133 source. This does not alter
alarms, package ID, signing or unrelated medical records.
"""
from pathlib import Path
from shutil import copyfile

root = Path("build-src/MediAgenda_Android_v1/app")
src = root / "src/main/java/com/mediagenda/app"
target = src / "ActivityHealthConnect.kt"
body = target.read_text(encoding="utf-8")

def change(before, after, label):
    global body
    n = body.count(before)
    if n != 1:
        raise AssertionError(f"1.9.134 {label}: expected one anchor, got {n}")
    body = body.replace(before, after, 1)

change(
    "import com.mediagenda.app.data.ProfileStore",
    """import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.data.HealthConnectSnapshotStore""",
    "snapshot import"
)

change(
    '    private val connectedProfile get() = prefs.getString("linked_profile", "").orEmpty()',
    '''    private val connectedProfile get() = prefs.getString("linked_profile", "").orEmpty()
    private val snapshots by lazy { HealthConnectSnapshotStore(this, profileId) }
    private var snapshotStatus: TextView? = null

    private fun saveHealthReading(day:LocalDate, key:String, value:Double,
                                  observedAt:Long?=null) {
        if (!canRead()) return
        val saved=snapshots.record(day,key,value,observedAt)
        snapshotStatus?.text=if(saved)
            "✓ Dados recebidos guardados neste perfil e incluídos no próximo backup."
        else
            "⚠ Não foi possível guardar uma medição. Verifica o armazenamento do telemóvel."
    }''',
    "profile-scoped snapshot save"
)

change(
    '''        requestGeneration++
        val current = requestGeneration''',
    '''        requestGeneration++
        snapshotStatus=null
        val current = requestGeneration''',
    "clear old status"
)

change(
    '''        info.addView(action("↻ Atualizar dados") { showScreen() })''',
    '''        info.addView(action("↻ Atualizar dados") { showScreen() })
        snapshotStatus=label(
            "As medições disponíveis serão guardadas localmente neste perfil " +
            "ao atualizar, para ficarem incluídas no próximo backup familiar.",
            12f, false, secondary)
        info.addView(snapshotStatus)''',
    "disclose local persistence on dashboard"
)

change(
    '''            loadMetric(TotalCaloriesBurnedRecord.ENERGY_TOTAL, from, until) { value, problem ->
                if (current == requestGeneration) totalEnergyView.text =''',
    '''            loadMetric(TotalCaloriesBurnedRecord.ENERGY_TOTAL, from, until) { value, problem ->
                if (current == requestGeneration && problem == null && value != null)
                    saveHealthReading(date, "total_kcal", value.inCalories / 1000.0)
                if (current == requestGeneration) totalEnergyView.text =''',
    "capture optional total energy"
)

change(
    '''        fun <T: Any> querySeries(index: Int, permission: String, metric: AggregationType<T>,
            convert: (T) -> Double, sleep: Boolean = false) {''',
    '''        val snapshotMetricKeys=listOf(
            "steps","distance_km","active_kcal","sleep_minutes","heart_bpm","weight_kg")
        fun <T: Any> querySeries(index: Int, permission: String, metric: AggregationType<T>,
            convert: (T) -> Double, sleep: Boolean = false) {''',
    "day/metric mapping"
)

change(
    '''                    if (error == null) datasets[index].values[dayIndex] = result?.let(convert)
                    if (index == selection) redraw()''',
    '''                    if (error == null) {
                        val amount=result?.let(convert)
                        datasets[index].values[dayIndex]=amount
                        if(amount!=null)saveHealthReading(
                            day,snapshotMetricKeys[index],amount)
                    }
                    if (index == selection) redraw()''',
    "capture seven days without converting missing values to zero"
)

change(
    '''                        done(result.records.firstOrNull(),null)''',
    '''                        val latest=result.records.firstOrNull()
                        if(latest!=null && canRead()){
                            val zone=ZoneId.systemDefault()
                            when(latest){
                                is OxygenSaturationRecord -> saveHealthReading(
                                    latest.time.atZone(zone).toLocalDate(),
                                    "oxygen_percent",latest.percentage.value,
                                    latest.time.toEpochMilli())
                                is WeightRecord -> saveHealthReading(
                                    latest.time.atZone(zone).toLocalDate(),
                                    "weight_kg",latest.weight.inGrams/1000.0,
                                    latest.time.toEpochMilli())
                                is RestingHeartRateRecord -> saveHealthReading(
                                    latest.time.atZone(zone).toLocalDate(),
                                    "resting_heart_bpm",latest.beatsPerMinute.toDouble(),
                                    latest.time.toEpochMilli())
                                is BloodPressureRecord -> {
                                    val day=latest.time.atZone(zone).toLocalDate()
                                    saveHealthReading(day,"systolic_mmhg",
                                        latest.systolic.inMillimetersOfMercury,
                                        latest.time.toEpochMilli())
                                    saveHealthReading(day,"diastolic_mmhg",
                                        latest.diastolic.inMillimetersOfMercury,
                                        latest.time.toEpochMilli())
                                }
                                is RespiratoryRateRecord -> saveHealthReading(
                                    latest.time.atZone(zone).toLocalDate(),
                                    "respiratory_per_min",latest.rate,
                                    latest.time.toEpochMilli())
                                is BodyTemperatureRecord -> saveHealthReading(
                                    latest.time.atZone(zone).toLocalDate(),
                                    "temperature_c",latest.temperature.inCelsius,
                                    latest.time.toEpochMilli())
                            }
                        }
                        done(latest,null)''',
    "persist latest vital-sign observations without altering display"
)

target.write_text(body, encoding="utf-8")
copyfile(Path("MediAgenda/v154_overrides/HealthConnectSnapshotStore.kt"),
         src / "data/HealthConnectSnapshotStore.kt")

# The complete ZIP backup already includes persistent 'saudepratica_*'
# directories. Assert snapshot path is in that set and exclude temporary
# files if a backup and a Health Connect update happen simultaneously.
family = src / "data/FamilyBackupStore.kt"
backup = family.read_text(encoding="utf-8")
old = '''        val top=path.substringBefore('/')
        return acceptedTop(top) && (top in setOf("agenda.json","medicacao.json") ||
            path.contains('/'))'''
new = '''        val top=path.substringBefore('/')
        if (path.endsWith(".tmp")) return false
        return acceptedTop(top) && (top in setOf("agenda.json","medicacao.json") ||
            path.contains('/'))'''
assert backup.count(old)==1, "FamilyBackupStore accepted file path changed"
family.write_text(backup.replace(old,new,1), encoding="utf-8")

gradle = root / "build.gradle.kts"
version = gradle.read_text(encoding="utf-8")
assert version.count("versionCode = 143")==1
assert version.count('versionName = "1.9.133"')==1
version=version.replace("versionCode = 143", "versionCode = 144", 1)
version=version.replace('versionName = "1.9.133"', 'versionName = "1.9.134"', 1)
gradle.write_text(version, encoding="utf-8")

print("Android 1.9.134: 7-day Health Connect daily aggregates and latest vital signs")
print("persisted locally per authorised profile, included in next complete ZIP backup.")
print("Manual weights, alarms, permissions, app identity and sync unchanged.")
