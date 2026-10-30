package com.mediagenda.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.Typeface
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.LayerDrawable
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.ScrollView
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.model.Appointment
import com.mediagenda.app.notifications.NotificationScheduler
import com.mediagenda.app.work.WorkDocument
import com.mediagenda.app.work.WorkMedicineStore
import com.mediagenda.app.work.WorkplaceClassifier
import java.io.File
import java.time.LocalDate
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import java.time.format.ResolverStyle
import java.util.Locale

/** Per-person local archive of occupational medical documents. */
class WorkMedicineActivity:AppCompatActivity(){
    companion object {const val EXTRA_PROFILE_ID="profile_id"}
    private lateinit var store:WorkMedicineStore
    private lateinit var patientId:String
    private lateinit var patientName:String
    private lateinit var body:LinearLayout
    private var chosenCategory:String?=null
    private var activeFilter="all"
    private var cameraTmp:File?=null
    private var working=false

    private val teal=Color.rgb(12,173,163)
    private val dark get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true;"light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val ink get()=if(dark)Color.rgb(245,250,250)else Color.rgb(19,35,51)
    private val muted get()=if(dark)Color.rgb(191,210,220)else Color.rgb(96,111,126)
    private val surface get()=if(dark)Color.rgb(28,43,55)else Color.WHITE
    private val border get()=if(dark)Color.rgb(58,87,100)else Color.rgb(218,232,237)
    private fun dp(v:Int)=(v*resources.displayMetrics.density+.5f).toInt()

    private val zipPicker=registerForActivityResult(ActivityResultContracts.OpenDocument()){uri->
        if(uri!=null)importZip(uri)
    }
    private val documentPicker=registerForActivityResult(ActivityResultContracts.OpenDocument()){uri->
        if(uri!=null)promptImport(uri,null)
    }
    private val camera=registerForActivityResult(ActivityResultContracts.TakePicture()){ok->
        val temp=cameraTmp
        cameraTmp=null
        if(ok&&temp!=null)promptImport(
            FileProvider.getUriForFile(this,packageName+".documents",temp),temp
        )else temp?.delete()
    }
    private val permission=registerForActivityResult(ActivityResultContracts.RequestPermission()){
        if(it)takePhoto()else message("Sem autorização para usar a câmara.")
    }

    override fun onCreate(state:Bundle?){
        super.onCreate(state)
        val people=ProfileStore(this).all()
        val person=people.firstOrNull{it.id==intent.getStringExtra(EXTRA_PROFILE_ID)}
            ?:people.singleOrNull()?:run{finish();return}
        patientId=person.id;patientName=person.name
        store=WorkMedicineStore(this,patientId)
        val backdrop=ContextCompat.getDrawable(this,R.drawable.saude_background)
        if(backdrop is BitmapDrawable)backdrop.gravity=Gravity.FILL
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            background=if(dark&&backdrop!=null)
                LayerDrawable(arrayOf(backdrop,ColorDrawable(Color.argb(125,0,13,24))))
            else ColorDrawable(if(dark)Color.rgb(4,21,31) else Color.rgb(245,249,250))
        }
        val header=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(14),dp(7),dp(14),dp(13))
        }
        header.addView(text("‹",36f,false,teal).apply{
            gravity=Gravity.CENTER
            contentDescription="Voltar ao início"
            setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(34),dp(65)))
        val head=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        head.addView(text("SaúdePrática",13f,true,teal))
        head.addView(text("🏥 Medicina do Trabalho",23f,true))
        head.addView(text(patientName+" · historial médico ocupacional",
            13f,false,muted))
        header.addView(head)
        root.addView(header)
        val scroll=ScrollView(this).apply{overScrollMode=View.OVER_SCROLL_NEVER}
        body=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(4),dp(16),dp(30))
        }
        scroll.addView(body)
        root.addView(scroll,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,0,1f))
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT
        window.navigationBarColor=Color.TRANSPARENT
        val controls=WindowInsetsControllerCompat(window,window.decorView)
        controls.isAppearanceLightStatusBars=!dark
        controls.isAppearanceLightNavigationBars=!dark
        ViewCompat.setOnApplyWindowInsetsListener(root){view,insets->
            val safe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.navigationBars() or
                WindowInsetsCompat.Type.displayCutout())
            view.setPadding(safe.left,safe.top,safe.right,safe.bottom)
            insets
        }
        setContentView(root)
        ViewCompat.requestApplyInsets(root)
        redraw()
    }
    private fun text(s:String,size:Float=14f,bold:Boolean=false,
                     color:Int=ink)=TextView(this).apply{
        text=s;textSize=size;setTextColor(color)
        if(bold)setTypeface(null,Typeface.BOLD)
    }
    private fun card(title:String,detail:String=""):LinearLayout{
        val container=MaterialCardView(this).apply{
            radius=dp(18).toFloat();strokeWidth=dp(1);strokeColor=border
            setCardBackgroundColor(surface)
        }
        val column=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(14),dp(16),dp(16))
        }
        column.addView(text(title,17f,true))
        if(detail.isNotBlank())column.addView(text(detail,13f,false,muted).apply{
            setPadding(0,dp(7),0,dp(7))
        })
        container.addView(column)
        body.addView(container,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT)
            .apply{bottomMargin=dp(13)})
        return column
    }
    private fun button(label:String,action:()->Unit)=MaterialButton(this).apply{
        text=label;isAllCaps=false;textSize=13f
        setTextColor(if(dark)Color.rgb(148,240,230)else Color.rgb(3,107,105))
        backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        strokeColor=ColorStateList.valueOf(teal);strokeWidth=dp(1)
        cornerRadius=dp(14);setOnClickListener{action()}
    }
    private fun field(label:String,value:String=""):EditText=EditText(this).apply{
        hint=label
        setText(value)
        isSingleLine=true
        textSize=15f
        setTextColor(ink);setHintTextColor(muted)
        backgroundTintList=ColorStateList.valueOf(teal)
        setPadding(dp(3),dp(8),dp(3),dp(8))
    }
    private fun multiline(label:String,value:String=""):EditText=field(label,value).apply{
        isSingleLine=false;minLines=2;maxLines=5
    }
    private fun message(s:String)=MaterialAlertDialogBuilder(this).setTitle("SaúdePrática")
        .setMessage(s).setPositiveButton("OK",null).show()

    private fun caption(category:String)=when(category){
        WorkplaceClassifier.COMPLETED->"Exames efetuados"
        WorkplaceClassifier.SCHEDULED->"Exames marcados"
        WorkplaceClassifier.CLINICAL->"Relatórios clínicos"
        WorkplaceClassifier.ARCHIVE->"Arquivo de exames"
        else->"Outros documentos"
    }
    private fun redraw(){
        body.removeAllViews()
        val items=runCatching{store.all()}.getOrElse{
            message("Erro ao ler o arquivo: "+it.message); emptyList()
        }
        val summary=card("Visão geral",
            "Acompanhamento de exames, aptidão, convocatórias e histórico.")
        summary.addView(text("${items.size} documento(s) · "+
            "${items.count{it.category==WorkplaceClassifier.COMPLETED}} exames efetuados · "+
            "${items.count{it.category==WorkplaceClassifier.SCHEDULED}} marcações",
            13f,false,teal))
        items.filter{it.examType=="Ficha de aptidão"}.maxByOrNull{it.date}
            ?.let{last->
                summary.addView(text("Última ficha de aptidão: "+
                    showDate(last.date)+" · "+last.aptitude,13f,false,muted)
                    .apply{setPadding(0,dp(9),0,0)})
            }
        val actions=card("Adicionar documentos",
            "PDFs, fotografias ou exportação ZIP da plataforma MCG.")
        actions.addView(button("📦 Importar ZIP MCG"){
            if(!working)zipPicker.launch(arrayOf("application/zip",
                "application/x-zip-compressed","application/octet-stream"))
        })
        actions.addView(button("📄 Anexar PDF ou imagem"){
            if(!working)chooseCategory {
                documentPicker.launch(arrayOf("application/pdf","image/*"))
            }
        })
        actions.addView(button("📷 Digitalizar com a câmara"){
            if(!working)chooseCategory {
                if(ContextCompat.checkSelfPermission(this,Manifest.permission.CAMERA)
                    ==PackageManager.PERMISSION_GRANTED)takePhoto()
                else permission.launch(Manifest.permission.CAMERA)
            }
        })
        actions.addView(button("＋ Criar registo manual"){
            chooseCategory{
                val selected=chosenCategory?:WorkplaceClassifier.OTHER
                val created=store.createManual("Novo registo de Medicina do Trabalho",selected)
                editor(created)
            }
        })
        val filter=card("Consultar documentos","Seleciona uma secção, como no menu MCG.")
        val tabs=listOf("all" to "Todos")+
            WorkplaceClassifier.types.map{it to caption(it)}
        val scroll=ScrollView(this).apply{isHorizontalScrollBarEnabled=false}
        val tags=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        tabs.chunked(2).forEach{pair->
            val row=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
            pair.forEach{(key,label)->
                row.addView(button((if(activeFilter==key)"✓ " else "")+
                    "$label (${if(key=="all")items.size else items.count{it.category==key}})"){
                    activeFilter=key;redraw()
                },LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f)
                    .apply{marginEnd=dp(5)})
            }
            tags.addView(row)
        }
        scroll.addView(tags)
        filter.addView(scroll)
        val selected=items.filter{activeFilter=="all"||it.category==activeFilter}
        if(selected.isEmpty()){
            card("Sem documentos nesta secção",
                "Importa o ZIP MCG, anexa um documento ou adiciona um registo.")
        }
        selected.forEach{record->
            val detail=buildString{
                append(caption(record.category))
                if(record.date.isNotBlank())append(" · ").append(showDate(record.date))
                append("\n").append(record.examType)
                if(record.aptitude!="Por confirmar"&&
                    record.aptitude!="Não aplicável")
                    append("\nAptidão: ").append(record.aptitude)
                if(record.nextReview.isNotBlank())
                    append("\nPróxima avaliação: ").append(showDate(record.nextReview))
            }
            val box=card(record.name,detail)
            box.addView(button("📋 Abrir ficha / editar dados"){editor(record)})
            if(record.filename.isNotBlank()) {
                box.addView(button("📄 Ver PDF ou imagem original"){openDocument(record)})
                box.addView(button("🔎 OCR deste documento"){
                    if(!working)scan(record)
                })
            }
            if(record.category==WorkplaceClassifier.SCHEDULED||
                record.nextReview.isNotBlank()){
                box.addView(button("🔔 Agendar lembrete na Agenda"){
                    scheduleReminder(record)
                })
            }
            box.addView(button("🗑 Eliminar documento"){
                MaterialAlertDialogBuilder(this).setTitle("Apagar do arquivo?")
                    .setMessage("O registo e o documento correspondente serão apagados.")
                    .setPositiveButton("Apagar"){_,_->
                        runCatching{store.remove(record)}.onSuccess{redraw()}
                            .onFailure{message(it.message?:"Não foi possível apagar.")}
                    }.setNegativeButton("Cancelar",null).show()
            })
        }
        val final=card("Privacidade e interpretação clínica")
        final.addView(text("Documentos privados por utilizador, guardados "+
            "neste telemóvel. A importação ZIP ignora ficheiros repetidos. "+
            "O OCR é apenas auxiliar: não determina aptidão, diagnóstico, "+
            "resultado de eletrocardiograma ou audiometria. "+
            "Confirma sempre os documentos com o médico do trabalho. "+
            "As fichas de aptidão não têm aqui uma validade presumida.",
            13f,false,muted))
        final.addView(button("🧪 Abrir Análises Clínicas"){
            startActivity(Intent(this,ClinicalLabsActivity::class.java)
                .putExtra(ClinicalLabsActivity.EXTRA_PROFILE_ID,patientId))
        })
    }
    private fun showDate(d:String)=runCatching{
        LocalDate.parse(d).format(DateTimeFormatter.ofPattern("dd/MM/yyyy"))
    }.getOrDefault("Data por confirmar")

    private fun chooseCategory(onPicked:()->Unit){
        val names=WorkplaceClassifier.types.map(::caption)
        MaterialAlertDialogBuilder(this).setTitle("Tipo de documento")
            .setItems(names.toTypedArray()){_,position->
                chosenCategory=WorkplaceClassifier.types[position]
                onPicked()
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun promptImport(uri:Uri,temp:File?){
        val name=field("Nome do documento","Medicina do Trabalho")
        val box=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(10),dp(18),dp(8))
            addView(text("Os ficheiros ficam privados no perfil de "+
                patientName+". Podes corrigir a classificação após importar.",
                13f,false,muted))
            addView(name)
        }
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Adicionar documento")
            .setView(box)
            .setNegativeButton("Cancelar"){_,_->temp?.delete()}
            .setOnCancelListener{temp?.delete()}
            .setPositiveButton("Guardar",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener{
                val title=name.text.toString().trim()
                if(title.isBlank()){name.error="Indica um nome.";return@setOnClickListener}
                runCatching{
                    store.add(uri,title,chosenCategory?:WorkplaceClassifier.OTHER)
                }.onSuccess{
                    dialog.dismiss();temp?.delete();redraw()
                    Toast.makeText(this,"Documento guardado.",Toast.LENGTH_LONG).show()
                }.onFailure{message(it.message?:"Não foi possível importar.")}
            }
    }
    private fun takePhoto(){
        runCatching{
            val dir=File(cacheDir,"work_med_camera").apply{mkdirs()}
            val photo=File.createTempFile("exame_",".jpg",dir)
            cameraTmp=photo
            camera.launch(FileProvider.getUriForFile(this,
                packageName+".documents",photo))
        }.onFailure{message("Erro da câmara: "+it.message)}
    }
    private fun importZip(uri:Uri){
        if(working)return
        working=true
        val progress=MaterialAlertDialogBuilder(this)
            .setTitle("A importar o ZIP MCG")
            .setMessage("A verificar ficheiros e duplicados. Não feches esta janela.")
            .setView(ProgressBar(this).apply{
                setPadding(dp(26),dp(10),dp(26),dp(18))
                isIndeterminate=true
            }).setCancelable(false).show()
        Thread {
            val outcome=runCatching{store.importZip(uri)}
            runOnUiThread{
                working=false
                if(!isFinishing)progress.dismiss()
                outcome.onSuccess{result->
                    redraw()
                    message("Importação concluída.\n"+
                        "Novos documentos: ${result.added}\n"+
                        "Duplicados ignorados: ${result.duplicates}\n"+
                        "Outros ficheiros ignorados: ${result.skipped}\n\n"+
                        "Abre cada ficha para confirmar datas, exame e aptidão.")
                }.onFailure{
                    redraw()
                    message("Importação interrompida: "+
                        (it.message?:"Erro ao ler o ZIP.")+
                        "\nOs ficheiros já guardados mantêm-se disponíveis.")
                }
            }
        }.start()
    }
    private fun openDocument(item:WorkDocument){
        runCatching{
            val uri=store.openUri(item)
            startActivity(Intent.createChooser(Intent(Intent.ACTION_VIEW).apply{
                setDataAndType(uri,item.mime)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            },"Abrir documento"))
        }.onFailure{message("Não foi possível abrir: "+it.message)}
    }
    private fun validDate(value:String):String?{
        val v=value.trim()
        if(v.isBlank())return ""
        val fmt=DateTimeFormatter.ofPattern("dd/MM/uuuu")
            .withResolverStyle(ResolverStyle.STRICT)
        return runCatching{
            if(v.contains('/'))LocalDate.parse(v,fmt).toString()
            else LocalDate.parse(v).toString()
        }.getOrNull()
    }
    private fun editor(item:WorkDocument){
        val form=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(17),dp(6),dp(17),dp(12))
        }
        fun add(v:View){form.addView(v,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT)
            .apply{bottomMargin=dp(9)})}
        add(text("Identificação do exame / documento",14f,true,teal))
        val name=field("Nome do documento",item.name)
        val type=field("Tipo de exame (audiometria, ECG, aptidão…)",item.examType)
        val date=field("Data do exame (DD/MM/AAAA)",showDate(item.date).takeIf{
            item.date.isNotBlank()}?:"")
        val time=field("Hora (HH:MM)",item.time)
        listOf(name,type,date,time).forEach(::add)
        add(text("Informação profissional",14f,true,teal))
        val employer=field("Empresa / empregador",item.employer)
        val clinic=field("Unidade / local do exame",item.clinic)
        val doctor=field("Médico do trabalho",item.doctor)
        listOf(employer,clinic,doctor).forEach(::add)
        add(text("Aptidão — apenas segundo a ficha assinada",14f,true,teal))
        val aptitudes=listOf("Por confirmar","Não aplicável","Apto",
            "Apto condicionalmente","Inapto temporariamente",
            "Inapto definitivamente")
        val spinner=Spinner(this)
        spinner.adapter=ArrayAdapter(this,android.R.layout.simple_spinner_dropdown_item,
            aptitudes)
        spinner.setSelection(aptitudes.indexOf(item.aptitude).coerceAtLeast(0))
        add(spinner)
        val restrictions=multiline("Restrições / medidas corretivas",item.restrictions)
        val observations=multiline("Relatório / observações pessoais",item.notes)
        val next=field("Próxima avaliação (DD/MM/AAAA, se indicada)",if(
            item.nextReview.isBlank())"" else showDate(item.nextReview))
        listOf(restrictions,observations,next).forEach(::add)
        if(item.rawOcr.isNotBlank()){
            add(button("🔎 Ver texto do OCR (não confirmado)"){
                val txt=text(item.rawOcr,13f,false,ink).apply{
                    setTextIsSelectable(true);setPadding(dp(16),dp(14),dp(16),dp(14))
                }
                MaterialAlertDialogBuilder(this).setTitle("Texto reconhecido")
                    .setView(ScrollView(this).apply{addView(txt)})
                    .setPositiveButton("Fechar",null).show()
            })
        }
        add(text("Os dados clínicos, análises, audiometrias e ECG devem ser "+
            "interpretados pelo médico. A aptidão não é calculada automaticamente.",
            12f,false,muted))
        val dialog=MaterialAlertDialogBuilder(this).setTitle("Ficha de Medicina do Trabalho")
            .setView(ScrollView(this).apply{addView(form)})
            .setPositiveButton("Guardar",null)
            .setNegativeButton("Cancelar",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener{
                val raw=date.text.toString()
                val checked=validDate(raw)
                val nextChecked=validDate(next.text.toString())
                if(checked==null){date.error="Data inválida.";return@setOnClickListener}
                if(nextChecked==null){next.error="Data inválida.";return@setOnClickListener}
                val t=time.text.toString().trim()
                if(t.isNotBlank()&&runCatching{LocalTime.parse(t)}.isFailure){
                    time.error="Usa HH:MM.";return@setOnClickListener
                }
                val record=item.copy(
                    name=name.text.toString().trim().take(105),
                    examType=type.text.toString().trim().take(90),
                    date=checked,time=t,employer=employer.text.toString().trim(),
                    clinic=clinic.text.toString().trim(),
                    doctor=doctor.text.toString().trim(),
                    aptitude=aptitudes[spinner.selectedItemPosition],
                    restrictions=restrictions.text.toString().trim().take(2000),
                    notes=observations.text.toString().trim().take(5000),
                    nextReview=nextChecked)
                if(record.name.isBlank()){name.error="Obrigatório.";return@setOnClickListener}
                runCatching{store.update(record)}.onSuccess{
                    dialog.dismiss();redraw()
                    Toast.makeText(this,"Ficha guardada.",Toast.LENGTH_SHORT).show()
                }.onFailure{message("Erro ao guardar: "+it.message)}
            }
    }
    private fun scheduleReminder(doc:WorkDocument){
        val date=field("Data (DD/MM/AAAA)",
            if(doc.nextReview.isNotBlank())showDate(doc.nextReview)
            else if(doc.date.isNotBlank())showDate(doc.date) else "")
        val hour=field("Hora (HH:MM)",doc.time.ifBlank{"09:00"})
        val place=field("Local do exame",doc.clinic)
        val view=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(8),dp(18),dp(12))
            listOf(date,hour,place).forEach{addView(it)}
            addView(text("É criado um lembrete normal na Agenda, "+
                "incluindo o aviso às 18:00 do dia anterior.",
                12f,false,muted))
        }
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Criar marcação na Agenda")
            .setView(view).setPositiveButton("Adicionar",null)
            .setNegativeButton("Cancelar",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener{
                val d=validDate(date.text.toString())
                val t=hour.text.toString().trim()
                if(d.isNullOrBlank()){date.error="Data inválida.";return@setOnClickListener}
                if(runCatching{LocalTime.parse(t)}.isFailure){
                    hour.error="Hora inválida.";return@setOnClickListener
                }
                if(!LocalDate.parse(d).isAfter(LocalDate.now())){
                    message("Escolhe uma data futura para criar o lembrete.")
                    return@setOnClickListener
                }
                runCatching{
                    val repository=DataRepository(this,patientId)
                    val appointments=repository.loadAppointments()
                    val entry=Appointment(date=d,time=t,
                        department="Medicina do Trabalho",
                        activity=if(doc.examType.contains("aptidão",true))
                            "Exame de Medicina do Trabalho" else doc.examType,
                        resource=doc.employer,
                        location=place.text.toString().trim(),
                        type="consulta",
                        remindersMinutes=mutableListOf(1440,120))
                    val exists=appointments.any{
                        it.date==d&&it.time==t&&
                        it.department=="Medicina do Trabalho"
                    }
                    require(!exists){"Já existe essa marcação na Agenda."}
                    appointments.add(entry)
                    repository.saveAppointments(appointments)
                    NotificationScheduler(this).scheduleAllProfiles()
                }.onSuccess{
                    dialog.dismiss();message("Marcação criada na Agenda de "+patientName+".")
                }.onFailure{message(it.message?:"Não foi possível criar o alerta.")}
            }
    }

    /** OCR runs offline, at the user's request, over up to 20 PDF pages. */
    private fun scan(doc:WorkDocument){
        if(working)return
        working=true
        val status=text("A reconhecer o documento…",13f)
        val panel=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(20),dp(10),dp(20),dp(10))
            addView(ProgressBar(this@WorkMedicineActivity))
            addView(status)
        }
        val wait=MaterialAlertDialogBuilder(this).setTitle("Leitura OCR local")
            .setView(panel).setCancelable(false).show()
        val client=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        val raw=StringBuilder()
        fun done(error:String?=null){
            working=false
            client.close()
            if(!isFinishing)wait.dismiss()
            if(isFinishing)return
            if(error!=null){message(error);return}
            val parsed=raw.toString().take(25000)
            val suggestedType=WorkplaceClassifier.type(doc.originalName,parsed)
            val updated=doc.copy(
                examType=if(doc.examType=="Exame complementar / documento")
                    suggestedType else doc.examType,
                date=doc.date.ifBlank{
                    WorkplaceClassifier.date(doc.originalName,parsed)
                },rawOcr=parsed
            )
            // Do not persist the OCR or status without an explicit Save.
            editor(updated)
        }
        fun read(page:Int,img:InputImage,after:()->Unit){
            client.process(img).addOnSuccessListener{
                raw.append("\n--- PÁGINA ").append(page).append(" ---\n")
                raw.append(it.text).append("\n")
                after()
            }.addOnFailureListener{
                raw.append("\n--- PÁGINA ").append(page)
                    .append(" — texto ilegível ---\n")
                after()
            }
        }
        val uri=runCatching{store.openUri(doc)}.getOrElse{
            done(it.message?:"Não foi possível abrir.");return
        }
        if(doc.mime=="application/pdf"){
            try{
                val descriptor=contentResolver.openFileDescriptor(uri,"r")
                    ?:error("PDF não disponível.")
                val pdf=PdfRenderer(descriptor)
                if(pdf.pageCount !in 1..20){
                    pdf.close()
                    done("A leitura OCR suporta até 20 páginas por documento.")
                    return
                }
                fun next(index:Int){
                    if(index>=pdf.pageCount){pdf.close();done();return}
                    try{
                        val page=pdf.openPage(index)
                        status.text="Página "+(index+1)+" / "+pdf.pageCount
                        val factor=minOf(2.5f,1800f/page.width.toFloat())
                        val w=(page.width*factor).toInt().coerceAtLeast(1)
                        val h=(page.height*factor).toInt().coerceAtLeast(1)
                        val bitmap=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888)
                        bitmap.eraseColor(Color.WHITE)
                        page.render(bitmap,null,Matrix().apply{postScale(factor,factor)},
                            PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                        page.close()
                        read(index+1,InputImage.fromBitmap(bitmap,0)){
                            bitmap.recycle();next(index+1)
                        }
                    }catch(e:Exception){pdf.close();done("Erro OCR: "+e.message)}
                }
                next(0)
            }catch(e:Exception){done("Erro PDF: "+e.message)}
        }else{
            try{
                val img=InputImage.fromFilePath(this,uri)
                read(1,img){done()}
            }catch(e:Exception){done("Erro na imagem: "+e.message)}
        }
    }
}
