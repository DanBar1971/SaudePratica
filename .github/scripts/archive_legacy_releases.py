#!/usr/bin/env python3
"""Copy original public SaúdePrática release assets without changing signed APK bytes."""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

SOURCE="DanBar1971/AndroidAppDev"
DEST="DanBar1971/SaudePratica"

def gh(*args,check=True):
    p=subprocess.run(["gh",*map(str,args)],text=True,capture_output=True)
    if check and p.returncode:
        raise RuntimeError("gh command failed: "+repr(args)+"\n"+p.stderr[-2000:])
    return p

def metadata(repo,tag):
    return json.loads(gh("api",f"repos/{repo}/releases/tags/{tag}").stdout)

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    start=int(sys.argv[1])
    assert 76<=start<=116 and (start-76)%5==0
    for n in range(start,min(start+5,119)):
        tag=f"v1.9.{n}"
        original=metadata(SOURCE,tag)
        print("MIGRATING:",tag,flush=True)
        with tempfile.TemporaryDirectory(prefix="saudepratica-migrate-") as tmp:
            folder=pathlib.Path(tmp)
            gh("release","download",tag,"--repo",SOURCE,"--dir",tmp)
            expected={}
            for asset in original["assets"]:
                p=folder/asset["name"]
                if not p.is_file() or p.stat().st_size!=asset["size"]:
                    raise RuntimeError(f"Original asset missing/different: {tag} {asset['name']}")
                d=asset.get("digest") or ""
                if d.startswith("sha256:") and "sha256:"+digest(p)!=d:
                    raise RuntimeError(f"SHA256 mismatch: {tag} {asset['name']}")
                expected[asset["name"]]=asset["size"]
            existing=gh("release","view",tag,"--repo",DEST,check=False).returncode==0
            if not existing:
                note=folder.parent/(tag+"-notes.md")
                note.write_text("# SaúdePrática "+tag+" — arquivo\n\n"+
                    "Release original: "+original["html_url"]+"\n\n"+
                    "Publicado originalmente: "+str(original.get("published_at"))+"\n\n"+
                    "Ref original: "+str(original.get("target_commitish"))+"\n\n"+
                    "APKs e outros anexos copiados sem modificar assinatura ou conteúdo.\n\n"+
                    "---\n\n"+(original.get("body") or ""),encoding="utf8")
                try:
                    gh("release","create",tag,*[str(folder/name) for name in expected],
                       "--repo",DEST,"--target","main","--latest=false",
                       "--title","SaúdePrática "+tag+" — Android","--notes-file",str(note))
                finally:
                    note.unlink(missing_ok=True)
            migrated=metadata(DEST,tag)
            got={x["name"]:x["size"] for x in migrated["assets"]}
            if got!=expected:
                raise RuntimeError(f"Release mismatch {tag}: expected {expected}, got {got}")
            print("VERIFIED:",tag,len(expected),"original assets",flush=True)

if __name__=="__main__":
    main()
