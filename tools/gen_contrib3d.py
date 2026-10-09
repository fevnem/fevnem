#!/usr/bin/env python3
"""Author images/contrib-3d.svg -- an isometric 3-D contribution calendar.

One-off authoring tool (not wired to any workflow):

    python3 tools/gen_contrib3d.py [contributions.json]

Data source: the GitHub GraphQL contribution calendar for the last 12 months.
If no JSON path is given the script asks `gh` for it, falling back to
~/.hermes/cache/scratch/fevnem/contrib.json.

Layout notes (learned the hard way):
  * the 53x7 grid projects to a long thin diamond; the empty upper-left and
    lower-left corners are where the title, total and legend go
  * month ticks ride the front (day-7) edge so they never collide with bars
  * empty cells are filled without a stroke -- stroking them aliases into moire
"""
import json
import math
import pathlib
import subprocess
import sys

W, H = 900, 400
OX, OY = 190.0, 126.0       # far corner of the base plane
TW, TH = 20.0, 10.0         # isometric tile width / height (2:1)
BZ = 3.05                   # pixels of height per contribution
DAYS, WEEKS = 7, 53

QUERY = ('{user(login:"fevnem"){contributionsCollection{contributionCalendar'
         '{totalContributions,weeks{contributionDays{contributionCount,date}}}}}}')
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

THEMES = {
    "dark": dict(bg0="#0a0710", bg1="#150e26", grid="#2a1c4d", ink="#efe9ff",
                 dim="#b9a5ea", tick="#e2d7ff", empty="#241b46", empty_top="#2e2358",
                 plane="#0f0a1e", plane_edge="#4a3778",
                 scale=[("#4a2586", "#341a5f"), ("#7c3aed", "#5b21b6"),
                        ("#b41fbb", "#8b158f"), ("#FF00F6", "#c026d3")],
                 total="#FF00F6"),
    "light": dict(bg0="#ffffff", bg1="#f5f2ff", grid="#e6dff8", ink="#1a1030",
                  dim="#6b5a99", tick="#412f70", empty="#e6dff8", empty_top="#efebfb",
                  plane="#f7f4ff", plane_edge="#b9a8e6",
                  scale=[("#7c3aed", "#a78bfa"), ("#a21caf", "#c026d3"),
                         ("#d600d0", "#e879f9"), ("#c200c2", "#f0abfc")],
                  total="#a21caf"),
}


def load_calendar(argv):
    if len(argv) > 1:
        return json.loads(pathlib.Path(argv[1]).read_text())
    try:
        raw = subprocess.run(["gh", "api", "graphql", "-f", f"query={QUERY}"],
                             capture_output=True, text=True, check=True).stdout
        return json.loads(raw)
    except Exception:                                            # noqa: BLE001
        return json.loads((pathlib.Path.home()
                           / ".hermes/cache/scratch/fevnem/contrib.json").read_text())


def iso(w, d, h=0.0):
    return (OX + (w + d) * (TW / 2), OY + (w - d) * (TH / 2) - h)


def shade(hex_color, factor):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * factor), int(g * factor), int(b * factor))


def level(count, cuts):
    for i, c in enumerate(cuts):
        if count >= c:
            return i + 1
    return 0


def column(w, d, count, pal, cuts):
    h = count * BZ
    top, r, f, b = iso(w, d, h), iso(w + 1, d, h), iso(w, d + 1, h), iso(w + 1, d + 1, h)
    rb, fb, bb = iso(w + 1, d), iso(w, d + 1), iso(w + 1, d + 1)
    lv = level(count, cuts)
    if lv == 0:
        top_fill, side = pal["empty_top"], pal["empty"]
    else:
        top_fill, side = pal["scale"][lv - 1]
    side_b = shade(side, 0.74)
    svg = ""
    if count:
        svg += (f'<path d="M{r[0]:.1f} {r[1]:.1f} L{b[0]:.1f} {b[1]:.1f} '
                f'L{bb[0]:.1f} {bb[1]:.1f} L{rb[0]:.1f} {rb[1]:.1f} Z" fill="{side}"/>'
                f'<path d="M{f[0]:.1f} {f[1]:.1f} L{b[0]:.1f} {b[1]:.1f} '
                f'L{bb[0]:.1f} {bb[1]:.1f} L{fb[0]:.1f} {fb[1]:.1f} Z" fill="{side_b}"/>')
    svg += (f'<path d="M{top[0]:.1f} {top[1]:.1f} L{r[0]:.1f} {r[1]:.1f} '
            f'L{b[0]:.1f} {b[1]:.1f} L{f[0]:.1f} {f[1]:.1f} Z" fill="{top_fill}"'
            + (f' stroke="{pal["plane_edge"]}" stroke-opacity="1"'
               f' stroke-width="1"' if lv == 0 else '') + '/>')
    return (w - d, svg)


def build(mode, cal):
    pal = THEMES[mode]
    weeks = cal["weeks"]
    days = [d for wk in weeks for d in wk["contributionDays"]]
    peak = max(d["contributionCount"] for d in days) or 1
    cuts = sorted({max(1, math.ceil(peak * f)) for f in (.10, .25, .48, .75)})

    cols = []
    for wi, wk in enumerate(weeks):
        for di, day in enumerate(wk["contributionDays"]):
            cols.append(column(wi, di, day["contributionCount"], pal, cuts))
    cols.sort(key=lambda c: c[0])                     # back-to-front overlap

    a, b, c, d = iso(0, 0), iso(WEEKS, 0), iso(WEEKS, DAYS), iso(0, DAYS)
    plane = (f'<path d="M{a[0]:.1f} {a[1]:.1f} L{b[0]:.1f} {b[1]:.1f} '
             f'L{c[0]:.1f} {c[1]:.1f} L{d[0]:.1f} {d[1]:.1f} Z" fill="{pal["plane"]}"'
             f' stroke="{pal["plane_edge"]}" stroke-width="1"/>')

    ticks = []
    marks, seen = [], set()
    for wi, wk in enumerate(weeks):
        m = wk["contributionDays"][0]["date"][:7]
        if m not in seen:
            seen.add(m)
            marks.append((wi, m))
    if len(marks) > 1 and marks[0][1][5:] == marks[-1][1][5:]:
        marks.pop()                                   # trailing partial month
    for wi, m in marks:
        x, y = iso(wi, DAYS + 0.05)
        ticks.append(f'<text x="{x - 4:.0f}" y="{y + 17:.0f}" font-size="14"'
                     f' font-family="ui-monospace,Menlo,monospace" fill="{pal["tick"]}"'
                     f' letter-spacing="1">{MONTHS[int(m[5:7]) - 1]}</text>')

    legend = [f'<text x="{a[0] - 178:.0f}" y="{H - 44}" font-size="11"'
              f' font-family="ui-monospace,Menlo,monospace" fill="{pal["dim"]}"'
              f' letter-spacing="1.4">LESS</text>']
    for i in range(5):
        fill = pal["empty_top"] if i == 0 else pal["scale"][i - 1][0]
        legend.append(f'<rect x="{a[0] - 134 + i * 19:.0f}" y="{H - 56}" width="14"'
                      f' height="14" rx="3" fill="{fill}" stroke="{pal["plane_edge"]}"'
                      f' stroke-width=".7"/>')
    legend.append(f'<text x="{a[0] - 134 + 5 * 19 + 4:.0f}" y="{H - 44}" font-size="11"'
                  f' font-family="ui-monospace,Menlo,monospace" fill="{pal["dim"]}"'
                  f' letter-spacing="1.4">MORE</text>')
    legend.append(f'<text x="{a[0] - 178:.0f}" y="{H - 68}" font-size="11"'
                  f' font-family="ui-monospace,Menlo,monospace" fill="{pal["dim"]}"'
                  f' letter-spacing="1.4">CONTRIBUTIONS PER DAY</text>')

    total = str(cal["totalContributions"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="ct cd">
<title id="ct">Contribution calendar, 3-D</title>
<desc id="cd">{cal['totalContributions']} contributions over the last 12 months, drawn as an isometric bar field.</desc>
<defs>
<linearGradient id="cbg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{pal['bg0']}"/><stop offset="1" stop-color="{pal['bg1']}"/></linearGradient>
<filter id="cglow" x="-12%" y="-12%" width="124%" height="128%">
  <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#7C3AED" flood-opacity=".3"/></filter>
</defs>
<rect width="{W}" height="{H}" fill="url(#cbg)"/>
<g filter="url(#cglow)">{plane}{"".join(c[1] for c in cols)}</g>
{"".join(ticks)}
<text x="30" y="56" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="12" letter-spacing="3" fill="{pal['dim']}">CONTRIBUTION FIELD &#183; LAST 12 MONTHS</text>
<text x="30" y="118" font-family="'Segoe UI',system-ui,-apple-system,Arial,sans-serif" font-size="46" font-weight="800" fill="{pal['total']}">{total}</text>
<text x="{30 + len(total) * 27 + 10}" y="118" font-family="ui-monospace,Menlo,monospace" font-size="13" letter-spacing="2.5" fill="{pal['dim']}">CONTRIBUTIONS</text>
{"".join(legend)}
</svg>
'''


def main():
    data = load_calendar(sys.argv)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    root = pathlib.Path(__file__).resolve().parent.parent / "images"
    for mode, name in (("dark", "contrib-3d.svg"), ("light", "contrib-3d-light.svg")):
        path = root / name
        path.write_text(build(mode, cal), encoding="utf-8")
        print(f"{name:22} {path.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
