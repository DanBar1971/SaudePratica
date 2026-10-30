#!/usr/bin/env python3
"""SaudePratica 1.9.106: pending Alteracoes 1, backwards-compatible UI and persistence."""
from pathlib import Path
ROOT=Path('build-src/MediAgenda_Android_v1/app')
APP=ROOT/'src/main/java/com/mediagenda/app'
def edit(name,fn):
    p=APP/name; s=p.read_text(encoding='utf-8'); t=fn(s)
    if t==s:raise ValueError(f'No change: {name}')
    p.write_text(t,encoding='utf-8')
def one(s,old,new,label):
    n=s.count(old)
    assert n==1,(label,n)
    return s.replace(old,new,1)

# Data model: cancelled is a real stored state. Old JSON reads false by default.
def appointment_model(s):
    return one(s,'    var done: Boolean = false,\n    var remindersMinutes:',
        '    var done: Boolean = false,\n    var cancelled: Boolean = false,\n    var remindersMinutes:', 'appointment cancellation model')
edit('model/Models.kt',appointment_model)
def appointment_repo(s):
    s=one(s,'                done = o.optBoolean("done", false),\n                remindersMinutes = rem,',
        '                done = o.optBoolean("done", false),\n                cancelled = o.optBoolean("cancelled", false),\n                remindersMinutes = rem,', 'read cancellation')
    s=one(s,'                .put("done", a.done)\n                .put("reminders_minutes",',
        '                .put("done", a.done)\n                .put("cancelled", a.cancelled)\n                .put("reminders_minutes",','write cancellation')
    return s
edit('data/DataRepository.kt',appointment_repo)

# Clinical registers: reuse the exact offline HealthcareCatalog as Agenda.
def clinical(s):
    old='''            val hospital=field("Hospital ou clínica (opcional)",savedUnit)
            val number=field("Número de observação ou processo",savedNumber)
            sheet.addView(hospital);sheet.addView(number)'''
    new='''            val hospital=field("Hospital ou clínica (opcional)",savedUnit)
            val number=field("Número de observação ou processo",savedNumber)
            sheet.addView(hospital)
            sheet.addView(button("🏥 Escolher unidade · Distrito → Concelho"){
                chooseClinicalDistrict{selected->hospital.setText(selected)}
            })
            sheet.addView(number)'''
    s=one(s,old,new,'clinical chooser button')
    start=s.index('        clinicalCard.addView(button("✎ Editar número antigo (opcional)"){')
    end=s.index('        val items=runCatching{store.all()}',start)
    s=s[:start]+s[end:]
    # Keep original number untouched: shown as archived read-only; user specifically requested removing its editor.
    helper='''    private fun chooseClinicalDistrict(chosen:(String)->Unit){
        val districts=HealthcareCatalog.districts(this)
        MaterialAlertDialogBuilder(this).setTitle("Distrito · Unidade clínica")
            .setItems(districts.toTypedArray()){_,index->
                val district=districts[index]
                val municipalities=HealthcareCatalog.municipalities(this,district)
                MaterialAlertDialogBuilder(this).setTitle("Concelho · $district")
                    .setItems(municipalities.toTypedArray()){_,cIndex->
                        val municipality=municipalities[cIndex]
                        val units=HealthcareCatalog.facilities(this,district,municipality)
                        val choices=units.map{it.name}+listOf("✍️ Outra unidade (escrever)")
                        MaterialAlertDialogBuilder(this)
                            .setTitle("Unidade · $municipality")
                            .setItems(choices.toTypedArray()){_,uIndex->
                                if(uIndex<units.size)chosen(units[uIndex].name)
                                else {
                                    val custom=field("Nome do hospital ou clínica")
                                    MaterialAlertDialogBuilder(this)
                                        .setTitle("Introduzir unidade de saúde")
                                        .setView(custom)
                                        .setPositiveButton("Escolher"){_,_->
                                            val name=custom.text.toString().trim()
                                            if(name.isNotBlank()){
                                                runCatching{HealthcareCatalog.remember(
                                                    this,name,district,municipality)}
                                                chosen(name)
                                            }
                                        }.setNegativeButton("Cancelar",null).show()
                                }
                            }.setNegativeButton("Cancelar",null).show()
                    }.setNegativeButton("Cancelar",null).show()
            }.setNegativeButton("Cancelar",null).show()
    }

'''
    s=one(s,'    private fun redraw(){',helper+'    private fun redraw(){','clinical chooser method')
    # Day/light branding and local translation
    s=one(s,'background=if(dark&&backdrop!=null)\n                LayerDrawable(arrayOf(backdrop,ColorDrawable(Color.argb(125,0,13,24))))\n            else ColorDrawable(if(dark)Color.rgb(4,21,31) else Color.rgb(245,249,250))',
        '''background=if(backdrop!=null)
                LayerDrawable(arrayOf(backdrop,ColorDrawable(if(dark)
                    Color.argb(125,0,13,24) else Color.argb(224,248,251,252))))
            else ColorDrawable(if(dark)Color.rgb(4,21,31) else Color.rgb(245,249,250))''','clinical light background')
    s=one(s,'        text=s;textSize=size;setTextColor(color)',
          '        text=com.mediagenda.app.i18n.AppLanguage.t(this@WorkMedicineActivity,s);textSize=size;setTextColor(color)', 'clinical translated text')
    s=one(s,'        text=label;isAllCaps=false;textSize=13f',
          '        text=com.mediagenda.app.i18n.AppLanguage.t(this@WorkMedicineActivity,label);isAllCaps=false;textSize=13f', 'clinical translated buttons')
    return s
edit('WorkMedicineActivity.kt',clinical)

# Calendar + meds + main shell.
def main(s):
    old='''            } else {
                setBackgroundColor(appBackground)
            }
        }
'''
    new='''            } else {
                // A lighter variation of the SAME official SaúdePrática wallpaper,
                // so switching appearance never removes the branded background.
                val wallpaper=androidx.core.content.ContextCompat.getDrawable(
                    this@MainActivity,R.drawable.saude_background)?.mutate()
                if(wallpaper is android.graphics.drawable.BitmapDrawable)
                    wallpaper.gravity=Gravity.FILL
                background=if(wallpaper!=null)android.graphics.drawable.LayerDrawable(
                    arrayOf(wallpaper,android.graphics.drawable.ColorDrawable(
                        Color.argb(224,248,251,252))))
                    else android.graphics.drawable.ColorDrawable(appBackground)
            }
        }
'''
    s=one(s,old,new,'main light background')
    # Agenda compaction and filter. Keep filter per profile.
    s=one(s,'quickActions.addView(secondaryButton("🏥 Procurar unidade") { showHealthcareSearchHelp() },\n            LinearLayout.LayoutParams(0,dp(44),1f)',
       'quickActions.addView(secondaryButton("🏥 Procurar unidade") { showHealthcareSearchHelp() }.apply {textSize=11f;minHeight=dp(34);setPadding(dp(5),0,dp(5),0)},\n            LinearLayout.LayoutParams(0,dp(38),1f)','agenda compact search')
    s=one(s,'quickActions.addView(secondaryButton("📎 Importar guia") { pickHealthDocument("agenda") },\n            LinearLayout.LayoutParams(0,dp(44),1f)',
       'quickActions.addView(secondaryButton("📎 Importar guia") { pickHealthDocument("agenda") }.apply {textSize=11f;minHeight=dp(34);setPadding(dp(5),0,dp(5),0)},\n            LinearLayout.LayoutParams(0,dp(38),1f)','agenda compact import')
    s=one(s,'content.addView(quickActions,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(14)})\n        val items = repo.loadAppointments().sortedWith(compareBy<Appointment>{it.date}.thenBy{it.time})',
'''content.addView(quickActions,LinearLayout.LayoutParams(-1,-2).apply{bottomMargin=dp(6)})
        val allAppointments=repo.loadAppointments().sortedWith(compareBy<Appointment>{it.date}.thenBy{it.time})
        val filters=listOf("Todas","Pendentes","Realizadas","Canceladas")
        val selection=getSharedPreferences("saudepratica_agenda_filters",MODE_PRIVATE)
            .getString(activeProfileId,"Todas") ?: "Todas"
        val filterRow=LinearLayout(this).apply{
            orientation=LinearLayout.HORIZONTAL
            setPadding(0,0,0,dp(7))
        }
        filters.forEach{option->
            filterRow.addView(secondaryButton(option) {}.apply{
                textSize=10f;minHeight=dp(34)
                setPadding(dp(3),0,dp(3),0)
                alpha=if(selection==option)1f else 0.65f
                setOnClickListener{
                    getSharedPreferences("saudepratica_agenda_filters",MODE_PRIVATE)
                        .edit().putString(activeProfileId,option).apply()
                    showAgenda()
                }
            },LinearLayout.LayoutParams(0,dp(38),1f))
        }
        content.addView(filterRow)
        val items=allAppointments.filter{appt->when(selection){
            "Pendentes" -> !appt.done && !appt.cancelled
            "Realizadas" -> appt.done && !appt.cancelled
            "Canceladas" -> appt.cancelled
            else -> true
        }}''','agenda filters')
    s=one(s,'content.addView(sectionRow("Marcações", "${items.size} no total") {',
          'content.addView(sectionRow("Marcações", "${items.size} de ${allAppointments.size}") {','agenda total after filters')
    # Order category/state; keep name and date supported.
    s=one(s,'val items = if (sorting == "date") allItems.sortedWith(\n            compareBy<Medication> { nextMedicationTime(it) ?: LocalDateTime.MAX }\n                .thenBy { it.medication.lowercase(Locale("pt", "PT")) }\n        ) else allItems.sortedBy { it.medication.lowercase(Locale("pt", "PT")) }',
'''val items=when(sorting){
            "date" -> allItems.sortedWith(compareBy<Medication>{nextMedicationTime(it)?:LocalDateTime.MAX}
                .thenBy{it.medication.lowercase(Locale("pt","PT"))})
            "category" -> allItems.sortedWith(compareBy<Medication>{it.dosePattern}
                .thenBy{it.medication.lowercase(Locale("pt","PT"))})
            "status" -> allItems.sortedWith(compareBy<Medication>{med->
                if(med.suspendedFrom.isNotBlank() &&
                    runCatching{!LocalDate.parse(med.suspendedFrom).isAfter(LocalDate.now())}.getOrDefault(true)) 3
                else if(med.dosePattern.equals("sos",true))2 else 0
            }.thenBy{it.medication.lowercase(Locale("pt","PT"))})
            else -> allItems.sortedBy{it.medication.lowercase(Locale("pt","PT"))}
        }''','med sorting')
    s=one(s,'secondaryButton(if (sorting == "date") "📅 Data / hora ▾" else "A–Z Nome ▾") {',
'''secondaryButton(when(sorting){
            "date"->"📅 Próxima toma ▾"
            "category"->"💊 Categoria ▾"
            "status"->"◉ Estado ▾"
            else->"A–Z Nome ▾"
        }) {''','med sorting label')
    s=one(s,'''                .setSingleChoiceItems(arrayOf("Nome (A–Z)", "Próxima data e hora"),
                    if (sorting == "date") 1 else 0) { dialog, selected ->
                    getSharedPreferences("saudepratica_med_sort", MODE_PRIVATE)
                        .edit().putString(activeProfileId, if (selected == 0) "name" else "date").apply()''',
'''                .setSingleChoiceItems(arrayOf("Nome (A–Z)", "Próxima toma", "Categoria", "Estado"),
                    listOf("name","date","category","status").indexOf(sorting).coerceAtLeast(0)) { dialog, selected ->
                    getSharedPreferences("saudepratica_med_sort", MODE_PRIVATE)
                        .edit().putString(activeProfileId,
                            listOf("name","date","category","status")[selected]).apply()''','med sort options')
    # Appointment editor: two boolean flags with mutually exclusive state semantics.
    anchor='''        val ocr=inputMulti("Texto reconhecido / notas",a.ocrText)
        box.addView(noteBox("Local, edifício e especialidade",'''
    replacement='''        val ocr=inputMulti("Texto reconhecido / notas",a.ocrText)
        val statusField=android.widget.Spinner(this).apply{
            adapter=android.widget.ArrayAdapter(this@MainActivity,
                android.R.layout.simple_spinner_dropdown_item,
                listOf("Pendente","Realizada","Cancelada"))
            setSelection(if(a.cancelled)2 else if(a.done)1 else 0)
        }
        box.addView(noteBox("Estado da marcação",
            "Escolhe Pendente, Realizada ou Cancelada. As marcações antigas não mudam de estado automaticamente."))
        box.addView(statusField)
        box.addView(noteBox("Local, edifício e especialidade",'''
    s=one(s,anchor,replacement,'appointment status editor')
    s=one(s,'                a.ocrText=ocr.edit.text.toString()\n                val all=repo.loadAppointments()',
'''                a.ocrText=ocr.edit.text.toString()
                a.done=statusField.selectedItemPosition==1
                a.cancelled=statusField.selectedItemPosition==2
                val all=repo.loadAppointments()''','appointment save state')
    # Medication visual status is rendered by its adapter below.
    return s
edit('MainActivity.kt',main)

# Medication and agenda adapters: readable labels and state differentiation.
def adapters(s):
    s=one(s,'val leafletBadge:TextView):RecyclerView.ViewHolder(card)',
        'val leafletBadge:TextView,val stateBadge:TextView):RecyclerView.ViewHolder(card)','med viewholder state')
    s=one(s,'        val stack=LinearLayout(c).apply{orientation=LinearLayout.VERTICAL}\n        stack.addView(suspended,LinearLayout.LayoutParams(-1,-2));stack.addView(row)\n        card.addView(stack)\n        return H(card,title,detail,code,del,clock,icon,image,take,taken,suspended,leaflet)',
'''        val stateBadge=TextView(c).apply{
            textSize=11f;setTypeface(typeface,Typeface.BOLD)
            setTextColor(Color.parseColor("#09675E"))
            setPadding(dp(12),dp(7),dp(12),dp(8))
        }
        val stack=LinearLayout(c).apply{orientation=LinearLayout.VERTICAL}
        stack.addView(suspended,LinearLayout.LayoutParams(-1,-2))
        stack.addView(row)
        stack.addView(stateBadge,LinearLayout.LayoutParams(-1,-2))
        card.addView(stack)
        return H(card,title,detail,code,del,clock,icon,image,take,taken,suspended,leaflet,stateBadge)''','med status badge')
    s=one(s,'        h.takeButton.setOnClickListener{onTaken(m)}',
'''        val today=java.time.LocalDate.now()
        val scheduled=runCatching{java.time.LocalTime.parse(alarm)}.getOrNull()
        val lastDate=last?.let{java.time.Instant.ofEpochMilli(it)
            .atZone(java.time.ZoneId.systemDefault()).toLocalDate()}
        val confirmedToday=lastDate==today
        val overdue=scheduled!=null && scheduled.isBefore(java.time.LocalTime.now()) &&
            !confirmedToday && !suspended && m.dosePattern!="sos"
        val state=when{
            suspended -> "⏸ SUSPENSA"
            m.dosePattern.equals("sos",true) -> "🆘 SOS · Registo manual"
            overdue -> "⚠️ Hora prevista ultrapassada · confirmar toma"
            confirmedToday -> "✓ Toma registada hoje"
            else -> "● Ativa · A aguardar toma"
        }
        h.stateBadge.text=com.mediagenda.app.i18n.AppLanguage.t(h.card.context,state)
        h.stateBadge.setTextColor(if(overdue)Color.parseColor("#AE4D21")
            else if(suspended)Color.parseColor("#A95117") else Color.parseColor("#09675E"))
        h.card.alpha=if(suspended)0.8f else 1f
        h.takeButton.setOnClickListener{onTaken(m)}''','med state inference')
    # appointments specific explicit state label and next/today highlight.
    s=one(s,'        val title:TextView,val detail:TextView,val share:TextView,\n        val delete:TextView):RecyclerView.ViewHolder(card)',
        '        val title:TextView,val detail:TextView,val state:TextView,val share:TextView,\n        val delete:TextView):RecyclerView.ViewHolder(card)','appt viewholder')
    s=one(s,'        texts.addView(title);texts.addView(detail)\n        val del=TextView(c)',
'''        texts.addView(title);texts.addView(detail)
        val status=TextView(c).apply{textSize=11f;setTypeface(typeface,Typeface.BOLD)
            setPadding(0,dp(5),0,0)}
        texts.addView(status)
        val del=TextView(c)''','appt status view')
    s=one(s,'return H(card,date,clock,title,detail,share,del)',
        'return H(card,date,clock,title,detail,status,share,del)','appt holder return')
    start='''        val completed=a.done
        h.card.alpha=if(completed)0.67f else 1f
        h.card.setCardBackgroundColor(if(completed)Color.parseColor("#E8F1EF") else Color.WHITE)
        h.card.strokeColor=if(completed)Color.parseColor("#89B5A9") else
            if(expired)Color.parseColor("#E0B88B") else Color.parseColor("#E3E8EF")
        h.dateBox.text=if(completed)"✓\\n"+formatDate(a.date).replace("\\n"," ") else formatDate(a.date)'''
    end='''        val completed=a.done && !a.cancelled
        val canceled=a.cancelled
        val today=runCatching{java.time.LocalDate.parse(a.date)==java.time.LocalDate.now()}
            .getOrDefault(false)
        h.card.alpha=if(canceled)0.58f else if(completed)0.72f else 1f
        h.card.setCardBackgroundColor(when {
            canceled -> Color.parseColor("#F3F4F6")
            completed -> Color.parseColor("#E8F1EF")
            today -> Color.parseColor("#F0FCFA")
            else -> Color.WHITE
        })
        h.card.strokeColor=when {
            canceled -> Color.parseColor("#C0C6CD")
            completed -> Color.parseColor("#89B5A9")
            today -> Color.parseColor("#13A89A")
            expired -> Color.parseColor("#E0B88B")
            else -> Color.parseColor("#E3E8EF")
        }
        h.state.text=when {
            canceled -> "✕ CANCELADA"
            completed -> "✓ REALIZADA"
            today -> "● HOJE · PENDENTE"
            expired -> "⚠️ POR CONFIRMAR"
            else -> "● PENDENTE"
        }
        h.state.setTextColor(if(canceled)Color.parseColor("#697585")
            else if(completed)Color.parseColor("#0A6655")
            else if(expired)Color.parseColor("#AE4D21")
            else Color.parseColor("#0B7A71"))
        h.dateBox.text=if(completed)"✓\\n"+formatDate(a.date).replace("\\n"," ") else formatDate(a.date)'''
    s=one(s,start,end,'appointment state colors')
    return s
edit('MainActivity.kt',adapters)

# Six-step wizard with optional clinical/contact fields and saved recap.
def wizard(s):
    s=one(s,'/** Guided 4-step profile creation.', '/** Guided 6-step profile creation.','wizard doc')
    s=one(s,'    private var email=""','''    private var email=""
    private var address=""
    private var emergencyName=""
    private var emergencyPhone=""
    private var healthUnit=""
    private var observationNote=""''','wizard new fields')
    s=s.replace('step=state.getInt("wizard_step",0).coerceIn(0,3)','step=state.getInt("wizard_step",0).coerceIn(0,5)')
    s=one(s,'            email=state.getString("wizard_email","")','''            email=state.getString("wizard_email","")
            address=state.getString("wizard_address","")
            emergencyName=state.getString("wizard_emergency_name","")
            emergencyPhone=state.getString("wizard_emergency_phone","")
            healthUnit=state.getString("wizard_health_unit","")
            observationNote=state.getString("wizard_observation_note","")''','wizard restore fields')
    s=one(s,'        state.putString("wizard_phone",phone);state.putString("wizard_email",email)',
'''        state.putString("wizard_phone",phone);state.putString("wizard_email",email)
        state.putString("wizard_address",address)
        state.putString("wizard_emergency_name",emergencyName)
        state.putString("wizard_emergency_phone",emergencyPhone)
        state.putString("wizard_health_unit",healthUnit)
        state.putString("wizard_observation_note",observationNote)''','wizard persist fields')
    s=one(s,'progress.text="● ${step+1}/4   "+listOf("Identificação","Cartão de Cidadão","Perfis e funções","Confirmar e guardar")[step]',
'''progress.text="● ${step+1}/6   "+listOf("Identificação", "Documento",
            "Tipo de perfil", "Contactos", "Dados clínicos", "Confirmar e guardar")[step]''','wizard 6 steps')
    s=one(s,'next.text=if(step==3)"✓ Criar perfil" else "Seguinte ›"',
          'next.text=if(step==5)"✓ Criar perfil" else "Seguinte ›"','wizard last step')
    old='''            3->{
                body.addView(label("Últimos detalhes",22f,true))
                hint("Os contactos são opcionais. Confirma os dados antes de criar o perfil.")
                field("Telemóvel / telefone",phone){phone=it}
                field("Email",email){email=it}
                body.addView(label("Resumo",18f,true))
                hint("Perfil: "+name.ifBlank{"Sem nome"}+"\\n"+
                    "Cartão de Cidadão: "+(if(ccNumber.isNotBlank())"Dados inseridos" else "Opcional"))
                hint("Fotografia: "+(if(tempFiles["avatar"]!=null)"Sim" else "Ainda não")+
                    " · CC: "+(if(saveCcPhotos)"Guardar fotos" else "Não guardar fotos"))
                hint("Deste telemóvel: "+(if(owner)"Sim" else "Não"))
                hint("Cuidador: "+(if(caregiver)"Sim" else "Não"))
            }'''
    new='''            3->{
                body.addView(label("Contactos e dados base",22f,true))
                hint("O telemóvel, a morada e os contactos de emergência podem ser alterados depois.")
                field("Telemóvel / telefone",phone){phone=it}
                field("Email",email){email=it}
                field("Morada",address){address=it}
                field("Contacto de emergência · Nome",emergencyName){emergencyName=it}
                field("Contacto de emergência · Telefone",emergencyPhone){emergencyPhone=it}
            }
            4->{
                body.addView(label("Dados clínicos essenciais",22f,true))
                hint("Podes deixar estes campos em branco. Os números clínicos ficam na Situação Clínica.")
                field("Unidade de saúde preferencial",healthUnit){healthUnit=it}
                field("Observações clínicas (opcional)",observationNote){observationNote=it}
                hint("Para associar um hospital a cada número de observação, abre Situação Clínica após criares o perfil.")
            }
            5->{
                body.addView(label("Confirmar e guardar",22f,true))
                hint("Revê a informação. Todos os campos podem ser corrigidos mais tarde.")
                photo("avatar")
                body.addView(label("Resumo",18f,true))
                hint("Perfil: "+name.ifBlank{"Sem nome"}+"\\n"+
                    "Cartão de Cidadão: "+(if(ccNumber.isNotBlank())"Dados inseridos" else "Opcional"))
                hint("Fotografia: "+(if(tempFiles["avatar"]!=null)"Sim" else "Ainda não")+
                    " · CC: "+(if(saveCcPhotos)"Guardar fotos" else "Não guardar fotos"))
                hint("Deste telemóvel: "+(if(owner)"Sim" else "Não"))
                hint("Cuidador: "+(if(caregiver)"Sim" else "Não"))
                hint("Contacto de emergência: "+emergencyName.ifBlank{"Não indicado"})
                hint("Unidade de saúde: "+healthUnit.ifBlank{"Não indicada"})
            }'''
    s=one(s,old,new,'wizard redesign screens')
    s=one(s,'if(step<3){step++;render()}else finishWizard()',
          'if(step<5){step++;render()}else finishWizard()','wizard final logic')
    s=one(s,'                .putString("email",email.trim())',
'''                .putString("email",email.trim())
                .putString("address",address.trim())
                .putString("contact_name",emergencyName.trim())
                .putString("contact_phone",emergencyPhone.trim())
                .putString("health_unit",healthUnit.trim())
                .putString("clinical_notes",observationNote.trim())''','wizard save extras')
    # App's original wallpaper, rather than fixed dark wizard even when user selected light.
    s=one(s,'            setBackgroundColor(bg)\n        }\n        ViewCompat.setOnApplyWindowInsetsListener(root)',
'''            val savedTheme=getSharedPreferences("mediagenda_ui",MODE_PRIVATE)
                .getString("theme_mode","system")
            val light=savedTheme=="light" || (savedTheme=="system" &&
                (resources.configuration.uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK)
                  !=android.content.res.Configuration.UI_MODE_NIGHT_YES)
            val wallpaper=androidx.core.content.ContextCompat.getDrawable(
                this@ProfileWizardActivity,R.drawable.saude_background)?.mutate()
            if(wallpaper is android.graphics.drawable.BitmapDrawable)wallpaper.gravity=Gravity.FILL
            background=if(wallpaper!=null)android.graphics.drawable.LayerDrawable(arrayOf(
                wallpaper,android.graphics.drawable.ColorDrawable(if(light)
                    Color.argb(224,248,251,252) else Color.argb(115,0,12,20))))
                else android.graphics.drawable.ColorDrawable(bg)
        }
        ViewCompat.setOnApplyWindowInsetsListener(root)''','wizard light background')
    return s
edit('ProfileWizardActivity.kt',wizard)

# Light wallpaper also on meal diary; keep cards legible.
def nutrition(s):
    s=one(s,'''            if (isDark && bg != null) { if(bg is BitmapDrawable)bg.gravity=Gravity.FILL
                background=LayerDrawable(arrayOf(bg, ColorDrawable(Color.argb(100,1,14,24))))
            } else setBackgroundColor(Color.rgb(245,248,250))''',
'''            if (bg != null) { if(bg is BitmapDrawable)bg.gravity=Gravity.FILL
                background=LayerDrawable(arrayOf(bg,ColorDrawable(if(isDark)
                    Color.argb(100,1,14,24) else Color.argb(224,248,251,252))))
            } else setBackgroundColor(Color.rgb(245,248,250))''','nutrition light background')
    # Existing gallery cards, source class visibly shown; no loss of old fields.
    s=one(s,'card.addView(label(date,11f).apply{setTextColor(secondary)})',
'''card.addView(label(date,11f).apply{setTextColor(secondary)})
                val origin=record.optString("source","manual")
                card.addView(label(if(origin.contains("Gemini",true))
                    "✨ Analisada com Gemini" else "✍ Registo manual",11f,true).apply{
                    setTextColor(if(isDark)Color.rgb(138,232,213) else Color.rgb(4,116,107))
                })''','nutrition meal origin')
    s=one(s,'holder.addView(label("${row.optString("foods")}\\n\\nEnergia: " +',
'''val ingredients=row.optString("foods").lines()
            .map{it.trim()}.filter{it.isNotBlank()}
        holder.addView(label("🍽 Alimentos",17f,true))
        ingredients.forEach{item->
            val itemCard=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL
                background=GradientDrawable().apply{
                    setColor(if(isDark)Color.rgb(29,58,62) else Color.rgb(233,248,244))
                    cornerRadius=dp(14).toFloat()
                }
                setPadding(dp(12),dp(9),dp(12),dp(9))
                addView(label(item,14f,true))
            }
            holder.addView(itemCard,LinearLayout.LayoutParams(-1,-2).apply{
                bottomMargin=dp(6)
            })
        }
        holder.addView(label("Energia: " +''','nutrition food mini cards')
    return s
edit('MealAiActivity.kt',nutrition)

# Expand strings dictionary; deliberately don't machine-translate clinical user content.
def i18n(s):
    s=one(s,'Oferecer um café via PayPal (opcional)\tBuy the author a beer via PayPal (optional)\tOffrir une bière via PayPal (facultatif)\tDem Autor via PayPal ein Bier spendieren (freiwillig)\tInvitar a una cerveza por PayPal (opcional)',
'''Oferecer um café via PayPal (opcional)\tOffer a coffee via PayPal (optional)\tOffrir un café via PayPal (facultatif)\tDem Autor via PayPal einen Kaffee spendieren (freiwillig)\tInvitar a un café por PayPal (opcional)''','coffee translations')
    entries=[
("Todas","All","Toutes","Alle","Todas"),
("Pendentes","Pending","En attente","Ausstehend","Pendientes"),
("Realizadas","Completed","Terminées","Erledigt","Realizadas"),
("Canceladas","Cancelled","Annulées","Abgesagt","Canceladas"),
("Estado da marcação","Appointment status","Statut du rendez-vous","Terminstatus","Estado de la cita"),
("Pendente","Pending","En attente","Ausstehend","Pendiente"),
("Realizada","Completed","Terminée","Erledigt","Realizada"),
("Cancelada","Cancelled","Annulée","Abgesagt","Cancelada"),
("Nome (A–Z)","Name (A–Z)","Nom (A–Z)","Name (A–Z)","Nombre (A–Z)"),
("Próxima toma","Next dose","Prochaine prise","Nächste Einnahme","Próxima toma"),
("Categoria","Category","Catégorie","Kategorie","Categoría"),
("Estado","Status","Statut","Status","Estado"),
("Dados clínicos essenciais","Essential clinical details","Données cliniques essentielles","Wichtige klinische Daten","Datos clínicos esenciales"),
("Contactos e dados base","Contacts and basic data","Contacts et données de base","Kontakte und Grunddaten","Contactos y datos básicos"),
("Confirmar e guardar","Review and save","Vérifier et enregistrer","Prüfen und speichern","Revisar y guardar"),
("Hospital ou clínica (opcional)","Hospital or clinic (optional)","Hôpital ou clinique (facultatif)","Krankenhaus oder Klinik (optional)","Hospital o clínica (opcional)"),
("Número de observação ou processo","Clinical reference or case number","Numéro de dossier ou d'observation","Beobachtungs- oder Fallnummer","Número de observación o expediente"),
("Escolher unidade · Distrito → Concelho","Choose facility · District → Municipality","Choisir un établissement · District → Commune","Einrichtung wählen · Bezirk → Gemeinde","Elegir centro · Distrito → Municipio"),
("Número antigo (preservado):","Older number (preserved):","Ancien numéro (conservé) :","Alte Nummer (beibehalten):","Número antiguo (conservado):"),
("Analisada com Gemini","Analyzed with Gemini","Analysé avec Gemini","Mit Gemini analysiert","Analizada con Gemini"),
("Registo manual","Manual entry","Saisie manuelle","Manueller Eintrag","Registro manual"),
("Alimentos","Foods","Aliments","Lebensmittel","Alimentos"),
("CANCELADA","CANCELLED","ANNULÉE","ABGESAGT","CANCELADA"),
("REALIZADA","COMPLETED","TERMINÉE","ERLEDIGT","REALIZADA"),
("SUSPENSA","SUSPENDED","SUSPENDUE","AUSGESETZT","SUSPENDIDA"),
("Toma registada hoje","Dose recorded today","Prise enregistrée aujourd'hui","Einnahme heute erfasst","Toma registrada hoy"),
("Clínica","Clinic","Clinique","Klinik","Clínica"),
]
    lines='\n'.join('\t'.join(row) for row in entries)+'\n'
    return one(s,'""".trimIndent()',''+lines+'""".trimIndent()','locale catalog additions')
edit('i18n/AppLanguage.kt',i18n)

# Android release identity only; no secret keys and no automatic data migration.
p=ROOT/'build.gradle.kts';g=p.read_text(encoding='utf-8')
g=one(g,'versionCode = 115','versionCode = 116','version code 106')
g=one(g,'versionName = "1.9.105"','versionName = "1.9.106"','version name 106')
p.write_text(g,encoding='utf-8')
print('SaudePratica 1.9.106 patch applied. Original signing identity and user records retained.')