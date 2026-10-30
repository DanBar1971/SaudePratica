#!/usr/bin/env python3
from pathlib import Path
import re
base=Path("build-src/MediAgenda_Android_v1/app/src/main/java/com/mediagenda/app")
needles=("Editar medicação","Posologia / indicação","Hora inicial do aviso","Fotografias guardadas","Tipo de toma prescrito","Sem alarme","Validade da prescrição","Bula / Folheto informativo")
for p in base.rglob("*.kt"):
    s=p.read_text(encoding="utf8")
    lines=s.splitlines()
    hits=[(n,i) for n in needles for i,l in enumerate(lines) if n in l]
    if not hits:continue
    print("\n@@ FILE",p.relative_to(base),"LINES",len(lines))
    indexes=set()
    for (n,i) in hits:
        print("@@ MATCH",repr(n),"LINE",i+1)
        for k in range(max(0,i-55),min(len(lines),i+105)):indexes.add(k)
    for i in sorted(indexes): print(f"{i+1:05d}: {lines[i]}")
# additional function listing
p=base/"MainActivity.kt"
if p.exists():
    lines=p.read_text(encoding="utf8").splitlines()
    print("@@ FUNCTIONS")
    for i,l in enumerate(lines):
        if re.search(r"(?:private )?fun .*([Mm]edicat|[Mm]edic|[Aa]larm|[Ss]uspend)",l):
            print(f"{i+1:05d} {l.strip()}")

print("\n@@ DATA MODEL AND REPOSITORY")
for p in base.rglob("*.kt"):
    s=p.read_text(encoding="utf8")
    lines=s.splitlines()
    if "data class Medication(" in s:
        for i,l in enumerate(lines):
            if "data class Medication(" in l:
                print("@@ MODEL",p.relative_to(base),"LINE",i+1)
                for k in range(i,min(len(lines),i+95)):print(f"{k+1:05d}: {lines[k]}")
    if p.name=="DataRepository.kt":
        for phrase in ["fun loadMedications(","fun saveMedications(","\"medication\" to","\"dose_pattern\""]:
            for i,l in enumerate(lines):
                if phrase in l:
                    print("@@ REPO",phrase,"LINE",i+1)
                    for k in range(max(0,i-12),min(len(lines),i+90)):print(f"{k+1:05d}: {lines[k]}")
                    break
