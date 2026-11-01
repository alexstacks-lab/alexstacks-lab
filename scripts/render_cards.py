#!/usr/bin/env python3
"""
Dibuja las tarjetas "CV" del perfil a partir de data/profile.json:

  assets/boot.svg        banner: logo ANSI-shadow + secuencia de arranque
  assets/neofetch.svg    ficha tipo `neofetch` (va al lado del retrato)
  assets/experience.svg  experiencia y formación como `git log --graph`
  assets/projects.svg    proyectos como `ls -la ~/proyectos`

Todo es SVG puro con animación CSS/SMIL (GitHub no ejecuta JS dentro de <img>).

    python scripts/render_cards.py
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (BG, TILE, FRAME, MUTED, INK, GREEN, CYAN, PINK, SAGE, CREAM,
                   SKIN, GOLD, PAD, TITLEBAR_H, HOST, esc, svg_open, window)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
P = json.load(open(os.path.join(ROOT, "data", "profile.json"), encoding="utf-8"))
USER = P.get("prompt_user", "alex")
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)

COLORS = {"pink": PINK, "cyan": CYAN, "green": GREEN, "sage": SAGE,
          "cream": CREAM, "skin": SKIN, "gold": GOLD, "muted": MUTED}

FADE_CSS = (".f{opacity:0;animation:f .5s ease-out both}"
            "@keyframes f{0%{opacity:0;transform:translateX(-10px)}100%{opacity:1;transform:none}}"
            ".blink{animation:b 1s steps(1) infinite}@keyframes b{50%{opacity:0}}")


def save(name, parts):
    parts.append("</svg>")
    svg = "".join(parts)
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote assets/{name} ({len(svg)//1024} KB)")


def wipe(uid, x, y, w, h, begin, dur):
    """clipPath que revela de izquierda a derecha (efecto 'tipeo')."""
    return (f'<clipPath id="{uid}"><rect x="{x}" y="{y}" height="{h}" width="0">'
            f'<animate attributeName="width" from="0" to="{w}" begin="{begin:.2f}s" '
            f'dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>')


def pill(x, y, text, color, size=12, anchor="start"):
    w = len(text) * size * 0.62 + 16
    if anchor == "end":
        x -= w
    return (f'<rect x="{x:.1f}" y="{y - size - 3:.1f}" width="{w:.1f}" height="{size + 9}" rx="{(size+9)/2:.1f}" '
            f'fill="{color}" fill-opacity="0.14" stroke="{color}" stroke-opacity="0.55"/>'
            f'<text x="{x + w/2:.1f}" y="{y:.1f}" fill="{color}" font-size="{size}" '
            f'text-anchor="middle">{esc(text)}</text>')


# =============================================================================
# 1. BOOT — logo ANSI shadow + secuencia de arranque
# =============================================================================
def figlet_rows(text):
    try:
        import pyfiglet
        rows = pyfiglet.figlet_format(text, font="ansi_shadow").rstrip("\n").split("\n")
    except Exception:  # sin pyfiglet: logo de respaldo para "ALEX"
        rows = [" █████╗ ██╗     ███████╗██╗  ██╗",
                "██╔══██╗██║     ██╔════╝╚██╗██╔╝",
                "███████║██║     █████╗   ╚███╔╝ ",
                "██╔══██║██║     ██╔══╝   ██╔██╗ ",
                "██║  ██║███████╗███████╗██╔╝ ██╗",
                "╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝"]
    return [r for r in rows if r.strip()]


# segmentos desde el centro de la celda: L R U D
BOX = {"═": "LR", "║": "UD", "╗": "LD", "╔": "RD", "╝": "LU", "╚": "RU"}


def render_boot():
    W = 880
    rows = figlet_rows(P.get("banner_text", "ALEX"))
    n_cols = max(len(r) for r in rows)
    cw = min(16.0, (W - 2 * PAD - 40) / n_cols)
    chh = cw * 1.55
    logo_w, logo_h = n_cols * cw, len(rows) * chh
    boot = P.get("boot", [])
    line_h = 26
    logo_y = TITLEBAR_H + 26
    name_y = logo_y + logo_h + 38
    tag_y = name_y + 26
    sep_y = tag_y + 22
    lines_y = sep_y + 30
    H = int(lines_y + len(boot) * line_h + 18)

    parts = svg_open(W, H, FADE_CSS)
    parts += window(W, H, f"{USER}@{HOST}: ~$ ./boot.sh")
    parts.append('<defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1">'
                 f'<stop offset="0" stop-color="{PINK}"/><stop offset="0.5" stop-color="{SKIN}"/>'
                 f'<stop offset="1" stop-color="{SAGE}"/></linearGradient></defs>')

    lx = (W - logo_w) / 2
    # logo: bloques llenos con degradado + "sombra" de líneas finas
    parts.append(wipe("logo", lx - 2, logo_y - 2, logo_w + 4, logo_h + 4, 0.2, 1.1))
    parts.append('<g clip-path="url(#logo)">')
    blocks, shadow = [], []
    for ry, row in enumerate(rows):
        for cx, ch in enumerate(row):
            x, y = lx + cx * cw, logo_y + ry * chh
            if ch == "█":
                blocks.append(f'M{x:.1f} {y:.1f}h{cw+0.4:.1f}v{chh+0.4:.1f}h-{cw+0.4:.1f}z')
            elif ch in BOX:
                mx, my = x + cw / 2, y + chh / 2
                for seg in BOX[ch]:
                    ex, ey = {"L": (x, my), "R": (x + cw, my), "U": (mx, y), "D": (mx, y + chh)}[seg]
                    shadow.append(f'M{mx:.1f} {my:.1f}L{ex:.1f} {ey:.1f}')
    parts.append(f'<path d="{"".join(shadow)}" stroke="{PINK}" stroke-opacity="0.45" stroke-width="1.6" fill="none"/>')
    parts.append(f'<path d="{"".join(blocks)}" fill="url(#lg)"/>')
    parts.append('</g>')

    parts.append(f'<text class="f" style="animation-delay:1.3s" x="{W/2}" y="{name_y:.0f}" fill="{INK}" '
                 f'font-size="22" font-weight="700" text-anchor="middle">{esc(P["full_name"])}</text>')
    parts.append(f'<text class="f" style="animation-delay:1.5s" x="{W/2}" y="{tag_y:.0f}" fill="{MUTED}" '
                 f'font-size="14" text-anchor="middle">{esc(P["tagline"])}</text>')
    parts.append(f'<line x1="{PAD}" y1="{sep_y:.0f}" x2="{W-PAD}" y2="{sep_y:.0f}" stroke="{FRAME}" stroke-dasharray="3 5"/>')

    t = 1.9
    for i, (status, msg) in enumerate(boot):
        y = lines_y + i * line_h
        col = GREEN if status == "OK" else GOLD
        label = f"[{status.center(6)}]"
        dur = 0.25 + len(msg) * 0.012
        parts.append(wipe(f"b{i}", PAD, y - 18, W - 2 * PAD, line_h, t, dur))
        parts.append(f'<g clip-path="url(#b{i})"><text x="{PAD}" y="{y:.0f}" font-size="15" xml:space="preserve">'
                     f'<tspan fill="{MUTED}">[</tspan><tspan fill="{col}" font-weight="700">{esc(status.center(6))}</tspan>'
                     f'<tspan fill="{MUTED}">] </tspan><tspan fill="{INK}">{esc(msg)}</tspan></text></g>')
        if status != "OK":  # cursor parpadeante al final de la línea en espera
            cx = PAD + (len(label) + 1 + len(msg)) * 15 * 0.6 + 6
            parts.append(f'<rect x="{cx:.0f}" y="{y-14:.0f}" width="9" height="17" fill="{GOLD}" opacity="0">'
                         f'<set attributeName="opacity" to="1" begin="{t+dur:.2f}s"/>'
                         f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
                         f'dur="1s" begin="{t+dur:.2f}s" repeatCount="indefinite"/></rect>')
        t += dur + 0.15
    save("boot.svg", parts)


# =============================================================================
# 2. NEOFETCH — ficha al lado del retrato (mismo lienzo 840x880)
# =============================================================================
def render_neofetch():
    W, H = 840, 880
    items = P["neofetch"]
    parts = svg_open(W, H, FADE_CSS)
    parts += window(W, H, f"{USER}@{HOST}: ~$ neofetch")

    x0 = PAD + 22
    y = TITLEBAR_H + 58
    head = f"{USER}@{HOST}"
    parts.append(f'<text x="{x0}" y="{y}" font-size="30" font-weight="700">'
                 f'<tspan fill="{SKIN}">{USER}</tspan><tspan fill="{MUTED}">@</tspan>'
                 f'<tspan fill="{SKIN}">{HOST}</tspan></text>')
    y += 16
    parts.append(f'<rect x="{x0}" y="{y}" width="{len(head) * 30 * 0.6:.0f}" height="2" fill="{FRAME}"/>')
    y += 44

    key_w = max(len(k) for k, _ in items) * 22 * 0.6 + 26
    avail = H - y - 120
    lh = min(38, avail / max(1, len(items) - 1))
    for i, (k, v) in enumerate(items):
        yy = y + i * lh
        delay = 0.25 + i * 0.09
        is_status = k.lower().startswith("estado")
        vcol = GREEN if is_status else INK
        bold = ' font-weight="700"' if is_status else ""
        key = f'<tspan fill="{SKIN}" font-weight="700">{esc(k)}</tspan>' if k else ""
        colon = f'<tspan fill="{MUTED}">:</tspan>' if k else ""
        parts.append(f'<text class="f" style="animation-delay:{delay:.2f}s" x="{x0}" y="{yy:.1f}" font-size="22">'
                     f'{key}{colon}</text>')
        parts.append(f'<text class="f" style="animation-delay:{delay:.2f}s" x="{x0 + key_w:.0f}" y="{yy:.1f}" '
                     f'font-size="22" fill="{vcol}"{bold}>{esc(v)}</text>')
        if is_status:  # pulso del punto verde
            parts.append(f'<circle cx="{x0 + key_w + 7:.0f}" cy="{yy - 7:.1f}" r="11" fill="{GREEN}" opacity="0">'
                         f'<animate attributeName="opacity" values="0;0.35;0" dur="2s" begin="{delay+0.5:.2f}s" repeatCount="indefinite"/>'
                         f'<animate attributeName="r" values="6;14;6" dur="2s" begin="{delay+0.5:.2f}s" repeatCount="indefinite"/></circle>')

    # paleta tipo neofetch con los colores del polo del personaje
    py = H - 86
    sw = 46
    pal = [BG, PINK, SKIN, GOLD, SAGE, CYAN, CREAM, INK]
    for i, c in enumerate(pal):
        d = 0.3 + len(items) * 0.09 + i * 0.06
        parts.append(f'<rect class="f" style="animation-delay:{d:.2f}s" x="{x0 + i * sw}" y="{py}" '
                     f'width="{sw}" height="26" fill="{c}" stroke="{FRAME}" stroke-width="{1 if c == BG else 0}"/>')
    if P.get("neofetch_footnote"):
        parts.append(f'<text x="{W - PAD - 10}" y="{H - 24}" fill="{MUTED}" font-size="18" '
                     f'text-anchor="end">{esc(P["neofetch_footnote"])}</text>')
    save("neofetch.svg", parts)


# =============================================================================
# 3. EXPERIENCIA — git log --graph
# =============================================================================
def short_hash(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:7]


def render_experience():
    W = 880
    exp = P["experience"]
    top = TITLEBAR_H + 28
    item_h = 56
    H = top + len(exp) * item_h - 6
    parts = svg_open(W, H, FADE_CSS)
    parts += window(W, H, f"{USER}@{HOST}: ~/carrera $ git log --graph --oneline")

    gx = PAD + 10
    # línea del grafo
    parts.append(f'<line x1="{gx}" y1="{top - 4}" x2="{gx}" y2="{top + (len(exp) - 1) * item_h}" '
                 f'stroke="{FRAME}" stroke-width="2"/>')
    for i, e in enumerate(exp):
        y = top + i * item_h
        d = 0.2 + i * 0.18
        dot = GREEN if e.get("head") else (SKIN if e.get("init") else CYAN)
        parts.append(f'<g class="f" style="animation-delay:{d:.2f}s">')
        parts.append(f'<circle cx="{gx}" cy="{y - 5}" r="6" fill="{BG}" stroke="{dot}" stroke-width="2.5"/>')
        if e.get("head"):
            parts.append(f'<circle cx="{gx}" cy="{y - 5}" r="2.6" fill="{dot}"/>')
        x = gx + 22
        h = short_hash(e["title"])
        refs = ""
        if e.get("head"):
            refs = (f'<tspan fill="{GOLD}"> (</tspan><tspan fill="{CYAN}" font-weight="700">HEAD -&gt; </tspan>'
                    f'<tspan fill="{GREEN}" font-weight="700">main</tspan><tspan fill="{GOLD}">)</tspan>')
        if e.get("init"):
            refs = f'<tspan fill="{GOLD}"> (</tspan><tspan fill="{SKIN}" font-weight="700">tag: init</tspan><tspan fill="{GOLD}">)</tspan>'
        parts.append(f'<text x="{x}" y="{y}" font-size="15" xml:space="preserve">'
                     f'<tspan fill="{GOLD}">{h}</tspan>{refs}'
                     f'<tspan fill="{MUTED}">  {esc(e["year"])}  </tspan>'
                     f'<tspan fill="{INK}" font-weight="700">{esc(e["title"])}</tspan></text>')
        parts.append(f'<text x="{x + 8.9 * 9}" y="{y + 22}" font-size="13.5" fill="{MUTED}">{esc(e["detail"])}</text>')
        if e.get("tag"):
            parts.append(pill(W - PAD - 6, y + 1, e["tag"], GOLD, 12, anchor="end"))
        parts.append('</g>')
    save("experience.svg", parts)


# =============================================================================
# 4. PROYECTOS — ls -la ~/proyectos
# =============================================================================
def render_projects():
    W = 880
    pr = P["projects"]
    top = TITLEBAR_H + 30
    row_h = 36
    H = top + 22 + len(pr) * row_h + 4
    parts = svg_open(W, H, FADE_CSS)
    parts += window(W, H, f"{USER}@{HOST}: ~$ ls -la ~/proyectos")

    parts.append(f'<text x="{PAD}" y="{top}" font-size="13" fill="{MUTED}">total {len(pr)}</text>')
    name_w = max(len(p_["name"]) for p_ in pr) * 15 * 0.6 + 30
    for i, p_ in enumerate(pr):
        y = top + 30 + i * row_h
        d = 0.2 + i * 0.12
        col = COLORS.get(p_.get("color", "cyan"), CYAN)
        parts.append(f'<g class="f" style="animation-delay:{d:.2f}s">')
        if i % 2 == 0:
            parts.append(f'<rect x="{PAD - 8}" y="{y - 22}" width="{W - 2 * PAD + 16}" height="{row_h - 4}" rx="6" '
                         f'fill="{TILE}" fill-opacity="0.7"/>')
        parts.append(f'<text x="{PAD}" y="{y}" font-size="15" font-weight="700" fill="{CYAN}">{esc(p_["name"])}</text>')
        parts.append(f'<text x="{PAD + name_w:.0f}" y="{y}" font-size="14" fill="{INK}">{esc(p_["desc"])}</text>')
        parts.append(pill(W - PAD, y, p_["tag"], col, 12, anchor="end"))
        parts.append('</g>')
    save("projects.svg", parts)


if __name__ == "__main__":
    render_boot()
    render_neofetch()
    render_experience()
    render_projects()
