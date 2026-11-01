"""
Paleta y helpers compartidos por todas las tarjetas SVG del perfil.

Base: el modo oscuro de GitHub (para que las tarjetas se vean "nativas").
Acentos: tomados del polo del personaje (rosa, salvia, crema) + verde terminal.
Cambia aquí un color y se actualizan todas las tarjetas.
"""

FONT = "ui-monospace, SFMono-Regular, 'JetBrains Mono', Menlo, Consolas, monospace"

BG = "#0d1117"
BG2 = "#111722"
TILE = "#161b22"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"

GREEN = "#39d353"     # terminal / contribuciones
CYAN = "#22d3ee"      # comandos y enlaces
PINK = "#e8857f"      # franja rosa del polo
SAGE = "#7fae8c"      # franja verde salvia del polo
CREAM = "#fbe8c8"     # base crema del polo
SKIN = "#efa157"      # tono del personaje
GOLD = "#f2cc60"

TITLEBAR_H = 30
PAD = 20

# Usuario y prompt que aparecen en todas las ventanas
USER = "alex"
HOST = "github"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# Paleta "hacker clásico" (verde y negro) para la sección whoami
HK_BG1 = "#020b04"
HK_BG2 = "#000000"
HK_FRAME = "#1d6b31"
HK_GREEN = "#00ff41"     # verde Matrix
HK_MID = "#00c934"
HK_DIM = "#0f7a2a"
HK_PALE = "#a6f5b5"
HK_TITLE = "#2f9e4f"


def window(w, h, title, grad_id="bg", bg1=BG2, bg2=BG, frame=FRAME, title_col=MUTED, dots=None):
    """Marco de ventana de terminal: fondo, borde, barra con los 3 puntos y título."""
    dots = dots or ["#ff5f56", "#ffbd2e", "#27c93f"]
    parts = [
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/>'
        f'</linearGradient></defs>',
        f'<rect width="{w}" height="{h}" rx="12" fill="url(#{grad_id})"/>',
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="none" stroke="{frame}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{w}" y2="{TITLEBAR_H}" stroke="{frame}"/>',
    ]
    for i, dot in enumerate(dots):
        parts.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dot}"/>')
    parts.append(f'<text x="{w/2}" y="{TITLEBAR_H/2 + 4}" fill="{title_col}" font-size="12" '
                 f'text-anchor="middle">{esc(title)}</text>')
    return parts


def hacker_window(w, h, title, grad_id="bg"):
    return window(w, h, title, grad_id, HK_BG1, HK_BG2, HK_FRAME, HK_TITLE,
                  [HK_GREEN, HK_MID, HK_DIM])


def svg_open(w, h, extra_css=""):
    css = ("@media (prefers-reduced-motion: reduce){*{animation:none!important;"
           "opacity:1!important;transform:none!important}}" + extra_css)
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="{FONT}">', f'<style>{css}</style>']
