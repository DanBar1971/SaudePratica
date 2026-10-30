from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
def swap(file,old,new,label):
    s=file.read_text(encoding="utf-8")
    if s.count(old)!=1:raise RuntimeError("v1.9.28 "+label+" anchor count "+str(s.count(old)))
    file.write_text(s.replace(old,new,1),encoding="utf-8")
main=base/"MainActivity.kt"
swap(main,'        "Análises Clínicas","Saúde Ocupacional","Beber água",',
          '        "Situação Clínica","Beber água",',"home checklist names")
swap(main,'''            DashboardModule("🧪", "Análises Clínicas", "Relatórios PDF, OCR e resultados") {
                startActivity(Intent(this,ClinicalLabsActivity::class.java)
                    .putExtra(ClinicalLabsActivity.EXTRA_PROFILE_ID,activeProfileId))
            },
            DashboardModule("🏥", "Saúde Ocupacional", "Medicina do Trabalho") {''',
          '''            DashboardModule("🏥", "Situação Clínica", "Medicina do Trabalho") {''',"home module removal/rename")
swap(main,'        val choice=BooleanArray(options.size){options[it] !in hidden}',
    '''        val choice=BooleanArray(options.size){options[it] !in hidden &&
            !(options[it]=="Situação Clínica" && "Saúde Ocupacional" in hidden)}''',
    "preserve old hidden preference in checklist")
swap(main,'''            it.title=="Mais" || it.title !in hiddenModules''',
    '''            it.title=="Mais" || (it.title !in hiddenModules &&
                !(it.title=="Situação Clínica" &&
                    "Saúde Ocupacional" in hiddenModules))''',
    "preserve existing visibility")
work=base/"WorkMedicineActivity.kt"
swap(work,'head.addView(text("🏥 Saúde Ocupacional",23f,true))',
    'head.addView(text("🏥 Situação Clínica",23f,true))',
    "clinical situation title, internal content unchanged")
target=base/"expenses/ExpenseReceiptOcrParser.kt"
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(Path("MediAgenda/v47_overrides/ExpenseReceiptOcrParser.kt")
    .read_text(encoding="utf-8"),encoding="utf-8")
expense=base/"HealthExpensesActivity.kt"
swap(expense,'import android.graphics.Color', '''import android.graphics.Color
import android.graphics.Bitmap
import android.graphics.Matrix
import android.graphics.pdf.PdfRenderer''',"OCR graphics imports")
swap(expense,'import android.widget.LinearLayout','''import android.widget.LinearLayout
import android.widget.ProgressBar''',"OCR progress")
swap(expense,'import com.mediagenda.app.data.ProfileStore','''import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.data.HealthDocumentStore
import com.mediagenda.app.expenses.ExpenseReceiptOcrParser
import com.mediagenda.app.expenses.ExpenseReceiptScan
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions''',"OCR + Documents imports")
swap(expense,'''    private var tempPhoto:File?=null''','''    private var tempPhoto:File?=null
    private var ocrCameraFile:File?=null
    private var ocrBusy=false
    private val receiptPicker=registerForActivityResult(
        ActivityResultContracts.OpenDocument()
    ){uri->if(uri!=null)recognizeReceipt(uri)}
    private val receiptCamera=registerForActivityResult(
        ActivityResultContracts.TakePicture()
    ){ok->
        val file=ocrCameraFile
        ocrCameraFile=null
        if(ok && file!=null){
            val uri=FileProvider.getUriForFile(this,packageName+".documents",file)
            recognizeReceipt(uri,file)
        }else file?.delete()
    }
    private val receiptPermission=registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ){ok->if(ok)captureReceipt()else notice("Permissão de câmara recusada.")}''',
    "receipt camera and picker")
swap(expense,'''        actions.addView(button("＋ Nova despesa"){edit(null)})''',
    '''        actions.addView(button("＋ Nova despesa"){chooseExpenseInput()})''',
    "new expense entry points")
swap(expense,'    private fun edit(existing:HealthExpense?){',
    '''    private fun edit(existing:HealthExpense?,
        draft:ExpenseReceiptScan?=null,source:Uri?=null){''',"reviewable OCR values")
swap(expense,'''        val date=input("Data da fatura (DD/MM/AAAA)",existing?.date?.let{
            runCatching{LocalDate.parse(it).format(DateTimeFormatter.ofPattern(
                "dd/MM/yyyy"))}.getOrNull()
        }?:LocalDate.now().format(DateTimeFormatter.ofPattern("dd/MM/yyyy")))''',
    '''        val rawDate=existing?.date ?: draft?.date.orEmpty()
        val date=input("Data da fatura (DD/MM/AAAA)",runCatching{
            LocalDate.parse(rawDate).format(DateTimeFormatter.ofPattern("dd/MM/yyyy"))
        }.getOrNull()?:LocalDate.now().format(DateTimeFormatter.ofPattern("dd/MM/yyyy")))''',
    "expense OCR date")
swap(expense,'setSelection(types.indexOf(existing?.category).coerceAtLeast(0))',
    'setSelection(types.indexOf(existing?.category ?: draft?.category).coerceAtLeast(0))',
    "expense OCR category")
for field,old,new in [
 ("merchant",'existing?.merchant.orEmpty()','existing?.merchant ?: draft?.merchant.orEmpty()'),
 ("description",'existing?.description.orEmpty()','existing?.description ?: draft?.description.orEmpty()'),
 ("receipt",'existing?.receiptNumber.orEmpty()','existing?.receiptNumber ?: draft?.receiptNumber.orEmpty()'),
 ("nif",'existing?.supplierNif.orEmpty()','existing?.supplierNif ?: draft?.supplierNif.orEmpty()')]:
    swap(expense,old,new,"OCR "+field)
swap(expense,'''        }?:"")
        val refund=input''',
    '''        }?:draft?.amount.orEmpty())
        val refund=input''',"OCR amount")
swap(expense,'''        add(text("Data e categoria",14f,true,blue));add(date);add(categories)''',
    '''        if(draft!=null){
            add(text("Dados sugeridos pelo OCR — confirma a entidade, "+
                "a data, o NIF e o total. A classificação fiscal continua manual. "+
                "O original já foi guardado em Documentos.",13f,true,blue))
            if(draft.raw.isBlank())
                add(text("Não foi possível extrair texto. Introduz apenas "+
                    "os campos em falta; o original está guardado.",13f,false,muted))
            else add(button("👁 Ver texto reconhecido"){
                MaterialAlertDialogBuilder(this)
                    .setTitle("Texto OCR — verifica os valores")
                    .setMessage(draft.raw.take(6500))
                    .setPositiveButton("Fechar",null).show()
            })
        }
        add(text("Data e categoria",14f,true,blue));add(date);add(categories)''',
    "OCR review notice")
swap(expense,'''                runCatching{vault.save(record)}
                    .onSuccess{
                        dialog.dismiss();year=normalized.take(4).toInt()
                        refresh()
                        if(existing==null)showDocuments(record)
                    }.onFailure{notice(it.message?:"Erro ao guardar.")}''',
    '''                runCatching{
                    vault.save(record)
                    if(source!=null) vault.attach(record.id,source,"Comprovativo digitalizado")
                }.onSuccess{
                    dialog.dismiss();year=normalized.take(4).toInt()
                    refresh()
                    if(existing==null && source==null)showDocuments(record)
                }.onFailure{
                    notice(it.message?:"Não foi possível guardar a despesa ou o anexo. "+
                        "O original permanece em Documentos.")
                }''',
    "OCR auto attach saved source")
swap(expense,'''    private fun showDocuments(expense:HealthExpense){''',
    '''    private fun chooseExpenseInput(){
        MaterialAlertDialogBuilder(this).setTitle("Nova despesa de saúde")
            .setItems(arrayOf(
                "✍ Inserir manualmente",
                "📷 Fotografar fatura ou comprovativo · OCR",
                "📄 Importar PDF ou imagem · OCR"
            )){_,option->
                when(option){
                    0->edit(null)
                    1->if(ContextCompat.checkSelfPermission(this,
                        Manifest.permission.CAMERA)==PackageManager.PERMISSION_GRANTED)
                            captureReceipt() else receiptPermission.launch(
                                Manifest.permission.CAMERA)
                    2->receiptPicker.launch(arrayOf("application/pdf","image/*"))
                }
            }.setNegativeButton("Cancelar",null).show()
    }
    private fun captureReceipt(){
        runCatching{
            val directory=File(cacheDir,"saudepratica_expense_camera")
                .apply{mkdirs()}
            val file=File.createTempFile("despesa_ocr_",".jpg",directory)
            ocrCameraFile=file
            receiptCamera.launch(FileProvider.getUriForFile(this,
                packageName+".documents",file))
        }.onFailure{notice(it.message?:"Não foi possível abrir a câmara.")}
    }
    private fun recognizeReceipt(uri:Uri,temp:File?=null){
        if(ocrBusy){temp?.delete();return}
        // Preserve original even when OCR finds no text or user cancels review.
        val stored=runCatching{
            val saved=HealthDocumentStore(this,activeProfileId).add(uri,
                "Despesa de saúde — "+LocalDate.now().toString())
            HealthDocumentStore(this,activeProfileId).contentUri(saved)
        }.getOrElse{e->
            temp?.delete()
            notice("Não foi possível arquivar o original em Documentos: "+e.message)
            return
        }
        temp?.delete()
        ocrBusy=true
        val message=text("A reconhecer o documento no telemóvel…",14f)
        val info=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(12),dp(16),dp(12))
            addView(ProgressBar(this@HealthExpensesActivity))
            addView(message)
        }
        val waiting=MaterialAlertDialogBuilder(this)
            .setTitle("OCR · Despesa de saúde").setView(info)
            .setCancelable(false).show()
        val client=TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
        val raw=StringBuilder()
        fun finish(){
            ocrBusy=false
            client.close()
            if(!isFinishing && !isDestroyed){
                waiting.dismiss()
                edit(null,ExpenseReceiptOcrParser.parse(raw.toString()),stored)
            }
        }
        fun process(page:Int,input:InputImage,next:()->Unit){
            client.process(input).addOnSuccessListener{result->
                raw.append("\\n--- Página ").append(page).append(" ---\\n")
                    .append(result.text).append("\\n")
            }.addOnFailureListener{error->
                raw.append("\\nOCR indisponível na página ").append(page)
                    .append(": ").append(error.message).append("\\n")
            }.addOnCompleteListener{next()}
        }
        val mime=contentResolver.getType(stored).orEmpty().lowercase()
        if(mime=="application/pdf"){
            try{
                val descriptor=contentResolver.openFileDescriptor(stored,"r")
                    ?:error("PDF inacessível.")
                val pdf=PdfRenderer(descriptor)
                val pages=pdf.pageCount
                if(pages==0 || pages>16){
                    pdf.close()
                    error("PDF com "+pages+" páginas; máximo 16. "+
                        "O original já está guardado em Documentos.")
                }
                fun next(pageIndex:Int){
                    if(pageIndex>=pages){pdf.close();finish();return}
                    message.text="A reconhecer página "+(pageIndex+1)+" de "+pages+"…"
                    try{
                        val page=pdf.openPage(pageIndex)
                        val scale=minOf(2.0f,1500f/
                            maxOf(page.width,page.height).coerceAtLeast(1))
                        val width=(page.width*scale).toInt().coerceAtLeast(1)
                        val height=(page.height*scale).toInt().coerceAtLeast(1)
                        val bitmap=Bitmap.createBitmap(width,height,
                            Bitmap.Config.ARGB_8888)
                        bitmap.eraseColor(Color.WHITE)
                        page.render(bitmap,null,Matrix().apply{
                            postScale(scale,scale)
                        },PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                        page.close()
                        process(pageIndex+1,InputImage.fromBitmap(bitmap,0)){
                            bitmap.recycle()
                            next(pageIndex+1)
                        }
                    }catch(e:Exception){
                        raw.append("\\nErro de leitura PDF: ").append(e.message)
                        pdf.close();finish()
                    }
                }
                next(0)
            }catch(e:Exception){
                raw.append("Não foi possível analisar este PDF: ").append(e.message)
                finish()
            }
        }else{
            try{
                process(1,InputImage.fromFilePath(this,stored)){finish()}
            }catch(e:Exception){
                raw.append("Não foi possível analisar a imagem: ").append(e.message)
                finish()
            }
        }
    }
    private fun showDocuments(expense:HealthExpense){''',"new expense input and OCR workflow")
swap(expense,'''        runCatching{vault.attach(expenseId,uri,selectedAttachmentTitle)}
            .onSuccess{''',
    '''        runCatching{
            val entry=vault.attach(expenseId,uri,selectedAttachmentTitle)
            HealthDocumentStore(this,activeProfileId).add(uri,
                selectedAttachmentTitle+" — "+entry.merchant)
        }.onSuccess{''',
    "mirror manually attached original to Documents")
gradle=root/"app/build.gradle.kts"
swap(gradle,'versionCode = 37','versionCode = 38',"version code")
swap(gradle,'versionName = "1.9.27"','versionName = "1.9.28"',"version name")
print("SaúdePrática v1.9.28: Situação Clínica; no separate home analyses; receipt camera/PDF OCR, review and persistent originals in Documentos.")
