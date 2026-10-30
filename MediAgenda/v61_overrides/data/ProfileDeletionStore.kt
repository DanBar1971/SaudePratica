package com.mediagenda.app.data

import android.content.Context
import android.net.Uri
import java.io.File
import org.json.JSONObject

/** Removes only the explicitly selected family member from local storage.
 * This does not send a delete to any other device, and never removes photos
 * that are still referenced by another user's medication records.
 */
class ProfileDeletionStore(private val context: Context) {
    private val profiles=ProfileStore(context)
    private val root=context.filesDir
    private val idPattern=Regex("(?:legacy|[a-fA-F0-9-]{36})")
    private val folders=listOf(
        "saudepratica_profiles", "saudepratica_health", "saudepratica_identity",
        "saudepratica_documents", "saudepratica_labs", "saudepratica_workplace",
        "saudepratica_cycle", "saudepratica_expenses"
    )
    private val individualPrefs=listOf("saudepratica_wellness_", "saudepratica_cycle_",
        "saudepratica_emergency_", "saudepratica_modules_")
    private val photoFilename=Regex("[A-Za-z0-9_.-]{1,140}\\.jpg",RegexOption.IGNORE_CASE)

    private fun medFile(id:String)=if(id=="legacy")File(root,"medicacao.json")
        else File(root,"saudepratica_profiles/$id/medicacao.json")

    private fun photosIn(id:String):Set<String> {
        val file=medFile(id)
        if(!file.isFile)return emptySet()
        val result=mutableSetOf<String>()
        val array=JSONObject(file.readText(Charsets.UTF_8))
            .optJSONArray("medications")?:return emptySet()
        for(i in 0 until array.length()){
            val images=array.optJSONObject(i)?.optJSONArray("images")?:continue
            for(j in 0 until images.length()){
                val value=images.optString(j)
                val name=runCatching{Uri.parse(value).lastPathSegment}
                    .getOrNull()?.substringAfterLast('/')?:continue
                if(photoFilename.matches(name))result.add(name)
            }
        }
        return result
    }

    private fun removeFileTree(file:File){
        if(!file.exists())return
        val allowed=root.canonicalFile
        val item=file.canonicalFile
        require(item.path.startsWith(allowed.path+File.separator)){
            "Destino de eliminação não autorizado."
        }
        require(!java.nio.file.Files.isSymbolicLink(file.toPath())){
            "Não é possível eliminar ligações simbólicas."
        }
        if(file.isDirectory){
            file.listFiles()?.forEach{ removeFileTree(it) }
        }
        check(file.delete()){"Não foi possível apagar ${file.name}."}
    }

    fun delete(id:String):String {
        require(idPattern.matches(id)){"Utilizador inválido."}
        val person=profiles.all().firstOrNull{it.id==id}
            ?:throw IllegalArgumentException("O utilizador já não existe.")
        val others=profiles.all().filterNot{it.id==id}
        // Fail closed on invalid metadata: don't risk deleting shared photos.
        val theirPhotos=others.flatMap{photosIn(it.id)}.toSet()
        val ownPhotos=photosIn(id)
        val photosRoot=File(root,"medication_photos").canonicalFile

        for(folder in folders){
            removeFileTree(File(root,"$folder/$id"))
        }
        if(id=="legacy"){
            removeFileTree(File(root,"medicacao.json"))
            removeFileTree(File(root,"agenda.json"))
        }
        for(filename in ownPhotos-theirPhotos){
            val file=File(photosRoot,filename).canonicalFile
            if(file.parentFile==photosRoot && file.isFile)removeFileTree(file)
        }
        val names=individualPrefs.map{it+id}+profiles.preferencesFor(id)
        for(name in names.distinct()){
            check(context.getSharedPreferences(name,Context.MODE_PRIVATE).edit().clear().commit()){
                "Não foi possível limpar dados pessoais do perfil."
            }
        }
        val sort=context.getSharedPreferences("saudepratica_med_sort",Context.MODE_PRIVATE)
        sort.edit().remove(id).commit()
        // Remove from the registry LAST. Any failure before this point leaves
        // the profile visible for troubleshooting rather than silently losing it.
        profiles.remove(id)
        return person.name
    }
}