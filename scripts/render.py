#!/usr/bin/env python3
"""Dependency-free profile generator. Render both themes and sizes from shared content and artwork."""
import json
from pathlib import Path
from html import escape
from artwork import artwork

ROOT = Path(__file__).resolve().parents[1]


def text(x, y, value, color='fg', size=15, extra=''):
    return f'<text x="{x}" y="{y}" class="{color}" font-size="{size}" {extra}>{escape(str(value))}</text>'


def line(x, y, xx, yy, color='guide', width=1):
    return f'<path d="M{x} {y} L{xx} {yy}" fill="none" stroke="var(--{color})" stroke-width="{width}"/>'


def render(data, theme, mobile=False):
    w, h = (420, 770) if mobile else (900, 406)
    colors = data['themes'][theme]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
           '<title id="title">GPU computing, Linux and neural networks</title>',
           '<desc id="desc">A large, densely connected multilayer neural network with fine red connections. Workstation, compute tools and projects.</desc>',
           '<style>:root{' + ';'.join(f'--{k}:{v}' for k, v in colors.items()) + '}text{font-family:"DejaVu Sans Mono",Consolas,monospace;white-space:pre}' + ''.join(f'.{k}{{fill:var(--{k})}}' for k in colors) + '</style>',
           f'<path fill="var(--bg)" d="M0 0h{w}v{h}H0z"/>']
    ax, ay = (28, 40)
    out.append(f'<g transform="translate({ax} {ay})">{artwork(json.loads((ROOT / "profile/network.json").read_text()))}</g>')
    x, top = (28, 400) if mobile else (404, 40)
    out.append(text(x, top, data['heading'], 'fg', 20))
    out.append(text(w - 40, top, '_', 'accent', 20))
    y = top + 38
    for group in data['groups']:
        out.append(text(x, y, group['title'], 'accent', 15))
        out.append(line(x + 112, y - 5, w - 28, y - 5))
        y += 24
        for label, value in group['rows']:
            size = 14 if mobile else 16
            out.append(text(x, y, label, 'muted', size))
            out.append(text(x + (99 if mobile else 110), y, value, 'fg', size))
            y += 22
        y += 12
    out.append('</svg>\n')
    return ''.join(out)


def readme(data):
    alt = 'Terminal profile: a densely connected multilayer neural network with fine red connections. Gentoo Linux and OpenRC; C++, C, Python and CUDA; GPU compression, neural-network benchmarking and Gentoo packaging.'
    return f'''<picture>
  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/profile-mobile-dark.svg">
  <source media="(max-width: 600px)" srcset="assets/profile-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/profile-dark.svg">
  <img src="assets/profile-light.svg" width="900" alt="{alt}">
</picture>

''' + ' · '.join(f'[{label}]({url})' for label, url in data['links']) + '\n'


def main():
    data = json.loads((ROOT / 'profile/content.json').read_text())
    outputs = {ROOT / 'README.md': readme(data)}
    for theme in data['themes']:
        for mobile in (False, True):
            name = f'profile-{"mobile-" if mobile else ""}{theme}.svg'
            outputs[ROOT / 'assets' / name] = render(data, theme, mobile)
    for path, value in outputs.items():
        if not path.exists() or path.read_text() != value:
            temporary = path.with_suffix(path.suffix + '.tmp')
            temporary.write_text(value)
            temporary.replace(path)


if __name__ == '__main__':
    main()
