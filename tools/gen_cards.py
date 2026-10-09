#!/usr/bin/env python3
"""Author the static fallback stat cards (streak + activity).

These exist so the README has a committed, self-hosted snapshot behind the
live card embeds -- if a third-party stats service is down or rate-limited,
readers still see real numbers.

    python3 tools/gen_cards.py [contributions.json]
"""
import json
import pathlib
import subprocess
import sys

MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "'Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
QUERY = ('{user(login:"fevnem"){contributionsCollection{contributionCalendar'
         '{totalContributions,weeks{contributionDays{contributionCount,date}}}}}}')

THEMES = {
    "dark": dict(bg="#0d0b14", border="#2f1a47", div="#42306e", ink="#ffffff",
                 dim="#a08cc9", a1="#FF00F6", a2="#7C3AED", a3="#22D3EE",
                 grid="#241a3d"),
    "light": dict(bg="#ffffff", border="#e3dcf7", div="#d6cbf2", ink="#160e2c",
                  dim="#6f5f9c", a1="#d600d0", a2="#6d28d9", a3="#0891b2",
                  grid="#ece7fa"),
}


def load(argv):
    if len(argv) > 1:
        return json.loads(pathlib.Path(argv[1]).read_text())
    try:
        raw = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}"],
                             capture_output=True, text=True, check=True).stdout
        return json.loads(raw)
    except Exception:                                            # noqa: BLE001
        return json.loads((pathlib.Path.home()
                           / ".hermes/cache/scratch/fevnem/contrib.json").read_text())


def analyse(days):
    """total, current streak, longest streak, [(week_start_date, week_total)]."""
    total = sum(d["contributionCount"] for d in days)
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    seq = list(days)
    if seq and seq[-1]["contributionCount"] == 0:       # today may be unfinished
        seq.pop()
    current = 0
    for d in reversed(seq):
        if d["contributionCount"] > 0:
            current += 1
        else:
            break
    weeks = [(days[i]["date"], sum(x["contributionCount"] for x in days[i:i + 7]))
             for i in range(0, len(days), 7)]
    return total, current, longest, weeks


def streak_card(p, total, current, longest):
    W, H, third = 520, 200, 520 / 3
    cols = [(total, "TOTAL CONTRIBUTIONS"), (current, "CURRENT STREAK"),
            (longest, "LONGEST STREAK")]
    parts = []
    for i, (value, label) in enumerate(cols):
        cx = third * (i + 0.5)
        parts.append(f'<text x="{cx:.0f}" y="112" text-anchor="middle"'
                     f' font-family="{SANS}" font-size="42" font-weight="800"'
                     f' fill="url(#sg)">{value}</text>')
        parts.append(f'<text x="{cx:.0f}" y="141" text-anchor="middle"'
                     f' font-family="{MONO}" font-size="9.5" letter-spacing="1.4"'
                     f' fill="{p["dim"]}">{label}</text>')
        if i:
            parts.append(f'<line x1="{third * i:.0f}" y1="72" x2="{third * i:.0f}"'
                         f' y2="148" stroke="{p["div"]}" stroke-width="1.2"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="st sd">
<title id="st">Contribution streak snapshot</title>
<desc id="sd">{total} contributions, current streak {current} days, longest streak {longest} days.</desc>
<defs>
<clipPath id="scard"><rect width="{W}" height="{H}" rx="12"/></clipPath>
<linearGradient id="sg" gradientUnits="userSpaceOnUse" x1="30" y1="0" x2="490" y2="0">
<stop offset="0" stop-color="{p['a1']}"/><stop offset=".55" stop-color="{p['a2']}"/>
<stop offset="1" stop-color="{p['a3']}"/></linearGradient>
<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{p['a1']}" stop-opacity="0"/>
<stop offset=".45" stop-color="{p['a1']}" stop-opacity=".95"/>
<stop offset="1" stop-color="{p['a3']}" stop-opacity="0"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="12" fill="{p['bg']}" stroke="{p['border']}"/>
<g clip-path="url(#scard)"><rect x="0" y="0" width="{W}" height="4" fill="url(#sh)"/></g>
<text x="{W / 2:.0f}" y="44" text-anchor="middle" font-family="{MONO}" font-size="10.5" letter-spacing="2" fill="{p['dim']}">STREAK SNAPSHOT &#183; SELF-HOSTED</text>
{"".join(parts)}
<text x="24" y="{H - 20}" font-family="{MONO}" font-size="10" letter-spacing="2.4" fill="{p['dim']}">STATIC SNAPSHOT</text>
<text x="{W - 24}" y="{H - 20}" text-anchor="end" font-family="{MONO}" font-size="10" letter-spacing="1.6" fill="{p['dim']}">github.com/fevnem</text>
</svg>
'''


def activity_card(p, weeks):
    W, H = 880, 250
    L, R, T, B = 58, 28, 70, 48
    iw, ih = W - L - R, H - T - B
    totals = [w[1] for w in weeks]
    peak = max(totals) or 1
    axis_max = max(10, -(-int(peak * 1.12) // 10) * 10)   # round the top up to 10s
    scale = ih / axis_max
    step = iw / max(1, len(totals) - 1)
    pts = [(L + i * step, T + ih - v * scale) for i, v in enumerate(totals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = ("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
            + f" L{L + iw:.1f} {T + ih} L{L} {T + ih} Z")
    grid = "".join(
        f'<line x1="{L}" y1="{T + ih * i / 4:.0f}" x2="{L + iw}" y2="{T + ih * i / 4:.0f}"'
        f' stroke="{p["grid"]}" stroke-width="1"/>' for i in range(5))
    grid += (f'<text x="{L - 12}" y="{T + 4}" text-anchor="end" font-family="{MONO}"'
             f' font-size="10" fill="{p["dim"]}">{axis_max}</text>'
             f'<text x="{L - 12}" y="{T + ih + 4}" text-anchor="end"'
             f' font-family="{MONO}" font-size="10" fill="{p["dim"]}">0</text>')

    marks, seen = [], set()
    for i, (date, _) in enumerate(weeks):
        month = date[:7]
        if month not in seen:
            seen.add(month)
            marks.append((i, month))
    if len(marks) > 1 and marks[0][1][5:] == marks[-1][1][5:]:
        marks.pop()                                  # trailing partial month
    labels = [f'<text x="{L + i * step:.0f}" y="{H - 18}" font-family="{MONO}"'
              f' font-size="10" fill="{p["dim"]}" letter-spacing="1">'
              f'{MONTHS[int(m[5:7]) - 1]}</text>' for i, m in marks]
    px, py = pts[totals.index(peak)]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="at ad">
<title id="at">Contribution activity snapshot</title>
<desc id="ad">Weekly contribution totals for the last 12 months; peak week {peak}.</desc>
<defs>
<linearGradient id="af" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="{p['a2']}" stop-opacity=".55"/>
<stop offset="1" stop-color="{p['a1']}" stop-opacity="0"/></linearGradient>
<linearGradient id="al" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{p['a3']}"/><stop offset="1" stop-color="{p['a1']}"/></linearGradient>
</defs>
<rect width="{W}" height="{H}" rx="12" fill="{p['bg']}" stroke="{p['border']}"/>
{grid}
<path d="{area}" fill="url(#af)"/>
<polyline points="{line}" fill="none" stroke="url(#al)" stroke-width="2.4" stroke-linejoin="round"/>
<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{p['a1']}"/>
<text x="{px - 10:.0f}" y="{py - 12:.0f}" text-anchor="end" font-family="{MONO}" font-size="10" fill="{p['ink']}" letter-spacing="1">peak {peak}/week</text>
<line x1="{L}" y1="{T + ih}" x2="{L + iw}" y2="{T + ih}" stroke="{p['border']}" stroke-width="1"/>
{"".join(labels)}
<text x="{L}" y="42" font-family="{MONO}" font-size="11" letter-spacing="2.4" fill="{p['dim']}">ACTIVITY SNAPSHOT &#183; WEEKLY TOTALS, LAST 12 MONTHS</text>
</svg>
'''


def main():
    data = load(sys.argv)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for wk in cal["weeks"] for d in wk["contributionDays"]]
    total, current, longest, weeks = analyse(days)
    weeks = weeks[1:] if len(weeks) > 52 else weeks
    out = pathlib.Path(__file__).resolve().parent.parent / "images"
    for mode in ("dark", "light"):
        p = THEMES[mode]
        suffix = "" if mode == "dark" else "-light"
        (out / f"card-streak{suffix}.svg").write_text(
            streak_card(p, total, current, longest), encoding="utf-8")
        (out / f"card-activity{suffix}.svg").write_text(
            activity_card(p, weeks), encoding="utf-8")
    for f in sorted(out.glob("card-*.svg")):
        print(f"{f.name:26} {f.stat().st_size / 1024:6.1f} KB")
    print(f"total={total} current={current} longest={longest} weeks={len(weeks)} peak={max(w[1] for w in weeks)}")


if __name__ == "__main__":
    main()
