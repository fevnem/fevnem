#!/usr/bin/env python3
"""Author the fevnem README hero banner (dark + light).

One-off authoring tool -- run manually:

    python3 tools/gen_hero.py

Deliberately NOT wired into any workflow. The generated SVGs are committed, so
the README renders with zero build steps and zero services.

Geometry: a real 3-D wireframe sphere (latitude rings + meridians) lit by a
fixed camera at 20 degrees elevation, tilted on its axis and spun with an SMIL
<animateTransform>. Each meridian carries its own opacity animation phased to
the spin, so lines fade as they travel round the back -- that depth cue is what
makes it read as a globe rather than a flat tangle. SMIL is used because it is
the only animation mechanism proven to run inside GitHub's <img>/camo sandbox,
where scripting is stripped.
"""
import math
import pathlib
import random

W, H = 1200, 420
CX, CY, R = 600, 208, 150.0
TILT = -18.0
ELEV = math.radians(20.0)
SPIN = "28s"
SPIN_S = 28.0
NM = 12                      # meridians
EXCLUDE = 96                 # no surface node inside this radius (wordmark zone)
FONT = "'Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
    "dark": dict(bg0="#0a0710", bg1="#170f29", ink="#ffffff", sub="#c4b4f2",
                 mono="#b6a2dd", a1="#FF00F6", a2="#7C3AED", a3="#22D3EE",
                 ring="#9077f0", ringdim="#553d96", star="#d8ccff",
                 node="#FF00F6", halo="#0a0710", star_a=1.0),
    "light": dict(bg0="#ffffff", bg1="#f4f1ff", ink="#160e2c", sub="#5b4a86",
                  mono="#6f5f9c", a1="#d600d0", a2="#6d28d9", a3="#0891b2",
                  ring="#9c86ea", ringdim="#cec0f2", star="#b9a8ee",
                  node="#d600d0", halo="#ffffff", star_a=0.55),
}


def lat_ring(theta_deg):
    """Horizontal circle at polar angle theta -> projected ellipse."""
    th = math.radians(theta_deg)
    rx = R * math.sin(th)
    return rx, rx * math.sin(ELEV), -R * math.cos(th) * math.cos(ELEV)


def meridian(phi_deg):
    """Great circle through the poles -> projected ellipse (or vertical line)."""
    ph = math.radians(phi_deg)
    return R * abs(math.cos(ph)), R * math.cos(ELEV)


def project(lat_deg, lon_deg):
    """3-D surface point -> 2-D with the camera elevation applied, plus depth z."""
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    x0 = R * math.cos(la) * math.sin(lo)
    y0 = -R * math.sin(la)
    z0 = R * math.cos(la) * math.cos(lo)
    return x0, y0 * math.cos(ELEV) - z0 * math.sin(ELEV), z0


def sphere(p, rng):
    """Wireframe sphere + glowing surface nodes, inside the spin group."""
    rings, meridians, nodes = [], [], []

    for th in range(12, 169, 16):
        rx, ry, cy = lat_ring(th)
        dash = ' stroke-dasharray="3 4"' if th in (76, 92) else ''
        rings.append(f'<ellipse rx="{rx:.1f}" ry="{ry:.1f}" cy="{cy:.1f}"{dash}/>')

    for i in range(NM):
        rx, ry = meridian(i * 180 / NM)
        begin = -(i / NM) * SPIN_S
        fade = (f'<animate attributeName="opacity" values="1;.12;1" dur="{SPIN}"'
                f' begin="{begin:.2f}s" repeatCount="indefinite"/>')
        if rx < 0.8:
            meridians.append(f'<line y1="{-ry:.1f}" y2="{ry:.1f}">{fade}</line>')
        else:
            meridians.append(f'<ellipse rx="{rx:.1f}" ry="{ry:.1f}">{fade}</ellipse>')

    placed = 0
    while placed < 20:
        lat, lon = rng.uniform(-74, 74), rng.uniform(0, 360)
        x, y, z = project(lat, lon)
        if math.hypot(x, y) < EXCLUDE:            # keep the wordmark clear
            continue
        placed += 1
        near = (z / R + 1) / 2                    # 0 = far side .. 1 = near side
        r = rng.choice([2.2, 2.6, 3.0, 3.6]) * (0.72 + 0.55 * near)
        base = 0.42 + 0.58 * near
        delay = round(rng.uniform(0, 3.2), 2)
        nodes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{p["node"]}"'
            f' opacity="{base:.2f}" filter="url(#nodeglow)">'
            f'<animate attributeName="opacity"'
            f' values="{base:.2f};{base * 0.25:.2f};{base:.2f}" dur="3.4s"'
            f' begin="{delay}s" repeatCount="indefinite"/></circle>')

    return (f'<g fill="none" stroke="{p["ring"]}" stroke-width="1"'
            f' opacity=".45">{"".join(rings)}</g>'
            f'<g fill="none" stroke="{p["ringdim"]}" stroke-width="1"'
            f' opacity=".9">{"".join(meridians)}</g>'
            f'<g>{"".join(nodes)}</g>')


def orbit(p):
    """Satellite ring outside the spin group, with travelling dots."""
    rx, ry = R + 46, (R + 46) * math.sin(ELEV)
    path = (f"M {-rx:.1f} 0 a {rx:.1f} {ry:.1f} 0 1 0 {2 * rx:.1f} 0"
            f" a {rx:.1f} {ry:.1f} 0 1 0 {-2 * rx:.1f} 0")
    dots = "".join(
        f'<circle r="{r}" fill="{p["a3"]}" filter="url(#nodeglow)">'
        f'<animateMotion dur="16s" begin="{b}" repeatCount="indefinite"'
        f' path="{path}"/></circle>' for r, b in ((3.4, "0s"), (2.4, "-8s")))
    return (f'<g transform="rotate({TILT + 8} {CX} {CY})" opacity=".65">'
            f'<path d="{path}" transform="translate({CX} {CY})" fill="none"'
            f' stroke="{p["ringdim"]}" stroke-width="1" stroke-dasharray="2 7"/>'
            f'<g transform="translate({CX} {CY})">{dots}</g></g>')


def stars(p, rng):
    out = []
    for _ in range(150):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.choice([0.6, 0.8, 1.0, 1.3])
        o = rng.uniform(0.16, 0.62) * p["star_a"]
        if rng.random() < 0.3:
            d, b = round(rng.uniform(0, 4), 2), round(rng.uniform(1.6, 4.4), 1)
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{p["star"]}"'
                       f' opacity="{o:.2f}"><animate attributeName="opacity"'
                       f' values="{o:.2f};0.04;{o:.2f}" dur="{d}s" begin="{b}s"'
                       f' repeatCount="indefinite"/></circle>')
        else:
            out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}"'
                       f' fill="{p["star"]}" opacity="{o:.2f}"/>')
    return "".join(out)


def aurora(p):
    blobs = [("#aur1", 250, 120, 300, 150, "30s", 0),
             ("#aur2", 900, 300, 340, 170, "38s", -14),
             ("#aur3", 620, 60, 260, 130, "44s", -22)]
    return "".join(
        f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="url({href})"'
        f' opacity=".5"><animateTransform attributeName="transform" type="translate"'
        f' values="0 0; 60 -26; -40 22; 0 0" dur="{dur}" begin="{delay}s"'
        f' repeatCount="indefinite"/></ellipse>'
        for href, x, y, rx, ry, dur, delay in blobs)


def build(mode):
    p = THEMES[mode]
    rng = random.Random(20261009)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">tri &#8212; python, go, js &amp; backend developer</title>
<desc id="d">An animated 3-D wireframe sphere with orbiting satellites above the name tri.</desc>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="{p['bg0']}"/><stop offset="1" stop-color="{p['bg1']}"/>
</linearGradient>
<linearGradient id="word" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{p['a1']}"><animate attributeName="offset" values="0;0.14;0" dur="9s" repeatCount="indefinite"/></stop>
  <stop offset=".5" stop-color="{p['a2']}"/>
  <stop offset="1" stop-color="{p['a3']}"><animate attributeName="offset" values="1;0.86;1" dur="9s" repeatCount="indefinite"/></stop>
</linearGradient>
<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{p['a1']}" stop-opacity="0"/>
  <stop offset=".5" stop-color="{p['a1']}"/><stop offset="1" stop-color="{p['a3']}" stop-opacity="0"/>
</linearGradient>
<radialGradient id="scrim">
  <stop offset="0" stop-color="{p['bg0']}" stop-opacity=".97"/>
  <stop offset=".6" stop-color="{p['bg0']}" stop-opacity=".8"/>
  <stop offset="1" stop-color="{p['bg0']}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="base" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{p['bg0']}" stop-opacity="0"/>
  <stop offset=".5" stop-color="{p['bg0']}" stop-opacity=".75"/>
  <stop offset="1" stop-color="{p['bg0']}" stop-opacity=".97"/>
</linearGradient>
<radialGradient id="aur1"><stop offset="0" stop-color="{p['a1']}" stop-opacity=".45"/><stop offset="1" stop-color="{p['a1']}" stop-opacity="0"/></radialGradient>
<radialGradient id="aur2"><stop offset="0" stop-color="{p['a2']}" stop-opacity=".5"/><stop offset="1" stop-color="{p['a2']}" stop-opacity="0"/></radialGradient>
<radialGradient id="aur3"><stop offset="0" stop-color="{p['a3']}" stop-opacity=".3"/><stop offset="1" stop-color="{p['a3']}" stop-opacity="0"/></radialGradient>
<radialGradient id="core"><stop offset="0" stop-color="{p['a2']}" stop-opacity=".38"/><stop offset=".62" stop-color="{p['a2']}" stop-opacity=".11"/><stop offset="1" stop-color="{p['a2']}" stop-opacity="0"/></radialGradient>
<radialGradient id="floor"><stop offset="0" stop-color="{p['a2']}" stop-opacity=".45"/><stop offset="1" stop-color="{p['a2']}" stop-opacity="0"/></radialGradient>
<filter id="bloom" x="-40%" y="-40%" width="180%" height="180%">
  <feGaussianBlur stdDeviation="7" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="nodeglow" x="-300%" y="-300%" width="700%" height="700%">
  <feGaussianBlur stdDeviation="2.4" result="g"/>
  <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
</defs>

<rect width="{W}" height="{H}" fill="url(#bg)"/>
<g>{aurora(p)}</g>
<g>{stars(p, rng)}</g>

<ellipse cx="{CX}" cy="{CY + R + 40}" rx="320" ry="42" fill="url(#floor)" opacity=".5"/>
<circle cx="{CX}" cy="{CY}" r="{R - 4}" fill="url(#core)"/>

<g transform="translate({CX} {CY}) rotate({TILT})">
  <g>
    <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="{SPIN}" repeatCount="indefinite"/>
    {sphere(p, rng)}
  </g>
</g>
{orbit(p)}

<rect x="0" y="244" width="{W}" height="176" fill="url(#base)"/>
<ellipse cx="{CX}" cy="{CY + 4}" rx="238" ry="100" fill="url(#scrim)"/>

<text x="{CX - 4}" y="{CY + 10}" text-anchor="middle" font-family="{FONT}" font-size="130" font-weight="800" letter-spacing="8" fill="url(#word)" stroke="{p['halo']}" stroke-opacity=".9" stroke-width="9" paint-order="stroke" filter="url(#bloom)">tri</text>

<path d="M {CX - 150} 300 h 300" stroke="url(#rule)" stroke-width="2" stroke-dasharray="300" stroke-dashoffset="300">
  <animate attributeName="stroke-dashoffset" from="300" to="0" dur="1.5s" fill="freeze" begin=".2s"/>
</path>

<text x="{CX}" y="334" text-anchor="middle" font-family="{MONO}" font-size="18" letter-spacing="6" fill="{p['sub']}">python &#183; go &#183; js &#183; backend</text>
<text x="{CX}" y="370" text-anchor="middle" font-family="{MONO}" font-size="13" letter-spacing="4" fill="{p['mono']}">Bangladesh &#183; open to collaboration</text>

<text x="48" y="58" font-family="{MONO}" font-size="15" letter-spacing="3" fill="{p['mono']}">// github.com/fevnem</text>
</svg>
'''


def main():
    out = pathlib.Path(__file__).resolve().parent.parent / "images"
    out.mkdir(exist_ok=True)
    for mode, name in (("dark", "hero-3d.svg"), ("light", "hero-3d-light.svg")):
        path = out / name
        path.write_text(build(mode), encoding="utf-8")
        print(f"{name:22} {path.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
