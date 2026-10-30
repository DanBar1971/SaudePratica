"""Approved SaúdePrática 16:9 wallpaper and colourful icon renderers.

Wallpaper comes from the user's approved dark teal/blue 16:9 artwork
(resampled WebP rendition embedded so release builds need no network).
No health records, avatars or fabricated medication images are included.
"""
from __future__ import annotations
import base64
from functools import lru_cache
from io import BytesIO
import os
from PIL import Image, ImageOps, ImageDraw, ImageFont

_BG_WEBP = (
"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"
)
# Module badge colours are fixed design tokens, never conditional on patient data.
COLOURS = [
    "#ec5353", "#65be5c", "#ff7457", "#429ee9", "#f4bd46",
    "#38a9d6", "#5ab5fa", "#48bce6", "#ee5c74", "#f079b2",
    "#e89e49", "#699be8", "#ae76d6", "#4baee3", "#e44a5e",
    "#5bbe78", "#6dc1cf", "#568dc5", "#57b9dd", "#eab064",
    "#5e96eb", "#e4b24f", "#62a7e9", "#5aaab6", "#a6a6d8",
]

@lru_cache(maxsize=12)
def wallpaper_image(width: int, height: int, light: bool = False):
    """Return approved art adapted to the full window size, no crop or blocks."""
    width, height = max(1,int(width)), max(1,int(height))
    im = Image.open(BytesIO(base64.b64decode(_BG_WEBP))).convert("RGB")
    im = im.resize((width,height), Image.Resampling.LANCZOS)
    if light:
        overlay = Image.new("RGB", im.size, "#edf4f7")
        im = Image.blend(im, overlay, .91)
    return im

def _font(size):
    candidates = [
        os.path.join(os.getenv("WINDIR", "C:\\Windows"), "Fonts", "seguiemj.ttf"),
        os.path.join(os.getenv("WINDIR", "C:\\Windows"), "Fonts", "segoeui.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate,size)
        except OSError:
            continue
    return ImageFont.load_default()

@lru_cache(maxsize=80)
def icon_image(icon: str, index: int, size: int = 50):
    """A colourful icon even where Tkinter renders emoji as monochrome."""
    scale = 3
    s=size*scale
    im=Image.new("RGBA",(s,s),(0,0,0,0))
    d=ImageDraw.Draw(im)
    color=COLOURS[index%len(COLOURS)]
    d.rounded_rectangle((4,4,s-4,s-4),radius=s//4,fill=color)
    d.rounded_rectangle((8,8,s-8,s-8),radius=s//4,
                        outline=(255,255,255,75),width=2)
    font=_font(int(s*.56))
    try:
        d.text((s//2,s//2),icon,font=font,anchor="mm",
               embedded_color=True,stroke_width=0)
    except (ValueError,OSError,TypeError):
        try:d.text((s//2,s//2),icon,font=font,anchor="mm",
                   fill="#ffffff",stroke_width=0)
        except Exception: d.text((s//2,s//2),"✚",font=_font(s//2),anchor="mm",fill="white")
    return im.resize((size,size),Image.Resampling.LANCZOS)

def circular_photo(photo_b64: str, size: int = 42):
    """Real profile photo only, never fabricate a person's portrait."""
    if not photo_b64:
        return None
    try:
        binary=base64.b64decode(photo_b64,validate=True)
        if len(binary)>450000:return None
        source=Image.open(BytesIO(binary))
        if source.width*source.height>20_000_000:return None
        source=ImageOps.fit(source.convert("RGBA"),(size,size),
                            method=Image.Resampling.LANCZOS)
        mask=Image.new("L",(size,size),0)
        ImageDraw.Draw(mask).ellipse((0,0,size-1,size-1),fill=255)
        source.putalpha(mask)
        return source
    except Exception:return None
