from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"

def change(path,old,new,label):
    source=path.read_text(encoding="utf-8")
    n=source.count(old)
    if n!=1: raise RuntimeError("v1.9.30 "+label+": expected 1 match, found "+str(n))
    path.write_text(source.replace(old,new,1),encoding="utf-8")

receiver=base/"notifications/NotificationReceiver.kt"
change(receiver,
    '            val body = intent.getStringExtra("body") ?: "Aviso de medicação"',
    '''            val rawBody = intent.getStringExtra("body") ?: "Aviso de medicação"
            val body = if(!medicationId.isNullOrBlank())
                rawBody + "\\nApós tomares, expande este aviso e toca em ✓ TOMEI."
                else rawBody''',
    "reminder action guidance")
change(receiver,
    '''                builder.addAction(android.R.drawable.ic_input_add,"✓ Tomei",pending)
            }

            // Box photos are optional.''',
    '''                builder.addAction(android.R.drawable.ic_input_add,"✓ TOMEI",pending)
            }else if(isMedication && intent.getBooleanExtra("demo_tomei",false)){
                // Safe demo: visually test the same notification action while
                // NEVER writing a medication intake to the health journal.
                val demo=Intent(context,IntakeActionReceiver::class.java).apply{
                    action=IntakeActionReceiver.ACTION
                    putExtra("demo_tomei",true)
                    putExtra("notification_id",id)
                }
                val pending=PendingIntent.getBroadcast(context,991503,demo,
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                builder.addAction(android.R.drawable.ic_input_add,
                    "✓ TOMEI (TESTE)",pending)
            }

            // Box photos are optional.''',
    "prominent TOMEI and safe demo")

intake=base/"notifications/IntakeActionReceiver.kt"
change(intake,
    '''        if(intent.action!=ACTION)return
        val profileId=''',
    '''        if(intent.action!=ACTION)return
        if(intent.getBooleanExtra("demo_tomei",false)){
            // The test confirms that the button works, but never logs a dose.
            val id=intent.getIntExtra("notification_id",991501)
            val manager=context.getSystemService(NotificationManager::class.java)
            val channelId="saudepratica_intake_demo_v1"
            if(Build.VERSION.SDK_INT>=Build.VERSION_CODES.O){
                manager.createNotificationChannel(NotificationChannel(channelId,
                    "Testes do botão TOMEI",NotificationManager.IMPORTANCE_LOW).apply{
                    enableVibration(false)
                    setSound(null,null)
                })
            }
            manager.cancel(id)
            if(Build.VERSION.SDK_INT>=33 && ContextCompat.checkSelfPermission(
                context,Manifest.permission.POST_NOTIFICATIONS)
                !=PackageManager.PERMISSION_GRANTED)return
            manager.notify(id,NotificationCompat.Builder(context,channelId)
                .setSmallIcon(android.R.drawable.ic_lock_idle_alarm)
                .setContentTitle("✓ Botão TOMEI testado")
                .setContentText("Teste concluído: nenhuma toma foi registada.")
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .setAutoCancel(true)
                .build())
            return
        }
        val profileId=''', "safe TOMEI demo")

main=base/"MainActivity.kt"
change(main,
    '''            "Estes dois testes enviam apenas um aviso e não registam tomas."))''',
    '''            "Estes dois testes enviam avisos. O teste de medicação também "+
            "mostra ✓ TOMEI (TESTE), mas não grava qualquer toma."))''',
    "menu safe test message")
change(main,
    '''            "O botão «Tomei» aparece apenas nos avisos reais de um medicamento."))''',
    '''            "Nos avisos reais, expande a notificação e toca em ✓ TOMEI "+
            "depois de tomares. O teste usa ✓ TOMEI (TESTE) sem registar medicação."))''',
    "menu action help")
change(main,
    '''                putExtra("notification_id",if(med)991501 else 991502)
            })''',
    '''                putExtra("notification_id",if(med)991501 else 991502)
                putExtra("demo_tomei",med)
            })''',
    "enable demo action for test alert")

gradle=root/"app/build.gradle.kts"
change(gradle,"versionCode = 39","versionCode = 40","versionCode")
change(gradle,'versionName = "1.9.29"','versionName = "1.9.30"',"versionName")
print("v1.9.30: clearer real medication TOMEI action, safe interactive demo and documented confirmation behavior.")
