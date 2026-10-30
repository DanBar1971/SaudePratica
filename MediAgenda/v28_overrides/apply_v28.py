from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
media=root/"app/src/main/java/com/mediagenda/app/data/ProfileMediaStore.kt"
s=media.read_text(encoding="utf-8")
old='''        resolver.openInputStream(uri)?.use{BitmapFactory.decodeStream(it,null,bounds)}
            ?:error("Não foi possível ler a imagem.")'''
new='''        // BitmapFactory returns null on purpose when inJustDecodeBounds=true.
        // Only the input stream is required here; dimensions are in 'bounds'.
        // The old Elvis on decodeStream always threw, even for a valid photo.
        val inspectionStream = resolver.openInputStream(uri)
            ?:error("Não foi possível abrir o ficheiro de imagem.")
        inspectionStream.use { input ->
            BitmapFactory.decodeStream(input, null, bounds)
        }'''
assert s.count(old)==1, "The known faulty bitmap header reading is missing"
s=s.replace(old,new,1)
assert "require(bounds.outWidth in 1..15000&&bounds.outHeight in 1..15000)" in s
assert "var bitmap=resolver.openInputStream(uri)?.use" in s
media.write_text(s,encoding="utf-8")
gradle=root/"app/build.gradle.kts"
g=gradle.read_text(encoding="utf-8")
assert 'applicationId = "com.mediagenda.app.stable"' in g
assert 'versionCode = 18' in g and 'versionName = "1.9.8"' in g
g=g.replace('versionCode = 18','versionCode = 19',1)
g=g.replace('versionName = "1.9.8"','versionName = "1.9.9"',1)
gradle.write_text(g,encoding="utf-8")
print("v1.9.9: photo and CC image decoding fixed for camera and gallery; existing profiles untouched.")
