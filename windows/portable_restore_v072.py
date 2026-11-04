"""Validated, non-duplicating SaúdePrática .spbackup family/profile restoration.

Never overwrite patient data based on name silently: the UI must preview the
identity mapping and require an affirmative replace confirmation. All bytes are
validated before writing. Compatible with legacy .spbackup v1 archives.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import copy
import json
import re
import uuid

from shared.python.saude_backup import BackupError

HEX = re.compile(r"^[a-f0-9]{64}$")
VALID_SCOPE = {"family", "profile"}

@dataclass(frozen=True)
class PersonPlan:
    source_id: str
    target_id: str
    name: str
    operation: str
    medications: int
    appointments: int
    attachments: int
    source_identity: str

@dataclass(frozen=True)
class RestorePlan:
    people: tuple[PersonPlan, ...]
    files: dict[str, bytes]
    scope: str
    file_count: int
    attachment_bytes: int


def _json(raw, title):
    try:
        obj=json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError, AttributeError) as exc:
        raise BackupError(f"Dados de {title} inválidos.") from exc
    return obj


def _profiles(files):
    result={}
    for path, raw in files.items():
        if not path.endswith("/profile.json"):
            continue
        data=_json(raw,"perfil")
        if not isinstance(data,dict) or not isinstance(data.get("id"),str):
            raise BackupError("Perfil sem identidade.")
        pid=data["id"]
        try:uuid.UUID(pid)
        except ValueError as exc:raise BackupError("UUID de perfil inválido.") from exc
        if path != f"profiles/{pid}/profile.json" or pid in result:
            raise BackupError("Caminhos de perfis duplicados ou trocados.")
        if not isinstance(data.get("name"),str) or not data["name"].strip():
            raise BackupError("Perfil sem nome.")
        prefix=f"profiles/{pid}/"
        meds=_json(files.get(prefix+"medicacao.json"),"medicação")
        agenda=_json(files.get(prefix+"agenda.json"),"agenda")
        if not isinstance(meds,dict) or not isinstance(meds.get("medications"),list):
            raise BackupError("Medicação em falta ou inválida.")
        if not isinstance(agenda,dict) or not isinstance(agenda.get("appointments"),list):
            raise BackupError("Agenda em falta ou inválida.")
        if len(meds["medications"])>2000 or len(agenda["appointments"])>2000:
            raise BackupError("Demasiados registos.")
        attachments=_json(files.get(prefix+"attachments.json",b"[]"),"anexos")
        if not isinstance(attachments,list):raise BackupError("Lista de anexos inválida.")
        for a in attachments:
            if not isinstance(a,dict) or a.get("profile_id") != pid:
                raise BackupError("Anexo associado ao perfil errado.")
            digest=a.get("sha256","")
            if not isinstance(digest,str) or not HEX.fullmatch(digest):
                raise BackupError("Identificador de anexo inválido.")
            payload=files.get(f"attachments/{digest[:2]}/{digest}.bin")
            if payload is None or sha256(payload).hexdigest()!=digest:
                raise BackupError("Fotografia ou documento danificado ou em falta.")
        archives=_json(files.get(prefix+"android_archives.json",b"[]"),"originais Android")
        if not isinstance(archives,list):raise BackupError("Índice Android inválido.")
        for archive in archives:
            if not isinstance(archive,dict) or pid not in archive.get("profile_ids",[]):
                raise BackupError("Backup Android associado a outro perfil.")
            digest=archive.get("sha256","")
            if not isinstance(digest,str) or not HEX.fullmatch(digest):
                raise BackupError("Hash do backup original inválido.")
            payload=files.get(f"attachments/{digest[:2]}/{digest}.bin")
            if payload is None or sha256(payload).hexdigest()!=digest:
                raise BackupError("ZIP Android original não encontrado.")
        result[pid]=(data,meds["medications"],agenda["appointments"],attachments,archives)
    if not result:raise BackupError("O ficheiro não contém perfis.")
    return result


def inspect(files: dict[str,bytes], existing_profiles: list[dict]) -> RestorePlan:
    if not isinstance(files,dict):
        raise BackupError("Backup não verificado.")
    persons=_profiles(files)
    scopes=set()
    for pid in persons:
        p=f"profiles/{pid}/backup_scope.json"
        if p in files:
            obj=_json(files[p],"tipo de backup")
            if not isinstance(obj,dict) or obj.get("scope") not in VALID_SCOPE:
                raise BackupError("Tipo de backup não reconhecido.")
            scopes.add(obj["scope"])
    if len(scopes)>1:raise BackupError("Tipos de backup contraditórios.")
    scope=next(iter(scopes),"family")  # accepts existing encrypted v1 backups
    if scope=="profile" and len(persons)!=1:
        raise BackupError("O backup de perfil tem de conter exatamente um perfil.")

    existing=existing_profiles
    targets=set()
    planned=[]
    for pid,(person,meds,agenda,attachments,_) in persons.items():
        source=str(person.get("android_zip_source_id") or "")
        same_uuid=[p for p in existing if p.get("id")==pid]
        same_source=[p for p in existing if source and p.get("android_zip_source_id")==source]
        name=person["name"].strip()
        same_name=[p for p in existing if str(p.get("name","")).strip().casefold()==name.casefold()]
        # No guesswork on ambiguous sources/names; a human must fix duplicates.
        if len(same_uuid)>1 or len(same_source)>1 or len(same_name)>1:
            raise BackupError(f"Existem perfis Windows ambíguos para {name}.")
        candidate=(same_uuid or same_source or same_name or [None])[0]
        if candidate and candidate.get("android_zip_source_id") not in ("",None,source):
            raise BackupError("O perfil escolhido pertence a outra origem Android.")
        target=candidate.get("id") if candidate else pid
        if target in targets or (not candidate and any(p.get("id")==target for p in existing)):
            raise BackupError("Dois perfis do backup apontam para o mesmo destino.")
        targets.add(target)
        planned.append(PersonPlan(pid,target,name,
            "replace" if candidate else "create",
            len(meds),len(agenda),len(attachments),source))
    total=sum(len(files.get(f"attachments/{a['sha256'][:2]}/{a['sha256']}.bin",b""))
        for pid in persons for a in persons[pid][3])
    return RestorePlan(tuple(planned),files,scope,len(files),total)


def apply(store, plan:RestorePlan, password_for_safety_copy:str):
    """Verified backup replaces matched profiles only with explicit UI approval.

    Before any replacement create a recoverable encrypted snapshot. No partial
    profile/asset commit is allowed; unrelated profiles are preserved.
    """
    if not isinstance(plan,RestorePlan):
        raise BackupError("Pré-visualização de restauro inválida.")
    if len(password_for_safety_copy)<10:
        raise BackupError("Indica uma palavra-passe segura para a cópia de segurança.")
    import datetime
    previous=store.data
    # Verify again because another operation could have modified the plan.
    checked=inspect(plan.files,store.profiles())
    if checked.people!=plan.people:
        raise BackupError("Perfis alterados desde a pré-visualização. Prepara novamente.")
    persons=_profiles(plan.files)
    backup=None
    if store.profiles():
        # Auto backup of the entire current state before replacement.
        backup=store.export_backup(password_for_safety_copy)
        recovery=store.path.parent/"restores"
        recovery.mkdir(mode=0o700,parents=True,exist_ok=True)
        stamped=datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        recovery_file=recovery/("pre-restore-"+stamped+".spbackup")
        recovery_file.write_bytes(backup)
    else:
        recovery_file=None
    proposed=copy.deepcopy(previous)
    index={p["id"]:p for p in proposed["profiles"]}
    target_to_source={p.target_id:p.source_id for p in plan.people}
    source_to_target={p.source_id:p.target_id for p in plan.people}
    # Preserve prior attachment metadata for unrelated profiles only.
    selected=set(target_to_source)
    docs=[x for x in proposed.get("imported_files",[])
          if x.get("profile_id") not in selected]
    archives=[]
    for row in proposed.get("android_family_archives",[]):
        kept=copy.deepcopy(row)
        kept["profile_ids"]=[pid for pid in kept.get("profile_ids",[])
                             if pid not in selected]
        if kept["profile_ids"]:
            archives.append(kept)
    assets=[]
    module_totals={"meals":0,"meal_photos":0,"water":0,"symptoms":0,
                   "intakes":0,"measurements":0,"health_connect":0,
                   "manual_body":0,"sos":0,"residences":0,"invoices":0}
    from windows.android_full_restore_v0813 import (
        extract_profile_android,merge_snapshot,
    )
    for member in plan.people:
        person,meds,appointments,originals_attachments,originals=persons[member.source_id]
        attachments=originals_attachments
        pid=member.target_id
        source_id=person.get("android_zip_source_id")
        restored=copy.deepcopy(person)
        restored["id"]=pid
        restored["medications"]=copy.deepcopy(meds)
        restored["appointments"]=copy.deepcopy(appointments)
        if member.operation=="replace":
            # Older portable backups store only identity, medication and
            # agenda. Do not erase newer Windows modules just because their
            # keys did not yet exist when that backup was exported.
            earlier=index[pid]
            for key,value in earlier.items():
                if key not in restored and key not in ("medications","appointments"):
                    restored[key]=copy.deepcopy(value)
        if source_id:
            restored["android_zip_source_id"]=source_id
        # Android keeps the identity/health profile fields inside typed
        # SharedPreferences of its original ZIP, not in the portable summary.
        # Recover ONLY the source person's fields before storing this profile.
        # Existing Windows edits in the portable profile.json take precedence.
        if source_id and originals:
            from windows.android_profile_v067 import read_profile_extras
            from windows.profile_fields_v066 import missing_profile_fields
            for original_archive in originals:
                raw_digest=original_archive["sha256"]
                original_zip=plan.files[
                    f"attachments/{raw_digest[:2]}/{raw_digest}.bin"]
                extra_fields,_=read_profile_extras(original_zip,source_id)
                restored.update(missing_profile_fields(restored,extra_fields))
                # Caregiver is boolean metadata, not a free-text field.
                # Only populate it when the portable file did not already
                # contain a deliberate Windows caregiver choice.
                if "caregiver" not in restored and isinstance(
                        extra_fields.get("caregiver"),bool):
                    restored["caregiver"]=extra_fields["caregiver"]
        if member.operation=="replace":
            # Keep the stable local ID and original source identity. Replace
            # clinical fields only when explicitly confirmed in the UI.
            idx=next(i for i,p in enumerate(proposed["profiles"]) if p["id"]==pid)
            proposed["profiles"][idx]=restored
        else:
            proposed["profiles"].append(restored)
        for item in attachments:
            entry=copy.deepcopy(item)
            entry["profile_id"]=pid
            digest=entry["sha256"]
            docs.append(entry)
            assets.append((digest,plan.files[f"attachments/{digest[:2]}/{digest}.bin"]))
        if source_id and originals:
            for original_archive in originals:
                digest=original_archive["sha256"]
                raw=plan.files[f"attachments/{digest[:2]}/{digest}.bin"]
                snapshot=extract_profile_android(raw,source_id)
                new_docs,new_photos,counts=merge_snapshot(
                    restored,snapshot,source_to_target,docs)
                docs.extend(new_docs)
                assets.extend(new_photos)
                for module,amount in counts.items():
                    module_totals[module]+=amount
        for raw in originals:
            copyrow=copy.deepcopy(raw)
            # In a profile restore retain only the selected owner; never
            # associate a family archive with unrelated profiles.
            copyrow["profile_ids"]=[pid]
            digest=copyrow["sha256"]
            old=next((x for x in archives if x.get("sha256")==digest),None)
            if old:
                old["profile_ids"]=sorted(set(old["profile_ids"])|set(copyrow["profile_ids"]))
            else:archives.append(copyrow)
            assets.append((digest,plan.files[f"attachments/{digest[:2]}/{digest}.bin"]))
    proposed["imported_files"]=docs
    proposed["android_family_archives"]=archives
    created=store._write_assets(assets)
    try:
        store.data=proposed
        store.save()
    except Exception:
        store.data=previous
        for path in created:
            try:path.unlink()
            except OSError:pass
        raise
    return {
        "created":sum(x.operation=="create" for x in plan.people),
        "replaced":sum(x.operation=="replace" for x in plan.people),
        "profiles":len(plan.people),
        "recovery":str(recovery_file) if recovery_file else None,
        "android_modules":module_totals,
    }
