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

    def add_medication(self, profile_id: str, name: str, dose: str, time: str, route: str):
        p = self.get_profile(profile_id)
        if p is None:
            raise LocalStoreError("Escolhe primeiro um perfil.")
        name, dose, time = name.strip(), dose.strip(), time.strip()
        if not 1 <= len(name) <= 160 or len(dose) > 90:
            raise LocalStoreError("Nome ou dose inválidos.")
        # Time is stored as clinical input, NOT registered as a Windows alarm.
        if time and (len(time)!=5 or time[2]!=":" or not time[:2].isdigit() or
                     not time[3:].isdigit() or int(time[:2])>23 or int(time[3:])>59):
            raise LocalStoreError("Hora inválida. Usa HH:mm.")
        if route not in ("", "oral", "sublingual", "parenteral", "topical",
                         "inhaled", "rectal", "vaginal", "ocular", "otic", "nasal", "other"):
            raise LocalStoreError("Via de administração desconhecida.")
        medication = {"id": str(uuid.uuid4()), "name":name, "dose":dose,
                      "time":time, "administration_route":route}
        p["medications"].append(medication)
        self.save()
        return medication

    def export_backup(self, password: str) -> bytes:
        files = {}
        for p in self.profiles():
            pid = p["id"]
            uuid.UUID(pid)
            prefix = "profiles/" + pid + "/"
            files[prefix+"profile.json"] = json.dumps(
                {"id":pid,"name":p["name"]}, ensure_ascii=False).encode("utf-8")
            files[prefix+"medicacao.json"] = json.dumps(
                {"medications":p.get("medications",[])}, ensure_ascii=False).encode("utf-8")
            files[prefix+"agenda.json"] = json.dumps(
                {"appointments":p.get("appointments",[])}, ensure_ascii=False).encode("utf-8")
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
            pid = person["id"]
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
            added.append({"id":pid,"name":person["name"],
                          "medications":medications, "appointments":appointments})
        if not added:
            raise BackupError("Sem perfis para importar.")
        if len({p["id"] for p in added}) != len(added):
            raise BackupError("Perfis duplicados no ficheiro.")
        self.data["profiles"].extend(added)
        try:
            self.save()
        except Exception:
            del self.data["profiles"][-len(added):]
            raise
        return len(added)
