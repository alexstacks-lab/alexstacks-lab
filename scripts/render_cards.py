#!/usr/bin/env python3
"""
Dibuja las tarjetas "CV" del perfil a partir de data/profile.json:

  assets/boot.svg        banner: logo ANSI-shadow + secuencia de arranque
  assets/neofetch.svg    ficha tipo `neofetch` (va al lado del retrato)
  assets/experience.svg  experiencia y formación como `git log --graph`
  assets/projects.svg    proyectos como `ls -la ~/proyectos`
  assets/stack.svg       tecnologías como etiquetas flotantes con sus logos

Todo es SVG puro con animación CSS/SMIL (GitHub no ejecuta JS dentro de <img>).

    python scripts/render_cards.py
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (BG, TILE, FRAME, MUTED, INK, GREEN, CYAN, PINK, SAGE, CREAM,
                   SKIN, GOLD, PAD, TITLEBAR_H, HOST, esc, svg_open, window,
                   hacker_window, HK_GREEN, HK_MID, HK_DIM, HK_PALE, HK_FRAME, HK_TITLE)

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


def pill(x, y, text, color, size=12, anchor="start", lock=False, check=False, pulse=False):
    icon_w = 14 if (lock or check or pulse) else 0
    w = len(text) * size * 0.62 + 16 + icon_w
    if anchor == "end":
        x -= w
    out = (f'<rect x="{x:.1f}" y="{y - size - 3:.1f}" width="{w:.1f}" height="{size + 9}" rx="{(size+9)/2:.1f}" '
           f'fill="{color}" fill-opacity="0.14" stroke="{color}" stroke-opacity="0.55"/>')
    ix, iy = x + 9, y - size + 3          # esquina del icono (iconos dibujados, no emojis)
    if lock:
        out += (f'<path d="M{ix+1.5:.1f} {iy+4:.1f}v-1.8a2.5 2.5 0 0 1 5 0v1.8" fill="none" stroke="{color}" stroke-width="1.4"/>'
                f'<rect x="{ix:.1f}" y="{iy+4:.1f}" width="8" height="6.5" rx="1.3" fill="{color}"/>')
    if check:
        out += (f'<path d="M{ix:.1f} {iy+5.5:.1f}l3 3l5.5 -6.5" fill="none" stroke="{color}" '
                f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    if pulse:
        cx, cy = ix + 4, iy + 5
        out += (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.2" fill="{color}"/>'
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.2" fill="none" stroke="{color}" stroke-width="1.4">'
                f'<animate attributeName="r" values="3.2;7.5" dur="1.6s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0.9;0" dur="1.6s" repeatCount="indefinite"/></circle>')
    out += (f'<text x="{x + icon_w/2 + w/2:.1f}" y="{y:.1f}" fill="{color}" font-size="{size}" '
            f'text-anchor="middle">{esc(text)}</text>')
    return out


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
    hacker = P.get("whoami_style") == "hacker"
    KEY, VAL, SEP, HEAD, OK = ((HK_GREEN, HK_PALE, HK_DIM, HK_GREEN, HK_GREEN) if hacker
                               else (SKIN, INK, MUTED, SKIN, GREEN))
    css = FADE_CSS + (".glow{filter:url(#glow)}" if hacker else "")
    parts = svg_open(W, H, css)
    parts += (hacker_window if hacker else window)(W, H, f"{USER}@{HOST}: ~$ neofetch")
    if hacker:
        parts.append('<defs><filter id="glow" x="-5%" y="-20%" width="110%" height="140%">'
                     '<feGaussianBlur stdDeviation="2.2" result="b"/>'
                     '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
        # scanlines
        parts.append('<g opacity="0.06">' + "".join(
            f'<rect x="1" y="{gy}" width="{W-2}" height="1" fill="{HK_GREEN}"/>'
            for gy in range(TITLEBAR_H + 3, H - 2, 4)) + '</g>')

    x0 = PAD + 22
    y = TITLEBAR_H + 58
    head = f"{USER}@{HOST}"
    parts.append(f'<text class="glow" x="{x0}" y="{y}" font-size="30" font-weight="700">'
                 f'<tspan fill="{HEAD}">{USER}</tspan><tspan fill="{SEP}">@</tspan>'
                 f'<tspan fill="{HEAD}">{HOST}</tspan></text>')
    y += 16
    parts.append(f'<rect x="{x0}" y="{y}" width="{len(head) * 30 * 0.6:.0f}" height="2" '
                 f'fill="{HK_DIM if hacker else FRAME}"/>')
    y += 44

    key_w = max(len(k) for k, _ in items) * 22 * 0.6 + 26
    avail = H - y - 110
    lh = min(38, avail / max(1, len(items) - 1))
    for i, (k, v) in enumerate(items):
        yy = y + i * lh
        delay = 0.25 + i * 0.09
        is_status = k.lower().startswith("estado")
        vcol = OK if is_status else VAL
        bold = ' font-weight="700"' if is_status else ""
        key = f'<tspan fill="{KEY}" font-weight="700">{esc(k)}</tspan>' if k else ""
        colon = f'<tspan fill="{SEP}">:</tspan>' if k else ""
        parts.append(f'<text class="f" style="animation-delay:{delay:.2f}s" x="{x0}" y="{yy:.1f}" font-size="22">'
                     f'{key}{colon}</text>')
        parts.append(f'<text class="f" style="animation-delay:{delay:.2f}s" x="{x0 + key_w:.0f}" y="{yy:.1f}" '
                     f'font-size="22" fill="{vcol}"{bold}>{esc(v)}</text>')
        if is_status:  # pulso del punto verde
            parts.append(f'<circle cx="{x0 + key_w + 7:.0f}" cy="{yy - 7:.1f}" r="11" fill="{OK}" opacity="0">'
                         f'<animate attributeName="opacity" values="0;0.35;0" dur="2s" begin="{delay+0.5:.2f}s" repeatCount="indefinite"/>'
                         f'<animate attributeName="r" values="6;14;6" dur="2s" begin="{delay+0.5:.2f}s" repeatCount="indefinite"/></circle>')

    # paleta tipo neofetch
    py = H - 84
    sw = 46
    pal = (["#000000", "#002b0b", "#004d14", "#00731f", "#00a32b", "#00d136", "#00ff41", "#9dffb4"] if hacker
           else [BG, PINK, SKIN, GOLD, SAGE, CYAN, CREAM, INK])
    for i, c in enumerate(pal):
        d = 0.3 + len(items) * 0.09 + i * 0.06
        parts.append(f'<rect class="f" style="animation-delay:{d:.2f}s" x="{x0 + i * sw}" y="{py}" '
                     f'width="{sw}" height="26" fill="{c}" stroke="{HK_FRAME if hacker else FRAME}" '
                     f'stroke-width="{1 if i == 0 else 0}"/>')
    # cursor parpadeante al final, como prompt listo
    parts.append(f'<text x="{x0}" y="{H - 26}" font-size="20" fill="{SEP}">{esc(USER)}@{HOST}:~$</text>')
    parts.append(f'<rect x="{x0 + (len(USER) + len(HOST) + 4) * 12 + 6}" y="{H - 43}" width="11" height="21" fill="{OK}">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/></rect>')
    save("neofetch.svg", parts)


# =============================================================================
# 3. EXPERIENCIA — git log --graph
# =============================================================================
def short_hash(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:7]


def render_experience():
    W = 880
    exp = P["experience"]
    top = TITLEBAR_H + 30
    item_h = 52
    H = top + len(exp) * item_h - 4
    parts = svg_open(W, H, FADE_CSS)
    parts += window(W, H, f"{USER}@{HOST}: ~/carrera $ git log --graph --oneline")

    gx = PAD + 10
    yw = max(len(e["year"]) for e in exp)
    parts.append(f'<line x1="{gx}" y1="{top - 4}" x2="{gx}" y2="{top + (len(exp) - 1) * item_h}" '
                 f'stroke="{FRAME}" stroke-width="2"/>')
    for i, e in enumerate(exp):
        y = top + i * item_h
        d = 0.2 + i * 0.14
        ongoing = e.get("status") == "en curso"
        dot = GOLD if ongoing else GREEN
        parts.append(f'<g class="f" style="animation-delay:{d:.2f}s">')
        parts.append(f'<circle cx="{gx}" cy="{y - 5}" r="6" fill="{BG}" stroke="{dot}" stroke-width="2.5"/>')
        if e.get("head"):
            parts.append(f'<circle cx="{gx}" cy="{y - 5}" r="2.6" fill="{dot}"/>')
        x = gx + 22
        refs = ""
        if e.get("head"):
            refs = (f'<tspan fill="{GOLD}"> (</tspan><tspan fill="{CYAN}" font-weight="700">HEAD -&gt; </tspan>'
                    f'<tspan fill="{GREEN}" font-weight="700">main</tspan><tspan fill="{GOLD}">)</tspan>')
        parts.append(f'<text x="{x}" y="{y}" font-size="15" xml:space="preserve">'
                     f'<tspan fill="{GOLD}">{short_hash(e["title"])}</tspan>{refs}'
                     f'<tspan fill="{MUTED}">  {esc(e["year"].ljust(yw))}  </tspan>'
                     f'<tspan fill="{INK}" font-weight="700">{esc(e["title"])}</tspan></text>')
        parts.append(f'<text x="{x + 9 * 9}" y="{y + 21}" font-size="13" fill="{MUTED}">{esc(e["detail"])}</text>')
        if ongoing:
            parts.append(pill(W - PAD - 4, y + 1, "en curso", GOLD, 12, anchor="end", pulse=True))
        elif e.get("status") == "ok":
            parts.append(pill(W - PAD - 4, y + 1, "completado", GREEN, 12, anchor="end", check=True))
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
        parts.append(pill(W - PAD, y, p_["tag"], col, 12, anchor="end", lock=p_["tag"].lower() == "privado"))
        parts.append('</g>')
    save("projects.svg", parts)


# =============================================================================
# 5. STACK — etiquetas flotantes con logos
# =============================================================================
ICONS = json.load(open(os.path.join(ROOT, "data", "icons.json"), encoding="utf-8"))
# iconos propios (24x24) para lo que no está en simple-icons
EXTRA = {
    "windows": "M0 3.4L9.8 2v9.4H0zm11-1.6L24 0v11.3H11zM0 12.6h9.8V22L0 20.6zm11 0h13V24l-13-1.8z",
    "terminal": "M2 3h20a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm2.3 4.2L3 8.6l4 3.4-4 3.4 1.3 1.4L9.9 12zM11 15.5v2h8v-2z",
    "code": "M8.7 6.3L7.3 4.9 0.2 12l7.1 7.1 1.4-1.4L3 12zm6.6 0l1.4-1.4 7.1 7.1-7.1 7.1-1.4-1.4L21 12zM13.4 3l1.9.6-4.7 17.4-1.9-.6z",
    "radar": "M12 0a12 12 0 1 0 0 24 12 12 0 0 0 0-24zm0 2.2a9.8 9.8 0 0 1 9.7 8.3h-2.3A7.6 7.6 0 1 0 12 19.6v2.2A9.8 9.8 0 1 1 12 2.2zm0 4.4a5.4 5.4 0 0 1 5.2 3.9h-2.4A3.2 3.2 0 1 0 12 15.2v2.2a5.4 5.4 0 1 1 0-10.8zM12 10.9a1.1 1.1 0 1 1 0 2.2 1.1 1.1 0 0 1 0-2.2zm1.1.6l9-5.2 1.1 1.9-9 5.2z",
}


def icon_path(slug):
    if slug in EXTRA:
        return EXTRA[slug]
    return ICONS.get(slug, {}).get("path", EXTRA["terminal"])


def render_stack():
    W = 880
    groups = P.get("stack", [])
    FS = 13.5                     # tamaño de letra de las etiquetas
    CH = 34                       # alto de la etiqueta
    GAPX, GAPY = 10, 14
    LABEL_W = 150
    x_start, x_end = PAD + LABEL_W, W - PAD

    # 1) distribuir etiquetas en filas
    layout, y = [], TITLEBAR_H + 30
    for gi, (gname, items) in enumerate(groups):
        x = x_start
        row_y = y
        placed = []
        for name, slug, color in items:
            cw = 16 + 9 + len(name) * FS * 0.6 + 26
            if x + cw > x_end and placed:
                x, row_y = x_start, row_y + CH + GAPY
            placed.append((x, row_y, cw, name, slug, color))
            x += cw + GAPX
        layout.append((gname, y, placed))
        y = row_y + CH + 26
    H = int(y - 8)

    css = (".pop{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .55s cubic-bezier(.2,1.4,.4,1) both}"
           "@keyframes pop{0%{opacity:0;transform:translateY(14px) scale(.85)}100%{opacity:1;transform:none}}"
           ".fl{animation:fl ease-in-out infinite alternate}"
           "@keyframes fl{0%{transform:translateY(2px)}100%{transform:translateY(-5px)}}"
           ".sh{transform-box:fill-box;transform-origin:center;animation:sh ease-in-out infinite alternate}"
           "@keyframes sh{0%{transform:scaleX(1);opacity:.55}100%{transform:scaleX(.7);opacity:.18}}"
           ".lb{opacity:0;animation:lb .5s ease-out both}@keyframes lb{to{opacity:1}}")
    parts = svg_open(W, H, css)
    parts += window(W, H, f"{USER}@{HOST}: ~$ ./stack.sh --all")
    parts.append('<defs><filter id="blur" x="-30%" y="-200%" width="160%" height="500%">'
                 '<feGaussianBlur stdDeviation="3"/></filter></defs>')

    k = 0
    for gi, (gname, gy, placed) in enumerate(layout):
        parts.append(f'<text class="lb" style="animation-delay:{0.1 + gi * 0.15:.2f}s" x="{PAD}" '
                     f'y="{gy + CH / 2 + 5:.0f}" font-size="14" xml:space="preserve">'
                     f'<tspan fill="{GREEN}">▸ </tspan><tspan fill="{MUTED}">{esc(gname)}</tspan></text>')
        for (x, y, cw, name, slug, color) in placed:
            c = "#" + color.lstrip("#")
            dur = 2.6 + (k * 0.37) % 1.4          # cada etiqueta flota a su ritmo
            ph = -((k * 0.61) % dur)              # y desfasada
            appear = 0.2 + gi * 0.15 + (k % 6) * 0.05
            parts.append(f'<g class="pop" style="animation-delay:{appear:.2f}s">')
            # sombra que se achica cuando la etiqueta sube
            parts.append(f'<ellipse class="sh" style="animation-duration:{dur:.2f}s;animation-delay:{ph:.2f}s" '
                         f'cx="{x + cw / 2:.1f}" cy="{y + CH + 7:.1f}" rx="{cw / 2 - 6:.1f}" ry="3" fill="{c}" '
                         f'filter="url(#blur)"/>')
            parts.append(f'<g class="fl" style="animation-duration:{dur:.2f}s;animation-delay:{ph:.2f}s">')
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw:.1f}" height="{CH}" rx="9" fill="{TILE}" '
                         f'stroke="{c}" stroke-opacity="0.55"/>')
            parts.append(f'<rect x="{x + 1:.1f}" y="{y + 1:.1f}" width="{cw - 2:.1f}" height="{CH / 2 - 1:.1f}" rx="8" '
                         f'fill="{c}" fill-opacity="0.07"/>')
            s_ = 16 / 24
            parts.append(f'<path transform="translate({x + 13:.1f} {y + (CH - 16) / 2:.1f}) scale({s_:.4f})" '
                         f'd="{icon_path(slug)}" fill="{c}"/>')
            parts.append(f'<text x="{x + 13 + 16 + 9:.1f}" y="{y + CH / 2 + 5:.1f}" font-size="{FS}" '
                         f'font-weight="700" fill="{INK}">{esc(name)}</text>')
            parts.append('</g></g>')
            k += 1
    save("stack.svg", parts)


if __name__ == "__main__":
    render_boot()
    render_neofetch()
    render_experience()
    render_projects()
    render_stack()
