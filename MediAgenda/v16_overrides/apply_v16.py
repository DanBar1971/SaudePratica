from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")
package = root / "app/src/main/java/com/mediagenda/app"
model = package / "model/Models.kt"
repo = package / "data/DataRepository.kt"
main = package / "MainActivity.kt"
gradle = root / "app/build.gradle.kts"

def edit(path, replacements):
    s = path.read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in s:
            raise RuntimeError(f"v1.6 patch target missing in {path}: {old[:120]!r}")
        s = s.replace(old, new, 1)
    path.write_text(s, encoding="utf-8")

edit(model, [(
    '    var schedule: MutableMap<String, MutableList<Int>> = mutableMapOf(),',
    '''    var repeatMode: String = "daily",
    var repeatStart: String = "",
    var repeatUntil: String = "",
    var repeatWeekdays: MutableList<Int> = mutableListOf(),
    var schedule: MutableMap<String, MutableList<Int>> = mutableMapOf(),'''
)])

edit(repo, [(
    '                schedule = schedule,\n                images = images',
    '''                repeatMode = o.optString("repeat_mode",
                    if (schedule.values.any { it.isNotEmpty() }) "dates" else "daily"),
                repeatStart = o.optString("repeat_start"),
                repeatUntil = o.optString("repeat_until"),
                repeatWeekdays = mutableListOf<Int>().apply {
                    val arr = o.optJSONArray("repeat_weekdays")
                    if (arr != null) for (j in 0 until arr.length()) add(arr.optInt(j))
                },
                schedule = schedule,
                images = images'''
), (
    '                .put("reminder_time", m.reminderTime)',
    '''                .put("reminder_time", m.reminderTime)
                .put("repeat_mode", m.repeatMode)
                .put("repeat_start", m.repeatStart)
                .put("repeat_until", m.repeatUntil)
                .put("repeat_weekdays", JSONArray(m.repeatWeekdays))'''
), (
    'Hora Aviso;N.º Prescrição;',
    'Hora Aviso;Frequência;Início;Fim;Dias Semana;N.º Prescrição;'
), (
    'm.id,m.medication,m.dose,m.indication,m.time,m.reminderTime,',
    'm.id,m.medication,m.dose,m.indication,m.time,m.reminderTime,m.repeatMode,m.repeatStart,m.repeatUntil,m.repeatWeekdays.joinToString(","),'
)])

s = main.read_text(encoding="utf-8")
def replace(old, new):
    global s
    if old not in s:
        raise RuntimeError("v1.6 main patch target missing: " + repr(old[:135]))
    s = s.replace(old, new, 1)

replace(
    'import com.mediagenda.app.ocr.AppointmentOcrParser\n',
    'import com.mediagenda.app.ocr.AppointmentOcrParser\nimport com.mediagenda.app.ocr.MultiAppointmentOcrParser\nimport com.mediagenda.app.ocr.LocatedOcrLine\n'
)
replace(
    'import com.mediagenda.app.notifications.NotificationScheduler\n',
    'import com.mediagenda.app.notifications.NotificationScheduler\nimport com.mediagenda.app.notifications.NotificationReceiver\n'
)

# Changes to a working medication form are additive.
replace('''            images = base.images.toMutableList()
''',
'''            images = base.images.toMutableList(),
            repeatWeekdays = base.repeatWeekdays.toMutableList()
''')

repeat_form = '''        // Easy recurring schedules. No need to enter every date for a daily dose.
        val repeatNames = arrayOf("Todos os dias", "Dias da semana",
            "Entre duas datas", "Datas individuais")
        val repeatValues = arrayOf("daily", "weekly", "range", "dates")
        var selectedRepeat = m.repeatMode.ifBlank {
            if (m.schedule.values.any { it.isNotEmpty() }) "dates" else "daily"
        }
        if (selectedRepeat !in repeatValues) selectedRepeat = "daily"
        lateinit var repeatButton: MaterialButton
        fun buttonTitle(): String = "🔁 Repetição: " +
            repeatNames[repeatValues.indexOf(selectedRepeat).coerceAtLeast(0)]
        repeatButton = secondaryButton(buttonTitle()) {
            val active = repeatValues.indexOf(selectedRepeat).coerceAtLeast(0)
            MaterialAlertDialogBuilder(this)
                .setTitle("Quando tomar este medicamento?")
                .setSingleChoiceItems(repeatNames, active) { dialog, which ->
                    selectedRepeat = repeatValues[which]
                    repeatButton.text = buttonTitle()
                    dialog.dismiss()
                }.setNegativeButton("Cancelar", null).show()
        }
        val repeatStart = input("Início da medicação (AAAA-MM-DD, opcional)", m.repeatStart)
        val repeatUntil = input("Fim da medicação (AAAA-MM-DD, opcional)", m.repeatUntil)
        val repeatWeekdays = input("Dias da semana (0=seg, 6=dom)", m.repeatWeekdays.joinToString(","))
        box.addView(noteBox("Avisos", "Selecione a repetição e indique a hora. Todos os dias funciona sem introduzir datas. Os dias da semana aplicam-se à opção semanal."))
        box.addView(repeatButton)
        listOf(repeatStart, repeatUntil, repeatWeekdays).forEach { box.addView(it.container) }
        box.addView(secondaryButton("📅 Escolher início") {
            val today = Calendar.getInstance()
            DatePickerDialog(this, { _, y, month, day ->
                repeatStart.edit.setText("%04d-%02d-%02d".format(y, month + 1, day))
            }, today.get(Calendar.YEAR), today.get(Calendar.MONTH), today.get(Calendar.DAY_OF_MONTH)).show()
        })
        box.addView(secondaryButton("📅 Escolher fim") {
            val today = Calendar.getInstance()
            DatePickerDialog(this, { _, y, month, day ->
                repeatUntil.edit.setText("%04d-%02d-%02d".format(y, month + 1, day))
            }, today.get(Calendar.YEAR), today.get(Calendar.MONTH), today.get(Calendar.DAY_OF_MONTH)).show()
        })
        box.addView(secondaryButton("✓ Escolher dias da semana") {
            val options = arrayOf("Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo")
            val selected = repeatWeekdays.edit.text.toString().split(",").mapNotNull {
                it.trim().toIntOrNull()
            }.filter { it in 0..6 }.toSet()
            val flags = BooleanArray(7) { it in selected }
            MaterialAlertDialogBuilder(this)
                .setTitle("Dias da semana")
                .setMultiChoiceItems(options, flags) { _, which, checked -> flags[which] = checked }
                .setPositiveButton("Aplicar") { _, _ ->
                    repeatWeekdays.edit.setText((0..6).filter { flags[it] }.joinToString(","))
                    selectedRepeat = "weekly"
                    repeatButton.text = buttonTitle()
                }
                .setNegativeButton("Cancelar", null).show()
        })
'''
needle='''        box.addView(secondaryButton("＋ Adicionar data") {'''
replace(needle,repeat_form+needle)

needle='''                m.schedule=datesToSchedule(dates.edit.text.toString())'''
replace(needle,'''                m.repeatMode = selectedRepeat
                m.repeatStart = repeatStart.edit.text.toString().trim()
                m.repeatUntil = repeatUntil.edit.text.toString().trim()
                m.repeatWeekdays = repeatWeekdays.edit.text.toString().split(",")
                    .mapNotNull { it.trim().toIntOrNull() }
                    .filter { it in 0..6 }.distinct().toMutableList()
                m.schedule=datesToSchedule(dates.edit.text.toString())''')

# Replace the previous single-entry OCR behavior with per-entry review.
old = '''    private fun recognizeAppointment(uri: Uri) {
        val input=InputImage.fromFilePath(this,uri)
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS).process(input)
            .addOnSuccessListener { vision ->
                val p=AppointmentOcrParser.parse(vision.text)
                editAppointment(null, Appointment(date=p.date,time=p.time,department=p.department,activity=p.activity,resource=p.resource,location=p.location,type=p.type,photoUri=uri.toString(),ocrText=p.raw))
            }
            .addOnFailureListener { showError("Não foi possível reconhecer o texto. Pode inserir a marcação manualmente.") }
    }'''
new = '''    private fun recognizeAppointment(uri: Uri) {
        val input = InputImage.fromFilePath(this, uri)
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS).process(input)
            .addOnSuccessListener { vision ->
                val locations = vision.textBlocks.flatMap { it.lines }.mapNotNull { line ->
                    val b = line.boundingBox ?: return@mapNotNull null
                    LocatedOcrLine(line.text, b.left, b.top, b.right, b.bottom)
                }
                val rows = MultiAppointmentOcrParser.parseMany(vision.text, locations)
                    .map { p -> Appointment(
                        date = p.date, time = p.time, department = p.department,
                        activity = p.activity, resource = p.resource,
                        location = p.location, type = p.type,
                        photoUri = uri.toString(), ocrText = p.raw
                    ) }
                if (rows.isEmpty()) {
                    showError("Não consegui identificar datas e horas nesta folha. Tente fotografá-la direita e completa.")
                } else if (rows.size == 1) {
                    editAppointment(null, rows.first())
                } else {
                    confirmImportedAppointments(rows)
                }
            }
            .addOnFailureListener {
                showError("Não foi possível reconhecer o texto. Tente novamente ou insira as marcações manualmente.")
            }
    }

    private fun appointmentMatchKey(ap: Appointment): String {
        val normalized = ap.activity.lowercase(Locale.ROOT)
            .replace(Regex("""[^\p{L}\p{N}]+"""), " ").trim()
        return "${ap.date}|${ap.time}|$normalized"
    }

    private fun confirmImportedAppointments(candidates: List<Appointment>) {
        val already = repo.loadAppointments().map(::appointmentMatchKey).toSet()
        val selections = BooleanArray(candidates.size) { i ->
            val c = candidates[i]
            c.activity.isNotBlank() && appointmentMatchKey(c) !in already
        }
        val labels = candidates.map { a ->
            val name = a.activity.ifBlank { a.department.ifBlank { "Descrição não identificada" } }
            val suffix = when {
                a.activity.isBlank() && a.department.isBlank() -> " — rever antes de guardar"
                appointmentMatchKey(a) in already -> " — JÁ REGISTADA"
                else -> ""
            }
            "${a.date}  ${a.time}\\n$name\\n${a.location}$suffix"
        }.toTypedArray()

        MaterialAlertDialogBuilder(this)
            .setTitle("${candidates.size} marcações encontradas")
            .setMessage("Confirme cada data, hora e descrição. Desmarque os resultados incorretos. As entradas já existentes não serão duplicadas. Pode editar cada ficha na Agenda depois de importar.")
            .setMultiChoiceItems(labels, selections) { _, idx, chosen -> selections[idx] = chosen }
            .setPositiveButton("Guardar selecionadas") { _, _ ->
                val stored = repo.loadAppointments()
                val seen = stored.map(::appointmentMatchKey).toMutableSet()
                var added = 0
                candidates.forEachIndexed { idx, appointment ->
                    if (!selections[idx]) return@forEachIndexed
                    if (appointment.activity.isBlank() && appointment.department.isBlank())
                        return@forEachIndexed
                    if (seen.add(appointmentMatchKey(appointment))) {
                        // Each entry carries just the corresponding OCR row, not the whole sheet.
                        stored += appointment
                        added++
                    }
                }
                if (added > 0) {
                    repo.saveAppointments(stored)
                    reschedule()
                }
                Toast.makeText(this, "$added marcação(ões) importada(s). Confirme os detalhes na Agenda.", Toast.LENGTH_LONG).show()
                showAgenda()
            }
            .setNegativeButton("Cancelar", null)
            .show()
    }'''
replace(old,new)

# A one-tap immediate test helps distinguish permissions from scheduling issues.
needle='''        box.addView(infoCard("⇩", "Importar JSON",'''
addition='''        box.addView(infoCard("🔔", "Testar notificação", "Envia já um aviso de teste. Se não aparecer, verifique as permissões de notificações, alarmes e bateria.") {
            if (android.os.Build.VERSION.SDK_INT >= 33 &&
                ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                requestNotificationPermission()
                Toast.makeText(this, "Autorize as notificações e volte a testar.", Toast.LENGTH_LONG).show()
            } else {
                NotificationReceiver().onReceive(this,
                    Intent(this, NotificationReceiver::class.java).apply {
                        putExtra("title", "🔔 MediAgenda — teste")
                        putExtra("body", "Se recebeu este aviso, as notificações estão autorizadas.")
                        putExtra("notification_id", 900101)
                    })
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S &&
                    !getSystemService(AlarmManager::class.java).canScheduleExactAlarms()) {
                    Toast.makeText(this, "Teste enviado. Para avisos à hora exata, autorize Alarmes e lembretes.", Toast.LENGTH_LONG).show()
                    requestExactAlarmAccess()
                }
            }
        })
'''
replace(needle,addition+needle)

main.write_text(s, encoding="utf-8")
edit(gradle, [(
    'versionCode = 6','versionCode = 7'
),(
    'versionName = "1.5.0"','versionName = "1.6.0"'
)])
print("v1.6: recurrence scheduling, test notifications, batch hospital sheet OCR")
