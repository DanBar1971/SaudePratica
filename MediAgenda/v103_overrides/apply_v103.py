"""SaúdePrática v1.9.84: portable JSON medication photos extraction on import.

All photos stay private on the Android device. No patient or photo data is
committed to GitHub. Legacy JSON import remains unchanged if no payload exists.
"""
from pathlib import Path
root=Path("build-src/MediAgenda_Android_v1")
base=root/"app/src/main/java/com/mediagenda/app"
data=base/"data/DataRepository.kt"
text=data.read_text(encoding="utf-8")
old='root.has("medications") -> { atomicWrite(medFile, root.toString(2)); "Medicação importada" }'
new='''root.has("medications") -> {
                val photos=EmbeddedMedicationImporter.materialize(context,profileId,root)
                atomicWrite(medFile,root.toString(2))
                "Medicação importada" + if(photos>0) " · $photos fotografias" else ""
            }'''
if text.count(old)!=1:raise RuntimeError("DataRepository medication import anchor changed")
text=text.replace(old,new,1)
data.write_text(text,encoding="utf-8")
dest=base/"data/EmbeddedMedicationImporter.kt"
src=Path("MediAgenda/v103_overrides/EmbeddedMedicationImporter.kt")
dest.write_text(src.read_text(encoding="utf-8"),encoding="utf-8")
build=root/"app/build.gradle.kts"
s=build.read_text(encoding="utf-8")
assert s.count("versionCode = 93")==1 and s.count('versionName = "1.9.83"')==1
s=s.replace("versionCode = 93","versionCode = 94",1)
s=s.replace('versionName = "1.9.83"','versionName = "1.9.84"',1)
build.write_text(s,encoding="utf-8")
print("v1.9.84: JSON medication photos embedded as Base64 now materialize in local photos folder")
