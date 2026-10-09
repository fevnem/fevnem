#!/usr/bin/env python3
"""Author images/terminal.svg -- a typing terminal card (SMIL only, no services).

One-off authoring tool:  python3 tools/gen_terminal.py
Self-contained dark card, so it reads correctly in both GitHub themes.
"""
import pathlib

W, H = 980, 300
PAD_X, LINE_H = 30, 31
TOP = 76
FS = 16.0
ADV = FS * 0.601          # monospace advance width for the fallback stack

BG, BAR, INK, DIM = "#0e0918", "#1b1230", "#e9e2ff", "#8d7ab8"
A1, A2, A3 = "#FF00F6", "#7C3AED", "#22D3EE"

LINES = [
    ("$ whoami", "cmd", 0.35),
    ("tri \u2014 python \u00b7 go \u00b7 js \u00b7 backend developer", "out", 0.30),
    ("$ cat stack.txt", "cmd", 0.80),
    ("python  go  javascript  typescript  react  node  docker  linux", "out", 0.60),
    ("$ ./status --long", "cmd", 0.35),
    ("507 contributions in the last 12 months \u00b7 Bangladesh \u00b7 UTC+6", "ok", 0.15),
    ("$ ", "cmd", 0.20),
]
COLORS = {"cmd": INK, "out": "#bfa9f5", "ok": A3}


def build():
    clips, texts, cursor_x, cursor_y = [], [], PAD_X, TOP
    t = 0.6
    for i, (text, kind, pause) in enumerate(LINES):
        y = TOP + i * LINE_H
        w = len(text) * ADV + 6
        dur = max(0.3, len(text) * 0.024)
        clips.append(
            f'<clipPath id="c{i}"><rect x="{PAD_X}" y="{y - FS}" width="0" height="{FS + 12}">'
            f'<animate attributeName="width" from="0" to="{w:.0f}" dur="{dur:.2f}s"'
            f' begin="{t:.2f}s" fill="freeze"/></rect></clipPath>')
        texts.append(
            f'<g clip-path="url(#c{i})"><text x="{PAD_X}" y="{y}" font-size="{FS:.0f}"'
            f' fill="{COLORS[kind]}">{esc(text)}</text></g>')
        t += dur + pause
        if i == len(LINES) - 1:
            cursor_x = PAD_X + int(len(text) * ADV) + 6
            cursor_y = y
    t += 0.1

    chevrons = "".join(
        f'<circle cx="{30 + i * 22}" cy="22" r="6" fill="{c}"/>'
        for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="tt dd">
<title id="tt">tri terminal</title>
<desc id="dd">A terminal window typing out tri's identity, stack and activity.</desc>
<defs>
<clipPath id="win"><rect width="{W}" height="{H}" rx="14"/></clipPath>
<linearGradient id="hair" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{A1}"/><stop offset=".5" stop-color="{A2}"/>
  <stop offset="1" stop-color="{A3}"/></linearGradient>
<linearGradient id="glass" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#ffffff" stop-opacity=".07"/>
  <stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>
<filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
  <feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#4b1fa8" flood-opacity=".42"/>
</filter>
<filter id="blinkglow" x="-300%" y="-300%" width="700%" height="700%">
  <feGaussianBlur stdDeviation="2.2" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
{"".join(clips)}
</defs>

<g filter="url(#shadow)"><rect width="{W}" height="{H}" rx="14" fill="{BG}"/></g>
<g clip-path="url(#win)">
  <rect width="{W}" height="44" fill="{BAR}"/>
  <rect width="{W}" height="44" fill="url(#glass)"/>
  <rect y="43" width="{W}" height="1" fill="url(#hair)" opacity=".55"/>
</g>
<rect width="{W}" height="{H}" rx="14" fill="none" stroke="url(#hair)" stroke-opacity=".38"/>
{chevrons}
<text x="{W / 2}" y="27" text-anchor="middle" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="13" letter-spacing="2" fill="{DIM}">tri@github: ~ &#8212; zsh</text>
<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace" xml:space="preserve">
{"".join(texts)}
<rect x="{cursor_x}" y="{cursor_y - 15}" width="10" height="19" fill="{A1}" filter="url(#blinkglow)">
  <animate attributeName="opacity" values="1;1;0;0;1" dur="1.1s" begin="{t:.2f}s" repeatCount="indefinite"/>
</rect>
</g>
</svg>
'''


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    out = pathlib.Path(__file__).resolve().parent.parent / "images" / "terminal.svg"
    out.write_text(build(), encoding="utf-8")
    print(f"terminal.svg           {out.stat().st_size / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
