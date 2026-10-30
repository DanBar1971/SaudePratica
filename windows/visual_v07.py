"""SaúdePrática desktop v0.6.1: native-resolution wallpaper and Android module symbols.

Do NOT upscale the severely compressed base64 thumbnail from v0.6.0.
Build a widescreen composition from the ORIGINAL 941x1672 Android background,
without changing the proportions of any motif. The desktop source is already
shipped as assets/saude_background.png by the existing PyInstaller workflow.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
from io import BytesIO
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance

ROOT=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))
COLORS=["#f4d54b","#65cd68","#f35b54","#43a2df","#efb84c",
        "#ed6e7f","#f2aa4f","#45caff","#ec5670","#ef9bd2",
        "#eab063","#69a3df","#a982dc","#6bbfe8","#e45b65",
        "#5bdc8a","#58c9ce","#5c9dc9","#6acbe0","#f3bc65",
        "#85b2ed","#f0c668","#6bb4ed","#61bfbd","#b4a7e8"]

def _source():
    path=ROOT/"assets"/"saude_background.png"
    with Image.open(path) as f:
        rgb=f.convert("RGB")
        if min(rgb.size)<900:
            raise RuntimeError("O fundo Android original não tem resolução suficiente.")
        return rgb

@lru_cache(maxsize=1)
def _widescreen():
    """1672x941 16:9 master. Never stretch or tile a low-res wallpaper."""
    w,h=1672,941
    bg=Image.new("RGB",(w,h),"#051523")
    source=_source()
    # The portrait image is RESIZED PROPORTIONALLY, so circles stay circles.
    sw=round(source.width*h/source.height)
    side=source.resize((sw,h),Image.Resampling.LANCZOS)
    # Keep the authentic top-left luminous curve and lower-left medical cross.
    # Fade the right-hand side of this strip into a dark, quiet central canvas.
    mask=Image.new("L",(sw,h))
    pixels=mask.load()
    for y in range(h):
        for x in range(sw):
            edge=max(0,min(1,(435-x)/100))
            if y>540:
                edge*=max(0,min(1,(320-x)/75))
            pixels[x,y]=int(255*edge)
    bg.paste(side,(0,0),mask)
    # On the right only the lower-right teal motif is retained, rather than
    # duplicating the cross or the top-left cyan cloud in the middle of screen.
    mask=Image.new("L",(sw,h))
    pixels=mask.load()
    for y in range(h):
        vy=max(0,min(1,(y-410)/180))
        for x in range(sw):
            pixels[x,y]=int(255*vy*max(0,min(1,(x-290)/90)))
    bg.paste(side,(w-sw,0),mask)
    return bg

@lru_cache(maxsize=6)
def wallpaper_image(width:int,height:int,light:bool=False):
    width,height=max(1,int(width)),max(1,int(height))
    # Fit with aspect ratio protected. No low-resolution base64 assets.
    base=ImageOps.fit(_widescreen(),(width,height),
          method=Image.Resampling.LANCZOS,centering=(.5,.5))
    if light:
        veil=Image.new("RGB",base.size,"#edf4f7")
        base=Image.blend(base,veil,.91)
    return base

def _font(size:int):
    paths=[Path(os.getenv("WINDIR","C:\\Windows"))/"Fonts"/"seguiemj.ttf",
           Path(os.getenv("WINDIR","C:\\Windows"))/"Fonts"/"segoeui.ttf",
           Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    for path in paths:
        try:return ImageFont.truetype(str(path),size)
        except OSError:pass
    return ImageFont.load_default()

@lru_cache(maxsize=100)
def icon_image(icon:str,index:int,size:int=64):
    """Render the same Emoji symbols as Android, with NO badge or square.

    Windows Segoe UI Emoji holds colour glyphs; Pillow embedded_color renders
    them at 3x and downsamples for good antialiasing.
    """
    scale=3
    s=size*scale
    canvas=Image.new("RGBA",(s,s),(0,0,0,0))
    d=ImageDraw.Draw(canvas)
    font=_font(int(s*.72))
    try:
        d.text((s//2,s//2),icon,font=font,anchor="mm",
               embedded_color=True,stroke_width=0)
    except (ValueError,OSError,TypeError):
        d.text((s//2,s//2),icon,font=font,anchor="mm",
               fill=COLORS[index%len(COLORS)])
    # On computers without colour emoji fonts, tint white/monochrome glyphs.
    if canvas.getbbox() is None:
        d.text((s//2,s//2),"✚",font=_font(int(s*.7)),anchor="mm",
               fill=COLORS[index%len(COLORS)])
    else:
        rgba=canvas.getdata()
        sample=[p for p in rgba if p[3]>170]
        if sample and max(max(p[:3])-min(p[:3]) for p in sample)<14:
            alpha=canvas.getchannel("A")
            color=Image.new("RGBA",(s,s),COLORS[index%len(COLORS)])
            color.putalpha(alpha)
            canvas=color
    return canvas.resize((size,size),Image.Resampling.LANCZOS)

def circular_photo(photo_b64:str,size:int=42):
    import base64
    if not photo_b64:return None
    try:
        raw=base64.b64decode(photo_b64,validate=True)
        if len(raw)>450000:return None
        with Image.open(BytesIO(raw)) as src:
            if src.width*src.height>20_000_000:return None
            image=ImageOps.fit(src.convert("RGBA"),(size,size),
                               method=Image.Resampling.LANCZOS)
        alpha=Image.new("L",(size,size))
        ImageDraw.Draw(alpha).ellipse((0,0,size-1,size-1),fill=255)
        image.putalpha(alpha)
        return image
    except Exception:return None
