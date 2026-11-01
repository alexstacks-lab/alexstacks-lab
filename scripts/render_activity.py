#!/usr/bin/env python3
"""
A partir de data/contributions.json dibuja:

  assets/heatmap.svg   calendario de contribuciones (53 semanas x 7 días) que se
                       revela en diagonal, con leyenda y resumen.
  assets/stats.svg     6 tarjetas con números que "cuentan hacia arriba" +
                       barras de contribuciones por mes.

    python scripts/render_activity.py
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import (TILE, FRAME, MUTED, INK, GREEN, CYAN, GOLD, PAD, TITLEBAR_H,
                   HOST, esc, svg_open, window)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = json.load(open(os.path.join(ROOT, "data", "contributions.json"), encoding="utf-8"))
PROFILE = json.load(open(os.path.join(ROOT, "data", "profile.json"), encoding="utf-8"))
USER = PROFILE.get("prompt_user", "alex")
ASSETS = os.path.join(ROOT, "assets")

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]   # niveles 0-4 de GitHub


def fecha_corta(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {MESES[d.month - 1].lower()}"


def save(name, parts):
    parts.append("</svg>")
    svg = "".join(parts)
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote assets/{name} ({len(svg)//1024} KB)")


# =============================================================================
# HEATMAP
# =============================================================================
def render_heatmap():
    CELL, GAP = 12, 3
    STEP = CELL + GAP
    LEFT_W, TOP_H = 34, 22
    days = DATA["days"]

    first = datetime.date.fromisoformat(days[0]["date"])
    grid, col = [], [None] * ((first.weekday() + 1) % 7)       # domingo = 0
    for d in days:
        wd = (datetime.date.fromisoformat(d["date"]).weekday() + 1) % 7
        while len(col) < wd:
            col.append(None)
        col.append(d)
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        grid.append(col + [None] * (7 - len(col)))

    art_w = len(grid) * STEP
    W = PAD + LEFT_W + art_w + PAD
    grid_top = TITLEBAR_H + TOP_H + 6
    grid_left = PAD + LEFT_W
    legend_y = grid_top + 7 * STEP + 8
    sep_y = legend_y + CELL + 14
    H = sep_y + 62

    css = (".c{opacity:0;animation:c .42s cubic-bezier(.2,.8,.2,1) both}"
           "@keyframes c{0%{opacity:0;transform:translateY(-6px)}100%{opacity:1;transform:none}}")
    parts = svg_open(W, H, css)
    parts += window(W, H, f"{USER}@{HOST}: ~$ ./contribuciones.sh --graph")

    seen = set()
    for ci, column in enumerate(grid):
        cell = next((c for c in column if c), None)
        if not cell:
            continue
        d = datetime.date.fromisoformat(cell["date"])
        if (d.year, d.month) not in seen and d.day <= 7:
            seen.add((d.year, d.month))
            parts.append(f'<text x="{grid_left + ci * STEP}" y="{TITLEBAR_H + 18}" fill="{MUTED}" '
                         f'font-size="10">{MESES[d.month - 1]}</text>')
    for wi, wn in [(1, "Lun"), (3, "Mié"), (5, "Vie")]:
        parts.append(f'<text x="{PAD}" y="{grid_top + wi * STEP + CELL * 0.8:.1f}" fill="{MUTED}" '
                     f'font-size="9">{wn}</text>')

    for ci, column in enumerate(grid):
        for ri, c in enumerate(column):
            if not c:
                continue
            lvl = max(0, min(4, c.get("level", 0)))
            n = c["count"]
            parts.append(f'<rect class="c" x="{grid_left + ci * STEP}" y="{grid_top + ri * STEP}" '
                         f'width="{CELL}" height="{CELL}" rx="2.5" fill="{PALETTE[lvl]}" '
                         f'style="animation-delay:{ci * 0.018 + ri * 0.045:.3f}s">'
                         f'<title>{c["date"]}: {n} contribución{"" if n == 1 else "es"}</title></rect>')

    lx = W - PAD - (len(PALETTE) * CELL + 40)
    parts.append(f'<text x="{lx - 6}" y="{legend_y + CELL * 0.8:.1f}" fill="{MUTED}" font-size="10" '
                 f'text-anchor="end">Menos</text>')
    for i, c in enumerate(PALETTE):
        parts.append(f'<rect x="{lx + i * CELL}" y="{legend_y}" width="{CELL - 2}" height="{CELL - 2}" rx="2" fill="{c}"/>')
    parts.append(f'<text x="{lx + len(PALETTE) * CELL + 4}" y="{legend_y + CELL * 0.8:.1f}" fill="{MUTED}" '
                 f'font-size="10">Más</text>')

    parts.append(f'<line x1="0" y1="{sep_y}" x2="{W}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.6"/>')
    cs, ls, best, rng = (DATA["current_streak"], DATA["longest_streak"], DATA["best_day"], DATA["range"])
    y1, y2 = sep_y + 24, sep_y + 46
    parts.append(f'<text x="{PAD}" y="{y1}" font-size="13" fill="{GREEN}"><tspan font-weight="700">'
                 f'{DATA["total_contributions"]:,}</tspan><tspan fill="{MUTED}"> contribuciones en el último año</tspan></text>')
    parts.append(f'<text x="{W - PAD}" y="{y1}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'{fecha_corta(rng["start"])} {rng["start"][:4]} → {fecha_corta(rng["end"])} {rng["end"][:4]}</text>')
    parts.append(f'<text x="{PAD}" y="{y2}" font-size="13" fill="{MUTED}">racha actual '
                 f'<tspan fill="{CYAN}" font-weight="700">{cs["length"]} días</tspan>   ·   más larga '
                 f'<tspan fill="{CYAN}" font-weight="700">{ls["length"]} días</tspan></text>')
    if best["count"]:
        parts.append(f'<text x="{W - PAD}" y="{y2}" font-size="12" fill="{MUTED}" text-anchor="end">mejor día '
                     f'<tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> el {fecha_corta(best["date"])}</text>')
    save("heatmap.svg", parts)
    return W


# =============================================================================
# STATS
# =============================================================================
def render_stats(W):
    H = 316
    LEFT_W = 548
    TG = 12
    TW = (LEFT_W - PAD - TG * 2) / 3
    TH = (H - TITLEBAR_H - PAD * 2 - TG) / 2
    top = TITLEBAR_H + PAD

    cur, lng, best = DATA["current_streak"], DATA["longest_streak"], DATA["best_day"]
    n_days = len(DATA["days"]) or 1

    def span(s):
        return f'{fecha_corta(s["start"])} – {fecha_corta(s["end"])}' if s["length"] else "¡empieza hoy!"

    tiles = [
        ("racha actual", cur["length"], " días", span(cur), GREEN),
        ("racha más larga", lng["length"], " días", span(lng), INK),
        ("contribuciones", DATA["total_contributions"], "", "último año", INK),
        ("días activos", DATA["active_days"], f" /{n_days}", f'{DATA["active_days"] / n_days:.0%} del año', INK),
        ("mejor día", best["count"], "", fecha_corta(best["date"]) if best["count"] else "—", GOLD),
        ("promedio / día", float(DATA["avg_per_active_day"]), "", "contribuciones", INK),
    ]

    css = (".t{opacity:0;animation:in .45s ease-out both}"
           "@keyframes in{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:none}}"
           ".b{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:g .6s ease-out both}"
           "@keyframes g{to{transform:scaleY(1)}}")
    parts = svg_open(W, H, css)
    parts += window(W, H, f"{USER}@{HOST}: ~$ ./stats.sh")

    FR, CNT = 14, 1.1
    for i, (label, value, suffix, caption, accent) in enumerate(tiles):
        x = PAD + (i % 3) * (TW + TG)
        y = top + (i // 3) * (TH + TG)
        st = i * 0.12
        parts.append(f'<g class="t" style="animation-delay:{st:.2f}s">')
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{TW:.1f}" height="{TH:.1f}" rx="9" fill="{TILE}" stroke="{FRAME}"/>')
        parts.append(f'<text x="{x + 14:.1f}" y="{y + 24:.1f}" fill="{MUTED}" font-size="12">$ {esc(label)}</text>')
        for k in range(1, FR + 1):
            p = k / FR
            v = value * (1 - (1 - p) ** 3)
            txt = f"{v:,.1f}" if isinstance(value, float) else f"{int(round(v)):,}"
            on = st + 0.3 + CNT * (k - 1) / FR
            anim = f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>'
            if k < FR:
                anim += f'<set attributeName="opacity" to="0" begin="{st + 0.3 + CNT * k / FR:.3f}s"/>'
            parts.append(f'<text x="{x + 14:.1f}" y="{y + 66:.1f}" opacity="0" font-size="32" font-weight="700" '
                         f'fill="{accent}">{txt}<tspan font-size="13" font-weight="400" fill="{MUTED}">{esc(suffix)}</tspan>{anim}</text>')
        parts.append(f'<text x="{x + 14:.1f}" y="{y + TH - 14:.1f}" fill="{MUTED}" font-size="11.5">{esc(caption)}</text>')
        parts.append('</g>')

    # barras por mes
    cx, cy = LEFT_W + 4, top
    cw, chh = W - PAD - cx, H - PAD - top
    parts.append(f'<g class="t" style="animation-delay:.5s"><rect x="{cx}" y="{cy}" width="{cw}" height="{chh}" '
                 f'rx="9" fill="{TILE}" stroke="{FRAME}"/>'
                 f'<text x="{cx + 14}" y="{cy + 24}" fill="{MUTED}" font-size="12">$ contribuciones / mes</text></g>')
    monthly = DATA["monthly"][-12:]
    pl, pr_, pt, pb = cx + 14, cx + cw - 14, cy + 48, cy + chh - 26
    slot = (pr_ - pl) / max(1, len(monthly))
    bw = slot * 0.62
    peak = max([m["total"] for m in monthly] + [1])
    for i, m in enumerate(monthly):
        h = max(2, (pb - pt) * m["total"] / peak)
        bx = pl + i * slot + (slot - bw) / 2
        d = 0.9 + i * 0.05
        fill = GREEN if m["total"] == peak and peak > 1 else "#26a641"
        parts.append(f'<rect class="b" x="{bx:.1f}" y="{pb - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2.5" '
                     f'fill="{fill}" style="animation-delay:{d:.2f}s"><title>{m["month"]}: {m["total"]}</title></rect>')
        mes = MESES[int(m["month"][5:7]) - 1][0]
        parts.append(f'<text x="{bx + bw / 2:.1f}" y="{pb + 16:.1f}" fill="{MUTED}" font-size="10.5" '
                     f'text-anchor="middle">{mes}</text>')
        if m["total"] == peak and peak > 1:
            parts.append(f'<text class="t" style="animation-delay:{d + 0.6:.2f}s" x="{bx + bw / 2:.1f}" '
                         f'y="{pb - h - 6:.1f}" fill="{INK}" font-size="10.5" text-anchor="middle">{peak:,}</text>')
    save("stats.svg", parts)


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    render_stats(render_heatmap())
