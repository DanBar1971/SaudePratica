#!/usr/bin/env python3
from pathlib import Path
from shutil import copyfile
app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
copyfile(Path("MediAgenda/v155_overrides/PortableWindowsBackup.kt"),
         src/"data/PortableWindowsBackup.kt")
main=src/"MainActivity.kt"
body=main.read_text(encoding="utf-8")
def change(old,new,label):
    global body
    n=body.count(old)
    if n!=1:raise AssertionError(f"1.9.135 {label}: esperado 1, obtido {n}")
    body=body.replace(old,new,1)

change('    private fun chooseWindowsExport(){',
'''    private fun backupPinInput(hint:String)=android.widget.EditText(this).apply{
        this.hint=hint
        inputType=android.text.InputType.TYPE_CLASS_NUMBER or
            android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD
        filters=arrayOf(android.text.InputFilter.LengthFilter(4))
    }
    private fun chooseWindowsExport(){''',"numeric keypad")
change('val pass=passwordInput("Palavra-passe (mínimo 10 caracteres)")',
       'val pass=backupPinInput("PIN do backup · 4 números")',"export field")
change('val confirm=passwordInput("Repetir palavra-passe")',
       'val confirm=backupPinInput("Confirmar PIN")',"repeat field")
change('if(pwd.size<10||!pwd.contentEquals(check)){',
       "if(pwd.size!=4 || !pwd.all{it in '0'..'9'} || !pwd.contentEquals(check)){",
       "PIN validation")
change('confirm.error="Usa duas palavras-passe iguais com 10 ou mais caracteres."',
       'confirm.error="Usa dois PINs iguais com 4 números."',"PIN error")
change('val pass=passwordInput("Palavra-passe do .spbackup")',
'''val legacy=runCatching{PortableWindowsBackup(this).usesLegacyPassword(uri)}
            .getOrElse{showError("Backup inválido: "+it.message);return}
        val pass=if(legacy)passwordInput("Palavra-passe antiga")
                 else backupPinInput("PIN do backup (4 números)")''',"legacy restore")
change('''if(pwd.size<10){
                        pwd.fill(0.toChar());pass.error="Mínimo 10 caracteres"''',
'''if(if(legacy)pwd.size<10 else pwd.size!=4 || !pwd.all{it in '0'..'9'}){
                        pwd.fill(0.toChar())
                        pass.error=if(legacy)"Palavra-passe antiga obrigatória"
                                   else "PIN de 4 números"''',"restore input")
