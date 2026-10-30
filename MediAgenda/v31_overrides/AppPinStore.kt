package com.mediagenda.app.data

import android.content.Context
import android.os.SystemClock
import android.util.Base64
import java.security.MessageDigest
import java.security.SecureRandom
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.PBEKeySpec

/**
 * Optional app-entry PIN shared by all users of this installation.
 * The PIN is not saved in plaintext. This is a UI access control, not file
 * encryption: Android screen lock is still essential for private CC photos.
 */
class AppPinStore(context:Context) {
    private val preferences=context.getSharedPreferences("saudepratica_app_pin_v1",Context.MODE_PRIVATE)
    private val iterations=150000
    fun enabled():Boolean=preferences.getString("digest",null)!=null &&
        preferences.getString("salt",null)!=null
    fun blockedSeconds():Long {
        val until=preferences.getLong("blocked_until",0)
        return ((until-System.currentTimeMillis()+999)/1000).coerceAtLeast(0)
    }
    private fun hash(pin:CharArray,salt:ByteArray):ByteArray{
        val spec=PBEKeySpec(pin,salt,iterations,256)
        return try { SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
            .generateSecret(spec).encoded } finally { spec.clearPassword() }
    }
    fun verify(value:String):Boolean {
        if(!enabled())return true
        if(blockedSeconds()>0)return false
        if(!value.matches(Regex("""\d{4}""")))return false
        val salt=runCatching{Base64.decode(
            preferences.getString("salt",""),Base64.NO_WRAP)}.getOrNull()?:return false
        val stored=runCatching{Base64.decode(
            preferences.getString("digest",""),Base64.NO_WRAP)}.getOrNull()?:return false
        val correct=MessageDigest.isEqual(hash(value.toCharArray(),salt),stored)
        if(correct){
            preferences.edit().remove("failed").remove("blocked_until").apply()
        }else{
            val attempts=preferences.getInt("failed",0)+1
            val lock=when{
                attempts>=10->System.currentTimeMillis()+5*60_000
                attempts>=5->System.currentTimeMillis()+30_000
                else->0L
            }
            preferences.edit().putInt("failed",attempts)
                .putLong("blocked_until",lock).apply()
        }
        return correct
    }
    fun createOrReplace(value:String) {
        require(value.matches(Regex("""\d{4}"""))){"Introduza exatamente 4 dígitos."}
        val salt=ByteArray(16).also{SecureRandom().nextBytes(it)}
        val digest=hash(value.toCharArray(),salt)
        check(preferences.edit().putString("salt",Base64.encodeToString(salt,Base64.NO_WRAP))
            .putString("digest",Base64.encodeToString(digest,Base64.NO_WRAP))
            .remove("failed").remove("blocked_until").commit()){
            "Não foi possível guardar o PIN."
        }
    }
    fun remove(){
        check(preferences.edit().remove("salt").remove("digest")
            .remove("failed").remove("blocked_until").commit()){
            "Não foi possível desativar o PIN."
        }
    }
}
