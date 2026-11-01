#!/usr/bin/env python3
"""
Convierte el personaje pixel-art (source/personaje.png) en un retrato ASCII a
COLOR dentro de una ventana de terminal, que se "imprime" fila por fila con un
cursor y luego se congela.

- El fondo gris claro se elimina con un flood-fill desde los bordes.
- La densidad del carácter sale de la luminancia (oscuro = denso, como el perfil
  de referencia) y el color de cada carácter es el color ORIGINAL del pixel,
  solo aclarado lo justo para que el pelo negro/pantalón azul se lean sobre el
  fondo oscuro. Así el personaje conserva su paleta e identidad.
- GitHub no ejecuta JS en SVG dentro de <img>, pero sí SMIL/CSS: la animación
  es un recorte (clipPath) que barre cada fila + un cursor de bloque.

    python scripts/make_portrait_svg.py [entrada.png] [salida.svg]
    STATIC=1 python scripts/make_portrait_svg.py   # versión sin animación (previews)
"""
import base64
import colorsys
import io
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (BG, FRAME, INK, MUTED, GREEN, PAD, TITLEBAR_H, USER, HOST,
                   esc, svg_open, window)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source", "personaje.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "assets", "portrait.svg")
STATIC = bool(os.environ.get("STATIC"))
NAME = os.environ.get("PORTRAIT_NAME", "Alexandro Alanya")

W, H = 840, 880                 # mismo lienzo que neofetch.svg / stats.svg
STATUS_H = 34
COLS = int(os.environ.get("COLS", 112))
RAMP = " .:-=+*#%@"             # claro (disperso) -> oscuro (denso)
MIN_IDX = 5                     # todo lo que es personaje usa al menos '+' (el color manda)
L_FLOOR = 0.40                  # luminosidad mínima: negros -> gris tenue (pelo/contorno)
L_FLOOR_SAT = 0.52              # colores saturados oscuros (pantalón azul) un poco más claros
BG_TOL = 18                     # tolerancia del flood-fill del fondo
BACKDROP = float(os.environ.get("BACKDROP", 0.32))  # opacidad del pixel-art original bajo el ASCII


# ---- 1. quitar fondo ---------------------------------------------------------
im = Image.open(SRC).convert("RGB")
w0, h0 = im.size
mask_src = im.copy()
for seed in [(0, 0), (w0 - 1, 0), (0, h0 - 1), (w0 - 1, h0 - 1)]:
    ImageDraw.floodfill(mask_src, seed, (255, 0, 255), thresh=BG_TOL)
alpha = Image.new("L", im.size, 255)
mpx, apx = mask_src.load(), alpha.load()
for y in range(h0):
    for x in range(w0):
        if mpx[x, y] == (255, 0, 255):
            apx[x, y] = 0
rgba = im.copy()
rgba.putalpha(alpha)
rgba = rgba.crop(alpha.getbbox())
cw, ch = rgba.size

# ---- 2. muestrear la grilla --------------------------------------------------
CELL_ASPECT = 15 / 8            # alto/ancho de un carácter monoespaciado
ROWS = round(COLS * ch / cw / CELL_ASPECT)
art_h_max = H - TITLEBAR_H - STATUS_H - PAD * 2
cell_h = art_h_max / ROWS
cell_w = cell_h / CELL_ASPECT
art_w, art_h = cell_w * COLS, cell_h * ROWS
art_x = (W - art_w) / 2
art_y = TITLEBAR_H + PAD

small = rgba.resize((COLS, ROWS), Image.BOX)
a_small = rgba.getchannel("A").resize((COLS, ROWS), Image.BOX)
# color "puro" sin mezcla con el fondo: promedia solo pixeles opacos
rgb_on_black = Image.new("RGB", rgba.size, (0, 0, 0))
rgb_on_black.paste(rgba, mask=rgba.getchannel("A"))
sum_small = rgb_on_black.resize((COLS, ROWS), Image.BOX)
spx, apx2 = sum_small.load(), a_small.load()


def ink(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    l = max(l, L_FLOOR_SAT if s > 0.25 else L_FLOOR)
    s = min(1.0, s * 1.08)
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    # cuantiza un poco para agrupar caracteres del mismo color en un <tspan>
    q = lambda v: min(255, int(round(v * 255 / 12)) * 12)
    return "#%02x%02x%02x" % (q(r2), q(g2), q(b2))


rows = []          # lista de filas; cada fila = lista de (char, color)
for y in range(ROWS):
    row = []
    for x in range(COLS):
        a = apx2[x, y] / 255
        if a < 0.35:
            row.append((" ", None))
            continue
        r, g, b = (c / a for c in spx[x, y])
        lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
        idx = int((1 - lum) * (len(RAMP) - 1) + 0.5)
        idx = max(MIN_IDX, min(len(RAMP) - 1, idx))
        row.append((RAMP[idx], ink(r, g, b)))
    rows.append(row)


def row_markup(row):
    """Agrupa corridas del mismo color en un solo <tspan>."""
    out, cur, buf = [], None, ""
    for ch_, col in row:
        col = col or cur  # los espacios heredan el color actual
        if col != cur and buf:
            out.append(f'<tspan fill="{cur or INK}">{esc(buf)}</tspan>')
            buf = ""
        cur = col
        buf += ch_
    if buf.strip():
        out.append(f'<tspan fill="{cur or INK}">{esc(buf)}</tspan>')
    return "".join(out)


# ---- 3. armar el SVG ---------------------------------------------------------
parts = svg_open(W, H)
parts += window(W, H, f"{USER}@{HOST}: ~$ ./portrait.sh --color")

# grilla tenue de fondo (toque "scanlines")
parts.append(f'<g opacity="0.035">')
for gy in range(int(TITLEBAR_H + 4), int(H - STATUS_H), 4):
    parts.append(f'<rect x="1" y="{gy}" width="{W-2}" height="1" fill="{INK}"/>')
parts.append('</g>')

# pixel-art original (sin fondo) como "fantasma" bajo el ASCII: aparece al final
buf = io.BytesIO()
rgba.save(buf, "PNG", optimize=True)
data_uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
TYPE_TOTAL = 5.0
img = (f'<image href="{data_uri}" x="{art_x:.1f}" y="{art_y:.1f}" width="{art_w:.1f}" height="{art_h:.1f}" '
       f'preserveAspectRatio="none" style="image-rendering:pixelated"')
if STATIC:
    parts.append(img + f' opacity="{BACKDROP}"/>')
else:
    parts.append(img + f' opacity="0"><animate attributeName="opacity" from="0" to="{BACKDROP}" '
                 f'begin="{TYPE_TOTAL:.1f}s" dur="1.6s" fill="freeze"/></image>')

ROW_DUR = TYPE_TOTAL / ROWS
font_size = cell_h * 0.92
for ry, row in enumerate(rows):
    if not any(c.strip() for c, _ in row):
        continue
    ty = art_y + ry * cell_h + cell_h * 0.78
    row_y = art_y + ry * cell_h
    text = (f'<text xml:space="preserve" x="{art_x:.1f}" y="{ty:.1f}" font-size="{font_size:.2f}" font-weight="700" '
            f'textLength="{art_w:.1f}" lengthAdjust="spacing">{row_markup(row)}</text>')
    if STATIC:
        parts.append(text)
        continue
    delay = ry * ROW_DUR
    parts.append(f'<clipPath id="r{ry}"><rect x="{art_x:.1f}" y="{row_y:.1f}" height="{cell_h:.2f}" width="0">'
                 f'<animate attributeName="width" from="0" to="{art_w:.1f}" begin="{delay:.3f}s" '
                 f'dur="{ROW_DUR:.3f}s" fill="freeze"/></rect></clipPath>')
    parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
    parts.append(f'<rect y="{row_y+1:.1f}" width="{cell_w:.2f}" height="{cell_h-2:.2f}" fill="{GREEN}" opacity="0">'
                 f'<animate attributeName="x" from="{art_x:.1f}" to="{art_x+art_w:.1f}" begin="{delay:.3f}s" '
                 f'dur="{ROW_DUR:.3f}s" fill="freeze"/>'
                 f'<set attributeName="opacity" to="0.9" begin="{delay:.3f}s"/>'
                 f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>')

# barra de estado con cursor parpadeante
sl_y = H - STATUS_H
st_y = sl_y + 22
parts.append(f'<line x1="0" y1="{sl_y}" x2="{W}" y2="{sl_y}" stroke="{FRAME}"/>')
prompt = f"{USER}@{HOST}:~$ whoami "
parts.append(f'<text x="{PAD}" y="{st_y}" fill="{MUTED}" font-size="14">{esc(prompt)}'
             f'<tspan fill="{INK}" font-weight="700">{esc(NAME)}</tspan></text>')
cur_x = PAD + len(prompt + NAME + " ") * 14 * 0.6
parts.append(f'<rect x="{cur_x:.1f}" y="{st_y-13}" width="8" height="16" fill="{GREEN}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" repeatCount="indefinite"/></rect>')

parts.append("</svg>")
svg = "".join(parts)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w").write(svg)
print(f"wrote {OUT}: {COLS}x{ROWS} chars, {len(svg)//1024} KB")
