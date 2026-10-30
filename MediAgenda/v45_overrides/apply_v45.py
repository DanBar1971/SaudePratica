from pathlib import Path

root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"

def patch_once(file, old, new, label):
    s=file.read_text(encoding="utf-8")
    if s.count(old)!=1:
        raise RuntimeError("v1.9.26 "+label+": expected 1 anchor, got "+str(s.count(old)))
    file.write_text(s.replace(old,new,1),encoding="utf-8")

# BitmapFactory.decodeStream returns null intentionally when inJustDecodeBounds
# is true. Its dimensions are still valid. Do not reject a photograph for that.
loader=base/"data/MedicationPhotoLoader.kt"
patch_once(loader,
    '        stream()?.use{BitmapFactory.decodeStream(it,null,bounds)}?:return null',
    '''        val boundsStream=stream()?:return null
        boundsStream.use{BitmapFactory.decodeStream(it,null,bounds)}''',
    "image bounds decoder")

# Gallery photos are visual medicine identification aids, NOT OCR documents.
# Bitmap decoding, resizing and JPEG encoding already validate file integrity.
main=base/"MainActivity.kt"
patch_once(main,
    '''                check(file.length()>128L &&
                    MedicationPhotoLoader.decode(this,file.absolutePath,320)!=null){
                    "A imagem escolhida não é legível. Seleciona outra."
                }
''',
    "",
    "remove incorrect medicine-photo legibility rejection")

# Use the newest readable medication image for notifications (same as list).
receiver=base/"notifications/NotificationReceiver.kt"
patch_once(receiver,
    'import com.mediagenda.app.data.ProfileStore',
    'import com.mediagenda.app.data.ProfileStore\nimport com.mediagenda.app.data.MedicationPhotoLoader',
    "notification photo loader import")
patch_once(receiver,
    '''                val photo = runCatching {
                    DataRepository(context, profileId).loadMedications()
                        .firstOrNull { it.id == medicationId }
                        ?.images?.firstOrNull()
                }.getOrNull()
                if (!photo.isNullOrBlank()) {
                    decodeMedicationPhoto(context, photo)?.let { bitmap ->''',
    '''                val photos = runCatching {
                    DataRepository(context, profileId).loadMedications()
                        .firstOrNull { it.id == medicationId }
                        ?.images.orEmpty()
                }.getOrDefault(emptyList())
                MedicationPhotoLoader.load(context,photos,900)?.let { bitmap ->''',
    "notification newest photo selection")
# The above replacement consumes the old if block, so one closing brace must
# be removed while preserving the nested bitmap/style conditional block.
patch_once(receiver,
    '''                            .setSummaryText(body))
                    }
                }
            }
            manager.notify(id, builder.build())''',
    '''                            .setSummaryText(body))
                }
            }
            manager.notify(id, builder.build())''',
    "notification bitmap block closing")

gradle=root/"app/build.gradle.kts"
patch_once(gradle,'versionCode = 35','versionCode = 36',"versionCode")
patch_once(gradle,'versionName = "1.9.25"','versionName = "1.9.26"',"versionName")
print("v1.9.26: accepts valid medicine-box photos without OCR, fixes image bounds decoding, displays newest readable photo in the list and notifications.")
