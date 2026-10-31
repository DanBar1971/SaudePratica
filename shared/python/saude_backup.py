"""SaúdePrática portable encrypted backup v1 (reference implementation).

This format is new. Android/iOS support requires independent implementation and
interoperability tests; legacy Nearby v2 ZIPs are NOT accepted as backups.

Never log clinical data or passwords. ZIP entries are in memory; no plaintext
temporary files are written. Consumer is responsible for secure destination.
"""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import PurePosixPath
import base64
import hashlib
import json
import os
import re
import struct
from typing import Mapping
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

MAGIC = b"SAUDEPRATICA-BACKUP-V1\n"
ITERATIONS = 600_000
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_ARCHIVED_ANDROID_BYTES = 240 * 1024 * 1024
MAX_FILES = 2000
_PATH = re.compile(r"^(profiles/[0-9a-fA-F-]{36}/[A-Za-z0-9_.-]+|attachments/[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+)$")


class BackupError(ValueError):
    pass


def _valid_path(path: str) -> bool:
    p = PurePosixPath(path)
    return bool(_PATH.fullmatch(path)) and len(path) <= 200 and ".." not in p.parts and not path.startswith("/")


def _file_limit(path: str) -> int:
    # A verified original Android ZIP is stored as an opaque binary attachment;
    # keep all JSON/ordinary attachments under the original 100 MB limit.
    if re.fullmatch(r"attachments/[a-f0-9]{2}/[a-f0-9]{64}\.bin", path):
        return MAX_ARCHIVED_ANDROID_BYTES
    return MAX_FILE_BYTES


def _derive(password: str, salt: bytes, iterations: int) -> bytes:
    if not isinstance(password, str) or len(password) < 10:
        raise BackupError("A palavra-passe deve ter pelo menos 10 caracteres.")
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=iterations).derive(password.encode("utf-8"))


def create_backup(files: Mapping[str, bytes], password: str) -> bytes:
    """Build portable encrypted archive from validated per-profile files."""
    if not files or len(files) > MAX_FILES:
        raise BackupError("Quantidade de ficheiros inválida.")
    if sum(len(x) for x in files.values()) > MAX_ARCHIVE_BYTES:
        raise BackupError("Arquivo demasiado grande.")
    listed = []
    for path, data in sorted(files.items()):
        if not _valid_path(path) or not isinstance(data, bytes):
            raise BackupError("Caminho inválido ou conteúdo não binário.")
        if len(data) > _file_limit(path):
            raise BackupError("Anexo demasiado grande.")
        listed.append({"path": path, "size": len(data),
                       "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {"kind": "saudepratica-portable-v1",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "file_count": len(listed), "files": listed}
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=6) as z:
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        for path, data in sorted(files.items()):
            z.writestr("data/" + path, data)
    zipped = output.getvalue()
    salt, nonce = os.urandom(16), os.urandom(12)
    header = {"kind": "saudepratica-encrypted-v1",
              "kdf": "PBKDF2-HMAC-SHA256", "iterations": ITERATIONS,
              "salt_b64": base64.b64encode(salt).decode("ascii"),
              "cipher": "AES-256-GCM", "nonce_b64": base64.b64encode(nonce).decode("ascii")}
    header_bytes = json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")
    prefix = MAGIC + struct.pack(">I", len(header_bytes)) + header_bytes
    return prefix + AESGCM(_derive(password, salt, ITERATIONS)).encrypt(nonce, zipped, prefix)


def read_backup(encrypted: bytes, password: str) -> dict[str, bytes]:
    """Return verified bytes by path, no filesystem writes or silent merges."""
    if not isinstance(encrypted, bytes) or not encrypted.startswith(MAGIC):
        raise BackupError("Não é um backup SaúdePrática compatível.")
    if len(encrypted) > MAX_ARCHIVE_BYTES + 1024:
        raise BackupError("Backup demasiado grande.")
    offset = len(MAGIC)
    if len(encrypted) < offset + 4:
        raise BackupError("Cabeçalho incompleto.")
    size = struct.unpack(">I", encrypted[offset:offset+4])[0]
    if size < 30 or size > 4096:
        raise BackupError("Cabeçalho inválido.")
    end = offset + 4 + size
    try:
        header = json.loads(encrypted[offset+4:end])
        if header.get("kind") != "saudepratica-encrypted-v1" or header.get("cipher") != "AES-256-GCM":
            raise BackupError("Versão de encriptação desconhecida.")
        if header.get("kdf") != "PBKDF2-HMAC-SHA256" or header.get("iterations") != ITERATIONS:
            raise BackupError("Derivação de chave não suportada.")
        salt, nonce = base64.b64decode(header["salt_b64"], validate=True), base64.b64decode(header["nonce_b64"], validate=True)
        if len(salt) != 16 or len(nonce) != 12:
            raise BackupError("Parâmetros de encriptação inválidos.")
        zipped = AESGCM(_derive(password, salt, ITERATIONS)).decrypt(nonce, encrypted[end:], encrypted[:end])
    except BackupError:
        raise
    except Exception as exc:
        raise BackupError("Palavra-passe errada ou backup danificado.") from exc
    if len(zipped) > MAX_ARCHIVE_BYTES:
        raise BackupError("Conteúdo demasiado grande.")
    with ZipFile(BytesIO(zipped), "r") as z:
        items = z.infolist()
        if not 1 <= len(items) <= MAX_FILES + 1:
            raise BackupError("Número de ficheiros inválido.")
        names = [i.filename for i in items]
        if len(names) != len(set(names)) or names.count("manifest.json") != 1:
            raise BackupError("Entradas duplicadas ou manifesto em falta.")
        if any(i.is_dir() or i.file_size >
               _file_limit(i.filename.removeprefix("data/")) for i in items):
            raise BackupError("Ficheiro interno inválido.")
        if sum(i.file_size for i in items) > MAX_ARCHIVE_BYTES:
            raise BackupError("Conteúdo excede o limite de segurança.")
        manifest = json.loads(z.read("manifest.json"))
        if manifest.get("kind") != "saudepratica-portable-v1":
            raise BackupError("Formato clínico não suportado.")
        records = manifest.get("files")
        if not isinstance(records, list) or manifest.get("file_count") != len(records):
            raise BackupError("Manifesto inconsistente.")
        result = {}
        for record in records:
            path = record.get("path")
            if not isinstance(path, str) or not _valid_path(path) or path in result:
                raise BackupError("Caminho de backup inválido.")
            packed = "data/" + path
            if packed not in names:
                raise BackupError("Anexo não encontrado.")
            data = z.read(packed)
            if len(data) != record.get("size") or hashlib.sha256(data).hexdigest() != record.get("sha256"):
                raise BackupError("Falhou a verificação de integridade.")
            result[path] = data
        if set(names) != {"manifest.json"} | {"data/" + p for p in result}:
            raise BackupError("Entradas adicionais não autorizadas.")
        return result
