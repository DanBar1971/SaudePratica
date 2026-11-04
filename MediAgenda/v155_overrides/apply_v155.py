#!/usr/bin/env python3
"""Android 1.9.135: numeric PIN for portable backups, retaining v147 profiles/clinical restore.

Run after v154. Patch the CURRENT generated Kotlin, never overwrite the
v147+ PortableWindowsBackup implementation with its obsolete v143 version.
"""
from pathlib import Path

app=Path("build-src/MediAgenda_Android_v1/app")
src=app/"src/main/java/com/mediagenda/app"
main=src/"MainActivity.kt"
portable=src/"data/PortableWindowsBackup.kt"

def patch(text,old,new,label):
    number=text.count(old)
    if number!=1:
        raise AssertionError(f"1.9.135 {label}: expected 1 anchor, got {number}")
    return text.replace(old,new,1)

p=portable.read_text(encoding="utf-8")
p=patch(p,
    """private fun secret(password:CharArray,salt:ByteArray):SecretKeySpec{
        require(password.size>=10){"A palavra-passe precisa de 10 caracteres ou mais."}
        val spec=PBEKeySpec(password,salt,600_000,256)""",
    """private fun secret(password:CharArray,salt:ByteArray,
                       rounds:Int,pinMode:Boolean):SecretKeySpec{
        if(pinMode)require(password.size==4 && password.all{it in '0'..'9'}){
            "O PIN precisa de 4 dígitos."}
        else require(password.size>=10){
            "Para abrir backups antigos, usa a palavra-passe original."}
        val spec=PBEKeySpec(password,salt,rounds,256)""",
    "numeric and legacy KDF validation")
p=patch(p,
    'val header=JSONObject().put("kind","saudepratica-encrypted-v1")\n                .put("kdf","PBKDF2-HMAC-SHA256").put("iterations",600000)',
    'val header=JSONObject().put("kind","saudepratica-encrypted-pin-v2")\n                .put("kdf","PBKDF2-HMAC-SHA256").put("iterations",1200000)',
    "PIN-v2 export header")
p=patch(p,
    'cipher.init(Cipher.ENCRYPT_MODE,secret(password,salt),GCMParameterSpec(128,nonce))',
    'cipher.init(Cipher.ENCRYPT_MODE,secret(password,salt,1200000,true),GCMParameterSpec(128,nonce))',
    "PIN-v2 encryption")
p=patch(p,
    '''require(header.optString("kind")=="saudepratica-encrypted-v1" &&
                    header.optString("kdf")=="PBKDF2-HMAC-SHA256" &&
                    header.optInt("iterations")==600000 &&
                    header.optString("cipher")=="AES-256-GCM"){
                    "Versão de backup Windows não suportada."
                }''',
    '''val kind=header.optString("kind")
                val legacy=kind=="saudepratica-encrypted-v1"
                val numeric=kind=="saudepratica-encrypted-pin-v2"
                val expectedRounds=if(numeric)1200000 else 600000
                require((legacy||numeric) &&
                    header.optString("kdf")=="PBKDF2-HMAC-SHA256" &&
                    header.optInt("iterations")==expectedRounds &&
                    header.optString("cipher")=="AES-256-GCM"){
                    "Versão de backup Windows não suportada."
                }''',
    "PIN-v2 and password-v1 decryption")
p=patch(p,
    'cipher.init(Cipher.DECRYPT_MODE,secret(password,salt),GCMParameterSpec(128,nonce))',
    'cipher.init(Cipher.DECRYPT_MODE,secret(password,salt,expectedRounds,numeric),GCMParameterSpec(128,nonce))',
    "backwards compatible KDF")
p=patch(p,'    data class Original(val sha256:String,val name:String,val size:Long)',
    '''    fun usesLegacyPassword(source:Uri):Boolean{
        (context.contentResolver.openInputStream(source)
            ?:error("Ficheiro de backup inacessível.")).use{input->
            val reader=DataInputStream(input)
            val prefix=ByteArray(magic.size)
            reader.readFully(prefix)
            require(prefix.contentEquals(magic)){"Não é um backup SaúdePrática."}
            val size=reader.readInt()
            require(size in 30..4096){"Cabeçalho inválido."}
            val head=ByteArray(size)
            reader.readFully(head)
            val kind=JSONObject(String(head,Charsets.UTF_8)).optString("kind")
            require(kind=="saudepratica-encrypted-v1" ||
                kind=="saudepratica-encrypted-pin-v2"){
                "Formato de backup desconhecido."
            }
            return kind=="saudepratica-encrypted-v1"
        }
    }
    data class Original(val sha256:String,val name:String,val size:Long)''',
    "read backup format without decrypting")
portable.write_text(p,encoding="utf-8")

s=main.read_text(encoding="utf-8")
s=patch(s,
    "    private fun chooseWindowsExport(onlyProfile:String?=null){",
    '''    private fun backupPinInput(hint:String)=android.widget.EditText(this).apply{
        this.hint=hint
        inputType=android.text.InputType.TYPE_CLASS_NUMBER or
            android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD
        filters=arrayOf(android.text.InputFilter.LengthFilter(4))
    }
    private fun chooseWindowsExport(onlyProfile:String?=null){''',
    "numeric keypad")
s=patch(s,
    'val pass=passwordInput("Palavra-passe (mínimo 10 caracteres)")',
    'val pass=backupPinInput("PIN do backup · 4 números")',"export pin field")
s=patch(s,
    'val confirm=passwordInput("Repetir palavra-passe")',
    'val confirm=backupPinInput("Confirmar PIN")',"export confirm field")
s=patch(s,
    'if(pwd.size<10||!pwd.contentEquals(check)){',
    "if(pwd.size!=4 || !pwd.all{it in '0'..'9'} || !pwd.contentEquals(check)){",
    "numeric PIN validation")
s=patch(s,
    'confirm.error="Usa duas palavras-passe iguais com 10 ou mais caracteres."',
    'confirm.error="Usa dois PINs iguais com 4 números."',"export validation feedback")
s=patch(s,
    'val pass=passwordInput("Palavra-passe do .spbackup")',
    '''val legacy=runCatching{PortableWindowsBackup(this).usesLegacyPassword(uri)}
            .getOrElse{showError("Backup inválido: "+it.message);return}
        val pass=if(legacy)passwordInput("Palavra-passe antiga")
                 else backupPinInput("PIN do backup (4 números)")''',
    "legacy file-aware restore input")
s=patch(s,
    '''if(pwd.size<10){
                        pwd.fill(0.toChar());pass.error="Mínimo 10 caracteres"''',
    '''if(if(legacy)pwd.size<10 else pwd.size!=4 || !pwd.all{it in '0'..'9'}){
                        pwd.fill(0.toChar())
                        pass.error=if(legacy)"Palavra-passe antiga obrigatória"
                                   else "PIN de 4 números"''',
    "restore validation")
# v147 replaces the menu: preserve distinct Family and Profile exports.
s=patch(s,'"Backup .spbackup · Família"', '"Backup Família · PIN de 4 números"',
        "family backup label")
s=patch(s,'"Backup .spbackup · Perfil"', '"Backup Perfil · PIN de 4 números"',
        "profile backup label")
s=patch(s,'infoCard("📥", "Restaurar .spbackup · Família ou Perfil"',
        'infoCard("📥", "Restaurar backup com PIN · Família ou Perfil"',
        "restore menu label")
s=patch(s,'val pass=backupPinInput("PIN do backup · 4 números")',
    'val pass=backupPinInput("PIN do backup · 4 números")',
    "no-op marker") if False else s
main.write_text(s,encoding="utf-8")

gradle=app/"build.gradle.kts"
version=gradle.read_text(encoding="utf-8")
assert version.count("versionCode = 144")==1
assert version.count('versionName = "1.9.134"')==1
version=version.replace("versionCode = 144","versionCode = 145",1)
version=version.replace('versionName = "1.9.134"','versionName = "1.9.135"',1)
gradle.write_text(version,encoding="utf-8")
print("1.9.135 numeric PIN backup and legacy original-password restore; scope retained.")
