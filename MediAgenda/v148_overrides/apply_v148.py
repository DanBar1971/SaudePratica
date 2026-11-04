#!/usr/bin/env python3
"""Android 1.9.128: measured backup progress and readable confirmation button.

Add progress reporting ONLY to manual .spbackup export. Do not touch alarm
classes, data records, backup format, passwords, restore logic or scheduling.
Run after all v147 patches. All stages are driven by actual completed work.
"""
from pathlib import Path

app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"

def edit(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    if s.count(old)!=1:
        raise AssertionError(f"{label} expected once in {path.name}, got {s.count(old)}")
    path.write_text(s.replace(old,new,1),encoding="utf-8")

family=src/"data/FamilyBackupStore.kt"
edit(family,
    "fun export(destination:Uri,onlyProfile:String?=null):FamilyBackupSummary {",
    "fun export(destination:Uri,onlyProfile:String?=null,onProgress:((Int)->Unit)?=null):FamilyBackupSummary {",
    "optional family progress callback")
edit(family,
    '''        var count=0L
        stream.use{output->''',
    '''        val totalBytes=files.sumOf{it.second.length()}.coerceAtLeast(1L)
        var lastPercentage=-1
        onProgress?.invoke(0)
        var count=0L
        stream.use{output->''',
    "actual source byte size")
edit(family,
    '''                            bytes+=n;count+=n
                            require(bytes<=maxEntry && count<=maxTotal){''',
    '''                            bytes+=n;count+=n
                            val percentage=(count*100L/totalBytes).toInt().coerceIn(0,100)
                            if(percentage>lastPercentage){
                                lastPercentage=percentage
                                onProgress?.invoke(percentage)
                            }
                            require(bytes<=maxEntry && count<=maxTotal){''',
    "measured family ZIP copy progress")
# Do not claim 100 before final ZIP is closed.
edit(family,
    '''        return FamilyBackupSummary(manifest.getInt("profiles"),files.size,count)''',
    '''        onProgress?.invoke(100)
        return FamilyBackupSummary(manifest.getInt("profiles"),files.size,count)''',
    "closed Android original ZIP")

portable=src/"data/PortableWindowsBackup.kt"
edit(portable,
    "fun export(destination:Uri,password:CharArray,onlyProfile:String?=null):Int{",
    "fun export(destination:Uri,password:CharArray,onlyProfile:String?=null,onProgress:((Int,String)->Unit)?=null):Int{",
    "optional portable progress callback")
edit(portable,
    '''            FamilyBackupStore(context).export(Uri.fromFile(source),onlyProfile)''',
    '''            onProgress?.invoke(0,"A recolher os registos de saúde")
            FamilyBackupStore(context).export(Uri.fromFile(source),onlyProfile){pct->
                onProgress?.invoke(pct*45/100,"A copiar documentos, fotografias e perfis")
            }
            onProgress?.invoke(45,"ZIP Android original fechado")''',
    "chain actual file byte progress")
edit(portable,
    '''            val rows=JSONArray()
            for(part in parts.sortedBy{it.path}){''',
    '''            onProgress?.invoke(46,"A calcular as verificações de integridade")
            val rows=JSONArray()
            for(part in parts.sortedBy{it.path}){''',
    "digest stage")
edit(portable,
    '''            val output=context.contentResolver.openOutputStream(destination,"w")
                ?:error("Não foi possível criar o backup no destino.")''',
    '''            onProgress?.invoke(55,"A encriptar os ficheiros do backup")
            val totalExport=parts.sumOf{it.size}.coerceAtLeast(1L)
            var exported=0L
            var lastExportPercent=55
            val output=context.contentResolver.openOutputStream(destination,"w")
                ?:error("Não foi possível criar o backup no destino.")''',
    "encrypted stream progress total")
edit(portable,
    '''                        part.open().use{copy(it,zip,240L*1024*1024)}''',
    '''                        part.open().use{input->
                            val buffer=ByteArray(32768)
                            var partBytes=0L
                            while(true){
                                val n=input.read(buffer)
                                if(n<0)break
                                partBytes+=n
                                require(partBytes<=240L*1024*1024){
                                    "Ficheiro excede o limite de segurança."
                                }
                                zip.write(buffer,0,n)
                                exported+=n
                                val percent=55+(exported*40L/totalExport).toInt()
                                if(percent>lastExportPercent){
                                    lastExportPercent=percent
                                    onProgress?.invoke(percent.coerceAtMost(95),
                                        "A encriptar o backup portátil")
                                }
                            }
                        }''',
    "measured encrypted bytes streamed")
edit(portable,
    r'''            return profiles.size
        }finally{source.delete();password.fill('\u0000')}''',
    r'''            onProgress?.invoke(95,"Ficheiro encriptado fechado")
            return profiles.size
        }finally{source.delete();password.fill('\u0000')}''',
    "portable export closure")

main=src/"MainActivity.kt"
edit(main,
    '''        val busy=MaterialAlertDialogBuilder(this)
            .setTitle("A preparar backup encriptado")
            .setMessage("A copiar documentos, perfis e registos…")
            .setCancelable(false).show()''',
    '''        val progressLabel=android.widget.TextView(this).apply{
            text="0% · A iniciar o backup"
            textSize=17f
        }
        val progressBar=android.widget.ProgressBar(this,null,
            android.R.attr.progressBarStyleHorizontal).apply{
            max=100
            progress=0
            minimumHeight=dp(18)
        }
        val progressBox=android.widget.LinearLayout(this).apply{
            orientation=android.widget.LinearLayout.VERTICAL
            setPadding(dp(25),dp(24),dp(25),dp(24))
            addView(progressLabel)
            addView(progressBar,android.widget.LinearLayout.LayoutParams(
                android.widget.LinearLayout.LayoutParams.MATCH_PARENT,dp(24)).apply{
                    topMargin=dp(16)
                })
        }
        val busy=MaterialAlertDialogBuilder(this)
            .setTitle("A preparar backup encriptado")
            .setView(progressBox)
            .setCancelable(false).show()''',
    "backup percentage dialog")
edit(main,
    '''                    .export(uri,pwd,onlyProfile)''',
    '''                    .export(uri,pwd,onlyProfile){percent,phase->
                        runOnUiThread{
                            if(!isFinishing){
                                progressBar.progress=percent
                                progressLabel.text=percent.toString()+"% · "+phase
                            }
                        }
                    }''',
    "forward measured progress on main thread")
edit(main,
    '''                    require(plan.people.size==exported){''',
    '''                    runOnUiThread{
                        if(!isFinishing){
                            progressBar.progress=97
                            progressLabel.text="97% · A verificar o backup criado"
                        }
                    }
                    require(plan.people.size==exported){''',
    "authenticating encrypted output")
edit(main,
    '''                        .setPositiveButton("OK",null).show()
                }.onFailure{showError("Falha ao exportar: "+it.message)}''',
    '''                        .setPositiveButton("OK",null).show().also{done->
                            done.getButton(androidx.appcompat.app.AlertDialog.BUTTON_POSITIVE)
                                .apply{
                                    minimumWidth=dp(112)
                                    minimumHeight=dp(54)
                                    textSize=17f
                                }
                        }
                }.onFailure{showError("Falha ao exportar: "+it.message)}''',
    "larger backup success button")
gradle=app/"build.gradle.kts"
edit(gradle, 'versionName = "1.9.127"', 'versionName = "1.9.128"', "version name")
edit(gradle, 'versionCode = 137', 'versionCode = 138', "version code")
print("Android 1.9.128: real backup byte progress, large OK, app identity preserved.")
