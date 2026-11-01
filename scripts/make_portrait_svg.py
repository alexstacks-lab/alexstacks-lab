#!/usr/bin/env python3
"""
Convierte el personaje pixel-art (source/personaje.png) en un retrato ASCII
dentro de una ventana de terminal, que se "imprime" fila por fila con un cursor
y luego se congela.

Dos estilos (data/profile.json -> "whoami_style"):
  "hacker"  verde y negro clásico: caracteres verdes con brillo, lluvia de
            código de fondo y el personaje en verde "visión nocturna" debajo.
  "color"   caracteres con los colores originales del personaje.

- El fondo gris claro se elimina con un flood-fill desde los bordes.
- La densidad del carácter sale de la luminancia (en "hacker", lo claro brilla más).
- GitHub no ejecuta JS en SVG dentro de <img>, pero sí SMIL/CSS: la animación
  es un recorte (clipPath) que barre cada fila + un cursor de bloque.

    python scripts/make_portrait_svg.py [entrada.png] [salida.svg]
    STATIC=1 python scripts/make_portrait_svg.py   # versión sin animación (previews)
"""
import base64
import colorsys
import io
import json
import os
import random
import sys

from PIL import Image, ImageDraw, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (INK, MUTED, GREEN, PAD, TITLEBAR_H, HOST, FRAME,
                   HK_GREEN, HK_DIM, HK_PALE, HK_FRAME, HK_TITLE,
                   esc, svg_open, window, hacker_window)

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE = json.load(open(os.path.join(HERE, "..", "data", "profile.json"), encoding="utf-8"))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source", "personaje.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "assets", "portrait.svg")
STATIC = bool(os.environ.get("STATIC"))
STYLE = os.environ.get("STYLE", PROFILE.get("whoami_style", "color"))
HACKER = STYLE == "hacker"
USER = PROFILE.get("prompt_user", "alex")
NAME = os.environ.get("PORTRAIT_NAME", "Alexandro Alanya")

W, H = 840, 880                 # mismo lienzo que neofetch.svg
STATUS_H = 34
COLS = int(os.environ.get("COLS", 112))
RAMP = " .:-=+*#%@"             # claro (disperso) -> oscuro (denso)
MIN_IDX = 2 if HACKER else 5
BG_TOL = 18
BACKDROP = float(os.environ.get("BACKDROP", 0.38 if HACKER else 0.32))


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
CELL_ASPECT = 15 / 8
ROWS = round(COLS * ch / cw / CELL_ASPECT)
art_h = H - TITLEBAR_H - STATUS_H - PAD * 2
cell_h = art_h / ROWS
cell_w = cell_h / CELL_ASPECT
art_w = cell_w * COLS
art_x = (W - art_w) / 2
art_y = TITLEBAR_H + PAD

a_small = rgba.getchannel("A").resize((COLS, ROWS), Image.BOX)
rgb_on_black = Image.new("RGB", rgba.size, (0, 0, 0))
rgb_on_black.paste(rgba, mask=rgba.getchannel("A"))
sum_small = rgb_on_black.resize((COLS, ROWS), Image.BOX)
spx, apx2 = sum_small.load(), a_small.load()


def q(v):
    return min(255, int(round(v * 255 / 12)) * 12)


def ink_color(r, g, b, lum):
    if HACKER:
        # verde: zonas claras brillan más, zonas oscuras (pelo, ojos) quedan en verde medio
        l = 0.20 + 0.48 * lum
        r2, g2, b2 = colorsys.hls_to_rgb(0.37, l, 1.0)
    else:
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        l = max(l, 0.52 if s > 0.25 else 0.40)
        r2, g2, b2 = colorsys.hls_to_rgb(h, l, min(1.0, s * 1.08))
    return "#%02x%02x%02x" % (q(r2), q(g2), q(b2))


rows = []
for y in range(ROWS):
    row = []
    for x in range(COLS):
        a = apx2[x, y] / 255
        if a < 0.35:
            row.append((" ", None))
            continue
        r, g, b = (c / a for c in spx[x, y])
        lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
        # hacker: brillo = densidad (como visión nocturna); color: oscuro = denso
        dens = lum if HACKER else 1 - lum
        idx = int(dens * (len(RAMP) - 1) + 0.5)
        idx = max(MIN_IDX, min(len(RAMP) - 1, idx))
        row.append((RAMP[idx], ink_color(r, g, b, lum)))
    rows.append(row)


def row_markup(row):
    out, cur, buf = [], None, ""
    for ch_, col in row:
        col = col or cur
        if col != cur and buf:
            out.append(f'<tspan fill="{cur or INK}">{esc(buf)}</tspan>')
            buf = ""
        cur = col
        buf += ch_
    if buf.strip():
        out.append(f'<tspan fill="{cur or INK}">{esc(buf)}</tspan>')
    return "".join(out)


# ---- 3. armar el SVG ---------------------------------------------------------
ACC = HK_GREEN if HACKER else GREEN
css = ""
if HACKER:
    css = (".rain{animation:rain linear infinite}"
           "@keyframes rain{0%{transform:translateY(-100%)}100%{transform:translateY(100%)}}")
parts = svg_open(W, H, css)
title = f"{USER}@{HOST}: ~$ ./portrait.sh --{'matrix' if HACKER else 'color'}"
parts += hacker_window(W, H, title) if HACKER else window(W, H, title)

if HACKER:
    parts.append('<defs><filter id="glow" x="-5%" y="-5%" width="110%" height="110%">'
                 '<feGaussianBlur stdDeviation="0.9" result="b"/>'
                 '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
                 f'<clipPath id="win"><rect x="1" y="{TITLEBAR_H + 1}" width="{W - 2}" '
                 f'height="{H - TITLEBAR_H - STATUS_H - 2}"/></clipPath></defs>')
    # lluvia de código de fondo
    rnd = random.Random(2005)
    glyphs = "01アイウエオカキクケコ0101<>{}#$%&*+=ABCDEF"
    parts.append('<g clip-path="url(#win)" opacity="0.16">')
    n_cols = 30
    for i in range(n_cols):
        x = 14 + i * (W - 28) / (n_cols - 1)
        n = rnd.randint(14, 30)
        chars = "".join(rnd.choice(glyphs) for _ in range(n))
        dur = rnd.uniform(7, 15)
        delay = -rnd.uniform(0, dur)
        tsp = "".join(f'<tspan x="{x:.0f}" dy="17" fill-opacity="{0.25 + 0.75 * (j / n):.2f}">{esc(c)}</tspan>'
                      for j, c in enumerate(chars))
        parts.append(f'<g class="rain" style="animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s">'
                     f'<text y="{TITLEBAR_H}" font-size="14" fill="{HK_GREEN}">{tsp}</text></g>')
    parts.append('</g>')

# scanlines
parts.append('<g opacity="0.05">' + "".join(
    f'<rect x="1" y="{gy}" width="{W - 2}" height="1" fill="{HK_GREEN if HACKER else INK}"/>'
    for gy in range(TITLEBAR_H + 4, H - STATUS_H, 4)) + '</g>')

# el personaje original debajo del ASCII ("fantasma"), en verde si es estilo hacker
ghost = rgba
if HACKER:
    gray = ImageOps.autocontrast(rgba.convert("L"), cutoff=1)
    ghost = ImageOps.colorize(gray, black="#001f08", white="#3ee86a").convert("RGBA")
    ghost.putalpha(rgba.getchannel("A"))
buf = io.BytesIO()
ghost.save(buf, "PNG", optimize=True)
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
parts.append('<g>')
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
    parts.append(f'<rect y="{row_y+1:.1f}" width="{cell_w:.2f}" height="{cell_h-2:.2f}" fill="{ACC}" opacity="0">'
                 f'<animate attributeName="x" from="{art_x:.1f}" to="{art_x+art_w:.1f}" begin="{delay:.3f}s" '
                 f'dur="{ROW_DUR:.3f}s" fill="freeze"/>'
                 f'<set attributeName="opacity" to="0.9" begin="{delay:.3f}s"/>'
                 f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>')
parts.append('</g>')

# barra de estado con cursor parpadeante
sl_y = H - STATUS_H
st_y = sl_y + 22
parts.append(f'<line x1="0" y1="{sl_y}" x2="{W}" y2="{sl_y}" stroke="{HK_FRAME if HACKER else FRAME}"/>')
prompt = f"{USER}@{HOST}:~$ whoami "
parts.append(f'<text x="{PAD}" y="{st_y}" fill="{HK_TITLE if HACKER else MUTED}" font-size="14">{esc(prompt)}'
             f'<tspan fill="{HK_PALE if HACKER else INK}" font-weight="700">{esc(NAME)}</tspan></text>')
cur_x = PAD + len(prompt + NAME + " ") * 14 * 0.6
parts.append(f'<rect x="{cur_x:.1f}" y="{st_y-13}" width="8" height="16" fill="{ACC}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" repeatCount="indefinite"/></rect>')

parts.append("</svg>")
svg = "".join(parts)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(svg)
print(f"wrote {OUT}: {STYLE}, {COLS}x{ROWS} chars, {len(svg)//1024} KB")
