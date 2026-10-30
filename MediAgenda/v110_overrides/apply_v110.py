"""SaúdePrática v1.9.91 — Fase A: stable medical profile identity in Nearby sync.
The implementation is additive and must not delete, merge, or guess patients by name.
"""
from pathlib import Path

root = Path("build-src/MediAgenda_Android_v1")
code = root / "app/src/main/java/com/mediagenda/app/sync/NearbySyncStore.kt"
source = Path("MediAgenda/v110_overrides/NearbySyncStore.kt")
assert code.is_file(), "Nearby store missing in reconstructed Android project"
assert source.is_file(), "Versioned sync source missing"
previous = code.read_text(encoding="utf-8")
assert "class NearbySyncStore" in previous
updated = source.read_text(encoding="utf-8")
assert updated.count('origin_profile_id') >= 2
assert "profileOrigin(it.id)" in updated
assert 'firstOrNull{it.name.equals(name,ignoreCase=true)}' not in updated
code.write_text(updated, encoding="utf-8")

build = root / "app/build.gradle.kts"
text = build.read_text(encoding="utf-8")
assert text.count("versionCode = 100") == 1
assert text.count('versionName = "1.9.90"') == 1
text = text.replace("versionCode = 100", "versionCode = 101", 1)
text = text.replace('versionName = "1.9.90"', 'versionName = "1.9.91"', 1)
build.write_text(text, encoding="utf-8")
print("SaúdePrática 1.9.91: verified patient origin in Nearby sync, without automatic merges")
