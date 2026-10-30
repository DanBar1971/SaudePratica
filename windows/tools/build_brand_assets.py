"""Build Windows icon and splash from exact official images — never crop splash.

The splash is the same full portrait artwork as Android, resized in a way that
preserves the entire canvas and aspect ratio for a 720px high Windows screen.
"""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)

icon = Image.open(ASSETS / "saude_icon.png").convert("RGBA")
original_splash = Image.open(ASSETS / "saude_splash.png").convert("RGB")

# Real multi-resolution .ico for EXE, shortcuts and installer.
icon.save(DIST / "saude_icon.ico", format="ICO",
          sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
if (DIST / "saude_icon.ico").stat().st_size < 5000:
    raise RuntimeError("O ícone oficial gerado é inválido.")

# Preserve EVERY pixel/region of the full source composition. No cropping,
# overlaid text, new logos, split-panel layout or synthetic decorative parts.
splash = ImageOps.contain(original_splash, (430, 720),
                          method=Image.Resampling.LANCZOS)
path = DIST / "saude_splash_windows.png"
splash.save(path, format="PNG", optimize=True)
if abs(splash.width/splash.height-original_splash.width/original_splash.height)>0.002:
    raise RuntimeError("A proporção do splash original foi alterada.")

print(f"Ícone oficial criado e splash integral: {splash.width}×{splash.height}")
