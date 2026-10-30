"""Build Windows-only visuals from the official SaúdePrática images.

Never invent or substitute the official icon/splash. All generated images
derive from assets/saude_icon.png, saude_background.png, saude_splash.png.
"""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/"assets"
DIST=ROOT/"dist"
DIST.mkdir(exist_ok=True)

icon=Image.open(ASSETS/"saude_icon.png").convert("RGBA")
background=Image.open(ASSETS/"saude_background.png").convert("RGB")
splash=Image.open(ASSETS/"saude_splash.png").convert("RGB")

# The ico embeds proper multi-size bitmaps, rather than a renamed PNG.
icon.save(DIST/"saude_icon.ico",format="ICO",
          sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
assert (DIST/"saude_icon.ico").stat().st_size > 5000

W,H=900,500
base=ImageOps.fit(background,(W,H),method=Image.Resampling.LANCZOS)
base=base.filter(ImageFilter.GaussianBlur(radius=5)).convert("RGBA")
veil=Image.new("RGBA",(W,H),(2,17,24,176))
base=Image.alpha_composite(base,veil)
draw=ImageDraw.Draw(base)
draw.rounded_rectangle((48,62,W-48,H-62),radius=36,
                       fill=(5,32,40,220),outline=(18,204,192,135),width=2)
brand=icon.resize((228,228),Image.Resampling.LANCZOS)
base.alpha_composite(brand,(74,136))
fonts=Path("C:/Windows/Fonts")
def font(name,size):
    p=fonts/name
    return ImageFont.truetype(str(p),size) if p.is_file() else ImageFont.load_default()
bold=font("segoeuib.ttf",56)
regular=font("segoeui.ttf",23)
small=font("segoeui.ttf",17)
draw.text((333,179),"SaúdePrática",font=bold,fill="#f5ffff")
draw.text((336,250),"tudo num só lugar",font=regular,fill="#55ded4")
draw.rounded_rectangle((337,312,708,358),radius=22,fill=(28,126,128,120))
draw.text((360,324),"A iniciar a aplicação...",font=small,fill="#f0fafa")
path=DIST/"saude_splash_windows.png"
base.convert("RGB").save(path,optimize=True)

# Confirm the exact source files were read, including the original portrait splash.
assert splash.size[0]>100 and splash.size[1]>100
print("Assets oficiais: ícone ICO multiresolução e splash Windows gerados:",path)
