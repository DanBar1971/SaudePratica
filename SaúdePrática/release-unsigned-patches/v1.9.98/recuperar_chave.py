#!/usr/bin/env python3
"""Recupera o ZIP privado a partir do backup cifrado da Release.
Requer: pip install cryptography
NUNCA commit do token/segredo de recuperação.
Uso: python recuperar_chave.py MediAgenda-CHAVE-PRIVADA-ENCRIPTADA.aesgcm
"""
from pathlib import Path
from getpass import getpass
from sys import argv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b'SAUDEPRATICA-KEYBACKUP-V1\n'
AAD = b'GitHub public encrypted backup of MediAgenda signing credentials'
if len(argv) != 2:
    raise SystemExit('Uso: python recuperar_chave.py MediAgenda-CHAVE-PRIVADA-ENCRIPTADA.aesgcm')
raw = Path(argv[1]).read_bytes()
if not raw.startswith(MAGIC):
    raise SystemExit('Formato de backup desconhecido.')
secret = bytes.fromhex(getpass('Cole a chave de recuperacao de 64 caracteres hexadecimais (sem eco): ').strip())
if len(secret)!=32:
    raise SystemExit('Chave de recuperacao invalida.')
nonce = raw[len(MAGIC):len(MAGIC)+12]
ciphertext=raw[len(MAGIC)+12:]
try:
    data=AESGCM(secret).decrypt(nonce,ciphertext,AAD)
except Exception:
    raise SystemExit('Chave incorreta ou backup alterado.')
if not data.startswith(b'PK\x03\x04'):
    raise SystemExit('O backup nao contem um ZIP valido.')
out=Path('MediAgenda-Chave-Assinatura-PRIVADA-RECUPERADA.zip')
if out.exists():
    raise SystemExit(f'Ja existe {out}; mova o ficheiro antes de descifrar.')
out.write_bytes(data)
print(f'Chave original recuperada em {out}. Guarde o ZIP fora do GitHub publico.')
