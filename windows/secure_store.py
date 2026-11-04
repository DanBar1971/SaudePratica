"""Windows-only local profile store; patient data protected by Windows DPAPI.

Does not use the Android signing certificate. Nothing is uploaded to GitHub.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import uuid

from shared.python.saude_backup import create_backup, read_backup, BackupError

STORE_FORMAT = 1

class LocalStoreError(Exception):
    pass


def _user_data_path() -> Path:
    if sys.platform != "win32":
        raise LocalStoreError("O armazenamento seguro requer Windows.")
    root = os.getenv("LOCALAPPDATA")
    if not root:
        raise LocalStoreError("A pasta de dados do Windows não está disponível.")
    p = Path(root) / "SaudePraticaDesktop"
    p.mkdir(parents=True, exist_ok=True)
    return p / "profile_data.dpapi"


def _encrypt(data: bytes) -> bytes:
    import win32crypt
    return win32crypt.CryptProtectData(data, "SaudePratica Desktop - Perfil", None, None, None, 0)


def _decrypt(data: bytes) -> bytes:
    import win32crypt
    return win32crypt.CryptUnprotectData(data, None, None, None, 0)[1]


class SecureStore:
    def __init__(self):
        self.path = _user_data_path()
        self.data = {"format": STORE_FORMAT, "profiles": []}
        if self.path.exists():
            try:
                if self.path.stat().st_size > 40_000_000:
                    raise LocalStoreError("Ficheiro local demasiado grande.")
                self.data = json.loads(_decrypt(self.path.read_bytes()))
                if self.data.get("format") != STORE_FORMAT or not isinstance(self.data.get("profiles"), list):
                    raise LocalStoreError("Formato de dados local desconhecido.")
            except Exception as e:
                raise LocalStoreError("Não foi possível abrir os dados protegidos desta conta Windows.") from e
        # Migrar uma única vez os módulos Android que já estejam guardados,
        # sem exigir que o utilizador carregue em Importar/Recuperar.
        self._automatic_android_recovery_error = None
        try:
            self._auto_restore_existing_android_modules()
        except (LocalStoreError, ValueError, OSError, KeyError, TypeError) as exc:
            # Um arquivo antigo danificado não pode impedir a abertura da app.
            # Não colocar dados clínicos ou caminhos pessoais num log.
            self._automatic_android_recovery_error = type(exc).__name__

    def _auto_restore_existing_android_modules(self):
        """Migração local 0.8.15: inclui dados Health Connect já arquivados."""
        from hashlib import sha256
        archives=self.android_archives()
        if not archives or not self.profiles():
            return
        linked=[]
        for person in self.profiles():
            source=person.get("android_zip_source_id")
            if not isinstance(source,str) or not source:
                continue
            for archive in archives:
                if (person.get("id") in archive.get("profile_ids",[])
                        and source in archive.get("source_ids",[])):
                    linked.append((person["id"],source,archive.get("sha256","")))
        if not linked:
            return
        fingerprint=sha256(json.dumps(sorted(linked),separators=(",",":")).encode()).hexdigest()
        marker="_android_auto_recovery_0815"
        if self.data.get(marker)==fingerprint:
            return
        # A cópia é o ficheiro DPAPI original: não exporta dados em claro
        # nem necessita de pedir a palavra-passe de um backup .spbackup.
        if self.path.exists():
            recovery_dir=self.path.parent/"restores"
            recovery_dir.mkdir(mode=0o700,parents=True,exist_ok=True)
            copy_path=recovery_dir/("before-automatic-restore-"+fingerprint[:16]+".dpapi")
            if not copy_path.exists():
                fd,temp_name=tempfile.mkstemp(prefix=".auto_restore_",suffix=".tmp",
                                               dir=recovery_dir)
                try:
                    with os.fdopen(fd,"wb") as dst:
                        dst.write(self.path.read_bytes())
                        dst.flush()
                        os.fsync(dst.fileno())
                    os.replace(temp_name,copy_path)
                finally:
                    if os.path.exists(temp_name):
                        os.unlink(temp_name)
        # Inclui refeições, fotos, hidratação, sintomas, tomas, SOS e lares,
        # com associação estrita ao identificador Android de cada pessoa.
        self._automatic_android_recovery_summary=self.recover_android_modules()
        old=self.data.get(marker)
        self.data[marker]=fingerprint
        try:
            self.save()
        except Exception:
            if old is None:
                self.data.pop(marker,None)
            else:
                self.data[marker]=old
            raise

    def save(self):
        blob = _encrypt(json.dumps(self.data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        fd, temp_name = tempfile.mkstemp(prefix=".saudepratica_", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(blob); f.flush(); os.fsync(f.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def profiles(self):
        return self.data["profiles"]

    def important_links(self):
        """Installation-wide website shortcuts; defaults are removable and
        remain removed after an explicit empty-list save.
        """
        from windows.important_links_v087 import DEFAULT_LINKS, validated_links
        if "important_web_links" not in self.data:
            return validated_links(DEFAULT_LINKS)
        try:
            return validated_links(self.data["important_web_links"])
        except ValueError as exc:
            raise LocalStoreError("Lista de atalhos guardada inválida.") from exc

    def save_important_links(self, links):
        """Atomic update, compatible with the existing DPAPI backup payload."""
        from windows.important_links_v087 import validated_links
        try:
            cleaned = validated_links(links)
        except ValueError as exc:
            raise LocalStoreError(str(exc)) from exc
        previous = self.data.get("important_web_links")
        existed = "important_web_links" in self.data
        self.data["important_web_links"] = cleaned
        try:
            self.save()
        except Exception:
            if existed:
                self.data["important_web_links"] = previous
            else:
                self.data.pop("important_web_links",None)
            raise
        return cleaned

    def health_records(self, profile_id: str, kind: str) -> list[dict]:
        """Independent clinical/expense records for ONE valid profile."""
        import copy
        column = {"clinical": "clinical_records",
                  "expenses": "health_expenses"}.get(kind)
        if column is None:
            raise LocalStoreError("Módulo de saúde desconhecido.")
        profile = self.get_profile(profile_id)
        if not profile:
            raise LocalStoreError("Perfil não encontrado.")
        records = profile.get(column, [])
        if not isinstance(records, list):
            raise LocalStoreError("Dados do módulo inválidos.")
        return sorted((copy.deepcopy(r) for r in records
                       if isinstance(r, dict)),
                      key=lambda x: (str(x.get("date", "")),
                                     str(x.get("createdAt", ""))), reverse=True)

    def save_health_record(self, profile_id: str, kind: str,
                           fields: dict, record_id: str | None = None) -> dict:
        """Atomic upsert, profile-bounded IDs and attachments; no real data in logs."""
        import copy
        from datetime import datetime
        from windows.clinical_expenses_v088 import clinical_record, expense_record
        if kind not in ("clinical", "expenses"):
            raise LocalStoreError("Módulo inválido.")
        profile = self.get_profile(profile_id)
        if not profile:
            raise LocalStoreError("Perfil não encontrado.")
        try:
            cleaned = (clinical_record(fields) if kind == "clinical"
                       else expense_record(fields))
        except ValueError as exc:
            raise LocalStoreError(str(exc)) from exc
        digest = cleaned.get("document_sha256", "")
        if digest and not any(
            x.get("profile_id") == profile_id and x.get("sha256") == digest
            for x in self.data.get("imported_files", []) if isinstance(x, dict)
        ):
            raise LocalStoreError("Documento não associado a este perfil.")
        column = "clinical_records" if kind == "clinical" else "health_expenses"
        existing = profile.get(column, [])
        if not isinstance(existing, list):
            raise LocalStoreError("Registos existentes inválidos.")
        old = next((r for r in existing if isinstance(r, dict)
                    and r.get("id") == record_id), None) if record_id else None
        if record_id and old is None:
            raise LocalStoreError("Registo não encontrado no perfil selecionado.")
        now = datetime.now().isoformat(timespec="seconds")
        item = {
            "id": record_id or str(uuid.uuid4()),
            **cleaned,
            "createdAt": old.get("createdAt", now) if old else now,
            "updatedAt": now,
            "source": "windows_manual",
        }
        prior = self.data
        proposed = copy.deepcopy(prior)
        target = next(p for p in proposed["profiles"] if p.get("id") == profile_id)
        values = target.setdefault(column, [])
        if record_id:
            index = next(i for i,x in enumerate(values) if
                         isinstance(x, dict) and x.get("id") == record_id)
            values[index] = item
        else:
            values.append(item)
        try:
            self.data = proposed
            self.save()
        except Exception:
            self.data = prior
            raise
        return copy.deepcopy(item)

    def delete_health_record(self, profile_id: str, kind: str, record_id: str):
        """Delete only a record belonging to the requested profile."""
        import copy
        if kind not in ("clinical", "expenses"):
            raise LocalStoreError("Módulo inválido.")
        profile = self.get_profile(profile_id)
        if not profile:
            raise LocalStoreError("Perfil não encontrado.")
        column = "clinical_records" if kind == "clinical" else "health_expenses"
        records = profile.get(column, [])
        if not any(isinstance(r, dict) and r.get("id") == record_id
                   for r in records):
            raise LocalStoreError("Registo não encontrado neste perfil.")
        prior = self.data
        proposed = copy.deepcopy(prior)
        target = next(p for p in proposed["profiles"] if p.get("id") == profile_id)
        target[column] = [r for r in target.get(column, []) if
                          not (isinstance(r, dict) and r.get("id") == record_id)]
        try:
            self.data = proposed
            self.save()
        except Exception:
            self.data = prior
            raise

    def wellness_data(self, profile_id: str, kind: str):
        """Encrypted, deep-copied state of one profile; no implicit backfill.

        Returns defaults in memory only. Access to other profiles fails closed.
        """
        import copy
        from windows.wellness_models_v089 import (
            water_settings, cycle_settings, iso_date,
        )
        profile=self.get_profile(profile_id)
        if profile is None:
            raise LocalStoreError("Perfil não encontrado.")
        columns={"water":"wellness_water", "activity":"wellness_activity",
                 "cycle":"wellness_cycle"}
        if kind not in columns:
            raise LocalStoreError("Módulo de bem-estar desconhecido.")
        raw=copy.deepcopy(profile.get(columns[kind], {}))
        if not isinstance(raw,dict):
            raise LocalStoreError("Registos de bem-estar inválidos.")
        if kind=="water":
            try: config=water_settings(raw.get("settings",{}))
            except ValueError as exc:raise LocalStoreError(str(exc)) from exc
            entries=raw.get("entries",[])
            if not isinstance(entries,list):
                raise LocalStoreError("Histórico de água inválido.")
            return {"settings":config,"entries":entries}
        if kind=="cycle":
            try: config=cycle_settings(raw.get("settings",{}))
            except ValueError as exc:raise LocalStoreError(str(exc)) from exc
            periods=raw.get("periods",[])
            taken=raw.get("pill_taken",[])
            if not isinstance(periods,list) or not isinstance(taken,list):
                raise LocalStoreError("Histórico do ciclo inválido.")
            return {"settings":config,"periods":periods,"pill_taken":taken}
        entries=raw.get("entries",[])
        if not isinstance(entries,list):
            raise LocalStoreError("Histórico de atividade inválido.")
        return {"entries":entries}

    def _wellness_commit(self, profile_id: str, kind: str, mutate):
        """Single-profile atomic commit, retaining opaque Android metadata."""
        import copy
        columns={"water":"wellness_water","activity":"wellness_activity",
                 "cycle":"wellness_cycle"}
        if kind not in columns:
            raise LocalStoreError("Módulo inválido.")
        # Validate profile and copy existing state before modifying.
        current=self.wellness_data(profile_id,kind)
        proposed=copy.deepcopy(self.data)
        target=next(p for p in proposed["profiles"] if p.get("id")==profile_id)
        column=columns[kind]
        working=copy.deepcopy(current)
        try:
            result=mutate(working)
        except ValueError as exc:
            raise LocalStoreError(str(exc)) from exc
        target[column]=working
        old=self.data
        try:
            self.data=proposed
            self.save()
        except Exception:
            self.data=old
            raise
        return copy.deepcopy(result)

    def set_water_settings(self, profile_id: str, settings: dict):
        from windows.wellness_models_v089 import water_settings
        def mutate(state):
            state["settings"]=water_settings(settings)
            return state["settings"]
        return self._wellness_commit(profile_id,"water",mutate)

    def add_water(self, profile_id: str, day: str, hhmm: str, ml: int):
        import uuid
        from windows.wellness_models_v089 import water_record,water_total
        def mutate(state):
            record=water_record(day,hhmm,ml)
            if water_total(state["entries"],record["date"])+record["ml"]>100000:
                raise ValueError("O total diário registado é demasiado elevado.")
            item={"id":str(uuid.uuid4()),**record,"source":"windows_manual"}
            state["entries"].append(item)
            return item
        return self._wellness_commit(profile_id,"water",mutate)

    def remove_water(self, profile_id: str, record_id: str):
        def mutate(state):
            index=next((i for i,x in enumerate(state["entries"]) if
                        isinstance(x,dict) and x.get("id")==record_id),None)
            if index is None:raise ValueError("Registo de água não encontrado neste perfil.")
            return state["entries"].pop(index)
        return self._wellness_commit(profile_id,"water",mutate)

    def save_activity_day(self, profile_id: str, fields: dict):
        from windows.wellness_models_v089 import activity_record
        from datetime import datetime
        def mutate(state):
            record=activity_record(fields)
            existing=next((r for r in state["entries"] if
                          isinstance(r,dict) and r.get("date")==record["date"]),None)
            item={"id":existing["id"] if existing else str(uuid.uuid4()),
                  **record,
                  "updatedAt":datetime.now().isoformat(timespec="seconds")}
            if existing:
                index=state["entries"].index(existing)
                state["entries"][index]=item
            else:state["entries"].append(item)
            return item
        return self._wellness_commit(profile_id,"activity",mutate)

    def delete_activity_day(self, profile_id: str, day: str):
        from windows.wellness_models_v089 import iso_date
        def mutate(state):
            target=iso_date(day)
            index=next((i for i,r in enumerate(state["entries"])
                        if isinstance(r,dict) and r.get("date")==target),None)
            if index is None:raise ValueError("Registo deste dia não encontrado.")
            return state["entries"].pop(index)
        return self._wellness_commit(profile_id,"activity",mutate)

    def set_cycle_settings(self, profile_id: str, settings: dict):
        from windows.wellness_models_v089 import cycle_settings
        def mutate(state):
            state["settings"]=cycle_settings(settings)
            return state["settings"]
        return self._wellness_commit(profile_id,"cycle",mutate)

    def add_cycle_period(self, profile_id: str,
                         start: str, end: str, notes: str = ""):
        import uuid
        from windows.wellness_models_v089 import (
            period_record, ensure_no_period_overlap,
        )
        def mutate(state):
            row=period_record(start,end,notes)
            ensure_no_period_overlap(state["periods"],row)
            item={"id":str(uuid.uuid4()),**row}
            state["periods"].append(item)
            return item
        return self._wellness_commit(profile_id,"cycle",mutate)

    def delete_cycle_period(self, profile_id: str, period_id: str):
        def mutate(state):
            index=next((i for i,row in enumerate(state["periods"])
                        if isinstance(row,dict) and row.get("id")==period_id),None)
            if index is None:raise ValueError("Período não existe neste perfil.")
            return state["periods"].pop(index)
        return self._wellness_commit(profile_id,"cycle",mutate)

    def set_pill_taken(self, profile_id: str, day: str, taken: bool):
        from windows.wellness_models_v089 import iso_date, pill_scheduled
        from datetime import date
        def mutate(state):
            normalized=iso_date(day)
            if normalized>date.today().isoformat():
                raise ValueError("Não é possível confirmar pílulas futuras.")
            previous=normalized in state["pill_taken"]
            if taken and not pill_scheduled(normalized,state["settings"]):
                raise ValueError("Não existe uma toma prevista para este dia.")
            state["pill_taken"]=[
                x for x in state["pill_taken"] if x!=normalized]
            if taken:state["pill_taken"].append(normalized)
            return {"date":normalized,"taken":taken,"previous":previous}
        if not isinstance(taken,bool):
            raise LocalStoreError("Estado de toma inválido.")
        return self._wellness_commit(profile_id,"cycle",mutate)

    def remaining_records(self, profile_id: str, kind: str) -> list[dict]:
        """Private rows for one selected profile. Never aggregate family data."""
        import copy
        from windows.remaining_models_v0810 import SCHEMAS
        profile=self.get_profile(profile_id)
        if profile is None:raise LocalStoreError("Perfil inválido.")
        if kind not in SCHEMAS:raise LocalStoreError("Módulo inválido.")
        rows=profile.get(SCHEMAS[kind]["storage"],[])
        if not isinstance(rows,list):raise LocalStoreError("Histórico inválido.")
        return sorted([copy.deepcopy(x) for x in rows if isinstance(x,dict)],
                      key=lambda x:(str(x.get("date","")),str(x.get("updatedAt",""))),
                      reverse=True)

    def save_remaining_record(self, profile_id: str, kind: str,
                              fields: dict, record_id: str | None = None):
        import copy
        from datetime import datetime
        from windows.remaining_models_v0810 import SCHEMAS,validate_record
        profile=self.get_profile(profile_id)
        if profile is None or kind not in SCHEMAS:
            raise LocalStoreError("Perfil ou módulo inválido.")
        try:clean=validate_record(kind,fields)
        except ValueError as exc:raise LocalStoreError(str(exc)) from exc
        digest=clean.get("document_sha256","")
        if digest and not any(x.get("profile_id")==profile_id and
                              x.get("sha256")==digest
                              for x in self.imported_assets(profile_id)):
            raise LocalStoreError("Este documento não pertence ao perfil.")
        key=SCHEMAS[kind]["storage"]
        previous=profile.get(key,[])
        if not isinstance(previous,list):raise LocalStoreError("Dados inválidos.")
        old=next((x for x in previous if x.get("id")==record_id),None) if record_id else None
        if record_id and old is None:
            raise LocalStoreError("Registo não encontrado neste perfil.")
        now=datetime.now().isoformat(timespec="seconds")
        item={"id":record_id or str(uuid.uuid4()),**clean,
              "createdAt":old.get("createdAt",now) if old else now,
              "updatedAt":now,"source":"windows_manual"}
        target=copy.deepcopy(self.data)
        person=next(x for x in target["profiles"] if x.get("id")==profile_id)
        entries=person.setdefault(key,[])
        if old:
            index=next(i for i,x in enumerate(entries) if x.get("id")==record_id)
            entries[index]=item
        else:
            entries.append(item)
        before=self.data
        try:self.data=target;self.save()
        except Exception:
            self.data=before
            raise
        return copy.deepcopy(item)

    def delete_remaining_record(self,profile_id:str,kind:str,record_id:str):
        import copy
        from windows.remaining_models_v0810 import SCHEMAS
        current=self.remaining_records(profile_id,kind)
        if not any(x.get("id")==record_id for x in current):
            raise LocalStoreError("Registo não encontrado neste perfil.")
        key=SCHEMAS[kind]["storage"]
        target=copy.deepcopy(self.data)
        p=next(x for x in target["profiles"] if x.get("id")==profile_id)
        p[key]=[x for x in p.get(key,[]) if x.get("id")!=record_id]
        prior=self.data
        try:self.data=target;self.save()
        except Exception:
            self.data=prior
            raise

    def emergency_data(self,profile_id:str):
        import copy
        from windows.remaining_models_v0810 import validate_emergency
        p=self.get_profile(profile_id)
        if p is None:raise LocalStoreError("Perfil inválido.")
        raw=p.get("emergency_contact_data",{})
        try:return copy.deepcopy(validate_emergency(raw))
        except ValueError as exc:raise LocalStoreError(str(exc)) from exc

    def save_emergency_data(self,profile_id:str,fields:dict):
        import copy
        from windows.remaining_models_v0810 import validate_emergency
        if self.get_profile(profile_id) is None:
            raise LocalStoreError("Perfil inválido.")
        try:clean=validate_emergency(fields)
        except ValueError as exc:raise LocalStoreError(str(exc)) from exc
        target=copy.deepcopy(self.data)
        p=next(x for x in target["profiles"] if x.get("id")==profile_id)
        p["emergency_contact_data"]=clean
        before=self.data
        try:self.data=target;self.save()
        except Exception:
            self.data=before
            raise
        return copy.deepcopy(clean)

    def meal_records(self,profile_id:str):
        import copy
        p=self.get_profile(profile_id)
        if p is None:raise LocalStoreError("Perfil inválido.")
        items=p.get("meal_records",[])
        if not isinstance(items,list):raise LocalStoreError("Diário alimentar inválido.")
        return sorted([copy.deepcopy(x) for x in items if isinstance(x,dict)],
                      key=lambda x:(str(x.get("date","")),str(x.get("clock",""))),
                      reverse=True)

    def meal_photo(self,profile_id:str,record_id:str):
        item=next((x for x in self.meal_records(profile_id)
                   if x.get("id")==record_id),None)
        if item is None:raise LocalStoreError("Refeição não encontrada neste perfil.")
        digest=item.get("photo_sha256","")
        if not digest:return None
        descriptor=next((x for x in self.imported_assets(profile_id) if
                         x.get("sha256")==digest),None)
        if descriptor is None:raise LocalStoreError("Fotografia não pertence ao perfil.")
        return self.read_imported_asset(descriptor)

    def save_meal(self, profile_id:str,fields:dict,record_id:str|None=None,
                  picture:bytes|None=None):
        from windows.remaining_models_v0810 import validate_meal,normalize_date
        import copy
        from hashlib import sha256
        from io import BytesIO
        from PIL import Image
        from datetime import datetime
        p=self.get_profile(profile_id)
        if p is None:raise LocalStoreError("Perfil inválido.")
        try:
            details=validate_meal(fields)
            date_value=normalize_date(fields.get("date",""))
            when=str(fields.get("clock","")).strip()
            datetime.strptime(when,"%H:%M")
        except (ValueError,TypeError) as exc:
            raise LocalStoreError(str(exc)) from exc
        prev=next((x for x in self.meal_records(profile_id)
                   if x.get("id")==record_id),None) if record_id else None
        if record_id and prev is None:
            raise LocalStoreError("Refeição não pertence a este perfil.")
        photo_digest=prev.get("photo_sha256","") if prev else ""
        assets=[]
        descriptors=[]
        if picture is not None:
            if not isinstance(picture,bytes) or len(picture)>8*1024*1024 or len(picture)<64:
                raise LocalStoreError("Fotografia inválida ou demasiado grande.")
            try:
                with Image.open(BytesIO(picture)) as image:
                    if image.format not in ("JPEG","PNG","WEBP") or image.width*image.height>25_000_000:
                        raise ValueError("Imagem não suportada.")
                    image.verify()
            except (OSError,ValueError) as exc:
                raise LocalStoreError("Fotografia inválida.") from exc
            photo_digest=sha256(picture).hexdigest()
            assets=[(photo_digest,picture)]
            if not any(x.get("profile_id")==profile_id and
                       x.get("sha256")==photo_digest for x in self.imported_assets(profile_id)):
                descriptors=[{"profile_id":profile_id,
                    "path":f"meal_photos/{profile_id}/{photo_digest}.bin",
                    "filename":photo_digest+".jpg","display_name":"Fotografia de refeição",
                    "category":"fotografia de refeição","sha256":photo_digest,
                    "bytes":len(picture)}]
        now=datetime.now().isoformat(timespec="seconds")
        item={"id":record_id or str(uuid.uuid4()),**details,
              "date":date_value,"clock":when,
              "photo_sha256":photo_digest,
              "source":prev.get("source","windows_manual") if prev else "windows_manual",
              "createdAt":prev.get("createdAt",now) if prev else now,
              "updatedAt":now}
        if prev:
            for preserved in ("android_source","android_id","android_at","estimated"):
                if preserved in prev:item[preserved]=prev[preserved]
        target=copy.deepcopy(self.data)
        person=next(x for x in target["profiles"] if x.get("id")==profile_id)
        rows=person.setdefault("meal_records",[])
        if prev:
            i=next(i for i,x in enumerate(rows) if x.get("id")==record_id)
            rows[i]=item
        else:rows.append(item)
        target.setdefault("imported_files",[]).extend(descriptors)
        created=self._write_assets(assets)
        before=self.data
        try:
            self.data=target
            self.save()
        except Exception:
            self.data=before
            for file in created:
                try:file.unlink()
                except OSError:pass
            raise
        return copy.deepcopy(item)

    def delete_meal(self,profile_id:str,record_id:str):
        import copy
        if not any(x.get("id")==record_id for x in self.meal_records(profile_id)):
            raise LocalStoreError("Refeição não encontrada neste perfil.")
        target=copy.deepcopy(self.data)
        p=next(x for x in target["profiles"] if x.get("id")==profile_id)
        p["meal_records"]=[x for x in p.get("meal_records",[]) if x.get("id")!=record_id]
        old=self.data
        try:self.data=target;self.save()
        except Exception:self.data=old;raise

    def import_meal_diary_android(self, profile_id:str):
        """Read linked Android backup without asking for another upload.

        Only the linked profile index and its original JPEGs are selected.
        Existing meal entries are never replaced; reimport is idempotent.
        """
        import copy
        from windows.meal_android_import_v0810 import extract_meal_diary
        from windows.android_archive_v063 import AndroidImportError
        p=self.get_profile(profile_id)
        if p is None:raise LocalStoreError("Perfil inválido.")
        source=p.get("android_zip_source_id")
        if not source:raise LocalStoreError(
            "Este perfil ainda não está associado a um backup Android.")
        matching=[a for a in self.android_archives()
                  if profile_id in a.get("profile_ids",[]) and
                  source in a.get("source_ids",[])]
        if not matching:raise LocalStoreError(
            "Não existe um backup Android deste perfil guardado no Windows.")
        rows=[];photos=[]
        # An archive older than the diary may contain none; newer archives
        # are inspected too, and every source-specific ID is deduplicated.
        for archive in matching:
            original=self.read_imported_asset({"sha256":archive["sha256"]})
            try:
                part,assets=extract_meal_diary(original,source)
            except (ValueError,AndroidImportError) as exc:
                raise LocalStoreError("Histórico Android inválido: "+str(exc)) from exc
            rows.extend(part);photos.extend(assets)
        known={x.get("id") for x in self.meal_records(profile_id)}
        fresh=[]
        for row in rows:
            if row["id"] not in known:
                known.add(row["id"])
                fresh.append(row)
        allowed_hashes={row.get("photo_sha256") for row in fresh}
        unique={}
        for digest,data,name in photos:
            if digest in allowed_hashes:
                unique[digest]=(data,name)
        descriptors=[]
        existing={(x.get("profile_id"),x.get("sha256"))
                  for x in self.data.get("imported_files",[])}
        blobs=[]
        for digest,(data,name) in unique.items():
            if (profile_id,digest) not in existing:
                descriptors.append({"profile_id":profile_id,
                    "path":f"android_meals/{source}/{name}",
                    "filename":name,"display_name":"Refeição Android",
                    "category":"fotografia de refeição",
                    "sha256":digest,"bytes":len(data),
                    "android_source":source})
                blobs.append((digest,data))
        target=copy.deepcopy(self.data)
        person=next(x for x in target["profiles"] if x.get("id")==profile_id)
        person.setdefault("meal_records",[]).extend(fresh)
        target.setdefault("imported_files",[]).extend(descriptors)
        created=self._write_assets(blobs)
        before=self.data
        try:self.data=target;self.save()
        except Exception:
            self.data=before
            for file in created:
                try:file.unlink()
                except OSError:pass
            raise
        return {"added":len(fresh),"photos":len(descriptors),
                "available":len(rows)}

    def import_android_sos_lares(self, profile_id: str, kind: str):
        """Idempotent explicit import from the matching encrypted Android ZIP.

        SOS: fill only empty Windows fields. Care: add only missing stable
        records; never replace independently edited Windows entries.
        """
        import copy
        from windows.android_sos_lares_v0811 import extract_sos_care
        from windows.android_archive_v063 import AndroidImportError
        from windows.remaining_models_v0810 import validate_emergency
        if kind not in ("sos", "care"):
            raise LocalStoreError("Módulo a importar inválido.")
        p=self.get_profile(profile_id)
        if p is None:
            raise LocalStoreError("Perfil Windows inválido.")
        source=p.get("android_zip_source_id")
        if not isinstance(source,str) or not source:
            raise LocalStoreError("O perfil não tem origem Android associada. "
                "Importa primeiro o backup familiar Android.")
        relevant=[x for x in self.android_archives()
                  if profile_id in x.get("profile_ids",[]) and
                  source in x.get("source_ids",[])]
        if not relevant:
            raise LocalStoreError(
                "Ainda não existe neste Windows um backup Android para este perfil.")
        # Inspect only already linked archives; latest backup takes priority.
        sos={}
        institutions=[]
        invoices=[]
        seen_i=set()
        seen_m=set()
        for archive in reversed(relevant):
            raw=self.read_imported_asset({"sha256":archive["sha256"]})
            try:
                data=extract_sos_care(raw,source)
            except (AndroidImportError,ValueError) as exc:
                raise LocalStoreError("Falhou a leitura do backup Android: "+str(exc)) from exc
            for key,value in data["sos"].items():
                if value and not sos.get(key):sos[key]=value
            for row in data["residences"]:
                if row["id"] not in seen_i:
                    institutions.append(row)
                    seen_i.add(row["id"])
            for row in data["residence_invoices"]:
                if row["id"] not in seen_m:
                    invoices.append(row)
                    seen_m.add(row["id"])
        prior=self.data
        proposed=copy.deepcopy(prior)
        target=next(x for x in proposed["profiles"] if x.get("id")==profile_id)
        summary={"sos_fields":0,"residences":0,"invoices":0,
                 "available_sos":sum(bool(x) for x in sos.values()),
                 "available_residences":len(institutions),
                 "available_invoices":len(invoices)}
        if kind=="sos":
            existing=validate_emergency(target.get("emergency_contact_data",{}))
            for key,value in sos.items():
                if value and not existing.get(key):
                    existing[key]=value
                    summary["sos_fields"]+=1
            target["emergency_contact_data"]=existing
            target["emergency_android_source"]=source
        else:
            for collection,records,label in (
                ("residence_records",institutions,"residences"),
                ("residence_invoices",invoices,"invoices"),
            ):
                current=target.setdefault(collection,[])
                if not isinstance(current,list):
                    raise LocalStoreError("Registos Windows inválidos.")
                ids={x.get("id") for x in current if isinstance(x,dict)}
                # Prevent duplicate monthly bills after earlier manual
                # entry of the same institution and month.
                def same_entry(a,b):
                    if collection=="residence_records":
                        return str(a.get("title","")).casefold().strip()==str(
                            b.get("title","")).casefold().strip()
                    return (str(a.get("date",""))[:7]==str(b.get("date",""))[:7]
                            and str(a.get("title","")).casefold().strip()==str(
                                b.get("title","")).casefold().strip())
                for row in records:
                    if row["id"] in ids or any(
                        isinstance(x,dict) and same_entry(x,row) for x in current):
                        continue
                    current.append(copy.deepcopy(row))
                    ids.add(row["id"])
                    summary[label]+=1
        try:
            self.data=proposed
            self.save()
        except Exception:
            self.data=prior
            raise
        return summary

    def recover_android_modules(self, profile_id: str | None = None):
        """Convert original Android family ZIP already stored under DPAPI.

        Atomic, additive, repeatable. Existing Windows edits, family
        medication/agenda, linked patients and protected originals stay intact.
        """
        import copy
        from windows.android_full_restore_v0813 import (
            extract_profile_android,merge_snapshot,
        )
        targets=([self.get_profile(profile_id)] if profile_id is not None
                 else list(self.profiles()))
        if not targets or any(p is None for p in targets):
            raise LocalStoreError("Seleciona um perfil existente.")
        source_to_target={
            p.get("android_zip_source_id"):p["id"]
            for p in self.profiles()
            if isinstance(p.get("android_zip_source_id"),str)
            and p.get("android_zip_source_id")
        }
        previous=self.data
        proposed=copy.deepcopy(previous)
        metadata=list(proposed.get("imported_files",[]))
        assets=[]
        counts={"meals":0,"meal_photos":0,"water":0,"symptoms":0,
                "intakes":0,"measurements":0,"health_connect":0,
                "manual_body":0,"sos":0,"residences":0,"invoices":0}
        linked=0
        for current in targets:
            pid=current["id"]
            source=current.get("android_zip_source_id")
            if not source:
                continue
            archives=[a for a in self.android_archives()
                      if pid in a.get("profile_ids",[]) and
                      source in a.get("source_ids",[])]
            if not archives:
                continue
            profile=next(p for p in proposed["profiles"] if p.get("id")==pid)
            linked+=1
            for archive in archives:
                original=self.read_imported_asset({"sha256":archive["sha256"]})
                try:
                    snapshot=extract_profile_android(original,source)
                    new_meta,new_assets,summary=merge_snapshot(
                        profile,snapshot,source_to_target,metadata)
                except ValueError as exc:
                    raise LocalStoreError("Origem Android inválida: "+str(exc)) from exc
                metadata.extend(new_meta)
                assets.extend(new_assets)
                for key,value in summary.items():
                    counts[key]+=value
        if not linked:
            raise LocalStoreError(
                "Não há nenhum backup Android original associado a estes perfis. "
                "Importa primeiro o backup completo do Android.")
        proposed["imported_files"]=metadata
        created=self._write_assets(assets)
        try:
            self.data=proposed
            self.save()
        except Exception:
            self.data=previous
            for path in created:
                try:path.unlink()
                except OSError:pass
            raise
        return {"profiles":linked,"android_modules":counts}

    def create_profile(self, name: str):
        name = name.strip()
        if not 1 <= len(name) <= 120:
            raise LocalStoreError("Indica um nome entre 1 e 120 caracteres.")
        profile = {"id": str(uuid.uuid4()), "name": name,
                   "medications": [], "appointments": []}
        self.data["profiles"].append(profile)
        self.save()
        return profile

    def get_profile(self, profile_id: str):
        return next((p for p in self.profiles() if p.get("id") == profile_id), None)

    def delete_profile(self, profile_id: str) -> dict:
        """User-confirmed profile deletion. Persist atomically before removing orphan assets.

        Other family members, their documents, and the original encrypted
        family archive are preserved. Never erase shared-content blobs.
        """
        import copy
        current=self.get_profile(profile_id)
        if current is None:
            raise LocalStoreError("O perfil já não existe.")
        previous=self.data
        proposed=copy.deepcopy(previous)
        proposed["profiles"]=[p for p in proposed["profiles"] if p.get("id")!=profile_id]
        attachments=proposed.get("imported_files",[])
        proposed["imported_files"]=[
            x for x in attachments if x.get("profile_id")!=profile_id]
        settings=proposed.get("settings")
        if isinstance(settings,dict) and settings.get("active_profile")==profile_id:
            settings["active_profile"]=(
                proposed["profiles"][0]["id"] if proposed["profiles"] else None)
        # Original family ZIPs contain other family members. Keep them encrypted,
        # but do not advertise the deleted profile as an active import destination.
        for archive in proposed.get("android_family_archives",[]):
            archive["profile_ids"]=[
                pid for pid in archive.get("profile_ids",[]) if pid!=profile_id]
        remaining={x.get("sha256") for x in proposed["imported_files"]}
        remaining.update(x.get("sha256") for x in
                         proposed.get("android_family_archives",[]))
        released={x.get("sha256") for x in attachments
                  if x.get("profile_id")==profile_id}
        try:
            self.data=proposed
            self.save()
        except Exception:
            self.data=previous
            raise
        # Only prune encrypted files unreferenced by ANY other profile/archive.
        for digest in released-remaining:
            try:self._asset_path(digest).unlink(missing_ok=True)
            except (LocalStoreError,OSError):pass
        return {"id":profile_id,"name":current.get("name",""),
                "remaining":len(proposed["profiles"]),
                "next_active":proposed.get("settings",{}).get("active_profile")}

    def settings(self):
        """Local preferences only; no new database or migration required."""
        return dict(self.data.get("settings") or {})

    def update_settings(self, **values):
        allowed = {"theme", "language", "active_profile"}
        if not set(values).issubset(allowed):
            raise LocalStoreError("Preferência desconhecida.")
        current = self.settings()
        current.update(values)
        if current.get("theme", "system") not in {"system", "dark", "light"}:
            raise LocalStoreError("Tema desconhecido.")
        if current.get("language", "pt") not in {"pt", "en", "fr", "de", "es"}:
            raise LocalStoreError("Idioma desconhecido.")
        chosen = current.get("active_profile")
        if chosen and not self.get_profile(chosen):
            raise LocalStoreError("Perfil não encontrado.")
        old = self.data.get("settings")
        self.data["settings"] = current
        try:
            self.save()
        except Exception:
            if old is None: self.data.pop("settings", None)
            else: self.data["settings"] = old
            raise
        return current

    def save_profile(self, fields: dict, profile_id: str | None = None):
        """Version-compatible profile editor with rollback and no unknown-field loss."""
        from datetime import date
        import base64
        if not isinstance(fields, dict):
            raise LocalStoreError("Dados do perfil inválidos.")
        name = str(fields.get("name", "")).strip()
        if not (1 <= len(name) <= 120):
            raise LocalStoreError("Indica um nome de 1 a 120 caracteres.")
        allowed_fields = {
            "name": 120, "birth_date": 10, "phone": 50, "email": 160,
            "niss": 40, "health_unit": 180, "address": 250, "city": 100,
            "postal_code": 24,
            "full_name": 160, "gender": 40, "height": 16,
            "nationality": 80, "birth_place": 120,
            "father": 160, "mother": 160, "nif": 24,
            "sns_number": 40, "adse_number": 50,
            "cc_number": 40, "cc_valid_until": 24,
            "notes": 3000, "photo_b64": 600000
        }
        cleaned = {}
        for key, limit in allowed_fields.items():
            value = fields.get(key, "")
            if not isinstance(value, str) or len(value) > limit:
                raise LocalStoreError("Campo do perfil inválido: " + key)
            cleaned[key] = value.strip() if key != "photo_b64" else value
        if cleaned["birth_date"]:
            try:
                if date.fromisoformat(cleaned["birth_date"]) > date.today():
                    raise ValueError("future")
            except ValueError as exc:
                raise LocalStoreError("A data de nascimento deve ser AAAA-MM-DD e não pode ser futura.") from exc
        if cleaned["photo_b64"]:
            try:
                photo = base64.b64decode(cleaned["photo_b64"], validate=True)
                if not photo.startswith(b"\xff\xd8\xff") or len(photo) > 450000:
                    raise ValueError("photo format")
            except Exception as exc:
                raise LocalStoreError("A fotografia deve ser JPEG válido e pequeno.") from exc
        cleaned["caregiver"] = bool(fields.get("caregiver", False))
        if profile_id:
            from windows.profile_data_guard_v075 import overlaps_medication
            old_person=self.get_profile(profile_id)
            if old_person and overlaps_medication(old_person,cleaned.get("notes")):
                # The original drug record retains this data.
                cleaned["notes"] = ""
        if profile_id:
            old = self.get_profile(profile_id)
            if old is None:
                raise LocalStoreError("Perfil inexistente.")
            new = dict(old)
            new.update(cleaned)
            index = self.data["profiles"].index(old)
            self.data["profiles"][index] = new
        else:
            new = {"id": str(uuid.uuid4()), "medications": [], "appointments": []}
            new.update(cleaned)
            self.data["profiles"].append(new)
        try:
            self.save()
        except Exception:
            if profile_id:
                self.data["profiles"][index] = old
            else:
                self.data["profiles"].pop()
            raise
        return new

    def save_appointment(self, profile_id: str, fields: dict,
                         appointment_id: str | None = None):
        """Persist the Windows appointment editor atomically.

        No Android synchronization, SMS or external medical cancellation is
        implied. Existing record IDs and android_original metadata are immutable.
        """
        from windows.appointment_editor_v070 import clean_appointment_fields
        profile=self.get_profile(profile_id)
        if profile is None:raise LocalStoreError("Perfil não encontrado.")
        appointments=profile.get("appointments",[])
        if not isinstance(appointments,list):
            raise LocalStoreError("A Agenda do perfil tem um formato inválido.")
        old=next((x for x in appointments if x.get("id")==appointment_id),
                 None) if appointment_id else None
        if appointment_id and old is None:
            raise LocalStoreError("A marcação já não existe.")
        try:cleaned=clean_appointment_fields(fields,old)
        except (ValueError,TypeError) as exc:raise LocalStoreError(str(exc)) from exc
        if cleaned.get("document_asset_sha256"):
            from windows.medication_editor_v080 import (
                medication_document_assets, medication_document_option)
            assets=medication_document_assets(self.imported_assets(profile_id))
            if medication_document_option(assets,cleaned["document_asset_sha256"]) is None:
                raise LocalStoreError("Documento da marcação não pertence a este perfil.")
        new=dict(old) if old else {"id":str(uuid.uuid4())}
        new.update(cleaned)
        if "desktop_status" in cleaned:
            new["status"]=cleaned["desktop_status"]
            # Keep the Android original intact, but let local status override
            # historical cancelled/done flags on future desktop edits.
        if old is not None:
            idx=appointments.index(old)
            appointments[idx]=new
        else:
            appointments.append(new)
        try:self.save()
        except Exception:
            if old is not None:appointments[idx]=old
            else:appointments.pop()
            raise
        return new

    def confirm_intake(self, profile_id: str, medication_id: str,
                       confirmed_at: str | None = None,
                       scheduled_at: str | None = None):
        """Explicit confirmed dose for ONE selected profile; never from a reminder.

        Planned slots are checked against the person's real medication schedule;
        ad-hoc/SOS doses have no scheduled slot and require an explicit click.
        """
        from datetime import datetime, timedelta
        from windows.doses_calendar_v085 import expected_slots

        profile = self.get_profile(profile_id)
        if profile is None:
            raise LocalStoreError("Perfil não encontrado.")
        med = next((m for m in profile.get("medications", [])
                    if isinstance(m, dict) and m.get("id") == medication_id), None)
        if med is None:
            raise LocalStoreError("Este medicamento não pertence ao perfil selecionado.")
        try:
            timestamp = datetime.fromisoformat(confirmed_at) if confirmed_at else datetime.now()
        except (ValueError, TypeError) as exc:
            raise LocalStoreError("Data/hora de toma inválida.") from exc
        if timestamp.tzinfo is not None:
            raise LocalStoreError("Usa uma hora local sem fuso horário.")
        if not 2000 <= timestamp.year <= 9999 or timestamp > datetime.now() + timedelta(minutes=5):
            raise LocalStoreError("Data/hora de confirmação fora do intervalo.")
        planned = None
        if scheduled_at:
            try:
                planned = datetime.fromisoformat(scheduled_at)
            except (TypeError, ValueError) as exc:
                raise LocalStoreError("Hora programada inválida.") from exc
            if planned.tzinfo is not None or not any(
                slot["scheduled_at"] == planned.isoformat(timespec="minutes") and
                slot["medication_id"] == medication_id
                for slot in expected_slots(profile, planned.date())
            ):
                raise LocalStoreError("A toma prevista não está associada a este perfil.")
        records = profile.setdefault("intakes", [])
        if not isinstance(records, list):
            raise LocalStoreError("Histórico de tomas inválido.")
        scheduled_key = planned.isoformat(timespec="minutes") if planned else ""
        if scheduled_key and any(
            r.get("medication_id") == medication_id and
            r.get("scheduled_at") == scheduled_key and
            r.get("status") == "confirmed"
            for r in records if isinstance(r, dict)
        ):
            raise LocalStoreError("Esta toma prevista já está confirmada.")
        moment = timestamp.isoformat(timespec="seconds")
        if not scheduled_key and any(
            r.get("medication_id") == medication_id and
            r.get("confirmed_at") == moment and
            r.get("status") == "confirmed"
            for r in records if isinstance(r, dict)
        ):
            raise LocalStoreError("Esta confirmação já está registada.")
        item = {
            "id": str(uuid.uuid4()),
            "medication_id": medication_id,
            "medication": str(med.get("name") or "Medicação"),
            "dose": str(med.get("dose") or ""),
            "scheduled_at": scheduled_key,
            "confirmed_at": moment,
            "source": "windows_explicit",
            "status": "confirmed",
        }
        records.append(item)
        try:
            self.save()
        except Exception:
            records.pop()
            raise
        return item

    def delete_intake(self, profile_id: str, intake_id: str):
        """Remove a confirmed history record only after explicit UI consent."""
        profile = self.get_profile(profile_id)
        if profile is None:
            raise LocalStoreError("Perfil não encontrado.")
        records = profile.get("intakes", [])
        if not isinstance(records, list):
            raise LocalStoreError("Histórico de tomas inválido.")
        found = next((i for i,r in enumerate(records) if
                      isinstance(r, dict) and r.get("id") == intake_id), None)
        if found is None:
            raise LocalStoreError("Toma não encontrada neste perfil.")
        prior = records.pop(found)
        try:
            self.save()
        except Exception:
            records.insert(found, prior)
            raise

    def add_medication(self, profile_id: str, name: str, dose: str, time: str, route: str):
        """Compatibility with records saved by the first experimental build."""
        return self.save_medication(profile_id, {
            "name": name, "dose": dose, "time": time,
            "administration_route": route,
            "no_alarm": not bool(time.strip()),
        })

    def save_medication(self, profile_id: str, fields: dict, medication_id: str | None = None):
        """Create/update without dropping unknown fields or existing attachments.

        Clinical time is recorded for later sync; no Windows alarm is scheduled.
        """
        p = self.get_profile(profile_id)
        if p is None:
            raise LocalStoreError("Perfil não encontrado.")
        if not isinstance(fields, dict):
            raise LocalStoreError("Os dados da medicação são inválidos.")

        route = str(fields.get("administration_route", "")).strip().lower()
        allowed_routes = ("", "oral", "sublingual", "parenteral", "topical",
                          "inhaled", "rectal", "vaginal", "ocular", "otic", "nasal", "other")
        if route not in allowed_routes:
            raise LocalStoreError("Seleciona uma via de administração válida.")
        injection = str(fields.get("injection_type", "")).lower().strip()
        if injection not in ("", "sc", "im", "iv", "id", "other"):
            raise LocalStoreError("O tipo de injeção é inválido.")
        if route != "parenteral":
            injection = ""

        name = str(fields.get("name", "")).strip()
        dose = str(fields.get("dose", "")).strip()
        time = str(fields.get("time", "")).strip()
        indication = str(fields.get("indication", "")).strip()
        notes = str(fields.get("notes", "")).strip()
        dose_pattern = str(fields.get("dose_pattern", "")).strip()
        if not 1 <= len(name) <= 160 or len(dose) > 90:
            raise LocalStoreError("Indica o nome e uma dose com até 90 caracteres.")
        if len(indication) > 2000 or len(notes) > 4000:
            raise LocalStoreError("O texto da indicação ou das notas é demasiado longo.")
        # Windows is currently a medication catalogue, NOT an alarm scheduler.
        # Android may encode a time as "Jejum" or a schedule in separate JSON.
        # Never force existing records to fabricate HH:mm, route, frequency or
        # dose simply to change their suspended/active status.
        if len(time)>100 or len(dose_pattern)>120:
            raise LocalStoreError("Campo da medicação demasiado comprido.")
        from windows.medication_flags_v076 import CLOCK
        reminder_supplied="reminder_time" in fields
        reminder_time=str(fields.get("reminder_time","")).strip()
        if reminder_supplied and reminder_time and not CLOCK.fullmatch(reminder_time):
            raise LocalStoreError("A hora de aviso deve ser HH:MM, por exemplo 07:00.")
        if reminder_supplied and CLOCK.fullmatch(time) and time!=reminder_time:
            raise LocalStoreError(
                "Existem duas horas diferentes. Altera a Hora de aviso e guarda novamente.")
        no_alarm = bool(fields.get("no_alarm", False)) or dose_pattern == "SOS"
        # The desktop may save an authentic photo of the medication package.
        # Keep legacy image/attachment fields untouched when the editor does
        # not supply a new photo, and never store unbounded or fake thumbnails.
        import base64
        supplied_photo = "photo_b64" in fields
        photo_b64 = fields.get("photo_b64", "")
        if supplied_photo:
            if not isinstance(photo_b64, str) or len(photo_b64) > 600000:
                raise LocalStoreError("Fotografia da medicação demasiado grande.")
            if photo_b64:
                try:
                    raw = base64.b64decode(photo_b64, validate=True)
                except Exception as exc:
                    raise LocalStoreError("Fotografia da medicação inválida.") from exc
                if not raw.startswith(bytes((0xff, 0xd8, 0xff))) or len(raw)>450000:
                    raise LocalStoreError("A fotografia deve ser JPEG válido e até 450 kB.")
        suspended = bool(fields.get("suspended", False))

        old = next((m for m in p["medications"] if m.get("id") == medication_id), None) if medication_id else None
        if medication_id and old is None:
            raise LocalStoreError("O medicamento já não está disponível neste perfil.")
        from windows.medication_editor_v080 import (
            ALL_FIELDS, DOC_KEYS, apply_extras, medication_document_assets,
            medication_document_option,
        )
        optional={key:fields[key] for key in ALL_FIELDS if key in fields}
        try:
            validated_extras=apply_extras(old,optional)
        except ValueError as exc:
            raise LocalStoreError(str(exc)) from exc
        allowed=medication_document_assets(self.imported_assets(profile_id))
        selected={}
        for key in DOC_KEYS:
            if key not in fields:continue
            digest=fields[key]
            if not isinstance(digest,str) or (
                    digest and not medication_document_option(allowed,digest)):
                raise LocalStoreError("Documento da medicação não pertence a este perfil.")
            selected[key]=digest
        new = dict(old) if old else {"id": str(uuid.uuid4())}
        new.update(validated_extras)
        new.update(selected)
        new.update({
            "name": name, "dose": dose, "time": time,
            "administration_route": route, "injection_type": injection,
            "dose_pattern": dose_pattern, "indication": indication, "notes": notes,
            "no_alarm": no_alarm, "suspended": suspended,
        })
        if reminder_supplied:
            new["reminder_time"]=reminder_time
        if supplied_photo:
            new["photo_b64"] = photo_b64
        if old is None:
            p["medications"].append(new)
        else:
            index = p["medications"].index(old)
            p["medications"][index] = new
        try:
            self.save()
        except Exception:
            if old is None:
                p["medications"].pop()
            else:
                p["medications"][index] = old
            raise
        return new

    def imported_assets(self, profile_id: str):
        return [dict(i) for i in self.data.get("imported_files",[])
                if i.get("profile_id")==profile_id]

    def import_local_document(self,profile_id:str,source_path:Path):
        from hashlib import sha256
        path=Path(source_path)
        if path.suffix.lower() not in {".pdf",".jpg",".jpeg",".png",".webp"}:
            raise LocalStoreError("Só PDF e imagens são aceites.")
        if not path.is_file() or path.stat().st_size>16*1024*1024:
            raise LocalStoreError("Documento inexistente ou superior a 16 MB.")
        if self.get_profile(profile_id) is None:
            raise LocalStoreError("Perfil de destino inválido.")
        raw=path.read_bytes()
        digest=sha256(raw).hexdigest()
        entries=self.data.get("imported_files",[])
        if any(x.get("profile_id")==profile_id and
               x.get("sha256")==digest for x in entries):
            return False
        descriptor={"profile_id":profile_id,"path":"manual/"+digest+"/"+path.name,
                    "filename":path.name,"display_name":path.stem,
                    "category":"documento manual","sha256":digest,"bytes":len(raw)}
        created=self._write_assets([(digest,raw)])
        self.data["imported_files"]=entries+[descriptor]
        try:self.save()
        except Exception:
            self.data["imported_files"]=entries
            for file in created:
                try:file.unlink()
                except OSError:pass
            raise
        return True

    def _asset_path(self, digest):
        import re
        if not isinstance(digest,str) or not re.fullmatch(r"[a-f0-9]{64}",digest):
            raise LocalStoreError("Identificador do documento inválido.")
        root=self.path.parent/"protected_assets"
        root.mkdir(parents=True,exist_ok=True)
        return root/(digest+".dpapi")

    def read_imported_asset(self, entry):
        from hashlib import sha256
        digest=entry["sha256"]
        path=self._asset_path(digest)
        data=_decrypt(path.read_bytes())
        if sha256(data).hexdigest()!=digest:
            raise LocalStoreError("O documento guardado falhou a verificação de integridade.")
        return data

    def _write_assets(self, assets):
        """Validated (hash, data) pairs -> encrypted DPAPI files (atomic writes)."""
        from hashlib import sha256
        newly=[]
        try:
            for digest,data in assets:
                if sha256(data).hexdigest()!=digest:
                    raise LocalStoreError("Integridade da fotografia/documento inválida.")
                path=self._asset_path(digest)
                if path.exists():
                    # Never trust an existing blob solely because its filename
                    # matches the digest. A damaged DPAPI file must block the
                    # restore before any profile/metadata are committed.
                    try:
                        current=_decrypt(path.read_bytes())
                        if sha256(current).hexdigest()!=digest:
                            raise LocalStoreError("Um anexo já guardado está corrompido.")
                    except Exception as exc:
                        raise LocalStoreError(
                            "Anexo protegido existente ilegível ou corrompido. "
                            "Os dados atuais não foram alterados.") from exc
                    continue
                fd,tmp=tempfile.mkstemp(prefix=".asset_",suffix=".tmp",dir=path.parent)
                try:
                    with os.fdopen(fd,"wb") as stream:
                        stream.write(_encrypt(data))
                        stream.flush()
                        os.fsync(stream.fileno())
                    # A single Windows user owns the storage; no plain temporary files.
                    os.replace(tmp,path)
                    newly.append(path)
                finally:
                    if os.path.exists(tmp):os.unlink(tmp)
        except Exception:
            for p in newly:
                try:p.unlink()
                except OSError:pass
            raise
        return newly

    def import_android_archive(self, plan):
        """All-or-nothing metadata+clinical commit, with encrypted attachments."""
        from windows.android_import_v062 import _existing_map,AndroidImportError
        import copy
        from pathlib import PurePosixPath
        p=self.get_profile(plan.profile_id)
        if p is None:raise AndroidImportError("Perfil Windows de destino inexistente.")
        if p.get("android_zip_source_id") not in (None,"",plan.source.identifier):
            raise AndroidImportError("O perfil Windows está ligado a outra origem Android.")
        for cat,part in (("medications",plan.medications),("appointments",plan.appointments)):
            existing=_existing_map(p.get(cat,[]),cat)
            if any(item["android_source_key"] in existing for item in part.new):
                raise AndroidImportError("Registos alterados desde a pré-visualização. Importa novamente.")
        previous_med=p.get("medications",[])
        previous_apt=p.get("appointments",[])
        previous_files=self.data.get("imported_files",[])
        old_source=p.get("android_zip_source_id")
        old_source_name=p.get("android_zip_source_name")
        old_avatar=p.get("photo_b64")
        descriptors=list(previous_files)
        known={(x.get("profile_id"),x.get("path"),x.get("sha256"))
               for x in previous_files}
        assets=[]
        for name,data,category,digest,display_name in plan.attachments:
            key=(p["id"],name,digest)
            if key in known:
                # A repeated import must not claim success if the original
                # protected attachment has since become unreadable.
                prior=next(x for x in previous_files if (
                    x.get("profile_id"),x.get("path"),x.get("sha256"))==key)
                try:self.read_imported_asset(prior)
                except Exception as exc:
                    raise AndroidImportError(
                        "Um anexo anterior deste perfil está corrompido. "
                        "Não foram importados dados novos.") from exc
                continue
            if any(x.get("profile_id")==p["id"] and x.get("path")==name and
                   x.get("sha256")!=digest for x in descriptors):
                raise AndroidImportError("Um anexo existente foi alterado. Importação interrompida.")
            filename=PurePosixPath(name).name
            descriptors.append({"profile_id":p["id"],"path":name,"filename":filename,
                                "category":category,"sha256":digest,"bytes":len(data), "display_name":display_name,
                                "android_source":plan.source.identifier})
            assets.append((digest,data))
        created=self._write_assets(assets)
        try:
            p["medications"]=previous_med+list(plan.medications.new)
            p["appointments"]=previous_apt+list(plan.appointments.new)
            p["android_zip_source_id"]=plan.source.identifier
            p["android_zip_source_name"]=plan.source.name
            if plan.avatar_b64 and not p.get("photo_b64"):
                p["photo_b64"]=plan.avatar_b64
            self.data["imported_files"]=descriptors
            self.save()
        except Exception:
            p["medications"]=previous_med
            p["appointments"]=previous_apt
            if old_source is None:p.pop("android_zip_source_id",None)
            else:p["android_zip_source_id"]=old_source
            if old_source_name is None:p.pop("android_zip_source_name",None)
            else:p["android_zip_source_name"]=old_source_name
            self.data["imported_files"]=previous_files
            if old_avatar is None:p.pop("photo_b64",None)
            else:p["photo_b64"]=old_avatar
            for path in created:
                try:path.unlink()
                except OSError:pass
            raise
        return {"medications":len(plan.medications.new),
                "appointments":len(plan.appointments.new),
                "attachments":len(assets)}

    def android_archives(self):
        """Metadata only: archive bytes remain in DPAPI, never in the profile JSON."""
        return [dict(item) for item in self.data.get("android_family_archives", [])]

    def profile_android_extras(self, profile_id: str):
        """Explicit-only, verified per-person source extraction. No UI-thread call."""
        from windows.android_profile_v067 import read_profile_extras
        p=self.get_profile(profile_id)
        if p is None:return {},()
        source_id=p.get("android_zip_source_id")
        if not source_id:return {},()
        for item in self.android_archives():
            if profile_id not in item.get("profile_ids",[]):continue
            try:
                raw=self.read_imported_asset({"sha256":item["sha256"]})
                return read_profile_extras(raw,source_id)
            except (ValueError,OSError,KeyError):
                continue
        return {},()

    def profile_android_images_and_fields(self, profile_id: str):
        """Load only own CC photos and identity fields, explicitly and off the UI thread."""
        from windows.android_profile_v067 import read_profile_view
        p=self.get_profile(profile_id)
        if p is None:return {},{}
        source_id=p.get("android_zip_source_id")
        if not source_id:return {},{}
        for item in self.android_archives():
            if profile_id not in item.get("profile_ids",[]):continue
            try:
                original=self.read_imported_asset({"sha256":item["sha256"]})
                return read_profile_view(original,source_id)
            except (ValueError,OSError,KeyError):
                continue
        return {},{}


    def export_original_android_zip(self, digest: str) -> bytes:
        """Return the byte-for-byte original (unencrypted) Android ZIP for user export."""
        from hashlib import sha256
        from windows.android_archive_v063 import validated_files
        row=next((x for x in self.android_archives() if x.get("sha256")==digest),None)
        if row is None:
            raise LocalStoreError("Não existe este backup Android guardado.")
        raw=self.read_imported_asset({"sha256":digest})
        if len(raw)!=row["bytes"] or sha256(raw).hexdigest()!=digest:
            raise LocalStoreError("O backup Android guardado está corrompido.")
        validated_files(raw)
        return raw

    def import_android_family(self, plan):
        """Atomic family import, including encrypted exact source ZIP for every category.

        Any unimplemented Android modules remain recoverable in the original ZIP;
        they are NOT misrepresented as Windows-compatible screens.
        """
        from windows.family_portability_v064 import FamilyPlan, plan_summary, _new_profile
        from windows.profile_fields_v066 import missing_profile_fields
        from windows.android_import_v062 import AndroidImportError, _existing_map
        from hashlib import sha256
        from pathlib import PurePosixPath
        import copy
        if not isinstance(plan,FamilyPlan):
            raise AndroidImportError("Pré-visualização familiar inválida.")
        if sha256(plan.original_zip).hexdigest()!=plan.digest:
            raise AndroidImportError("O ZIP familiar mudou desde a pré-visualização.")
        # Reverify manifest and sha256 when committing, not only on preview.
        from windows.android_archive_v063 import validated_files
        validated_files(plan.original_zip)
        previous=self.data
        proposed=copy.deepcopy(previous)
        people={p["id"]:p for p in proposed.get("profiles",[])}
        old_descriptors=list(proposed.get("imported_files",[]))
        descriptors=list(old_descriptors)
        known={(x.get("profile_id"),x.get("path"),x.get("sha256"))
               for x in old_descriptors}
        assets=[]
        summary=plan_summary(plan)
        for member in plan.members:
            pid=member.profile_id
            p=people.get(pid)
            if member.create:
                if p is not None:
                    raise AndroidImportError(
                        "Foi criado um perfil desde a pré-visualização. Prepara novamente.")
                p=_new_profile(member.source,member.original_profile)
                if p["id"]!=pid:
                    raise AndroidImportError("O identificador de destino mudou.")
                proposed["profiles"].append(p)
                people[pid]=p
            if p is None or p.get("android_zip_source_id") not in (
                None,"",member.source.identifier):
                raise AndroidImportError("O perfil Windows mudou desde a pré-visualização.")
            if not member.create and any(x.get("android_zip_source_id") ==
                    member.source.identifier and x["id"]!=pid
                    for x in proposed["profiles"]):
                raise AndroidImportError("Há uma associação Android duplicada.")
            for category,partial in (
                ("medications",member.imported.medications),
                ("appointments",member.imported.appointments)):
                existing=_existing_map(p.get(category,[]),category)
                if any(x["android_source_key"] in existing for x in partial.new):
                    raise AndroidImportError(
                        "Os dados foram alterados desde a pré-visualização. Tenta novamente.")
                p[category]=list(p.get(category,[]))+copy.deepcopy(list(partial.new))
            p["android_zip_source_id"]=member.source.identifier
            p["android_zip_source_name"]=member.source.name
            if member.original_profile:
                if not p.get("android_profile_original"):
                    p["android_profile_original"]=dict(member.original_profile)
                # Upgrade both newly-created and old imported profiles with the
                # fields Android already contains; never replace Windows edits.
                p.update(missing_profile_fields(p,member.original_profile))
            if member.imported.avatar_b64 and not p.get("photo_b64"):
                p["photo_b64"]=member.imported.avatar_b64
            for name,data,category,digest,display_name in member.imported.attachments:
                key=(pid,name,digest)
                if key in known:
                    old=next(x for x in old_descriptors if
                        (x.get("profile_id"),x.get("path"),x.get("sha256"))==key)
                    # A corrupted existing file must block this transaction.
                    self.read_imported_asset(old)
                    continue
                if any(x.get("profile_id")==pid and x.get("path")==name
                       and x.get("sha256")!=digest for x in descriptors):
                    raise AndroidImportError("Conflito num documento já importado.")
                descriptors.append({
                    "profile_id":pid,"path":name,"filename":PurePosixPath(name).name,
                    "category":category,"sha256":digest,"bytes":len(data),
                    "display_name":display_name,
                    "android_source":member.source.identifier,
                })
                known.add(key)
                assets.append((digest,data))
        proposed["imported_files"]=descriptors
        archives=list(proposed.get("android_family_archives",[]))
        prior=next((a for a in archives if a.get("sha256")==plan.digest),None)
        if prior:
            if prior.get("bytes")!=len(plan.original_zip):
                raise AndroidImportError("O arquivo original está inconsistente.")
            prior["profile_ids"]=sorted(set(prior.get("profile_ids",[]))|
                {m.profile_id for m in plan.members})
        else:
            archives.append({
                "sha256":plan.digest, "bytes":len(plan.original_zip),
                "filename":"SaudePratica-backup-Android-original.zip",
                "profile_ids":[m.profile_id for m in plan.members],
                "source_ids":[m.source.identifier for m in plan.members],
            })
        proposed["android_family_archives"]=archives
        # Importar também os módulos restantes no próprio restauro do ZIP
        # familiar, em vez de deixar ficheiros armazenados mas fichas vazias.
        from windows.android_full_restore_v0813 import (
            extract_profile_android, merge_snapshot,
        )
        source_to_target={m.source.identifier:m.profile_id for m in plan.members}
        imported_modules={}
        for member in plan.members:
            target=people[member.profile_id]
            snapshot=extract_profile_android(
                plan.original_zip,member.source.identifier)
            added_metadata,added_photos,counts=merge_snapshot(
                target,snapshot,source_to_target,descriptors)
            descriptors.extend(added_metadata)
            assets.extend(added_photos)
            for module,number in counts.items():
                imported_modules[module]=imported_modules.get(module,0)+number
        proposed["imported_files"]=descriptors
        assets.append((plan.digest,plan.original_zip))
        created=self._write_assets(assets)
        try:
            self.data=proposed
            self.save()
        except Exception:
            self.data=previous
            for file in created:
                try:file.unlink()
                except OSError:pass
            raise
        summary["new_attachments"]=len(assets)-1
        summary["android_modules"]=imported_modules
        return summary

    def export_backup(self, password: str, profile_id: str | None = None) -> bytes:
        """One .spbackup format; family or a single selected profile."""
        selected=([self.get_profile(profile_id)] if profile_id is not None
                  else list(self.profiles()))
        if not selected or any(p is None for p in selected):
            raise LocalStoreError("Escolhe um perfil válido ou a família inteira.")
        scope="profile" if profile_id is not None else "family"
        if profile_id is not None:
            # An original Android archive can contain all family members.
            # Never hide unrelated patients in a nominally single-profile
            # backup. Fail until a verified filtered source snapshot exists.
            for original in self.android_archives():
                owners=original.get("profile_ids",[])
                if profile_id in owners and (
                    len(owners)!=1 or owners[0]!=profile_id):
                    raise LocalStoreError(
                        "Este perfil ainda depende de um backup Android "
                        "com dados de outras pessoas. Para preservar a "
                        "privacidade e não perder dados, usa por agora "
                        "Backup Família. O backup Perfil será ativado "
                        "após separar todos os anexos por perfil.")
        files = {}
        for p in selected:
            pid = p["id"]
            uuid.UUID(pid)
            prefix = "profiles/" + pid + "/"
            # Include all profile fields (including photo, caregiver and future
            # metadata) while keeping medication and agenda as separate payloads.
            metadata = {k: v for k, v in p.items()
                        if k not in ("medications", "appointments")}
            from windows.profile_data_guard_v075 import overlaps_medication
            if overlaps_medication(p,metadata.get("notes")):
                metadata.pop("notes",None)
            files[prefix+"profile.json"] = json.dumps(
                metadata, ensure_ascii=False).encode("utf-8")
            files[prefix+"backup_scope.json"]=json.dumps({
                "scope":scope,"format":2,"profile_count":len(selected)
            },ensure_ascii=False).encode("utf-8")
            # Preserve preferences and future global metadata in the encrypted
            # archive, without overwriting preferences on a populated Windows.
            if scope=="family" and p is selected[0]:
                state={k:v for k,v in self.data.items()
                       if k not in ("profiles","imported_files",
                                    "android_family_archives","pin_login_v1")}
                files[prefix+"windows_state.json"]=json.dumps(
                    state,ensure_ascii=False).encode("utf-8")
            files[prefix+"medicacao.json"] = json.dumps(
                {"medications":p.get("medications",[])}, ensure_ascii=False).encode("utf-8")
            files[prefix+"agenda.json"] = json.dumps(
                {"appointments":p.get("appointments",[])}, ensure_ascii=False).encode("utf-8")
            entries=self.imported_assets(pid)
            files[prefix+"attachments.json"]=json.dumps(entries,
                ensure_ascii=False).encode("utf-8")
            for entry in entries:
                digest=entry["sha256"]
                archive_path="attachments/"+digest[:2]+"/"+digest+".bin"
                if archive_path not in files:
                    files[archive_path]=self.read_imported_asset(entry)
            # Full original Android archives retain all opaque categories and
            # profile prefs without pretending Windows can edit them today.
            archives=[dict(a) for a in self.android_archives()
                      if pid in a.get("profile_ids",[])]
            files[prefix+"android_archives.json"]=json.dumps(
                archives,ensure_ascii=False).encode("utf-8")
            for item in archives:
                digest=item["sha256"]
                archive_path="attachments/"+digest[:2]+"/"+digest+".bin"
                if archive_path not in files:
                    files[archive_path]=self.read_imported_asset({"sha256":digest})
        if not files:
            raise LocalStoreError("Cria pelo menos um perfil antes de fazer backup.")
        return create_backup(files, password)

    def inspect_portable_backup(self, encrypted: bytes, password: str):
        from windows.portable_restore_v072 import inspect
        verified=read_backup(encrypted,password)
        return inspect(verified,self.profiles())

    def restore_portable_backup(self, plan, password_for_safety_copy: str):
        from windows.portable_restore_v072 import apply
        return apply(self,plan,password_for_safety_copy)

    def inspect_backup(self, encrypted: bytes, password: str):
        data = read_backup(encrypted, password)
        people = []
        for path, content in data.items():
            if not path.endswith("/profile.json"):
                continue
            value = json.loads(content)
            uuid.UUID(value["id"])
            people.append({"id": value["id"], "name": value["name"]})
        if not people:
            raise BackupError("O backup não contém perfis.")
        return people, data

    def restore_backup(self, verified_files: dict[str, bytes]) -> int:
        # Add-only. Never silently overwrite medication, appointments or profiles.
        existing = {p["id"] for p in self.profiles()}
        added = []
        for path, blob in verified_files.items():
            if not path.endswith("/profile.json"):
                continue
            person = json.loads(blob)
            if not isinstance(person,dict) or not isinstance(person.get("id"),str):
                raise BackupError("Perfil inválido no backup.")
            pid = person["id"]
            try:uuid.UUID(pid)
            except (ValueError,AttributeError) as exc:
                raise BackupError("Identificador do perfil inválido.") from exc
            if path != "profiles/" + pid + "/profile.json":
                raise BackupError("Caminho do perfil não corresponde ao identificador.")
            if pid in existing:
                raise BackupError("O backup inclui um perfil já existente. Nada foi importado.")
            prefix = "profiles/" + pid + "/"
            meds = verified_files.get(prefix+"medicacao.json")
            agenda = verified_files.get(prefix+"agenda.json")
            if meds is None or agenda is None:
                raise BackupError("Ficheiros clínicos obrigatórios em falta.")
            medications = json.loads(meds).get("medications")
            appointments = json.loads(agenda).get("appointments")
            if not isinstance(medications,list) or not isinstance(appointments,list):
                raise BackupError("Medicação ou agenda inválidas.")
            if not isinstance(person.get("name"), str) or len(person["name"]) not in range(1,121):
                raise BackupError("Perfil inválido.")
            # Preserve forward-compatible profile fields, not just id/name.
            hydrated = dict(person)
            hydrated.update({"medications": medications, "appointments": appointments})
            added.append(hydrated)
        if not added:
            raise BackupError("Sem perfis para importar.")
        if len({p["id"] for p in added}) != len(added):
            raise BackupError("Perfis duplicados no ficheiro.")
        # Portable backup can include DPAPI-protected source attachments,
        # but all plaintext bytes are inside the encrypted .spbackup only.
        from hashlib import sha256
        attachment_meta=[]
        encrypted_assets=[]
        for person in added:
            pid=person["id"]
            key=f"profiles/{pid}/attachments.json"
            if key not in verified_files:continue
            entries=json.loads(verified_files[key])
            if not isinstance(entries,list):raise BackupError("Índice de anexos inválido.")
            for entry in entries:
                if not isinstance(entry,dict) or entry.get("profile_id")!=pid:
                    raise BackupError("Anexo com perfil de destino inválido.")
                digest=entry.get("sha256","")
                path="attachments/"+digest[:2]+"/"+digest+".bin"
                if path not in verified_files or sha256(verified_files[path]).hexdigest()!=digest:
                    raise BackupError("Anexo ausente ou com hash inválido.")
                attachment_meta.append(entry)
                encrypted_assets.append((digest,verified_files[path]))
        # All-or-nothing original Android ZIP recovery: preserve exactly,
        # validate the digest and attach it to all restored Windows profiles.
        from windows.android_archive_v063 import validated_files
        archive_rows={}
        for person in added:
            pid=person["id"]
            key=f"profiles/{pid}/android_archives.json"
            if key not in verified_files:continue  # previous backup v1
            rows=json.loads(verified_files[key])
            if not isinstance(rows,list) or len(rows)>100:
                raise BackupError("Índice dos backups Android inválido.")
            for row in rows:
                if not isinstance(row,dict) or pid not in row.get("profile_ids",[]):
                    raise BackupError("Associação de ZIP Android a perfil inválida.")
                digest=row.get("sha256","")
                if not isinstance(digest,str) or len(digest)!=64:
                    raise BackupError("Identificador de backup Android inválido.")
                key_data="attachments/"+digest[:2]+"/"+digest+".bin"
                raw=verified_files.get(key_data)
                if raw is None or sha256(raw).hexdigest()!=digest:
                    raise BackupError("Backup Android original incompleto.")
                validated_files(raw)
                previous=archive_rows.get(digest)
                if previous is not None and previous!=row:
                    raise BackupError("O mesmo backup tem metadados contraditórios.")
                archive_rows[digest]=row
                encrypted_assets.append((digest,raw))
        existing_archives=self.data.get("android_family_archives",[])
        if any(row["sha256"] in {p.get("sha256") for p in existing_archives}
               for row in archive_rows.values()):
            raise BackupError("O backup Android original já existe neste Windows.")
        old_global={k:v for k,v in self.data.items()
                    if k not in ("profiles","imported_files","android_family_archives")}
        # Recover global settings only into a fresh Windows data store.
        # Existing installations retain their current local preferences.
        incoming_state=None
        for person in added:
            key=f"profiles/{person['id']}/windows_state.json"
            if key in verified_files:
                state=json.loads(verified_files[key])
                if not isinstance(state,dict) or state.get("format")!=STORE_FORMAT:
                    raise BackupError("Metadados globais do Windows inválidos.")
                if incoming_state is not None and incoming_state!=state:
                    raise BackupError("Definições globais contraditórias no backup.")
                incoming_state=state
        restore_into_empty=not self.profiles()
        created=self._write_assets(encrypted_assets)
        old_files=self.data.get("imported_files",[])
        self.data["imported_files"]=old_files+attachment_meta
        self.data["android_family_archives"]=list(existing_archives)+list(archive_rows.values())
        self.data["profiles"].extend(added)
        if incoming_state is not None:
            if restore_into_empty:
                for key,value in incoming_state.items():
                    if key not in ("profiles","imported_files","android_family_archives"):
                        self.data[key]=value
            else:
                # Do not overwrite local settings when importing profiles.
                added[0]["windows_original_settings"]=incoming_state.get("settings",{})
        try:
            self.save()
        except Exception:
            del self.data["profiles"][-len(added):]
            self.data["imported_files"]=old_files
            self.data["android_family_archives"]=existing_archives
            for key in list(self.data):
                if key not in ("profiles","imported_files","android_family_archives"):
                    self.data.pop(key)
            self.data.update(old_global)
            for path in created:
                try:path.unlink()
                except OSError:pass
            raise
        return len(added)
