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
            "postal_code": 24, "emergency_name": 120, "emergency_phone": 50,
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
        if dose_pattern not in ("", "Jejum", "Pequeno-almoço", "Almoço", "Jantar",
                                "Às refeições", "Ao deitar", "SOS", "Horário livre",
                                "De 4 em 4 horas", "De 6 em 6 horas", "De 12 em 12 horas"):
            raise LocalStoreError("Tipo de toma inválido.")
        no_alarm = bool(fields.get("no_alarm", False)) or dose_pattern == "SOS"
        if not no_alarm:
            if (len(time) != 5 or time[2] != ":" or not time[:2].isdigit()
                    or not time[3:].isdigit() or int(time[:2]) > 23
                    or int(time[3:]) > 59):
                raise LocalStoreError("Indica uma hora de aviso válida (HH:mm) ou ativa Sem alarme.")
        elif time and (len(time) != 5 or time[2] != ":" or not time[:2].isdigit()
                       or not time[3:].isdigit() or int(time[:2]) > 23
                       or int(time[3:]) > 59):
            raise LocalStoreError("Hora inválida (HH:mm).")
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
        new = dict(old) if old else {"id": str(uuid.uuid4())}
        new.update({
            "name": name, "dose": dose, "time": time,
            "administration_route": route, "injection_type": injection,
            "dose_pattern": dose_pattern, "indication": indication, "notes": notes,
            "no_alarm": no_alarm, "suspended": suspended,
        })
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
            if member.original_profile and not p.get("android_profile_original"):
                p["android_profile_original"]=dict(member.original_profile)
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
        return summary

    def export_backup(self, password: str) -> bytes:
        files = {}
        for p in self.profiles():
            pid = p["id"]
            uuid.UUID(pid)
            prefix = "profiles/" + pid + "/"
            # Include all profile fields (including photo, caregiver and future
            # metadata) while keeping medication and agenda as separate payloads.
            metadata = {k: v for k, v in p.items()
                        if k not in ("medications", "appointments")}
            files[prefix+"profile.json"] = json.dumps(
                metadata, ensure_ascii=False).encode("utf-8")
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
        created=self._write_assets(encrypted_assets)
        old_files=self.data.get("imported_files",[])
        self.data["imported_files"]=old_files+attachment_meta
        self.data["android_family_archives"]=list(existing_archives)+list(archive_rows.values())
        self.data["profiles"].extend(added)
        try:
            self.save()
        except Exception:
            del self.data["profiles"][-len(added):]
            self.data["imported_files"]=old_files
            self.data["android_family_archives"]=existing_archives
            for path in created:
                try:path.unlink()
                except OSError:pass
            raise
        return len(added)
