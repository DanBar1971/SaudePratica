from pathlib import Path
file=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app/MainActivity.kt")
s=file.read_text(encoding="utf-8")
def sub(old,new,label):
 global s
 if old not in s:raise RuntimeError("v1.9.3 card anchor missing: "+label)
 s=s.replace(old,new,1)

sub('''class H(val card:MaterialCardView,val title:TextView,val detail:TextView,val code:TextView,val delete:TextView):RecyclerView.ViewHolder(card)''',
'''class H(val card:MaterialCardView,val title:TextView,val detail:TextView,val code:TextView,val delete:TextView,
        val timeBadge:TextView,val pill:TextView,val thumbnail:android.widget.ImageView):RecyclerView.ViewHolder(card)''',
'Medication holder')

sub('''        val icon=TextView(c).apply{text="💊";textSize=23f;gravity=Gravity.CENTER;background=GradientDrawable().apply{setColor(Color.parseColor("#E6F4F1"));shape=GradientDrawable.OVAL};layoutParams=LinearLayout.LayoutParams(dp(44),dp(44))}
        val texts=LinearLayout(c).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(12),0,dp(6),0)}''',
'''        val icon=TextView(c).apply{text="💊";textSize=23f;gravity=Gravity.CENTER;background=GradientDrawable().apply{setColor(Color.parseColor("#E6F4F1"));shape=GradientDrawable.OVAL};layoutParams=LinearLayout.LayoutParams(dp(44),dp(44))}
        val image=android.widget.ImageView(c).apply {
            scaleType=android.widget.ImageView.ScaleType.CENTER_CROP
            layoutParams=LinearLayout.LayoutParams(dp(44),dp(44))
            visibility=View.GONE
        }
        val clock=TextView(c).apply {
            textSize=11.5f;gravity=Gravity.CENTER;setTextColor(Color.parseColor("#0A5C56"))
            setTypeface(typeface,Typeface.BOLD);setPadding(0,dp(4),0,0)
        }
        val left=LinearLayout(c).apply{orientation=LinearLayout.VERTICAL;gravity=Gravity.CENTER_HORIZONTAL}
        left.addView(icon);left.addView(image);left.addView(clock)
        val texts=LinearLayout(c).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(12),0,dp(6),0)}''',
'Medication icon and clock')

sub('''        row.addView(icon);row.addView(texts,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));row.addView(del)
        card.addView(row);return H(card,title,detail,code,del)''',
'''        row.addView(left);row.addView(texts,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));row.addView(del)
        card.addView(row);return H(card,title,detail,code,del,clock,icon,image)''',
'Medication row')

sub('''        val alert=if(m.reminderTime.isBlank())"" else "  •  aviso ${m.reminderTime}"
        h.detail.text="$dose  •  $ind$alert"''',
'''        val alarm = m.reminderTime.ifBlank{m.time}
        h.timeBadge.text = if(Regex("""^\\d{1,2}:\\d{2}$""").matches(alarm)) alarm else "--:--"
        h.detail.text="$dose  •  $ind"
        h.pill.visibility=View.VISIBLE
        h.thumbnail.visibility=View.GONE
        h.thumbnail.setImageDrawable(null)
        m.images.firstOrNull()?.let { source ->
            try {
                val uri=Uri.parse(source)
                val options=android.graphics.BitmapFactory.Options().apply { inSampleSize=8 }
                val bmp=h.card.context.contentResolver.openInputStream(uri)?.use {
                    android.graphics.BitmapFactory.decodeStream(it,null,options)
                }
                if(bmp != null) {
                    h.thumbnail.setImageBitmap(bmp)
                    h.thumbnail.visibility=View.VISIBLE
                    h.pill.visibility=View.GONE
                }
            } catch (_:Exception) {}
        }''',
'Medication item bind')

sub('''class H(val card:MaterialCardView,val dateBox:TextView,val title:TextView,val detail:TextView,val delete:TextView):RecyclerView.ViewHolder(card)''',
'''class H(val card:MaterialCardView,val dateBox:TextView,val timeBadge:TextView,val title:TextView,val detail:TextView,val delete:TextView):RecyclerView.ViewHolder(card)''',
'Appointment holder')

sub('''        val date=TextView(c).apply{textSize=12f;gravity=Gravity.CENTER;setTypeface(typeface,Typeface.BOLD);setTextColor(Color.parseColor("#0A5C56"));background=GradientDrawable().apply{setColor(Color.parseColor("#E6F4F1"));cornerRadius=dp(14).toFloat()};layoutParams=LinearLayout.LayoutParams(dp(58),dp(58))}
        val texts=LinearLayout(c).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(12),0,dp(6),0)}''',
'''        val date=TextView(c).apply{textSize=12f;gravity=Gravity.CENTER;setTypeface(typeface,Typeface.BOLD);setTextColor(Color.parseColor("#0A5C56"));background=GradientDrawable().apply{setColor(Color.parseColor("#E6F4F1"));cornerRadius=dp(14).toFloat()};layoutParams=LinearLayout.LayoutParams(dp(58),dp(58))}
        val clock=TextView(c).apply{
            textSize=11.5f;gravity=Gravity.CENTER;setTextColor(Color.parseColor("#0A5C56"))
            setTypeface(typeface,Typeface.BOLD);setPadding(0,dp(4),0,0)
        }
        val left=LinearLayout(c).apply { orientation=LinearLayout.VERTICAL;gravity=Gravity.CENTER_HORIZONTAL }
        left.addView(date);left.addView(clock)
        val texts=LinearLayout(c).apply{orientation=LinearLayout.VERTICAL;setPadding(dp(12),0,dp(6),0)}''',
'Appointment date icon and clock')

sub('''        row.addView(date);row.addView(texts,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));row.addView(del);card.addView(row)
        return H(card,date,title,detail,del)''',
'''        row.addView(left);row.addView(texts,LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1f));row.addView(del);card.addView(row)
        return H(card,date,clock,title,detail,del)''',
'Appointment row')

sub('''        h.dateBox.text=formatDate(a.date)
        h.title.text="${a.time.ifBlank{"--:--"}}  ${a.activity.ifBlank{a.department.ifBlank{"Marcação"}}}"''',
'''        h.dateBox.text=formatDate(a.date)
        h.timeBadge.text=a.time.ifBlank{"--:--"}
        h.title.text=a.activity.ifBlank{a.department.ifBlank{"Marcação"}}''',
'Appointment bind')
file.write_text(s,encoding="utf-8")
print("v1.9.3 list cards: time under each date/medication graphic.")
