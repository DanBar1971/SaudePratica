"""Assemble v1.9.101 audited text-patch fragments, then set the Android version."""
from pathlib import Path
base=Path(__file__).parent
parts=sorted(base.glob("apply_v120.py.part[0-9][0-9]"))
assert len(parts)==2, "Missing SaúdePrática v120 patch fragments"
source="".join(p.read_text(encoding="utf-8").rstrip("\n") for p in parts)
exec(compile(source,str(base/"apply_v120.source.py"),"exec"),{"__file__":str(base/"apply_v120.py")})
gradle=Path("build-src/MediAgenda_Android_v1/app/build.gradle.kts")
s=gradle.read_text(encoding="utf-8")
assert s.count("versionCode = 110")==1 and s.count('versionName = "1.9.100"')==1
s=s.replace("versionCode = 110","versionCode = 111").replace('versionName = "1.9.100"','versionName = "1.9.101"')
gradle.write_text(s,encoding="utf-8")
print("SaúdePrática versionName 1.9.101 versionCode 111")
