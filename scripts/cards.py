#!/usr/bin/env python3
"""Regenerate the profile SVG cards in assets/ from live GitHub data.

Usage: python3 scripts/cards.py   (needs an authenticated `gh`; private
activity only shows up if the token can see it).
"""
import json
import subprocess
from datetime import date
from html import escape
from pathlib import Path

NAME = "Adonnay Bazaldua"
ROLES = ["AI Engineer", "Data Scientist", "Statistician"]
TAGLINE = "Agentic systems, data pipelines and production APIs, built with a statistician's skepticism."

OUT = Path(__file__).resolve().parent.parent / "assets"

BG, BORDER, TEXT, MUTED, EMPTY = "#0d1117", "#30363d", "#e6edf3", "#8b949e", "#161b22"
TEAL, INDIGO = "#2dd4bf", "#818cf8"
HEAT = ["#0f3d3a", "#14695f", "#1aa390", TEAL]
LANG_COLORS = [TEAL, INDIGO, "#fbbf24", "#f472b6", "#64748b"]
# ponytail: notebooks/markup dwarf real code by bytes (one notebook = 50 MB of outputs), so they are left out of the mix
NOT_CODE = {"Jupyter Notebook", "HTML", "CSS", "TeX", "Roff"}
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

QUERY = """{ viewer {
  repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
    totalCount
    nodes { isPrivate languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
  }
  contributionsCollection {
    restrictedContributionsCount
    contributionCalendar { totalContributions weeks { contributionDays { date contributionCount weekday } } }
  }
} }"""


def longest_streak(counts):
    best = run = 0
    for c in counts:
        run = run + 1 if c else 0
        best = max(best, run)
    return best


assert longest_streak([0, 1, 1, 0, 1]) == 2 and longest_streak([]) == 0


def t(x, y, s, size=12, fill=TEXT, weight=400, font=SANS, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-family="{font}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}" {extra}>{escape(str(s))}</text>')


def card(name, w, h, title, body, defs=""):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
           f'aria-label="{escape(title)}"><title>{escape(title)}</title><defs>'
           f'<linearGradient id="g" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{TEAL}"/>'
           f'<stop offset="1" stop-color="{INDIGO}"/></linearGradient>'
           f'<clipPath id="c"><rect width="{w}" height="{h}" rx="12"/></clipPath>{defs}</defs>'
           f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>'
           f'{body}</svg>\n')
    (OUT / name).write_text(svg)


def eyebrow(x, y, s):
    return t(x, y, s.upper(), 11, MUTED, 600, MONO, extra='letter-spacing="1.5"')


def main():
    raw = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}"],
                         check=True, capture_output=True, text=True).stdout
    viewer = json.loads(raw)["data"]["viewer"]
    cc = viewer["contributionsCollection"]
    weeks = cc["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    counts = [d["contributionCount"] for d in days]
    total = cc["contributionCalendar"]["totalContributions"]
    active = sum(1 for c in counts if c)
    best = max(days, key=lambda d: d["contributionCount"])
    private_pct = round(100 * cc["restrictedContributionsCount"] / total) if total else 0
    repos = viewer["repositories"]
    n_private = sum(r["isPrivate"] for r in repos["nodes"])

    OUT.mkdir(exist_ok=True)

    # ── header: name + a year of weekly activity as the backdrop ──────────
    W, H = 840, 200
    wk = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks]
    top = max(wk) or 1
    pts = [(i * W / (len(wk) - 1), H - 8 - 50 * v / top) for i, v in enumerate(wk)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    sep = f'<tspan fill="{TEAL}"> · </tspan>'
    roles = (f'<text x="36" y="98" fill="{MUTED}" font-family="{SANS}" font-size="16" font-weight="500">'
             + sep.join(escape(r) for r in ROLES) + '</text>')
    card("header.svg", W, H, f"{NAME}: {', '.join(ROLES)}",
         f'<g clip-path="url(#c)"><polygon points="0,{H} {line} {W},{H}" fill="url(#a)"/>'
         f'<polyline points="{line}" fill="none" stroke="url(#g)" stroke-width="1.5" stroke-linejoin="round" opacity=".7"/></g>'
         + t(36, 66, NAME, 34, TEXT, 700, extra='letter-spacing="-.5"') + roles
         + t(36, 124, TAGLINE, 13, MUTED)
         + t(W - 20, 26, "weekly contributions, last 12 months", 10, MUTED, 400, MONO, "end", 'opacity=".7"'),
         f'<linearGradient id="a" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{TEAL}" stop-opacity=".22"/>'
         f'<stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></linearGradient>')

    # ── pulse: contribution calendar + the numbers that matter ───────────
    W, H, X0, Y0, STEP = 840, 318, 28, 112, 15
    nz = sorted(c for c in counts if c)
    cuts = [nz[len(nz) * q // 4] for q in (1, 2, 3)] if nz else [1, 2, 3]
    body = [eyebrow(X0, 36, "last 12 months"),
            f'<text x="{X0}" y="76" font-family="{SANS}"><tspan fill="{TEXT}" font-size="34" font-weight="700">{total:,}</tspan>'
            f'<tspan fill="{MUTED}" font-size="15" dx="8">contributions</tspan></text>',
            f'<text x="{W - X0}" y="76" text-anchor="end" font-family="{SANS}" font-size="14" fill="{MUTED}">'
            f'<tspan fill="{TEAL}" font-weight="700">{private_pct}%</tspan> in private repositories</text>']
    prev_month, last_label_x = None, -99
    for i, w in enumerate(weeks):
        x = X0 + i * STEP
        first = date.fromisoformat(w["contributionDays"][0]["date"])
        if first.month != prev_month and x - last_label_x > 30 and i < len(weeks) - 1:
            body.append(t(x, Y0 - 9, first.strftime("%b"), 10, MUTED, 400, MONO))
            last_label_x = x
        prev_month = first.month
        for d in w["contributionDays"]:
            c = d["contributionCount"]
            fill = EMPTY if not c else HEAT[sum(c > k for k in cuts)]
            body.append(f'<rect x="{x}" y="{Y0 + d["weekday"] * STEP}" width="12" height="12" rx="3" fill="{fill}"/>')
    ly = Y0 + 7 * STEP + 8
    lx = X0 + len(weeks) * STEP - 3 - 34
    body.append(t(lx - 5 * 15 - 6, ly + 10, "less", 10, MUTED, 400, MONO, "end"))
    for k, colr in enumerate([EMPTY] + HEAT):
        body.append(f'<rect x="{lx - (5 - k) * 15}" y="{ly}" width="12" height="12" rx="3" fill="{colr}"/>')
    body.append(t(lx + 3, ly + 10, "more", 10, MUTED, 400, MONO))
    stats = [(active, "active days"), (f"{longest_streak(counts)}d", "longest streak"),
             (f"{total / active:.1f}" if active else "0", "per active day"),
             (best["contributionCount"], "busiest day, " + date.fromisoformat(best["date"]).strftime("%b %-d")),
             (repos["totalCount"], f"repositories, {n_private} private")]
    body.append(f'<line x1="{X0}" x2="{W - X0}" y1="{ly + 28}" y2="{ly + 28}" stroke="{BORDER}" opacity=".6"/>')
    for i, (v, label) in enumerate(stats):
        x = X0 + i * (W - 2 * X0) / len(stats)
        body.append(t(x, ly + 58, v, 20, TEXT, 700) + t(x, ly + 76, label, 11, MUTED))
    card("pulse.svg", W, H, f"{total:,} contributions in the last 12 months, {private_pct}% in private repositories",
         "".join(body))

    # ── languages: share of source code by bytes ─────────────────────────
    W, H, X0 = 412, 196, 24
    sizes, notebooks = {}, 0
    for r in repos["nodes"]:
        langs = {e["node"]["name"]: e["size"] for e in r["languages"]["edges"]}
        notebooks += "Jupyter Notebook" in langs
        for k, v in langs.items():
            if k not in NOT_CODE:
                sizes[k] = sizes.get(k, 0) + v
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1])
    rows = ranked[:3] + ([("Other", sum(v for _, v in ranked[3:]))] if ranked[3:] else [])
    whole = sum(v for _, v in rows) or 1
    bw, x = W - 2 * X0, X0
    body = [eyebrow(X0, 36, "what I write"),
            f'<clipPath id="b"><rect x="{X0}" y="52" width="{bw}" height="10" rx="5"/></clipPath><g clip-path="url(#b)">']
    for (k, v), colr in zip(rows, LANG_COLORS):
        seg = bw * v / whole
        body.append(f'<rect x="{x:.1f}" y="52" width="{max(seg - 2, 1):.1f}" height="10" fill="{colr}"/>')
        x += seg
    body.append("</g>")
    for i, ((k, v), colr) in enumerate(zip(rows, LANG_COLORS)):
        cx, cy = X0 + (i % 2) * bw / 2, 92 + (i // 2) * 24
        pct = 100 * v / whole
        body.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="4.5" fill="{colr}"/>' + t(cx + 18, cy, k, 12.5, TEXT, 500)
                    + t(cx + bw / 2 - 16, cy, f"{pct:.0f}%" if pct >= 1 else "<1%", 12, MUTED, 400, MONO, "end"))
    body.append(t(X0, H - 20, f"source code by bytes · plus Jupyter notebooks in {notebooks} repos", 10.5, MUTED))
    card("languages.svg", W, H, "Languages: " + ", ".join(f"{k} {100 * v / whole:.0f}%" for k, v in rows), "".join(body))

    # ── rhythm: contributions by weekday ─────────────────────────────────
    by_wd = [0] * 7
    for d in days:
        by_wd[d["weekday"]] += d["contributionCount"]
    order = [1, 2, 3, 4, 5, 6, 0]  # GitHub weekday 0 = Sunday; show Monday first
    peak = max(by_wd) or 1
    names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    body = [eyebrow(X0, 36, "when I ship")]
    slot, base, maxh = (W - 2 * X0) / 7, 138, 66
    for i, wd in enumerate(order):
        h = max(maxh * by_wd[wd] / peak, 2)
        bx = X0 + i * slot + (slot - 30) / 2
        hot = by_wd[wd] == peak
        body.append(f'<rect x="{bx:.1f}" y="{base - h:.1f}" width="30" height="{h:.1f}" rx="4" '
                    f'fill="{"url(#g)" if hot else "#21303b"}"/>'
                    + t(bx + 15, base - h - 6, by_wd[wd], 10, TEXT if hot else MUTED, 600 if hot else 400, MONO, "middle")
                    + t(bx + 15, base + 16, names[wd], 10.5, TEXT if hot else MUTED, 400, SANS, "middle"))
    weekend = 100 * (by_wd[0] + by_wd[6]) / (sum(by_wd) or 1)
    body.append(t(X0, H - 20, f"contributions by weekday · {weekend:.0f}% on weekends", 10.5, MUTED))
    card("rhythm.svg", W, H, "Contributions by weekday: "
         + ", ".join(f"{names[wd]} {by_wd[wd]}" for wd in order), "".join(body))


if __name__ == "__main__":
    main()
