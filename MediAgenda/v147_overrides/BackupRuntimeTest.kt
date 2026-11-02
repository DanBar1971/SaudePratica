package com.mediagenda.app

import android.net.Uri
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.mediagenda.app.data.DataRepository
import com.mediagenda.app.data.FamilyBackupStore
import com.mediagenda.app.data.PortableWindowsBackup
import com.mediagenda.app.data.PortableWindowsClinicalRestore
import com.mediagenda.app.data.ProfileStore
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.security.MessageDigest
import java.util.zip.ZipFile

/** Integration tests on an actual Android emulator using only fictional data. */
@RunWith(AndroidJUnit4::class)
class BackupRuntimeTest {
    private val app get()=InstrumentationRegistry.getInstrumentation().targetContext
    private fun data(name:String)=File(app.filesDir,name).apply{
        parentFile?.mkdirs()
    }
    private fun hash(text:String)=MessageDigest.getInstance("SHA-256")
        .digest(text.toByteArray()).joinToString(""){"%02x".format(it)}
    @Test fun encryptedFamilyAndIsolatedProfileKeepClinicalRecordsAndDiabetes(){
        val registry=ProfileStore(app)
        val a=registry.create("Pessoa Fictícia Alfa")
        val b=registry.create("Pessoa Fictícia Beta")
        val aPath=if(a.id=="legacy")"" else
            "saudepratica_profiles/"+a.id+"/"
        val bPath=if(b.id=="legacy")"" else
            "saudepratica_profiles/"+b.id+"/"
        val image=data("medication_photos/fake_box.jpg")
        image.writeBytes(byteArrayOf(0xff.toByte(),0xd8.toByte(),0xff.toByte(),0xd9.toByte()))
        data(aPath+"medicacao.json").writeText(JSONObject()
            .put("medications",JSONArray().put(JSONObject()
                .put("id","fake_med_a").put("medication","Medicamento fictício A")
                .put("dose","5 mg")
                .put("images",JSONArray().put(image.absolutePath)))).toString())
        data(aPath+"agenda.json").writeText(JSONObject()
            .put("appointments",JSONArray().put(JSONObject()
                .put("id","fake_apt_a").put("activity","Consulta fictícia A")
                .put("date","2026-12-01").put("time","09:30"))).toString())
        data(bPath+"medicacao.json").writeText(JSONObject()
            .put("medications",JSONArray().put(JSONObject()
                .put("id","fake_med_b").put("medication","Medicamento fictício B")
                .put("dose","2 mg"))).toString())
        data(bPath+"agenda.json").writeText(JSONObject()
            .put("appointments",JSONArray().put(JSONObject()
                .put("id","fake_apt_b").put("activity","Consulta fictícia B")
                .put("date","2026-12-04").put("time","11:00"))).toString())
        data("saudepratica_documents/"+b.id+"/fake.pdf")
            .writeBytes("%PDF-1.4\nFake PDF — no health information.\n%%EOF\n".toByteArray())
        data("diabetes_v1/"+hash(b.id)+".json")
            .writeText("""{"entries":[{"glucose":99,"fake":true}]}""")
        val writer=PortableWindowsBackup(app)
        val whole=File(app.cacheDir,"family_fake_test.spbackup")
        assertEquals(2,writer.export(Uri.fromFile(whole),
            "fictitious strong password".toCharArray()))
        assertTrue(whole.length()>1000L)
        val opened=writer.inspect(Uri.fromFile(whole),
            "fictitious strong password".toCharArray())
        try{
            val plan=PortableWindowsClinicalRestore(app).inspect(opened)
            assertEquals("family",plan.scope)
            assertEquals(2,plan.people.size)
            assertEquals(2,plan.people.sumOf{it.medicationCount})
            assertEquals(2,plan.people.sumOf{it.appointmentCount})
        }finally{opened.discard()}
        val one=File(app.cacheDir,"profile_fake_test.spbackup")
        assertEquals(1,writer.export(Uri.fromFile(one),
            "fictitious strong password".toCharArray(),b.id))
        val only=writer.inspect(Uri.fromFile(one),
            "fictitious strong password".toCharArray())
        try{
            val plan=PortableWindowsClinicalRestore(app).inspect(only)
            assertEquals("profile",plan.scope)
            assertEquals(1,plan.people.size)
            assertEquals("Pessoa Fictícia Beta",plan.people[0].name)
            ZipFile(only.decrypted).use{outer->
                val id=plan.people[0].source
                val descriptor=JSONArray(String(outer.getInputStream(
                    outer.getEntry("data/profiles/"+id+"/android_archives.json"))
                        .use{it.readBytes()})).getJSONObject(0)
                val h=descriptor.getString("sha256")
                val nested=File(app.cacheDir,"fake_nested_original.zip")
                nested.outputStream().use{out->
                    outer.getInputStream(outer.getEntry("data/attachments/"+
                        h.take(2)+"/"+h+".bin")).use{it.copyTo(out)}
                }
                try{
                    ZipFile(nested).use{inner->
                        val entries=inner.entries().asSequence().map{it.name}.toList()
                        assertTrue(entries.contains("data/diabetes_v1/"+hash(b.id)+".json"))
                        assertFalse(entries.contains("data/medicacao.json"))
                        assertFalse(entries.any{it.contains("/"+a.id+"/")})
                        assertTrue(entries.any{it.contains("fake.pdf")})
                    }
                }finally{nested.delete()}
            }
        }finally{only.discard()}
        // Exercise the real destructive restore path on synthetic profiles.
        // Never accept a plaintext recovery snapshot after a successful write.
        val toRestore=writer.inspect(Uri.fromFile(one),
            "fictitious strong password".toCharArray())
        try{
            val bridge=PortableWindowsClinicalRestore(app)
            val plan=bridge.inspect(toRestore)
            assertEquals(1,bridge.restore(toRestore,plan,
                "fictitious strong password".toCharArray()))
            assertEquals(2,registry.all().size)
            val restored=JSONObject(data(bPath+"medicacao.json").readText())
                .getJSONArray("medications")
            assertEquals("fake_med_b",restored.getJSONObject(0).getString("id"))
            assertEquals("Medicamento fictício B",
                restored.getJSONObject(0).getString("medication"))
            val recovery=File(app.filesDir,"sp_recovery_private")
                .listFiles()?.filter{it.extension=="spbackup"}.orEmpty()
            assertTrue("Encrypted safety copy missing",recovery.isNotEmpty())
            val snapshot=writer.inspect(Uri.fromFile(recovery.last()),
                "fictitious strong password".toCharArray())
            try{
                assertEquals(2,bridge.inspect(snapshot).people.size)
            }finally{snapshot.discard()}
        }finally{toRestore.discard()}
        try{
            writer.inspect(Uri.fromFile(whole),
                "incorrect password 2026".toCharArray())
            fail("Wrong password was accepted")
        }catch(expected:Exception){
            assertTrue(expected.message!=null || expected.javaClass.name.isNotBlank())
        }
    }
}
