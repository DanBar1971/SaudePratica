#!/usr/bin/env python3
"""Reconstruct previously signed public APK byte-for-byte from verified CI unsigned
APK and PUBLIC signed metadata delta. Does NOT handle any private signing key.
Mandatory SHA-256 and apksigner validation happens in publishing workflow.
"""
from pathlib import Path
from zipfile import ZipFile
import base64, mmap, struct, subprocess, hashlib

folder=Path("MediAgenda/release-verified/v1.9.121")
unsigned=Path("unsigned-original.apk")
target=Path("SaudePratica.apk")
assert unsigned.is_file() and unsigned.stat().st_size>100_000_000
parts=[(folder/f"metadata.part{i}.b64").read_text().strip() for i in (1,2,3)]
assert all(len(p)==3484 for p in parts)
compressed=base64.b64decode("".join(parts),validate=True)
assert hashlib.sha256(compressed).hexdigest()=="76679029e9751277f28a6656282bbcf3c89f4eb2ca858cb8bbc2b88eb8eccdc3"
Path("metadata.patch.zst").write_bytes(compressed)

with ZipFile(unsigned) as zip_file,unsigned.open("rb") as stream:
    mm=mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ)
    files=zip_file.infolist()
    segments=[];lens=[];end=0
    for entry in files:
        header=entry.header_offset
        sig=struct.unpack_from("<I",mm,header)[0]
        assert sig==0x04034b50
        name,extra=struct.unpack_from("<HH",mm,header+26)
        data=header+30+name+extra
        segment=mm[end:data]
        assert len(segment)<65536
        segments.append(segment);lens.append(len(segment))
        end=data+entry.compress_size
    segments.append(mm[end:])
    base=struct.pack("<H",len(files))+struct.pack("<"+"H"*len(files),*lens)+b"".join(segments)
    Path("metadata.original.bin").write_bytes(base)
    # Signed data = public signed header/central-directory/signature metadata
    # plus the original, unchanged compressed contents of each APK entry.
    subprocess.run(["zstd","--quiet","--decompress","--patch-from=metadata.original.bin",
                    "metadata.patch.zst","-o","metadata.signed.bin"],check=True)
    signed_metadata=Path("metadata.signed.bin").read_bytes()
    count=struct.unpack_from("<H",signed_metadata,0)[0]
    assert count==len(files)==1014
    lengths=struct.unpack_from("<"+"H"*count,signed_metadata,2)
    parts=memoryview(signed_metadata)[2+count*2:]
    pos=0
    with target.open("wb") as out:
        for entry,part_length in zip(files,lengths):
            out.write(parts[pos:pos+part_length]);pos+=part_length
            header=entry.header_offset
            n,e=struct.unpack_from("<HH",mm,header+26)
            data=header+30+n+e
            out.write(mm[data:data+entry.compress_size])
        out.write(parts[pos:])
assert target.stat().st_size==153323487
print("PUBLIC SIGNED APK RECONSTRUCTED (verify SHA/signature before publishing)")
