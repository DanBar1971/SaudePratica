package com.mediagenda.app

import android.content.res.Configuration
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.ColorDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.data.ProfileStore
import com.mediagenda.app.model.Appointment
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.util.Locale

/** A month-at-a-glance calendar using the user's existing appointment records. */
class MonthlyCalendarActivity:AppCompatActivity(){
    companion object{const val PROFILE="profile_id"}
    private var month=YearMonth.now()
    private var selected=LocalDate.now()
    private lateinit var profileId:String
    private lateinit var body:LinearLayout
    private val pt=Locale("pt","PT")
    private val teal=Color.rgb(5,163,153)
    private val dark get()=(resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES
    private val ink get()=if(dark)Color.WHITE else Color.rgb(16,31,49)
    private val muted get()=if(dark)Color.rgb(201,215,225)else Color.rgb(90,105,118)
    private fun dp(n:Int)=(n*resources.displayMetrics.density+.5f).toInt()
    private fun label(v:String,size:Float=14f,bold:Boolean=false,c:Int=ink)=TextView(this).apply{
        text=v;textSize=size;setTextColor(c);gravity=Gravity.CENTER
        if(bold)setTypeface(null,Typeface.BOLD)
    }
    private fun outlined(v:String,click:()->Unit)=MaterialButton(this).apply{
        text=v;isAllCaps=false;textSize=13f
        setTextColor(teal);backgroundTintList=ColorStateList.valueOf(Color.TRANSPARENT)
        strokeColor=ColorStateList.valueOf(teal);strokeWidth=dp(1)
        cornerRadius=dp(15);setOnClickListener{click()}
    }
    private fun box():MaterialCardView=MaterialCardView(this).apply{
        radius=dp(18).toFloat();strokeWidth=dp(1)
        strokeColor=if(dark)Color.rgb(79,103,116)else Color.rgb(214,226,234)
        setCardBackgroundColor(if(dark)Color.rgb(29,44,56)else Color.WHITE)
    }
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        val people=ProfileStore(this).all()
        profileId=people.firstOrNull{it.id==intent.getStringExtra(PROFILE)}?.id
            ?:people.singleOrNull()?.id?:run{finish();return}
        val root=LinearLayout(this).apply{
            orientation=LinearLayout.VERTICAL
            setPadding(dp(16),dp(10),dp(16),dp(10))
            setBackgroundColor(if(dark)Color.rgb(5,22,32)else Color.rgb(246,249,251))
        }
        val head=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER_VERTICAL}
        head.addView(label("‹",34f,c=teal).apply{
            contentDescription="Voltar ao Início"
            setOnClickListener{finish()}
        },LinearLayout.LayoutParams(dp(38),dp(64)))
        val textHead=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        textHead.addView(label("SaúdePrática",13f,true,teal))
        textHead.addView(label("📅 Calendário Mensal",23f,true))
        textHead.addView(label("Consultas e exames deste utilizador",12f,c=muted))
        head.addView(textHead,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f))
        root.addView(head)
        val scroller=ScrollView(this)
        body=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL}
        scroller.addView(body)
        root.addView(scroller,LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,0,1f))
        WindowCompat.setDecorFitsSystemWindows(window,false)
        window.statusBarColor=Color.TRANSPARENT
        window.navigationBarColor=Color.TRANSPARENT
        WindowInsetsControllerCompat(window,window.decorView).apply{
            isAppearanceLightStatusBars=!dark
            hide(WindowInsetsCompat.Type.navigationBars())
        }
        ViewCompat.setOnApplyWindowInsetsListener(root){v,insets->
            val insetsSafe=insets.getInsets(WindowInsetsCompat.Type.statusBars() or
                WindowInsetsCompat.Type.displayCutout() or WindowInsetsCompat.Type.navigationBars())
            v.setPadding(dp(16)+insetsSafe.left,dp(10)+insetsSafe.top,dp(16)+insetsSafe.right,dp(10)+insetsSafe.bottom)
            insets
        }
        setContentView(root);ViewCompat.requestApplyInsets(root)
        display()
    }
    private fun onDate(date:LocalDate):List<Appointment> =
        DataRepository(this,profileId).loadAppointments().filter{a->
            val beginning=runCatching{LocalDate.parse(a.date)}.getOrNull()?:return@filter false
            if(date.isBefore(beginning))return@filter false
            val recurrence=a.recurrence
            if(recurrence.mode=="none"||recurrence.mode.isBlank())return@filter date==beginning
            val until=runCatching{LocalDate.parse(recurrence.until)}.getOrNull()?:beginning
            if(date.isAfter(until))return@filter false
            when(recurrence.mode){
                "weekdays"->date.dayOfWeek.value<=5
                "weekly"->if(recurrence.weekdays.isEmpty())date.dayOfWeek==beginning.dayOfWeek
                    else (date.dayOfWeek.value-1) in recurrence.weekdays
                else->date==beginning
            }
        }.sortedBy{it.time}
    private fun display(){
        body.removeAllViews()
        val header=LinearLayout(this).apply{orientation=LinearLayout.HORIZONTAL;gravity=Gravity.CENTER}
        header.addView(outlined("‹"){month=month.minusMonths(1);selected=month.atDay(1);display()})
        val title=month.format(DateTimeFormatter.ofPattern("MMMM yyyy",pt))
        header.addView(label(title.replaceFirstChar{it.uppercase(pt)},19f,true),
            LinearLayout.LayoutParams(0,dp(60),1f))
        header.addView(outlined("›"){month=month.plusMonths(1);selected=month.atDay(1);display()})
        body.addView(header)
        val container=box()
        val grid=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(4),dp(9),dp(4),dp(9))}
        val weekday=LinearLayout(this)
        listOf("Seg","Ter","Qua","Qui","Sex","Sáb","Dom").forEach{weekday.addView(
            label(it,12f,true,muted),LinearLayout.LayoutParams(0,dp(33),1f))}
        grid.addView(weekday)
        val offset=month.atDay(1).dayOfWeek.value-1
        val weeks=(offset+month.lengthOfMonth()+6)/7
        for(w in 0 until weeks){
            val row=LinearLayout(this)
            for(d in 0..6){
                val num=w*7+d-offset+1
                if(num<1||num>month.lengthOfMonth()){
                    row.addView(TextView(this),LinearLayout.LayoutParams(0,dp(53),1f))
                    continue
                }
                val date=month.atDay(num)
                val count=onDate(date).size
                val cell=LinearLayout(this).apply{
                    orientation=LinearLayout.VERTICAL;gravity=Gravity.CENTER
                    setBackgroundColor(if(selected==date)
                        if(dark)Color.rgb(11,87,85)else Color.rgb(220,248,243)
                        else Color.TRANSPARENT)
                    setOnClickListener{selected=date;display()}
                }
                cell.addView(label(num.toString(),14f,date==LocalDate.now()))
                cell.addView(label(if(count>0)"●" else " ",13f,c=teal))
                row.addView(cell,LinearLayout.LayoutParams(0,dp(53),1f))
            }
            grid.addView(row)
        }
        container.addView(grid);body.addView(container)
        body.addView(label("● Dias com agendamentos",12f,c=muted).apply{
            setPadding(dp(4),dp(9),0,dp(11))
        })
        val titleDay=selected.format(DateTimeFormatter.ofPattern("EEEE, dd 'de' MMMM",pt))
        body.addView(label(titleDay.replaceFirstChar{it.uppercase(pt)},17f,true).apply{
            setPadding(0,dp(12),0,dp(10))
        })
        val appointments=onDate(selected)
        if(appointments.isEmpty())body.addView(label("Sem consultas neste dia.",14f,c=muted))
        appointments.forEach{a->
            val v=box()
            val content=LinearLayout(this).apply{
                orientation=LinearLayout.VERTICAL;setPadding(dp(16),dp(12),dp(16),dp(13))
            }
            content.addView(label(a.time+"  "+a.activity.ifBlank{a.department},16f,true))
            val location=listOf(a.department,a.location).filter{it.isNotBlank()}.distinct().joinToString(" · ")
            if(location.isNotBlank())content.addView(label(location,13f,c=muted))
            if(a.done)content.addView(label("Concluído",12f,c=teal))
            v.addView(content)
            body.addView(v,LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT).apply{bottomMargin=dp(10)})
        }
    }
}
