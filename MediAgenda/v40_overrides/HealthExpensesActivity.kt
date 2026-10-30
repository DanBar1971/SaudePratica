package com.mediagenda.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.content.res.ColorStateList
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.BitmapDrawable
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.LayerDrawable
import android.net.Uri
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.EditText
import android.widget.LinearLayout
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
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.expenses.HealthExpense
import com.mediagenda.app.expenses.HealthExpenseAttachment
import com.mediagenda.app.expenses.HealthExpensesStore
import java.io.File
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.ResolverStyle

class HealthExpensesActivity:AppCompatActivity(){
    companion object {const val EXTRA_PROFILE_ID="profile_id"}
    private lateinit var vault:HealthExpensesStore
    private lateinit var profileName:String
    private lateinit var body:LinearLayout
    private var year=LocalDate.now().year
    private var selectedExpense:String?=null
    private var selectedAttachmentTitle="Documento"
    private var tempPhoto:File?=null

    private val blue=Color.rgb(7,162,154)
    private val dark get()=when(getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
        .getString("theme_mode","system")){
        "dark"->true;"light"->false
        else->(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==
            Configuration.UI_MODE_NIGHT_YES
    }
    private val fg get()=if(dark)Color.rgb(242,248,250)else Color.rgb(22,36,52)
    private val muted get()=if(dark)Color.rgb(190,211,219)else Color.rgb(96,112,127)
    private val surface get()=if(dark)Color.rgb(29,44,55)else Color.WHITE
    private val outline get()=if(dark)Color.rgb(62,87,101)else Color.rgb(219,232,234)
    private fun dp(n:Int)=(n*resources.displayMetrics.density+.5f).toInt()

    private val attachmentPicker=registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ){uri->uri?.let{importAttachment(it,null)}}
    private val camera=registerForActivityResult(ActivityResultContracts.TakePicture()){ok->
        val file=tempPhoto
        tempPhoto=null
        if(ok && file!=null){
            val uri=FileProvider.getUriForFile(this,packageName+".documents",file)
            importAttachment(uri,file)
        }else file?.delete()
    }
    private val permission=registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ){allowed->if(allowed)photograph()else notice("Acesso à câmara recusado.")}
    private val csv=registerForActivityResult(
        ActivityResultContracts.CreateDocument("text/csv")
    ){uri->
        if(uri!=null){
            runCatching{
                val records=vault.list().filter{it.date.startsWith(year.toString())}
                val header=listOf("Data","Categoria","Entidade","Descrição",
                    "NIF da entidade","N.º fatura","Total (EUR)",
                    "Reembolso (EUR)","Estado e-Fatura/IRS","Notas")
                fun quote(s:String)="\""+s.replace("\"","\"\"")+"\""
                val lines=mutableListOf(header.joinToString(";"){quote(it)})
                records.forEach{e->
                    lines.add(listOf(e.date,e.category,e.merchant,e.description,
                        e.supplierNif,e.receiptNumber,
                        (e.amountCents/100).toString()+","+
                            (e.amountCents%100).toString().padStart(2,'0'),
                        (e.reimbursedCents/100).toString()+","+
                            (e.reimbursedCents%100).toString().padStart(2,'0'),
                        e.taxStatus,e.notes).joinToString(";"){quote(it)})
                }
                contentResolver.openOutputStream(uri,"w")?.use{output->
                    output.write(("\uFEFF"+lines.joinToString("\n")).toByteArray(
                        Charsets.UTF_8))
                }?:error("Não foi possível guardar o CSV.")
            }.onSuccess{notice("Resumo exportado. Os documentos não são incluídos no CSV.")}
                .onFailure{notice(it.message?:"Não foi possível exportar.")}
        }
    }

    override fun onCreate(state:Bundle?){
        super.onCreate(state)
        val users=ProfileStore(this).all()
        val person=users.firstOrNull{it.id==intent.getStringExtra(EXTRA_PROFILE_ID)}
            ?:users.singleOrNull()?:run{finish();return}
        profileName=person.name
        vault=HealthExpensesStore(this,person.id)
        val background=ContextCompat.getDrawable(this,R.drawable.saude_background)
        if(background is BitmapDrawable)background.gravity=Gravity.FILL
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            background=if(dark&&background!=null)
                LayerDrawable(arrayOf(background,ColorDrawable(Color.argb(120,3,17,26))))
            else ColorDrawable(if(dark)Color.rgb(3,19,29)else Color.rgb(247,250,251))
        }
        val header=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            gravity=Gravity.CENTER_VERTICAL
            setPadding(dp(13),dp(7),dp(13),dp(13))
        }
        header.addView(text("‹",35f,false,blue).apply{
            gravity=Gravity.CENTER
            contentDescription="Voltar ao Início"
            setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(38),dp(65)))
        val headings=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        headings.addView(text("SaúdePrática",13f,true,blue))
        headings.addView(text("🧾 Despesas de Saúde",24f,true))
        headings.addView(text(profileName+" · faturas e comprovativos",13f,false,muted))
        header.addView(headings)
        root.addView(header)
        val scroll=ScrollView(this)
        body=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL
            setPadding(dp(17),dp(3),dp(17),dp(30))}
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
        refresh()
    }
    private fun text(v:String,size:Float=14f,bold:Boolean=false,
        color:Int=fg)=TextView(this).apply{
        text=v;textSize=size;setTextColor(color)
        if(bold)setTypeface(null,Typeface.BOLD)
    }
    private fun card(title:String,info:String=""):LinearLayout{
        val shell=MaterialCardView(this).apply{
            radius=dp(18).toFloat()
            strokeWidth=dp(1);strokeColor=outline
            setCardBackgroundColor(surface)
        }
        val inner=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(14),dp(16),dp(16))
        }
        inner.addView(text(title,18f,true))
        if(info.isNotBlank())inner.addView(text(info,13f,false,muted).apply{
            setPadding(0,dp(8),0,dp(8))
        })
        shell.addView(inner)
        body.addView(shell,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT)
            .apply{bottomMargin=dp(12)})
        return inner
    }
    private fun button(title:String,onTap:()->Unit)=MaterialButton(this).apply{
        text=title;textSize=13f;isAllCaps=false
        setTextColor(if(dark)Color.rgb(148,241,223)else Color.rgb(3,108,101))
        backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        strokeColor=ColorStateList.valueOf(blue);strokeWidth=dp(1)
        cornerRadius=dp(14);setOnClickListener{onTap()}
    }
    private fun input(hint:String,v:String="")=EditText(this).apply{
        this.hint=hint;setText(v)
        isSingleLine=true;textSize=15f
        setTextColor(fg);setHintTextColor(muted)
        backgroundTintList=ColorStateList.valueOf(blue)
    }
    private fun notice(v:String)=MaterialAlertDialogBuilder(this)
        .setTitle("SaúdePrática").setMessage(v)
        .setPositiveButton("OK",null).show()
    private fun current():List<HealthExpense>=vault.list().filter{
        it.date.startsWith(year.toString())
    }
    private fun refresh(){
        body.removeAllViews()
        val entries=runCatching{current()}.getOrElse{
            notice(it.message?:"Erro ao carregar despesas.")
            emptyList()
        }
        val total=entries.sumOf{it.amountCents}
        val reimbursed=entries.sumOf{it.reimbursedCents}
        val summary=card("Resumo de "+year,
            entries.size.toString()+" despesa(s) registada(s)")
        summary.addView(text("Total: "+HealthExpensesStore.euros(total),19f,true,blue))
        summary.addView(text("Reembolsos registados: "+
            HealthExpensesStore.euros(reimbursed),14f,false,muted))
        summary.addView(text("Valor após reembolsos: "+
            HealthExpensesStore.euros((total-reimbursed).coerceAtLeast(0)),
            14f,false,muted))
        val buttons=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL}
        buttons.addView(button("‹ "+(year-1)){year--;refresh()},
            LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        buttons.addView(button((year+1).toString()+" ›"){
            year++;refresh()
        },LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        summary.addView(buttons)
        val actions=card("Registos e comprovativos",
            "Faturas, receitas médicas, despesas e pedidos de reembolso.")
        actions.addView(button("＋ Nova despesa"){edit(null)})
        actions.addView(button("▦ Exportar resumo CSV para Excel"){
            csv.launch("SaudePratica-despesas-"+year+".csv")
        })
        entries.forEach{expense->
            val detail=expense.date+" · "+expense.category+"\n"+
                expense.description+
                "\n"+expense.attachments.size+" documento(s) anexado(s) · "+
                expense.taxStatus
            val item=card(expense.merchant.ifBlank{"Despesa sem entidade"}+
                " · "+HealthExpensesStore.euros(expense.amountCents),detail)
            item.addView(button("✎ Editar despesa"){edit(expense)})
            item.addView(button("📎 Faturas, receitas e comprovativos"){
                showDocuments(expense)
            })
            item.addView(button("🗑 Eliminar despesa"){
                MaterialAlertDialogBuilder(this)
                    .setTitle("Apagar despesa?")
                    .setMessage("Também elimina os documentos anexados.")
                    .setPositiveButton("Apagar"){_,_->
                        runCatching{vault.remove(expense)}.onSuccess{refresh()}
                            .onFailure{notice(it.message?:"Erro ao apagar.")}
                    }.setNegativeButton("Cancelar",null).show()
            })
        }
        if(entries.isEmpty())card("Sem despesas neste ano",
            "Cria um registo, anexa a fatura ou fotografa a receita.")
        card("Informação sobre IRS e e-Fatura",
            "O estado fiscal é indicado por ti. A SaúdePrática não "+
            "confirma automaticamente que uma despesa é dedutível, "+
            "não comunica com a Autoridade Tributária e não substitui "+
            "o e-Fatura. Consulta os dados oficiais para confirmar a classificação.")
    }
    private fun validDate(v:String):String?{
        val value=v.trim()
        val format=DateTimeFormatter.ofPattern("dd/MM/uuuu")
            .withResolverStyle(ResolverStyle.STRICT)
        return runCatching{
            if(value.contains('/'))LocalDate.parse(value,format).toString()
            else LocalDate.parse(value).toString()
        }.getOrNull()
    }
    private fun edit(existing:HealthExpense?){
        val form=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(17),dp(6),dp(17),dp(12))
        }
        fun add(view:View){form.addView(view,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT)
            .apply{bottomMargin=dp(8)})}
        val date=input("Data da fatura (DD/MM/AAAA)",existing?.date?.let{
            runCatching{LocalDate.parse(it).format(DateTimeFormatter.ofPattern(
                "dd/MM/yyyy"))}.getOrNull()
        }?:LocalDate.now().format(DateTimeFormatter.ofPattern("dd/MM/yyyy")))
        val types=listOf("Farmácia","Consulta","Exame","Tratamento",
            "Óculos / Lentes","Dispositivo médico","Seguro / ADSE","Outros")
        val categories=Spinner(this).apply{
            adapter=ArrayAdapter(this@HealthExpensesActivity,
                android.R.layout.simple_spinner_dropdown_item,types)
            setSelection(types.indexOf(existing?.category).coerceAtLeast(0))
        }
        val merchant=input("Entidade / farmácia",existing?.merchant.orEmpty())
        val desc=input("Descrição",existing?.description.orEmpty())
        val receipt=input("N.º da fatura (opcional)",existing?.receiptNumber.orEmpty())
        val nif=input("NIF da entidade (opcional)",existing?.supplierNif.orEmpty())
        val total=input("Total (€)",existing?.let{
            HealthExpensesStore.euros(it.amountCents).removeSuffix(" €")
        }?:"")
        val refund=input("Reembolso de seguro/ADSE (€)",existing?.let{
            HealthExpensesStore.euros(it.reimbursedCents).removeSuffix(" €")
        }?:"")
        val states=listOf("Por verificar","Pendente no e-Fatura",
            "Confirmado no e-Fatura","Não aplicável")
        val status=Spinner(this).apply{
            adapter=ArrayAdapter(this@HealthExpensesActivity,
                android.R.layout.simple_spinner_dropdown_item,states)
            setSelection(states.indexOf(existing?.taxStatus).coerceAtLeast(0))
        }
        val note=input("Observações / indicação clínica",existing?.notes.orEmpty())
            .apply{isSingleLine=false;minLines=2}
        add(text("Data e categoria",14f,true,blue));add(date);add(categories)
        add(text("Fatura",14f,true,blue))
        listOf(merchant,desc,receipt,nif,total,refund).forEach(::add)
        add(text("Situação IRS / e-Fatura (confirmada por ti)",14f,true,blue))
        add(status);add(note)
        add(text("Os dados fiscais são informativos. "+
            "Só a verificação na Autoridade Tributária determina "+
            "a classificação efetiva.",12f,false,muted))
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle(if(existing==null)"Nova despesa de saúde" else "Editar despesa")
            .setView(ScrollView(this).apply{addView(form)})
            .setPositiveButton("Guardar",null)
            .setNegativeButton("Cancelar",null).show()
        dialog.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener{
                val normalized=validDate(date.text.toString())
                if(normalized==null){date.error="Data inválida.";return@setOnClickListener}
                val values=runCatching{
                    HealthExpensesStore.parseEuros(total.text.toString()) to
                    HealthExpensesStore.parseEuros(refund.text.toString())
                }.getOrElse{
                    total.error=it.message?:"Valor inválido."
                    return@setOnClickListener
                }
                if(values.first==0L&&total.text.toString().isBlank()){
                    total.error="Indica o valor.";return@setOnClickListener
                }
                val merchantValue=merchant.text.toString().trim()
                if(merchantValue.isBlank()){
                    merchant.error="Indica a entidade.";return@setOnClickListener
                }
                val nifValue=nif.text.toString().trim()
                if(nifValue.isNotBlank()&&!nifValue.matches(Regex("""\d{9}"""))){
                    nif.error="O NIF tem 9 dígitos.";return@setOnClickListener
                }
                val record=(existing?:vault.create(normalized,
                    types[categories.selectedItemPosition],merchantValue,
                    desc.text.toString(),receipt.text.toString(),nifValue,
                    values.first,values.second,states[status.selectedItemPosition],
                    note.text.toString())).copy(
                    date=normalized,category=types[categories.selectedItemPosition],
                    merchant=merchantValue,description=desc.text.toString().trim(),
                    receiptNumber=receipt.text.toString().trim(),
                    supplierNif=nifValue,amountCents=values.first,
                    reimbursedCents=values.second,
                    taxStatus=states[status.selectedItemPosition],
                    notes=note.text.toString().trim())
                runCatching{vault.save(record)}
                    .onSuccess{
                        dialog.dismiss();year=normalized.take(4).toInt()
                        refresh()
                        if(existing==null)showDocuments(record)
                    }.onFailure{notice(it.message?:"Erro ao guardar.")}
            }
    }
    private fun showDocuments(expense:HealthExpense){
        val latest=vault.list().firstOrNull{it.id==expense.id}?:return
        val choices=mutableListOf(
            "📎 Anexar PDF ou imagem existente",
            "📷 Fotografar fatura ou receita")
        latest.attachments.forEach{attachment->
            choices.add("📄 "+attachment.title)
        }
        MaterialAlertDialogBuilder(this).setTitle("Documentos · "+latest.merchant)
            .setItems(choices.toTypedArray()){_,which->
                selectedExpense=latest.id
                when(which){
                    0->askAttachmentTitle(false)
                    1->askAttachmentTitle(true)
                    else->openAttachment(latest,latest.attachments[which-2])
                }
            }.setPositiveButton("Fechar",null).show()
    }
    private fun askAttachmentTitle(photo:Boolean){
        val labels=arrayOf("Fatura","Receita médica",
            "Comprovativo ADSE/seguro","Outros documentos")
        MaterialAlertDialogBuilder(this).setTitle("Tipo de anexo")
            .setItems(labels){_,index->
                selectedAttachmentTitle=labels[index]
                if(photo){
                    if(ContextCompat.checkSelfPermission(this,Manifest.permission.CAMERA)
                        ==PackageManager.PERMISSION_GRANTED)photograph()
                    else permission.launch(Manifest.permission.CAMERA)
                }else attachmentPicker.launch(arrayOf("application/pdf","image/*"))
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun photograph(){
        runCatching{
            val dir=File(cacheDir,"saudepratica_expense_camera").apply{mkdirs()}
            val file=File.createTempFile("fatura_",".jpg",dir)
            tempPhoto=file
            camera.launch(FileProvider.getUriForFile(this,
                packageName+".documents",file))
        }.onFailure{notice(it.message?:"Não foi possível abrir a câmara.")}
    }
    private fun importAttachment(uri:Uri,temp:File?){
        val expenseId=selectedExpense
        if(expenseId.isNullOrBlank()){temp?.delete();return}
        runCatching{vault.attach(expenseId,uri,selectedAttachmentTitle)}
            .onSuccess{
                temp?.delete()
                refresh()
                Toast.makeText(this,"Documento guardado.",Toast.LENGTH_LONG).show()
            }.onFailure{
                temp?.delete()
                notice(it.message?:"Não foi possível guardar o anexo.")
            }
    }
    private fun openAttachment(e:HealthExpense,a:HealthExpenseAttachment){
        val actions=arrayOf("👁 Abrir documento","🗑 Eliminar anexo")
        MaterialAlertDialogBuilder(this).setTitle(a.title)
            .setItems(actions){_,index->
                if(index==0){
                    runCatching{
                        startActivity(Intent.createChooser(
                            Intent(Intent.ACTION_VIEW).apply{
                                setDataAndType(vault.open(e,a),a.mime)
                                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                            },"Abrir documento"))
                    }.onFailure{notice(it.message?:"Não foi possível abrir o documento.")}
                }else{
                    MaterialAlertDialogBuilder(this)
                        .setTitle("Eliminar este anexo?")
                        .setPositiveButton("Eliminar"){_,_->
                            runCatching{vault.removeAttachment(e,a.id)}
                                .onSuccess{refresh()}
                                .onFailure{notice(it.message?:"Erro ao eliminar.")}
                        }.setNegativeButton("Cancelar",null).show()
                }
            }.setNegativeButton("Cancelar",null).show()
    }
}
