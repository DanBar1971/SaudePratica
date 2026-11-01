#!/usr/bin/env python3
"""Reconstruct signed SaúdePrática 1.9.125 from public, verified unsigned APK.

No private signing key is needed. The small zstd delta only contains public
signed ZIP metadata (including signature blocks); original compressed APK
files remain byte-identical to the GitHub Actions unsigned artifact.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import mmap
import struct
import subprocess

base = Path('original-unsigned.apk')
signed = Path('SaudePratica.apk')
folder = Path('MediAgenda/release-verified/v1.9.125')
unsigned_sha = '3af42a77db1582f89f48ece437d26dcb5e8632e3abc6f885b1cb354b33c302f8'
patch_sha = 'a47ef1da37504127c7239821f9df407cd33811ee9fc7eb747dd95b278c529cf3'
meta_sha = '5ec12af74cd6abd3ddd0bcc460bda99ae59277f9f625e16b3c9ed857c83f0505'
signed_sha = '2574f1c085217d389d713a96802e434b4fecd090d88d4c8020c214138e9220d9'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

assert base.is_file() and sha(base) == unsigned_sha, 'Unexpected unsigned APK'
with ZipFile(base) as zip_file, base.open('rb') as file_stream:
    entries = zip_file.infolist()
    assert len(entries) == 1014, 'Unexpected original ZIP entry count'
    original = mmap.mmap(file_stream.fileno(), 0, access=mmap.ACCESS_READ)
    headers = []
    compressed = []
    pos = 0
    for entry in entries:
        offset = entry.header_offset
        assert struct.unpack_from('<I', original, offset)[0] == 0x04034b50
        name_len, extra_len = struct.unpack_from('<HH', original, offset + 26)
        data_at = offset + 30 + name_len + extra_len
        part = original[pos:data_at]
        assert len(part) < 65536
        headers.append(part)
        compressed.append((data_at, entry.compress_size))
        pos = data_at + entry.compress_size
    tail = original[pos:]
    unsigned_meta = (struct.pack('<H', len(entries))
                     + struct.pack('<' + 'H' * len(entries), *map(len, headers))
                     + b''.join(headers) + tail)
    Path('unsigned_metadata.bin').write_bytes(unsigned_meta)
    assert sha(Path('unsigned_metadata.bin')) == '66be5bb575408984b2784565341892f6cbf19db15045b7f68c96ff3906db08e8'

    patch = folder / 'metadata.patch.zst.b64'
    import base64
    compressed_delta = base64.b64decode(''.join(patch.read_text().split()), validate=True)
    Path('metadata.patch.zst').write_bytes(compressed_delta)
    assert sha(Path('metadata.patch.zst')) == patch_sha
    subprocess.run(['zstd', '--quiet', '--long=27', '--decompress',
                    '--patch-from=unsigned_metadata.bin', 'metadata.patch.zst', '-f',
                    '-o', 'signed_metadata.bin'], check=True)
    assert sha(Path('signed_metadata.bin')) == meta_sha

    data = Path('signed_metadata.bin').read_bytes()
    count = struct.unpack_from('<H', data, 0)[0]
    assert count == len(entries)
    lengths = struct.unpack_from('<' + 'H' * count, data, 2)
    segments = memoryview(data)[2 + 2 * count:]
    meta_offset = 0
    with signed.open('wb') as output:
        for (offset, size), header_len in zip(compressed, lengths):
            output.write(segments[meta_offset:meta_offset + header_len])
            meta_offset += header_len
            output.write(original[offset:offset + size])
        output.write(segments[meta_offset:])
    del segments
    original.close()
assert signed.stat().st_size == 153438374, 'Unexpected signed APK size'
assert sha(signed) == signed_sha, 'Signed APK SHA-256 differs from approved original'
print('Reconstructed signed APK matches approved original byte-for-byte:', signed_sha)