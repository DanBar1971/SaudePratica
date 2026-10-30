from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
main=root/"app/src/main/java/com/mediagenda/app/MainActivity.kt"
src=main.read_text(encoding="utf-8")
old='''    private fun showDashboardChecklist(){
        val hidden=dashboardPrefs().getStringSet("hidden",emptySet())
            .orEmpty().toMutableSet()
        val options=dashboardLabels.toTypedArray()
        val checked=BooleanArray(options.size){options[it] !in hidden}
        MaterialAlertDialogBuilder(this)
            .setTitle("Módulos do ecrã principal")
            .setMessage("Seleciona os módulos que queres ver no Início. "+
                "Os dados dos módulos ocultos não são apagados. "+
                "O módulo Mais fica sempre disponível.")
            .setMultiChoiceItems(options,checked){_,index,value->
                checked[index]=value
            }
            .setPositiveButton("Guardar"){_,_->
                val invisible=options.filterIndexed{index,_->!checked[index]}.toSet()
                dashboardPrefs().edit().putStringSet("hidden",invisible).apply()
                showDataTools()
            }
            .setNeutralButton("Mostrar todos"){_,_->
                dashboardPrefs().edit().remove("hidden").apply()
                showDataTools()
            }.setNegativeButton("Cancelar",null).show()
    }'''
new='''    private fun showDashboardChecklist(){
        val hidden=dashboardPrefs().getStringSet("hidden",emptySet()).orEmpty()
        val options=dashboardLabels
        val choice=BooleanArray(options.size){options[it] !in hidden}
        // The Material AlertDialog API cannot display setMessage alongside
        // setMultiChoiceItems: its message panel replaces the list panel.
        // Use a dedicated scrolling view, with real CheckBox controls.
        val column=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(8),dp(18),dp(12))
        }
        column.addView(TextView(this).apply{
            text="Marca os módulos que queres ver no Início. "+
                "Os dados dos módulos ocultos não são apagados. "+
                "O módulo Mais fica sempre disponível."
            textSize=13f
            setTextColor(mainTextColor)
            setPadding(0,0,0,dp(12))
        })
        val boxes=options.mapIndexed{index,name->
            android.widget.CheckBox(this).apply{
                text=name
                isChecked=choice[index]
                textSize=15f
                setTextColor(mainTextColor)
                buttonTintList=ColorStateList.valueOf(
                    if(darkMode)Color.rgb(96,217,201)else Color.rgb(8,139,127))
                minHeight=dp(43)
                setOnCheckedChangeListener{_,value->choice[index]=value}
                column.addView(this,LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,dp(44)))
            }
        }
        val scroll=ScrollView(this).apply{
            addView(column)
            isVerticalScrollBarEnabled=true
        }
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Módulos do ecrã principal")
            .setView(scroll)
            .setPositiveButton("Guardar"){_,_->
                val invisible=options.filterIndexed{index,_->!choice[index]}.toSet()
                dashboardPrefs().edit().putStringSet("hidden",invisible).apply()
                showHome()
            }
            .setNeutralButton("Mostrar todos"){_,_->
                dashboardPrefs().edit().remove("hidden").apply()
                showHome()
            }
            .setNegativeButton("Cancelar",null).show()
        val display=resources.displayMetrics
        val height=(display.heightPixels*0.65f).toInt().coerceAtLeast(dp(260))
        scroll.layoutParams=android.widget.FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,height)
    }'''
assert src.count(old)==1, "dashboard checklist original missing"
src=src.replace(old,new,1)
# Use UI theme logic directly from existing main rather than an undocumented darkMode field:
src=src.replace('if(darkMode)Color.rgb(96,217,201)else Color.rgb(8,139,127)',
                'if(isDarkPalette)Color.rgb(96,217,201)else Color.rgb(8,139,127)')
src=src.replace('val boxes=options.mapIndexed{index,name->',
                'options.forEachIndexed{index,name->')
# visual subtitle
old='''DashboardModule("🏥", "Saúde Ocupacional", "Medicina do Trabalho e exames")'''
new='''DashboardModule("🏥", "Saúde Ocupacional", "Medicina do Trabalho")'''
assert src.count(old)==1, "occupational subtitle original missing"
src=src.replace(old,new,1)
main.write_text(src,encoding="utf-8")

cycle=root/"app/src/main/java/com/mediagenda/app/MonthlyCalendarActivity.kt"
src=cycle.read_text(encoding="utf-8")
start=src.index("    private fun configurePill(){")
end=src.index("    private fun savePill(",start)
replacement='''    private fun configurePill(){
        val patterns=arrayOf(
            "Sem pílula / desativar",
            "Todos os dias",
            "21 dias de toma e 7 de pausa",
            "24 dias de toma e 4 de pausa ou placebo"
        )
        val selected=when(cycle.pillPattern){
            "daily"->1
            "21_7"->2
            "24_4"->3
            else->0
        }
        // A separate RadioGroup avoids setMessage + setItems hiding the list.
        val options=android.widget.RadioGroup(this).apply{
            orientation=android.widget.RadioGroup.VERTICAL
        }
        patterns.forEachIndexed{index,title->
            options.addView(android.widget.RadioButton(this).apply{
                id=View.generateViewId()
                text=title
                textSize=15f
                setTextColor(ink)
                buttonTintList=ColorStateList.valueOf(teal)
                isChecked=index==selected
                minHeight=dp(54)
                setPadding(dp(4),dp(5),0,dp(5))
                tag=index
            })
        }
        val column=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(18),dp(10),dp(18),dp(8))
            addView(label(
                "Seleciona apenas o esquema indicado pelo profissional "+
                "de saúde. Os lembretes são opcionais e começam desligados.",
                13f,c=muted).apply{
                gravity=Gravity.START
                setPadding(0,0,0,dp(10))
            })
            addView(options)
        }
        val scroll=ScrollView(this).apply{
            addView(column)
            isVerticalScrollBarEnabled=true
        }
        val dialog=MaterialAlertDialogBuilder(this)
            .setTitle("Esquema da pílula")
            .setView(scroll)
            .setPositiveButton("Continuar"){_,_->
                val option=options.findViewById<android.widget.RadioButton>(
                    options.checkedRadioButtonId)
                val which=option?.tag as? Int ?: selected
                if(which==0){
                    cycle.alerts=false
                    cycle.pillPattern="off"
                    NotificationScheduler(this).scheduleAllProfiles()
                    display()
                }else{
                    val pattern=when(which){1->"daily";2->"21_7";else->"24_4"}
                    datePicker(cycle.pillStart){start->
                        val t=cycle.pillTime
                        TimePickerDialog(this,{_,hour,minute->
                            MaterialAlertDialogBuilder(this)
                                .setTitle("Ativar lembretes?")
                                .setMessage("Queres receber um aviso à hora escolhida? "+
                                    "Os avisos devem seguir a tua receita.")
                                .setPositiveButton("Sim, ativar"){_,_->
                                    savePill(pattern,start,LocalTime.of(hour,minute),true)
                                }
                                .setNegativeButton("Sem avisos"){_,_->
                                    savePill(pattern,start,LocalTime.of(hour,minute),false)
                                }.show()
                        },t.hour,t.minute,true).show()
                    }
                }
            }.setNegativeButton("Cancelar",null).show()
        val height=(resources.displayMetrics.heightPixels*0.56f).toInt()
            .coerceAtLeast(dp(270))
        scroll.layoutParams=android.widget.FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,height)
    }
'''
src=src[:start]+replacement+src[end:]
cycle.write_text(src,encoding="utf-8")

gradle=root/"app/build.gradle.kts"
src=gradle.read_text(encoding="utf-8")
assert 'versionCode = 31' in src and 'versionName = "1.9.21"' in src
src=src.replace('versionCode = 31','versionCode = 32',1).replace('versionName = "1.9.21"','versionName = "1.9.22"',1)
gradle.write_text(src,encoding="utf-8")
print("v1.9.22: real module checkboxes, real pill regimen radios, and compact Saúde Ocupacional subtitle")
