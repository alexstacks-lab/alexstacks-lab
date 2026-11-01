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


def yako_data_uri(max_h=220):
    """Yako (source/yako.png) recortado y reducido, embebido como PNG."""
    import base64, io
    from PIL import Image
    im = Image.open(os.path.join(ROOT, "source", "yako.png")).convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox())
    scale = (max_h * 1.25) / im.height              # 1.25x para que se vea nítido en pantallas retina
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.width / im.height


def paw(cx, cy, r, color):
    """Huellita: almohadilla + 4 deditos."""
    return (f'<ellipse cx="{cx:.1f}" cy="{cy + r * 0.35:.1f}" rx="{r * 0.62:.1f}" ry="{r * 0.5:.1f}" fill="{color}"/>'
            + "".join(f'<circle cx="{cx + dx * r:.1f}" cy="{cy + dy * r:.1f}" r="{r * 0.24:.1f}" fill="{color}"/>'
                      for dx, dy in [(-0.62, -0.28), (-0.22, -0.62), (0.22, -0.62), (0.62, -0.28)]))


def render_boot():
    W = 880
    YH = 200                                   # alto de Yako
    uri, ratio = yako_data_uri(YH)
    YW = YH * ratio
    boot = P.get("boot", [])
    line_h = 26
    yako_y = TITLEBAR_H + 22
    yx = W / 2 - YW / 2 - 70
    name_y = yako_y + YH + 52
    tag_y = name_y + 26
    sep_y = tag_y + 22
    lines_y = sep_y + 30
    H = int(lines_y + len(boot) * line_h + 18)

    css = (FADE_CSS +
           ".yk{transform-box:fill-box;transform-origin:50% 100%;opacity:0;"
           "animation:yin .7s cubic-bezier(.2,1.5,.4,1) .15s both}"
           "@keyframes yin{0%{opacity:0;transform:translateY(30px) scale(.8)}100%{opacity:1;transform:none}}"
           ".bob{animation:bob 2.4s ease-in-out .9s infinite alternate}"
           "@keyframes bob{0%{transform:translateY(0)}100%{transform:translateY(-7px)}}"
           ".shd{transform-box:fill-box;transform-origin:center;animation:shd 2.4s ease-in-out .9s infinite alternate}"
           "@keyframes shd{0%{transform:scaleX(1);opacity:.5}100%{transform:scaleX(.78);opacity:.25}}"
           ".pw{opacity:0;animation:pw 3.6s ease-out infinite}"
           "@keyframes pw{0%{opacity:0;transform:translateY(0) scale(.6)}15%{opacity:.9}"
           "100%{opacity:0;transform:translateY(-70px) scale(1)}}"
           ".bub{transform-box:fill-box;transform-origin:0% 80%;opacity:0;animation:bub .5s cubic-bezier(.2,1.5,.4,1) 1s both}"
           "@keyframes bub{0%{opacity:0;transform:scale(.6)}100%{opacity:1;transform:none}}")
    parts = svg_open(W, H, css)
    parts += window(W, H, f"{USER}@{HOST}: ~$ ./boot.sh")

    # sombra + Yako flotando
    parts.append(f'<ellipse class="shd" cx="{yx + YW / 2:.1f}" cy="{yako_y + YH + 6:.1f}" rx="{YW * 0.36:.1f}" ry="7" '
                 f'fill="#000" opacity=".5"/>')
    parts.append(f'<g class="yk"><g class="bob"><image href="{uri}" x="{yx:.1f}" y="{yako_y}" '
                 f'width="{YW:.1f}" height="{YH}"/></g></g>')
    # huellitas que suben
    for i, (dx, dy, r, c, d) in enumerate([(-24, 40, 7, PINK, 1.6), (YW + 8, 70, 6, CREAM, 2.8),
                                           (-8, 120, 5, SKIN, 4.0), (YW - 6, 150, 6, PINK, 5.1)]):
        parts.append(f'<g class="pw" style="animation-delay:{d:.1f}s">{paw(yx + dx, yako_y + dy, r, c)}</g>')

    # globo de diálogo
    bx, by_, bw, bh = yx + YW + 26, yako_y + 34, 300, 74
    parts.append(f'<g class="bub">')
    parts.append(f'<path d="M{bx + 14} {by_}h{bw - 28}a14 14 0 0 1 14 14v{bh - 28}a14 14 0 0 1 -14 14'
                 f'h{-(bw - 46)}l-14 16l2 -16h-2a14 14 0 0 1 -14 -14v{-(bh - 28)}a14 14 0 0 1 14 -14z" '
                 f'fill="{TILE}" stroke="{PINK}" stroke-opacity=".7"/>')
    parts.append('</g>')
    l1, l2 = "¡guau! soy Yako 🐾".replace(" 🐾", ""), "bienvenido al perfil de Alex"
    parts.append(wipe("bub1", bx + 14, by_ + 10, bw - 28, 26, 1.4, 0.6))
    parts.append(f'<g clip-path="url(#bub1)"><text x="{bx + 18}" y="{by_ + 30}" font-size="17" font-weight="700" '
                 f'fill="{CREAM}">{esc(l1)}</text></g>')
    parts.append(wipe("bub2", bx + 14, by_ + 38, bw - 28, 26, 2.0, 0.8))
    parts.append(f'<g clip-path="url(#bub2)"><text x="{bx + 18}" y="{by_ + 56}" font-size="14" '
                 f'fill="{MUTED}">{esc(l2)}</text></g>')
    parts.append(f'<g class="pw" style="animation-delay:2.9s;animation-duration:3s">'
                 f'{paw(bx + bw - 26, by_ + 26, 7, PINK)}</g>')

    parts.append(f'<text class="f" style="animation-delay:.6s" x="{W/2}" y="{name_y:.0f}" fill="{INK}" '
                 f'font-size="24" font-weight="700" text-anchor="middle">{esc(P["full_name"])}</text>')
    parts.append(f'<text class="f" style="animation-delay:.8s" x="{W/2}" y="{tag_y:.0f}" fill="{MUTED}" '
                 f'font-size="14" text-anchor="middle">{esc(P["tagline"])}</text>')
    parts.append(f'<line x1="{PAD}" y1="{sep_y:.0f}" x2="{W-PAD}" y2="{sep_y:.0f}" stroke="{FRAME}" stroke-dasharray="3 5"/>')

    t = 1.2
    for i, (status, msg) in enumerate(boot):
        y = lines_y + i * line_h
        col = GREEN if status == "OK" else GOLD
        label = f"[{status.center(6)}]"
        dur = 0.25 + len(msg) * 0.012
        parts.append(wipe(f"b{i}", PAD, y - 18, W - 2 * PAD, line_h, t, dur))
        parts.append(f'<g clip-path="url(#b{i})"><text x="{PAD}" y="{y:.0f}" font-size="15" xml:space="preserve">'
                     f'<tspan fill="{MUTED}">[</tspan><tspan fill="{col}" font-weight="700">{esc(status.center(6))}</tspan>'
                     f'<tspan fill="{MUTED}">] </tspan><tspan fill="{INK}">{esc(msg)}</tspan></text></g>')
        if status != "OK":
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
    "usb": "M9 1h6v7H9zm1.3 2v2h1.2V3zm2.2 0v2h1.2V3zM7 9h10v11a3 3 0 0 1-3 3h-4a3 3 0 0 1-3-3z",
    "wrench": "M21.7 6.3l-3.4 3.4-3.2-.8-.8-3.2 3.4-3.4A6 6 0 0 0 10 10.1L2.6 17.5a2 2 0 0 0 0 2.8l1.1 1.1a2 2 0 0 0 2.8 0L13.9 14a6 6 0 0 0 7.8-7.7z",
    "gear": "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm9 5.2v-2.4l-2.6-.6a7 7 0 0 0-.8-1.8l1.4-2.3-1.7-1.7-2.3 1.4a7 7 0 0 0-1.8-.8L12.6 2h-2.4l-.6 2.6a7 7 0 0 0-1.8.8L5.5 4 3.8 5.7l1.4 2.3a7 7 0 0 0-.8 1.8L2 10.4v2.4l2.6.6a7 7 0 0 0 .8 1.8L4 17.5l1.7 1.7 2.3-1.4a7 7 0 0 0 1.8.8l.6 2.6h2.4l.6-2.6a7 7 0 0 0 1.8-.8l2.3 1.4 1.7-1.7-1.4-2.3a7 7 0 0 0 .8-1.8z",
    "chip": "M6 6h12v12H6zM9 1h2v4H9zm4 0h2v4h-2zM9 19h2v4H9zm4 0h2v4h-2zM1 9h4v2H1zm0 4h4v2H1zm18-4h4v2h-4zm0 4h4v2h-4zM9.5 9.5v5h5v-5z",
    "disk": "M3 4h18a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1zm9 3a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 3.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z",
    "globe": "M12 1a11 11 0 1 0 0 22 11 11 0 0 0 0-22zM3.1 11h4c.1-2.7.7-5.1 1.6-6.9A9 9 0 0 0 3.1 11zm0 2a9 9 0 0 0 5.6 6.9c-.9-1.8-1.5-4.2-1.6-6.9zm6 0c.2 4.4 1.7 7.5 2.9 8 1.2-.5 2.7-3.6 2.9-8zm0-2h5.8c-.2-4.4-1.7-7.5-2.9-8-1.2.5-2.7 3.6-2.9 8zm7.9 0h4a9 9 0 0 0-5.6-6.9c.9 1.8 1.5 4.2 1.6 6.9zm0 2c-.1 2.7-.7 5.1-1.6 6.9a9 9 0 0 0 5.6-6.9z",
    "shield": "M12 1L3 5v6c0 5.6 3.8 10.7 9 12 5.2-1.3 9-6.4 9-12V5zm-1.2 15.2L6.6 12l1.4-1.4 2.8 2.8 5.2-5.2 1.4 1.4z",
    "kanban": "M2 3h6v18H2zm7 0h6v12H9zm7 0h6v8h-6z",
    "heart": "M12 21l-1.5-1.3C5 15 2 12.2 2 8.6A5.4 5.4 0 0 1 7.5 3c1.8 0 3.4.9 4.5 2.2A5.9 5.9 0 0 1 16.5 3 5.4 5.4 0 0 1 22 8.6c0 3.6-3 6.4-8.5 11.1z",
    "game": "M7 6h10a5 5 0 0 1 5 5v4a3 3 0 0 1-5.4 1.8L15 15H9l-1.6 1.8A3 3 0 0 1 2 15v-4a5 5 0 0 1 5-5zm0 3v2H5v2h2v2h2v-2h2v-2H9V9zm9.5 1a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm-2 2a1 1 0 1 0 0 2 1 1 0 0 0 0-2z",
    "flag": "M4 2h2v20H4zm3 1h12l-3 4 3 4H7z",
    "cycle": "M12 4V1L7.5 5.5 12 10V7a5 5 0 1 1-5 5H4a8 8 0 1 0 8-8z",
}


def icon_rule(slug):
    return ' fill-rule="evenodd"' if slug in EXTRA else ""


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
                         f'd="{icon_path(slug)}" fill="{c}"{icon_rule(slug)}/>')
            parts.append(f'<text x="{x + 13 + 16 + 9:.1f}" y="{y + CH / 2 + 5:.1f}" font-size="{FS}" '
                         f'font-weight="700" fill="{INK}">{esc(name)}</text>')
            parts.append('</g></g>')
            k += 1
    save("stack.svg", parts)


# =============================================================================
# 6. CONTACTO — una etiqueta flotante por archivo (para que cada una sea un enlace)
# =============================================================================
def contact_chip(fname, label, value, color, slug=None, dot=False, delay=0.0):
    FS = 14
    text_w = (len(label) + len(value) + 2) * FS * 0.6
    icon_w = 18
    cw = 14 + icon_w + 10 + text_w + 16
    CH = 38
    W, H = int(cw + 8), CH + 22                     # espacio para flotar y la sombra
    x, y = 4, 6
    c = "#" + color.lstrip("#")
    dur = 2.4 + (len(fname) * 0.23) % 1.3
    css = (".pop{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .55s cubic-bezier(.2,1.4,.4,1) both}"
           "@keyframes pop{0%{opacity:0;transform:scale(.8)}100%{opacity:1;transform:none}}"
           f".fl{{animation:fl {dur:.2f}s ease-in-out infinite alternate}}"
           "@keyframes fl{0%{transform:translateY(3px)}100%{transform:translateY(-3px)}}"
           f".sh{{transform-box:fill-box;transform-origin:center;animation:sh {dur:.2f}s ease-in-out infinite alternate}}"
           "@keyframes sh{0%{transform:scaleX(1);opacity:.6}100%{transform:scaleX(.75);opacity:.2}}")
    parts = svg_open(W, H, css)
    parts.append('<defs><filter id="bl" x="-30%" y="-300%" width="160%" height="700%">'
                 '<feGaussianBlur stdDeviation="3"/></filter></defs>')
    parts.append(f'<g class="pop" style="animation-delay:{delay:.2f}s">')
    parts.append(f'<ellipse class="sh" cx="{x + cw / 2:.1f}" cy="{y + CH + 8}" rx="{cw / 2 - 8:.1f}" ry="3" '
                 f'fill="{c}" filter="url(#bl)"/>')
    parts.append('<g class="fl">')
    parts.append(f'<rect x="{x}" y="{y}" width="{cw:.1f}" height="{CH}" rx="10" fill="{TILE}" '
                 f'stroke="{c}" stroke-opacity=".65"/>')
    parts.append(f'<rect x="{x + 1}" y="{y + 1}" width="{cw - 2:.1f}" height="{CH / 2 - 1}" rx="9" fill="{c}" fill-opacity=".08"/>')
    ix, iy = x + 14, y + (CH - icon_w) / 2
    if dot:
        parts.append(f'<circle cx="{ix + 9}" cy="{iy + 9}" r="5" fill="{c}"/>'
                     f'<circle cx="{ix + 9}" cy="{iy + 9}" r="5" fill="none" stroke="{c}" stroke-width="1.5">'
                     f'<animate attributeName="r" values="5;10" dur="1.6s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values=".9;0" dur="1.6s" repeatCount="indefinite"/></circle>')
    elif slug == "linkedin":
        parts.append(f'<rect x="{ix}" y="{iy}" width="18" height="18" rx="3.5" fill="{c}"/>'
                     f'<text x="{ix + 9}" y="{iy + 14}" font-size="12.5" font-weight="700" fill="{BG}" '
                     f'text-anchor="middle" font-family="Arial, Helvetica, sans-serif">in</text>')
    elif slug:
        parts.append(f'<path transform="translate({ix} {iy}) scale(0.75)" d="{icon_path(slug)}" fill="{c}"{icon_rule(slug)}/>')
    parts.append(f'<text x="{ix + icon_w + 10}" y="{y + CH / 2 + 5}" font-size="{FS}" xml:space="preserve">'
                 f'<tspan fill="{INK}" font-weight="700">{esc(label)}</tspan>'
                 f'<tspan fill="{MUTED}">  {esc(value)}</tspan></text>')
    parts.append('</g></g>')
    os.makedirs(os.path.join(ASSETS, "contact"), exist_ok=True)
    save(f"contact/{fname}.svg", parts)


def render_contact():
    chips = [
        ("disponible", "Disponible", "prácticas pre-profesionales", "39d353", None, True),
        ("lima", "Lima", "Perú", "e8857f", "googlemaps", False),
        ("linkedin", "LinkedIn", "Alexandro Alanya", "2E8BEA", "linkedin", False),
        ("gmail", "Gmail", "alexandropriv2005@gmail.com", "EA4335", "gmail", False),
        ("instagram", "Instagram", "alexandroam_", "FF4F8B", "instagram", False),
        ("x", "X", "@tobicode2005", "E6EDF3", "x", False),
        ("github", "GitHub", "alexstacks-lab", "3FB950", "github", False),
    ]
    for i, (f, l, v, c, slug, dot) in enumerate(chips):
        contact_chip(f, l, v, c, slug, dot, delay=0.1 + i * 0.08)


# =============================================================================
# 7. HACK THE BOX — último pwn
# =============================================================================
HTB_BG1, HTB_BG2, HTB_LIME, HTB_TILE = "#1a2332", "#0b121c", "#9FEF00", "#111927"


def count_up(x, y, value, start, size, color, fmt="{:,}", prefix="", frames=14, dur=1.1, anchor="start"):
    out = []
    for k in range(1, frames + 1):
        v = value * (1 - (1 - k / frames) ** 3)
        on = start + dur * (k - 1) / frames
        anim = f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>'
        if k < frames:
            anim += f'<set attributeName="opacity" to="0" begin="{start + dur * k / frames:.3f}s"/>'
        out.append(f'<text x="{x}" y="{y}" opacity="0" font-size="{size}" font-weight="700" fill="{color}" '
                   f'text-anchor="{anchor}">{prefix}{fmt.format(int(round(v)))}{anim}</text>')
    return "".join(out)


def render_htb():
    h = P.get("htb")
    if not h:
        return
    W, H = 880, 250
    css = (FADE_CSS + ".ring{transform-box:fill-box;transform-origin:center;animation:spin 14s linear infinite}"
           "@keyframes spin{to{transform:rotate(360deg)}}"
           ".glw{animation:glw 2.4s ease-in-out infinite alternate}@keyframes glw{0%{opacity:.25}100%{opacity:.7}}")
    parts = svg_open(W, H, css)
    parts += window(W, H, f"{USER}@{HOST}: ~$ ./htb.sh --last-pwn", "hbg", HTB_BG1, HTB_BG2, "#2a3a52", "#8b9bb4")
    parts.append('<defs><filter id="hg"><feGaussianBlur stdDeviation="8"/></filter></defs>')
    # logo con anillo girando
    cx, cy, r = 110, 140, 62
    parts.append(f'<circle class="glw" cx="{cx}" cy="{cy}" r="{r}" fill="{HTB_LIME}" filter="url(#hg)"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{HTB_TILE}" stroke="{HTB_LIME}" stroke-width="3"/>')
    parts.append(f'<circle class="ring" cx="{cx}" cy="{cy}" r="{r + 9}" fill="none" stroke="{HTB_LIME}" '
                 f'stroke-width="2" stroke-dasharray="6 10" stroke-opacity=".6"/>')
    parts.append(f'<path transform="translate({cx - 30} {cy - 30}) scale(2.5)" d="{icon_path("hackthebox")}" fill="{HTB_LIME}"/>')
    # texto
    x0 = 210
    parts.append(f'<text class="f" style="animation-delay:.2s" x="{x0}" y="78" font-size="13" fill="#8b9bb4">'
                 f'Hack The Box · <tspan fill="{HTB_LIME}" font-weight="700">{esc(h["user"])}</tspan></text>')
    parts.append(f'<text class="f" style="animation-delay:.35s" x="{x0}" y="112" font-size="26" font-weight="700" '
                 f'fill="{INK}">Pwned: <tspan fill="{HTB_LIME}">{esc(h["machine"])}</tspan></text>')
    lines = [("[+]", "user.txt", "capturada"), ("[+]", "root.txt", "capturada")]
    t = 0.7
    for i, (pre, flag, st) in enumerate(lines):
        y = 146 + i * 24
        parts.append(wipe(f"hf{i}", x0, y - 16, 330, 22, t, 0.5))
        parts.append(f'<g clip-path="url(#hf{i})"><text x="{x0}" y="{y}" font-size="14" xml:space="preserve">'
                     f'<tspan fill="{HTB_LIME}" font-weight="700">{pre}</tspan><tspan fill="{INK}"> {flag}</tspan>'
                     f'<tspan fill="#8b9bb4">  {st}</tspan></text></g>')
        t += 0.55
    parts.append(f'<text class="f" style="animation-delay:{t + .1:.2f}s" x="{x0}" y="{146 + 2 * 24 + 8}" font-size="12.5" '
                 f'fill="#8b9bb4">ruta: {esc(h.get("path", ""))}</text>')
    # tarjetas de números
    tiles = [("machine rank", h["rank"], "#", HTB_LIME), ("XP ganada", h["xp"], "", "#C084FC"), ("fecha", None, h["date"], INK)]
    tx, tw, th, ty = 560, 300, 54, 52
    for i, (lab, val, extra, col) in enumerate(tiles):
        y = ty + i * (th + 10)
        parts.append(f'<g class="f" style="animation-delay:{.4 + i * .15:.2f}s">'
                     f'<rect x="{tx}" y="{y}" width="{tw}" height="{th}" rx="9" fill="{HTB_TILE}" stroke="#2a3a52"/>'
                     f'<text x="{tx + 16}" y="{y + 33}" font-size="13" fill="#8b9bb4">$ {esc(lab)}</text></g>')
        if val is None:
            parts.append(f'<text class="f" style="animation-delay:{.6 + i * .15:.2f}s" x="{tx + tw - 16}" y="{y + 36}" '
                         f'font-size="20" font-weight="700" fill="{col}" text-anchor="end">{esc(extra)}</text>')
        else:
            parts.append(count_up(tx + tw - 16, y + 37, val, .6 + i * .15, 24, col, prefix=extra, anchor="end",
                                  fmt="{}" if extra == "#" else "{:,}"))
    save("htb.svg", parts)


# =============================================================================
# 8. AHORA MISMO y FUN FACTS
# =============================================================================
NOW_COL = {"green": GREEN, "lime": "#9FEF00", "pink": PINK, "cyan": CYAN, "gold": GOLD, "sage": SAGE}


def render_now():
    items = P.get("now", [])
    if not items:
        return
    W = 880
    top, lh = TITLEBAR_H + 36, 34
    H = top + len(items) * lh + 6
    parts = svg_open(W, H, FADE_CSS)
    parts += window(W, H, f"{USER}@{HOST}: ~$ ./ahora.sh --live")
    t = 0.2
    for i, (col, text) in enumerate(items):
        y = top + i * lh
        c = NOW_COL.get(col, GREEN)
        dur = 0.3 + len(text) * 0.012
        # punto que late (desfasado para que no latan todos a la vez)
        parts.append(f'<circle cx="{PAD + 8}" cy="{y - 5}" r="4.5" fill="{c}"/>'
                     f'<circle cx="{PAD + 8}" cy="{y - 5}" r="4.5" fill="none" stroke="{c}" stroke-width="1.5">'
                     f'<animate attributeName="r" values="4.5;11" dur="2s" begin="{i * .33:.2f}s" repeatCount="indefinite"/>'
                     f'<animate attributeName="opacity" values=".9;0" dur="2s" begin="{i * .33:.2f}s" repeatCount="indefinite"/></circle>')
        parts.append(wipe(f"n{i}", PAD + 22, y - 18, W - 2 * PAD - 22, 26, t, dur))
        parts.append(f'<g clip-path="url(#n{i})"><text x="{PAD + 26}" y="{y}" font-size="15" fill="{INK}">{esc(text)}</text></g>')
        t += dur * 0.6
    save("now.svg", parts)


def render_fun():
    items = P.get("fun_facts", [])
    if not items:
        return
    W = 880
    top, lh = TITLEBAR_H + 36, 36
    H = top + len(items) * lh - 14
    css = FADE_CSS + (".wg{transform-box:fill-box;transform-origin:center;animation:wg 1.6s ease-in-out infinite alternate}"
                      "@keyframes wg{0%{transform:rotate(-10deg)}100%{transform:rotate(10deg)}}")
    parts = svg_open(W, H, css)
    parts += window(W, H, f"{USER}@{HOST}: ~$ cat -n ~/fun_facts.txt")
    cols = {"paw": PINK, "chip": GOLD, "game": CYAN, "heart": "#ff6b81"}
    for i, (icon, text, logos) in enumerate(items):
        y = top + i * lh
        d = 0.2 + i * 0.18
        c = cols.get(icon, GREEN)
        parts.append(f'<g class="f" style="animation-delay:{d:.2f}s">')
        parts.append(f'<text x="{PAD}" y="{y}" font-size="14" fill="{MUTED}">{i + 1:>2}</text>')
        ix, iy = PAD + 34, y - 15
        if icon == "paw":
            parts.append(f'<g class="wg">{paw(ix + 9, iy + 10, 9, c)}</g>')
        else:
            parts.append(f'<g class="wg"><path transform="translate({ix} {iy}) scale(0.75)" d="{icon_path(icon)}" '
                         f'fill="{c}"{icon_rule(icon)}/></g>')
        parts.append(f'<text x="{ix + 30}" y="{y}" font-size="15" fill="{INK}">{esc(text)}</text>')
        lx = ix + 30 + len(text) * 15 * 0.6 + 14
        for j, slug in enumerate(logos):
            col = "#" + ICONS[slug]["hex"] if slug != "mclaren" else "#FF8000"
            if slug == "dota2":
                col = "#E0503B"
            parts.append(f'<path transform="translate({lx + j * 26:.1f} {iy}) scale(0.75)" d="{icon_path(slug)}" fill="{col}"/>')
        parts.append('</g>')
    save("fun.svg", parts)


if __name__ == "__main__":
    render_boot()
    render_neofetch()
    render_experience()
    render_projects()
    render_stack()
    render_contact()
    render_htb()
    render_now()
    render_fun()
