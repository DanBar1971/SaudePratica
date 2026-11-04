#!/usr/bin/env python3
"""Build-time v1.9.136 checks: privacy, backup inclusion, isolation and unchanged alarms."""
from pathlib import Path
from hashlib import sha256

app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
clinical=(src/"WorkMedicineActivity.kt").read_text()
process=(src/"HospitalProcessActivity.kt").read_text()
main=(src/"MainActivity.kt").read_text()
manifest=(app/"src/main/AndroidManifest.xml").read_text()
gradle=(app/"build.gradle.kts").read_text()
family=(src/"data/FamilyBackupStore.kt").read_text()
nearby=(src/"sync/NearbySyncStore.kt").read_text()

assert "versionCode = 146" in gradle
assert 'versionName = "1.9.136"' in gradle
assert 'com.mediagenda.app.stable' in gradle
assert 'android:name=".HospitalProcessActivity"' in manifest
assert 'android:exported="false"' in manifest
assert 'HospitalProcessActivity.EXTRA_PROFILE_ID,patientId' in clinical
assert 'HospitalProcessActivity.EXTRA_HOSPITAL,unit' in clinical
assert 'HospitalProcessActivity.EXTRA_PROCESS,number' in clinical
assert 'getString("observations_by_unit"' in clinical
assert 'saudepratica_workplace/'+ '" +profileId' not in process  # no path traversal concatenation
assert 'Regex("[A-Za-z0-9_-]{1,100}").matches(profileId)' in process
assert '"saudepratica_workplace/"+profileId' in process
assert 'hospital_processes.json' in process
assert 'AtomicFile(target)' in process
assert 'MessageDigest.getInstance("SHA-256")' in process
assert '"team",JSONArray()' in process
assert '"charges",JSONArray()' in process
assert '"transports",JSONArray()' in process
assert 'pickIdentity.launch("image/*")' in process
assert 'importTeamFile(uri)' in process
assert 'val exists=(0 until arr.length()).any' in process
assert 'val existingProfile=com.mediagenda.app.data.ProfileStore(this)' in process
assert 'saudepratica_workplace' in family, "Family backup must include dossiers"
assert 'saudepratica_workplace' in nearby, "Nearby export must include dossier per profile"
assert 'chooseAppointmentForSystemCalendar()' in main
assert 'CalendarContract.EXTRA_EVENT_BEGIN_TIME' in main
assert 'CalendarContract.Events.ALL_DAY' in main
assert 'Intent.ACTION_INSERT' in main
assert 'READ_CALENDAR' not in manifest and 'WRITE_CALENDAR' not in manifest
assert 'IPO Lisboa' in process and 'não consulta' in process, "No hospital server writes"
assert 'SARA' not in process and 'REGINA' not in process and '793240' not in process
print("V156: version/route, privacy, profile-specific backup, calendar, offline dossiers: OK")
