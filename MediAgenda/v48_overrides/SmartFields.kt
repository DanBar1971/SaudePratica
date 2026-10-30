package com.mediagenda.app

import android.app.DatePickerDialog
import android.app.TimePickerDialog
import android.widget.EditText
import androidx.appcompat.app.AppCompatActivity
import java.time.LocalDate
import java.time.LocalTime
import java.time.format.DateTimeFormatter

/** Shared date and time pickers; each source field preserves its saved format. */
object SmartFields {
    fun attach(activity:AppCompatActivity,edit:EditText,label:String,
        enabled:Boolean=true){
        if(!enabled)return
        val l=label.lowercase()
        val date=l.startsWith("data") || l.contains("data de ") ||
            l.contains("nascimento") || l.contains("validade") ||
            l.contains("próxima avaliação") || l.contains("repetir até") ||
            l.startsWith("início da") || l.startsWith("fim da") ||
            l.contains("dd/mm") || l.contains("yyyy-mm-dd") ||
            l.contains("aaaa-mm-dd")
        val time= l.contains("hh:mm") || l.startsWith("hora ") ||
            l.contains("primeiro aviso") || l.contains("último aviso")
        if(date){
            edit.isFocusable=false;edit.isClickable=true
            edit.setCompoundDrawablesWithIntrinsicBounds(0,0,
                android.R.drawable.ic_menu_my_calendar,0)
            edit.compoundDrawablePadding=8
            edit.setOnClickListener{
                val value=edit.text.toString().trim()
                val current=runCatching{LocalDate.parse(value)}
                    .getOrElse{
                        runCatching{LocalDate.parse(value,
                            DateTimeFormatter.ofPattern("d/M/uuuu"))}
                            .getOrDefault(LocalDate.now())
                    }
                DatePickerDialog(activity,{_,year,month,day->
                    val selected=LocalDate.of(year,month+1,day)
                    val iso=l.contains("yyyy-mm-dd") ||
                        l.contains("aaaa-mm-dd") ||
                        value.matches(Regex("""\d{4}-\d{2}-\d{2}"""))
                    edit.setText(if(iso) selected.toString()
                        else selected.format(
                            DateTimeFormatter.ofPattern("dd/MM/uuuu")))
                },current.year,current.monthValue-1,current.dayOfMonth).show()
            }
        }else if(time){
            edit.isFocusable=false;edit.isClickable=true
            edit.setCompoundDrawablesWithIntrinsicBounds(0,0,
                android.R.drawable.ic_lock_idle_alarm,0)
            edit.compoundDrawablePadding=8
            edit.setOnClickListener{
                val current=runCatching{LocalTime.parse(
                    edit.text.toString().trim())}
                    .getOrDefault(LocalTime.of(9,0))
                TimePickerDialog(activity,{_,h,m->
                    edit.setText("%02d:%02d".format(h,m))
                },current.hour,current.minute,true).show()
            }
        }
    }
}
