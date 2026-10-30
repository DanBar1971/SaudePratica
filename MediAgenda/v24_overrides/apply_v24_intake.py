from pathlib import Path
f=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt")
s=f.read_text(encoding="utf-8")
def sub(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.5 med take missing "+label)
 s=s.replace(old,new,1)
sub('''                adapter = MedicationAdapter(items,
                    onClick = { editMedication(it) },
                    onDelete = { med -> confirmDelete("Apagar ${med.medication}?") {''',
'''                adapter = MedicationAdapter(items,
                    onClick = { editMedication(it) },
                    onTaken = { med ->
                        MaterialAlertDialogBuilder(this@MainActivity)
                            .setTitle("Confirmar toma de medicação")
                            .setMessage("Confirma que ${med.medication} foi realmente tomado agora? Este registo não altera os avisos programados.")
                            .setPositiveButton("Sim, tomei") { _,_ ->
                                runCatching {
                                    PersonalHealthStore(this@MainActivity,activeProfileId)
                                        .confirmIntake(med.id,med.medication)
                                }.onSuccess {
                                    Toast.makeText(this@MainActivity,"Toma confirmada.",Toast.LENGTH_SHORT).show()
                                    showMedication()
                                }.onFailure {
                                    showError(it.message?:"Não foi possível registar a toma.")
                                }
                            }.setNegativeButton("Cancelar",null).show()
                    },
                    lastTaken = { med ->
                        PersonalHealthStore(this@MainActivity,activeProfileId)
                            .latestIntakeFor(med.id)
                    },
                    onDelete = { med -> confirmDelete("Apagar ${med.medication}?") {''',
"adapter onTaken")
sub('''private class MedicationAdapter(
    private val items:List<Medication>, private val onClick:(Medication)->Unit, private val onDelete:(Medication)->Unit
):RecyclerView.Adapter<MedicationAdapter.H>() {''',
'''private class MedicationAdapter(
    private val items:List<Medication>,
    private val onClick:(Medication)->Unit,
    private val onTaken:(Medication)->Unit,
    private val lastTaken:(Medication)->Long?,
    private val onDelete:(Medication)->Unit
):RecyclerView.Adapter<MedicationAdapter.H>() {''',"adapter callbacks")
sub('''class H(val card:MaterialCardView,val title:TextView,val detail:TextView,val code:TextView,val delete:TextView,
        val timeBadge:TextView,val pill:TextView,val thumbnail:android.widget.ImageView):RecyclerView.ViewHolder(card)''',
'''class H(val card:MaterialCardView,val title:TextView,val detail:TextView,val code:TextView,val delete:TextView,
        val timeBadge:TextView,val pill:TextView,val thumbnail:android.widget.ImageView,
        val takeButton:com.google.android.material.button.MaterialButton,
        val lastTakenText:TextView):RecyclerView.ViewHolder(card)''',"holder")
sub('''        texts.addView(title);texts.addView(detail);texts.addView(code)
        val del=TextView(c)''',
'''        val taken=TextView(c).apply {
            textSize=11f;setTextColor(Color.parseColor("#0A5C56"))
            setPadding(0,dp(7),0,0)
        }
        val take=com.google.android.material.button.MaterialButton(c).apply {
            text="✓ Tomei";isAllCaps=false;textSize=11.5f
            setTextColor(Color.parseColor("#0A5C56"))
            backgroundTintList=ColorStateList.valueOf(Color.parseColor("#E6F4F1"))
            cornerRadius=dp(12);minHeight=dp(38)
        }
        texts.addView(title);texts.addView(detail);texts.addView(code)
        texts.addView(taken)
        texts.addView(take,LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT,ViewGroup.LayoutParams.WRAP_CONTENT))
        val del=TextView(c)''',"button")
sub('''        card.addView(row);return H(card,title,detail,code,del,clock,icon,image)''',
'''        card.addView(row);return H(card,title,detail,code,del,clock,icon,image,take,taken)''',"holder return")
sub('''        h.card.setOnClickListener{onClick(m)};h.delete.setOnClickListener{onDelete(m)}''',
'''        val last=runCatching{lastTaken(m)}.getOrNull()
        h.lastTakenText.text=if(last!=null)
            "Última toma confirmada: "+java.text.SimpleDateFormat(
                "dd/MM HH:mm",Locale("pt","PT")).format(java.util.Date(last))
            else ""
        h.lastTakenText.visibility=if(last==null)View.GONE else View.VISIBLE
        h.takeButton.setOnClickListener{onTaken(m)}
        h.card.setOnClickListener{onClick(m)}
        h.delete.setOnClickListener{onDelete(m)}''',"bind")
f.write_text(s,encoding="utf-8")
print("v1.9.5: medication taken button and recorded confirmation.")
