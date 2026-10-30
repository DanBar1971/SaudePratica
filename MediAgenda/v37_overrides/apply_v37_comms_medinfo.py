from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
path=root/"app/src/main/java/com/mediagenda/app/MainActivity.kt"
s=path.read_text(encoding="utf-8")
def edit(old,new,label):
    global s
    if s.count(old)!=1:raise RuntimeError("v1.9.18 missing "+label+": "+str(s.count(old)))
    s=s.replace(old,new,1)

edit('''import android.app.DatePickerDialog''',
'''import android.app.DatePickerDialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context''',"imports")

edit('''    private val exportAgendaCsv = registerForActivityResult(ActivityResultContracts.CreateDocument("text/csv")) { uri -> uri?.let { writeUri(it, repo.agendaCsv()) } }''',
'''    private val exportAgendaCsv = registerForActivityResult(ActivityResultContracts.CreateDocument("text/csv")) { uri -> uri?.let { writeUri(it, repo.agendaCsv()) } }
    private var pendingMedicineGalleryId:String?=null
    private val medicineGalleryPicker=registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ){uri->
        val target=pendingMedicineGalleryId
        pendingMedicineGalleryId=null
        if(uri==null||target.isNullOrBlank())return@registerForActivityResult
        runCatching{
            if(contentResolver.getType(uri)?.startsWith("image/")!=true)
                error("Escolhe uma imagem.")
            val stored=repo.loadMedications()
            val index=stored.indexOfFirst{it.id==target}
            if(index<0)error("Este medicamento não existe.")
            val directory=File(filesDir,"medication_photos").apply{mkdirs()}
            val file=File(directory,"galeria_"+java.util.UUID.randomUUID()+".jpg")
            try{
                val original=contentResolver.openInputStream(uri)?.use{
                    android.graphics.BitmapFactory.decodeStream(it)
                }?:error("A imagem não pôde ser lida.")
                if(original.width !in 1..10000||original.height !in 1..10000){
                    original.recycle()
                    error("Imagem inválida.")
                }
                val multiplier=minOf(1f,
                    1800f/maxOf(original.width,original.height).toFloat())
                val bitmap=if(multiplier<1f)
                    android.graphics.Bitmap.createScaledBitmap(original,
                        (original.width*multiplier).toInt().coerceAtLeast(1),
                        (original.height*multiplier).toInt().coerceAtLeast(1),true)
                    else original
                file.outputStream().use {
                    check(bitmap.compress(android.graphics.Bitmap.CompressFormat.JPEG,86,it))
                }
                if(bitmap!==original)bitmap.recycle()
                original.recycle()
                val local=FileProvider.getUriForFile(this,
                    BuildConfig.APPLICATION_ID+".fileprovider",file).toString()
                if(local !in stored[index].images)stored[index].images.add(local)
                repo.saveMedications(stored)
            }catch(e:Exception){file.delete();throw e}
        }.onSuccess{
            Toast.makeText(this,"Fotografia associada. Confirma que corresponde "+
                "à apresentação e dose certas.",Toast.LENGTH_LONG).show()
            showMedication()
        }.onFailure{showError(it.message?:"Não foi possível guardar a fotografia.")}
    }''',"medicine photo gallery")

edit('''                    onClick = { editAppointment(it) },
                    onDelete = { ap -> confirmDelete''',
'''                    onClick = { editAppointment(it) },
                    onShare = { shareAppointment(it) },
                    onDelete = { ap -> confirmDelete''',"appointment card share")

edit('''        listOf(date,time,dep,activity,resource,location,type,recMode,recUntil,weekdays,ocr).forEach{box.addView(it.container)}
        val title = if(existing==null''',
'''        listOf(date,time,dep,activity,resource,location,type,recMode,recUntil,weekdays,ocr).forEach{box.addView(it.container)}
        if(existing!=null)
            box.addView(secondaryButton("📤 Enviar lembrete · WhatsApp / email"){
                shareAppointment(existing)
            })
        val title = if(existing==null''',"share from appointment edit")

edit('''        if (existing != null) {
            box.addView(secondaryButton("📷 Adicionar foto da caixa a esta ficha")''',
'''        box.addView(secondaryButton("🔎 Procurar +info do medicamento") {
            val currentName=name.edit.text.toString().trim()
            if(currentName.isBlank())showError("Indica o nome antes de pesquisar.")
            else medicineMoreInfo(currentName,dose.edit.text.toString().trim(),existing?.id)
        })
        if(existing!=null){
            box.addView(secondaryButton("🖼️ Anexar foto existente da embalagem"){
                pendingMedicineGalleryId=existing.id
                activeMedicationDialog?.dismiss()
                activeMedicationDialog=null
                medicineGalleryPicker.launch(arrayOf("image/*"))
            })
        }
        if (existing != null) {
            box.addView(secondaryButton("📷 Adicionar foto da caixa a esta ficha")''',"medication info button and gallery")

methods='''    private fun appointmentReminder(a:Appointment):String{
        val d=runCatching{LocalDate.parse(a.date)}.getOrNull()
        val formatted=d?.format(DateTimeFormatter.ofPattern("dd/MM/yyyy"))
            ?:a.date.ifBlank{"data por confirmar"}
        val dateText=when(d){
            LocalDate.now().plusDays(1)->"amanhã, dia "+formatted
            LocalDate.now()->"hoje, dia "+formatted
            else->"no dia "+formatted
        }
        return "Olá! A SaúdePrática lembra que existe uma consulta ou exame "+
            "marcado "+dateText+" às "+a.time.ifBlank{"hora por confirmar"}+
            ". Consulta a aplicação para mais informações."
    }
    private fun shareAppointment(a:Appointment){
        val box=formBox()
        box.addView(noteBox("Lembrete de consulta",
            "Revê a mensagem e escolhe o destinatário na aplicação escolhida. "+
            "Não será enviada sem a tua confirmação."))
        val text=inputMulti("Mensagem",appointmentReminder(a))
        val address=input("Email do destinatário (opcional)","")
        box.addView(text.container)
        box.addView(address.container)
        lateinit var dialog:androidx.appcompat.app.AlertDialog
        box.addView(secondaryButton("🟢 WhatsApp"){
            val message=text.edit.text.toString().trim()
            if(message.isBlank()){showError("A mensagem está vazia.");return@secondaryButton}
            dialog.dismiss()
            val share=Intent(Intent.ACTION_SEND).apply{
                type="text/plain"
                putExtra(Intent.EXTRA_TEXT,message)
            }
            try{
                startActivity(Intent(share).setPackage("com.whatsapp"))
            }catch(_:Exception){
                try{startActivity(Intent(share).setPackage("com.whatsapp.w4b"))}
                catch(_:Exception){
                    runCatching{startActivity(Intent.createChooser(share,
                        "Escolher aplicação de mensagens"))}.onFailure{
                        showError("Não foi possível abrir WhatsApp ou mensagens.")
                    }
                }
            }
        })
        box.addView(secondaryButton("✉ Email"){
            val message=text.edit.text.toString().trim()
            if(message.isBlank()){showError("A mensagem está vazia.");return@secondaryButton}
            val email=address.edit.text.toString().trim()
            if(email.isNotBlank()&&!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()){
                address.edit.error="Confirma o endereço de email."
                return@secondaryButton
            }
            dialog.dismiss()
            val request=Intent(Intent.ACTION_SENDTO).apply{
                data=Uri.parse("mailto:")
                putExtra(Intent.EXTRA_EMAIL,
                    if(email.isBlank())emptyArray<String>() else arrayOf(email))
                putExtra(Intent.EXTRA_SUBJECT,"SaúdePrática · Lembrete de consulta")
                putExtra(Intent.EXTRA_TEXT,message)
            }
            runCatching{startActivity(Intent.createChooser(request,
                "Escolher aplicação de email"))}.onFailure{
                showError("Não foi possível abrir o email.")
            }
        })
        dialog=MaterialAlertDialogBuilder(this)
            .setTitle("📤 Enviar lembrete")
            .setView(scroll(box))
            .setNegativeButton("Cancelar",null).show()
    }

    private fun medicineMoreInfo(medicineName:String,dose:String,medId:String?){
        val term=(medicineName+" "+dose).trim()
        val box=formBox()
        box.addView(noteBox("Fontes fiáveis",
            "Pesquisa o Folheto Informativo (FI) e o Resumo das "+
            "Características do Medicamento (RCM). Confirma a marca, "+
            "a dosagem e a apresentação. Não alteres um tratamento "+
            "sem a orientação de um profissional de saúde."))
        box.addView(secondaryButton("📖 Procurar folheto · INFARMED"){
            openUrl("https://www.google.com/search?q="+Uri.encode(
                "site:infarmed.pt "+term+" folheto informativo RCM"))
        })
        box.addView(secondaryButton("🏛 Abrir base oficial INFOMED"){
            val clipboard=getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            clipboard.setPrimaryClip(ClipData.newPlainText("Medicamento",term))
            Toast.makeText(this,"Nome copiado. Pesquisa no INFOMED.",
                Toast.LENGTH_LONG).show()
            openUrl("https://www.infarmed.pt/web/infarmed/servicos-on-line")
        })
        box.addView(secondaryButton("🖼️ Procurar foto da embalagem"){
            openUrl("https://www.google.com/search?tbm=isch&q="+
                Uri.encode(term+" medicamento embalagem Portugal"))
        })
        if(!medId.isNullOrBlank()){
            box.addView(secondaryButton("📁 Escolher e guardar foto nesta ficha"){
                pendingMedicineGalleryId=medId
                medicineGalleryPicker.launch(arrayOf("image/*"))
            })
        }else{
            box.addView(noteBox("Guardar fotografia",
                "Primeiro guarda a nova ficha; depois podes associar uma "+
                "fotografia da embalagem encontrada ou recebida."))
        }
        box.addView(noteBox("Fotografias da Internet",
            "Podem pertencer a outro fabricante, dose ou apresentação. "+
            "Não são associadas automaticamente. Confirma a caixa correta."))
        MaterialAlertDialogBuilder(this)
            .setTitle("🔎 Procurar +info")
            .setView(scroll(box)).setPositiveButton("Fechar",null).show()
    }

'''
edit('''    // --- Agenda OCR ---''',methods+'''    // --- Agenda OCR ---''',"message and info features")

edit('''private class AppointmentAdapter(
    private val items:List<Appointment>, private val onClick:(Appointment)->Unit, private val onDelete:(Appointment)->Unit
):RecyclerView.Adapter<AppointmentAdapter.H>() {
    class H(val card:MaterialCardView,val dateBox:TextView,val timeBadge:TextView,val title:TextView,val detail:TextView,val delete:TextView):RecyclerView.ViewHolder(card)''',
'''private class AppointmentAdapter(
    private val items:List<Appointment>, private val onClick:(Appointment)->Unit,
    private val onShare:(Appointment)->Unit, private val onDelete:(Appointment)->Unit
):RecyclerView.Adapter<AppointmentAdapter.H>() {
    class H(val card:MaterialCardView,val dateBox:TextView,val timeBadge:TextView,
        val title:TextView,val detail:TextView,val share:TextView,
        val delete:TextView):RecyclerView.ViewHolder(card)''',"adapter definitions")

edit('''        row.addView(left);row.addView(texts,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));row.addView(del);card.addView(row)
        return H(card,date,clock,title,detail,del)''',
'''        val share=TextView(c).apply{
            text="✉";textSize=18f;gravity=Gravity.CENTER
            contentDescription="Partilhar lembrete por WhatsApp ou email"
            setTextColor(Color.parseColor("#0A5C56"))
            setPadding(dp(10),dp(10),dp(10),dp(10))
        }
        val actions=LinearLayout(c).apply{orientation=LinearLayout.VERTICAL}
        actions.addView(share);actions.addView(del)
        row.addView(left)
        row.addView(texts,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        row.addView(actions);card.addView(row)
        return H(card,date,clock,title,detail,share,del)''',"card mail action")

edit('''        h.card.setOnClickListener{onClick(a)};h.delete.setOnClickListener{onDelete(a)}''',
'''        h.card.setOnClickListener{onClick(a)}
        h.share.setOnClickListener{onShare(a)}
        h.delete.setOnClickListener{onDelete(a)}''',"wire mail action")

path.write_text(s,encoding="utf-8")
g=root/"app/build.gradle.kts"
config=g.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in config
assert 'versionCode = 27' in config and 'versionName = "1.9.17"' in config
g.write_text(config.replace('versionCode = 27','versionCode = 28',1)
    .replace('versionName = "1.9.17"','versionName = "1.9.18"',1),encoding="utf-8")
print("SaúdePrática v1.9.18: WhatsApp and email appointment sharing; medicine search and optional packaging photo import.")
