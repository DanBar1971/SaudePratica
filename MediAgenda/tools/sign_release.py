#!/usr/bin/env python3
"""Sign a trusted, already-built SaúdePrática release with the ORIGINAL key.

Only intended for a trusted GitHub Actions push/workflow_dispatch on master.
The encrypted backup is public; only the 64-hex recovery secret belongs in GitHub Secrets.
Never print or upload the original private signing key or password.
"""
import base64
import hashlib
import io
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"SAUDEPRATICA-KEYBACKUP-V1\n"
AAD = b"GitHub public encrypted backup of MediAgenda signing credentials"
CERT_SHA256 = "7f67082f5e0de76986a0078d5f998e65467c8468f4d09b0caf8e4b332cc60e6a"
APP_ID = "com.mediagenda.app.stable"
CIPHER_FILE = Path("SaúdePrática/release-unsigned-patches/v1.9.98/MediAgenda-CHAVE-PRIVADA-ENCRIPTADA.aesgcm.b64")
UNSIGNED = Path("build-src/MediAgenda_Android_v1/app/build/outputs/apk/release/app-release-unsigned.apk")
SIGNED = Path("SaudePratica.apk")


def run(*args, env=None):
    return subprocess.run(list(map(str, args)), capture_output=True, text=True, check=True, env=env).stdout


def main():
    # Absence of this value is a hard stop: never sign using a fresh key.
    key_hex = os.environ.get("SAUDEPRACTICA_SIGNING_RECOVERY_HEX", "").strip()
    if not re.fullmatch(r"[a-fA-F0-9]{64}", key_hex):
        raise SystemExit("Missing/invalid SAUDEPRACTICA_SIGNING_RECOVERY_HEX secret. Configure it once under GitHub Actions secrets; no APK was published.")
    if not UNSIGNED.is_file():
        raise SystemExit("Missing verified unsigned release APK; no APK published.")
    sdk = Path(os.environ["ANDROID_HOME"]) / "build-tools" / "35.0.0"
    apksigner, aapt2 = sdk / "apksigner", sdk / "aapt2"
    if not (apksigner.is_file() and aapt2.is_file()):
        raise SystemExit("Android SDK build-tools 35.0.0 required.")
    raw = base64.b64decode(CIPHER_FILE.read_text(encoding="ascii"), validate=True)
    if not raw.startswith(MAGIC):
        raise SystemExit("Unrecognized encrypted key backup format.")
    nonce, cipher_text = raw[len(MAGIC):len(MAGIC) + 12], raw[len(MAGIC) + 12:]
    recovered_zip = AESGCM(bytes.fromhex(key_hex)).decrypt(nonce, cipher_text, AAD)
    with zipfile.ZipFile(io.BytesIO(recovered_zip)) as z:
        needed = {"MediAgenda-stable-signing-key.jks", "GUARDAR_EM_LOCAL_SEGURO.txt"}
        if not needed.issubset(set(z.namelist())):
            raise SystemExit("Original key material incomplete; no APK published.")
        key_bytes = z.read("MediAgenda-stable-signing-key.jks")
        instructions = z.read("GUARDAR_EM_LOCAL_SEGURO.txt").decode("utf-8")
    alias = re.search(r"(?m)^Alias\s*:\s*(\S+)", instructions)
    pw = re.search(r"(?m)^Palavra-passe da keystore e da chave\s*:\s*(\S+)", instructions)
    if not alias or not pw or not key_bytes:
        raise SystemExit("Original alias/password missing; no APK published.")

    pkg_line = run(aapt2, "dump", "badging", UNSIGNED).splitlines()[0]
    package = re.search(r"name='([^']+)'", pkg_line)
    version_name = re.search(r"versionName='([^']+)'", pkg_line)
    version_code = re.search(r"versionCode='([^']+)'", pkg_line)
    if not package or package.group(1) != APP_ID:
        raise SystemExit("Unexpected Android package identity; refusing to sign.")
    if not version_name or not re.fullmatch(r"\d+\.\d+\.\d+", version_name.group(1)):
        raise SystemExit("Invalid versionName; refusing to sign.")
    if not version_code or not version_code.group(1).isdigit():
        raise SystemExit("Invalid versionCode; refusing to sign.")
    tag = "v" + version_name.group(1)

    with tempfile.TemporaryDirectory(prefix="saudepratica-key-") as folder:
        p = Path(folder) / "original.jks"
        p.write_bytes(key_bytes)
        os.chmod(p, 0o600)
        child_env = dict(os.environ, SP_APK_PASSWORD=pw.group(1))
        run(apksigner, "sign", "--ks", p, "--ks-key-alias", alias.group(1),
            "--ks-pass", "env:SP_APK_PASSWORD", "--key-pass", "env:SP_APK_PASSWORD",
            "--out", SIGNED, UNSIGNED, env=child_env)
    output = run(apksigner, "verify", "--verbose", "--print-certs", SIGNED)
    digest = re.search(r"Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F]+)", output)
    if not digest or digest.group(1).lower() != CERT_SHA256:
        SIGNED.unlink(missing_ok=True)
        raise SystemExit("Signing certificate mismatch: original identity required.")
    if not all(f"Verified using v{i} scheme (APK Signature Scheme v{i}): true" in output for i in (2, 3)):
        SIGNED.unlink(missing_ok=True)
        raise SystemExit("APK v2/v3 signature verification failed.")
    sha = hashlib.file_digest(SIGNED.open("rb"), "sha256").hexdigest()
    output_file = os.getenv("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"tag={tag}\nversion_name={version_name.group(1)}\nversion_code={version_code.group(1)}\nsha256={sha}\n")
    print(f"SIGNED AND VERIFIED: {tag}, versionCode={version_code.group(1)}, package={APP_ID}, original certificate confirmed, SHA-256={sha}")


if __name__ == "__main__":
    main()