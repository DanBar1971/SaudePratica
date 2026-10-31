"""Validated Android full-family ZIP reader and per-profile import plan.

Sensitive data NEVER goes to GitHub. ZIP is verified in memory; patient files
are only persisted via per-file Windows DPAPI by SecureStore.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile, BadZipFile
import base64
import json
import re

from windows.android_import_v062 import (
    plan_json, AndroidImportError, ImportPlan, MAX_JSON
)

MAX_ZIP = 220 * 1024 * 1024
MAX_UNPACKED = 260 * 1024 * 1024
MAX_ASSET = 16 * 1024 * 1024
MAX_FILES = 1200
ALLOWED_EXT = {".pdf",".jpg",".jpeg",".png",".webp",".json",".heic",".heif"}
SOURCES = re.compile(r"^(?:legacy|[a-fA-F0-9-]{36})$")
ALLOWED_CATEGORIES = {
    "medication_photos":"fotografia de medicamento",
    "saudepratica_documents":"documento",
    "saudepratica_labs":"análise",
    "saudepratica_identity":"identificação",
    "saudepratica_workplace":"situação clínica",
    "saudepratica_health":"saúde",
}

@dataclass(frozen=True)
class AndroidSource:
    identifier: str
    name: str
    medications: int
    appointments: int
    attachments: int

@dataclass(frozen=True)
class ZipPlan:
    profile_id: str
    source: AndroidSource
    medications: ImportPlan
    appointments: ImportPlan
    attachments: tuple[tuple[str,bytes,str,str],...]
    archive_digest: str

def _json(data,what):
    try: return json.loads(data.decode("utf-8-sig"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise AndroidImportError(what+" JSON inválido.") from exc

def validated_files(blob: bytes) -> tuple[dict[str,bytes],dict]:
    if not isinstance(blob,bytes) or len(blob)>MAX_ZIP:
        raise AndroidImportError("ZIP inválido ou maior do que 220 MB.")
    try:
        with ZipFile(BytesIO(blob)) as z:
            infos=z.infolist()
            if not 1<=len(infos)<=MAX_FILES:
                raise AndroidImportError("O ZIP contém uma quantidade de ficheiros inválida.")
            paths=set()
            total=0
            for i in infos:
                path=PurePosixPath(i.filename)
                if (i.filename.startswith("/") or "\\" in i.filename or ":" in i.filename or
                    "." in path.parts or ".." in path.parts or len(i.filename)>240 or
                    i.filename in paths or i.is_dir() or i.file_size>MAX_ASSET or
                    i.flag_bits & 1 or (i.external_attr >> 16) & 0o170000 == 0o120000):
                    raise AndroidImportError("ZIP com ficheiros duplicados, inseguros ou excessivos.")
                paths.add(i.filename)
                total+=i.file_size
                if total>MAX_UNPACKED:
                    raise AndroidImportError("ZIP descomprimido ultrapassa 260 MB.")
            if "backup.json" not in paths:
                raise AndroidImportError("Não foi encontrado backup.json do Android.")
            head=_json(z.read("backup.json"),"Manifesto")
            if head.get("kind")!="saudepratica-complete-backup" or head.get("format")!=1:
                raise AndroidImportError("O ZIP não é um backup familiar SaúdePrática reconhecido.")
            manifest=head.get("files")
            if not isinstance(manifest,list) or len(manifest)!=len(infos)-1:
                raise AndroidImportError("O manifesto não corresponde aos ficheiros do ZIP.")
            records={}
            for entry in manifest:
                if not isinstance(entry,dict):raise AndroidImportError("Manifesto inválido.")
                p=entry.get("path")
                if not isinstance(p,str) or ("data/"+p) not in paths or p in records:
                    raise AndroidImportError("Entrada inesperada no manifesto.")
                records[p]=entry
            if paths!={"backup.json"}|{"data/"+p for p in records}:
                raise AndroidImportError("O ZIP contém ficheiros não declarados.")
            files={}
            for path,rec in records.items():
                raw=z.read("data/"+path)
                if len(raw)!=rec.get("size") or sha256(raw).hexdigest()!=rec.get("sha256"):
                    raise AndroidImportError("Um ficheiro do ZIP falhou a verificação SHA-256.")
                files[path]=raw
            return files,head
    except (BadZipFile,RuntimeError,OSError,EOFError) as exc:
        raise AndroidImportError("Não foi possível validar o backup ZIP Android.") from exc

def _names_from_prefs(head):
    prefs=head.get("prefs",{})
    node=(prefs.get("saudepratica_profiles_v1",{}) if isinstance(prefs,dict) else {})
    value=node.get("profiles",{}) if isinstance(node,dict) else {}
    try:
        raw=_json(value.get("v","").encode("utf-8"),"Perfis")
        return {p.get("id"):p.get("name") for p in raw if isinstance(p,dict)
                and isinstance(p.get("name"),str) and SOURCES.fullmatch(str(p.get("id","")))}
    except (AndroidImportError,AttributeError,TypeError): return {}

def _source_path(source,kind):
    name="medicacao.json" if kind=="medications" else "agenda.json"
    return name if source=="legacy" else f"saudepratica_profiles/{source}/{name}"

def _asset_paths(files,source,medications):
    wanted=set()
    for name in files:
        bits=name.split("/")
        if (len(bits)==3 and bits[0] in ALLOWED_CATEGORIES and bits[1]==source and
            PurePosixPath(name).suffix.lower() in ALLOWED_EXT and
            not name.endswith("/index.json") and
            not name.endswith("/records.json") and
            not name.endswith("/lab_reports.json")):
            wanted.add(name)
    # Medicine photos are shared in the Android ZIP, but only import those
    # explicitly referenced by THIS source profile, not other patients'.
    refs=set()
    for med in medications:
        for raw in med.get("images",[]) if isinstance(med.get("images"),list) else []:
            if not isinstance(raw,str):continue
            fname=raw.split("?")[0].split("/")[-1]
            if fname and re.fullmatch(r"[A-Za-z0-9_.-]{1,140}",fname):
                refs.add("medication_photos/"+fname)
    wanted.update(refs & files.keys())
    return tuple(sorted(wanted))

def archive_sources(blob:bytes):
    files,head=validated_files(blob)
    names=_names_from_prefs(head)
    ids={"legacy"}
    ids.update(names)
    for p in files:
        parts=p.split("/")
        if len(parts)==3 and parts[0]=="saudepratica_profiles" and SOURCES.fullmatch(parts[1]):
            ids.add(parts[1])
    found=[]
    for source in sorted(ids,key=lambda i:(i!="legacy",names.get(i,""))):
        meds=_json(files.get(_source_path(source,"medications"),b'{"medications":[]}'),"Medicação")
        agenda=_json(files.get(_source_path(source,"appointments"),b'{"appointments":[]}'),"Agenda")
        m=meds.get("medications",[]) if isinstance(meds,dict) else []
        a=agenda.get("appointments",[]) if isinstance(agenda,dict) else []
        if not isinstance(m,list) or not isinstance(a,list):raise AndroidImportError("Categoria clínica inválida.")
        assets=_asset_paths(files,source,m)
        found.append(AndroidSource(source,str(names.get(source) or
            ("Principal (ficheiros gerais)" if source=="legacy" else source)),
            len(m),len(a),len(assets)))
    return tuple(found)

def _jpeg_thumbnail(data):
    # 450 KB cap in the Windows editor. Full original kept in DPAPI attachments.
    from PIL import Image,ImageOps
    with Image.open(BytesIO(data)) as src:
        if src.width*src.height>25_000_000: return ""
        thumb=ImageOps.contain(src.convert("RGB"),(700,700),Image.Resampling.LANCZOS)
        for quality in (85,72,60,45):
            buf=BytesIO()
            thumb.save(buf,format="JPEG",quality=quality,optimize=True)
            if len(buf.getvalue())<=400000:
                return base64.b64encode(buf.getvalue()).decode("ascii")
    return ""

def prepare_archive(blob:bytes,source_id:str,profile:dict)->ZipPlan:
    files,head=validated_files(blob)
    candidates=archive_sources(blob)
    source=next((x for x in candidates if x.identifier==source_id),None)
    if source is None:raise AndroidImportError("Perfil Android não encontrado no ZIP.")
    if not profile or not profile.get("id"):raise AndroidImportError("Seleciona um perfil Windows.")
    prior=profile.get("android_zip_source_id")
    if prior and prior!=source_id:
        raise AndroidImportError("Este perfil Windows já está associado a outro perfil Android.")
    mpath=_source_path(source_id,"medications")
    apath=_source_path(source_id,"appointments")
    meds=plan_json(files.get(mpath,b'{"medications":[]}'),"medications",profile)
    agenda=plan_json(files.get(apath,b'{"appointments":[]}'),"appointments",profile)
    paths=_asset_paths(files,source_id,meds.entries)
    attachments=[]
    for p in paths:
        data=files[p]
        cat=p.split("/")[0]
        attachments.append((p,data,ALLOWED_CATEGORIES.get(cat,"fotografia de medicamento"),
                           sha256(data).hexdigest()))
    # Preview photos from authenticated original Android image file.
    for med in meds.new:
        original=med["android_original"]
        image_refs=original.get("images") if isinstance(original.get("images"),list) else []
        for ref in image_refs:
            if not isinstance(ref,str):continue
            src="medication_photos/"+ref.split("?")[0].split("/")[-1]
            if src not in files:continue
            if PurePosixPath(src).suffix.lower() not in {".jpg",".jpeg",".png",".webp"}:continue
            try:
                med["photo_b64"]=_jpeg_thumbnail(files[src])
                if med["photo_b64"]:break
            except (ValueError,OSError):continue
    return ZipPlan(profile["id"],source,meds,agenda,tuple(attachments),
                   sha256(blob).hexdigest())

def apply_archive(store,plan:ZipPlan):
    """SecureStore commits BOTH clinical data and attachments with rollback."""
    if not isinstance(plan,ZipPlan):raise AndroidImportError("Pré-visualização ZIP em falta.")
    return store.import_android_archive(plan)
