# MeeGrid icon: launcher grid of 4 columns x 2 rows of tiny N9 squircles
# (motif by smyhu, 15.11.2026). Project style: dark N9 background with gloss arc,
# pictogram 231,255,205, soft glow.
# Usage: python3 icon.py background80.png n9mask80.png outdir
from PIL import Image, ImageDraw, ImageFilter
import sys, os
K = 8; W = 80 * K
LIGHT = (231, 255, 205); GLOW = (120, 170, 100)
base = Image.open(sys.argv[1]).convert('RGBA'); mask = Image.open(sys.argv[2]).convert('L'); out = sys.argv[3]
# squircle shape for the dots: the N9 mask itself, cropped to its 78 px body
dot_src = mask.crop((1, 1, 79, 79))

VARIANTS = {          # dot size, gap (px at 80), vertical offset
    'a': (11.0, 4.0, 0.0),
    'b': (12.5, 3.0, 0.0),
    'c': (10.0, 5.0, 0.0),
}

def pictogram(v):
    s, g, dy = VARIANTS[v]
    m = Image.new('L', (W, W), 0)
    dot = dot_src.resize((int(s * K), int(s * K)), Image.LANCZOS)
    tw = 4 * s + 3 * g; th = 2 * s + g
    x0 = (80 - tw) / 2.0; y0 = (80 - th) / 2.0 + dy
    for r in range(2):
        for c in range(4):
            m.paste(dot, (int((x0 + c * (s + g)) * K), int((y0 + r * (s + g)) * K)), dot)
    return m

def make(v):
    img = base.resize((W, W), Image.BICUBIC)
    m = pictogram(v)
    gl = m.filter(ImageFilter.GaussianBlur(K * 1.6)).point(lambda x: int(x * .55))
    img = Image.composite(Image.new('RGBA', (W, W), GLOW + (255,)), img, gl)
    img = Image.composite(Image.new('RGBA', (W, W), LIGHT + (255,)), img, m)
    s = img.resize((80, 80), Image.LANCZOS); s.putalpha(mask); return s

icons = {}
for v in sorted(VARIANTS):
    icons[v] = make(v)
    icons[v].save(os.path.join(out, 'meegrid80-%s.png' % v))
icons['a'].save(os.path.join(out, 'meegrid80.png'))
# preview: big + real size, on black and next to other project icons
from PIL import ImageFont
sheet = Image.new('RGBA', (3 * 220 + 20, 330), (0, 0, 0, 255)); d = ImageDraw.Draw(sheet)
for i, v in enumerate(sorted(VARIANTS)):
    sheet.alpha_composite(icons[v].resize((200, 200), Image.LANCZOS), (20 + i * 220, 20))
    sheet.alpha_composite(icons[v], (80 + i * 220, 230))
    d.text((20 + i * 220, 312), v.upper(), fill=(200, 200, 200))
sheet.save(os.path.join(out, 'meegrid-icon-preview.png'))
