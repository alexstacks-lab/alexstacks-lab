#!/usr/bin/env python3
"""
Descarga tus contribuciones REALES del último año desde el endpoint público que
usa la propia página de perfil de GitHub (sin token, sin API) y escribe
data/contributions.json con los días + estadísticas derivadas (racha actual,
racha más larga, mejor día, totales por mes).

Lo ejecuta a diario .github/workflows/update-profile.yml
"""
import datetime
import json
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE = json.load(open(os.path.join(HERE, "..", "data", "profile.json"), encoding="utf-8"))
USERNAME = os.environ.get("GH_PROFILE_USER", PROFILE.get("github_user", "alexstacks-lab"))
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(HERE, "..", "data", "contributions.json")


def fetch_days():
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot/1.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("no se encontraron celdas del calendario: GitHub cambió su HTML", file=sys.stderr)
        sys.exit(1)

    tooltips = {t.get("for"): t.get_text(strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        text = tooltips.get(td.get("id"), "")
        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.match(r"([\d,]+)", text)
            count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": date, "count": count, "level": int(td.get("data-level") or 0)})
    days.sort(key=lambda d: d["date"])
    return days


def current_streak(days):
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1  # hoy aún no termina: no rompe la racha
    end_idx, streak = idx, 0
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1
    if streak == 0:
        return {"length": 0, "start": None, "end": None}
    return {"length": streak, "start": days[idx + 1]["date"], "end": days[end_idx]["date"]}


def longest_streak(days):
    best = {"length": 0, "start": None, "end": None}
    run, start = 0, None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0:
                start = i
            run += 1
            if run > best["length"]:
                best = {"length": run, "start": days[start]["date"], "end": d["date"]}
        else:
            run = 0
    return best


def build(days):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"])
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0.0,
        "current_streak": current_streak(days),
        "longest_streak": longest_streak(days),
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "days": days,
    }


if __name__ == "__main__":
    data = build(fetch_days())
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    print(f"{USERNAME}: {data['total_contributions']} contribuciones, "
          f"racha actual {data['current_streak']['length']}, más larga {data['longest_streak']['length']}")
