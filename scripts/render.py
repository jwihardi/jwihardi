#!/usr/bin/env python3
"""Dependency-free profile generator. Render both themes and sizes from shared content and artwork."""
import json
from pathlib import Path
from html import escape
from artwork import artwork, compression_artwork, warp_artwork

ROOT = Path(__file__).resolve().parents[1]


def text(x, y, value, color='fg', size=15, extra=''):
    return f'<text x="{x}" y="{y}" class="{color}" font-size="{size}" {extra}>{escape(str(value))}</text>'


def line(x, y, xx, yy, color='guide', width=1):
    return f'<path d="M{x} {y} L{xx} {yy}" fill="none" stroke="var(--{color})" stroke-width="{width}"/>'


def render(data, theme, mobile=False, variant="network"):
    descriptions = {"network": "A densely connected multilayer neural network.", "compression": "A wireframe signal landscape transitioning into quantized terraces.", "warp": "A schematic GPU warp trace with 32 lanes, branching execution and reconvergence."}
    drawings = {"network": lambda: artwork(json.loads((ROOT / "profile/network.json").read_text())), "compression": compression_artwork, "warp": warp_artwork}
    extra_rows = max(0, len(data["rows"]) - 12)
    w, h = (420, 630 + extra_rows * 20) if mobile else (900, 330 + extra_rows * 20)
    colors = data['themes'][theme]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
           '<title id="title">GPU computing, Linux, Windows and game development</title>',
           f'<desc id="desc">{descriptions[variant]} Workstation, programming languages, compute tools and game development.</desc>',
           '<style>:root{' + ';'.join(f'--{k}:{v}' for k, v in colors.items()) + '}text{font-family:Consolas,"Liberation Mono",Menlo,monospace;white-space:pre}' + ''.join(f'.{k}{{fill:var(--{k})}}' for k in colors) + '</style>',
           f'<rect width="{w}" height="{h}" rx="12" fill="var(--bg)"/>']
    ax, ay = (18, 28)
    scale = 1 if variant == "warp" else 0.8
    out.append(f'<g transform="translate({ax} {ay}) scale({scale})">{drawings[variant]()}</g>')
    x, top = (18, 340) if mobile else (368, 28)
    size = 14
    char_width = size * 0.6
    columns = int((w - 18 - x) / char_width)
    out.append(text(x, top, data['heading'] + ' ' + '-' * (columns - len(data['heading']) - 1), 'fg', size))
    y = top + 26
    value_x = x + (112 if mobile else 134)
    for label, value in data['rows']:
        label = {'os': 'OS', 'gpu': 'GPU'}.get(label, label.capitalize()) + ':'
        out.append(text(x, y, label, 'accent', size))
        dot_x = x + (len(label) + 1) * char_width
        count = max(0, int((value_x - dot_x) / char_width) - 1)
        out.append(text(dot_x, y, '.' * count, 'muted', size))
        out.append(text(value_x, y, value, 'fg', size))
        y += 20
    out.append('</svg>\n')
    return ''.join(out)


def readme(data):
    alt = 'Terminal profile: a densely connected multilayer neural network with fine red connections. Gentoo Linux and Windows; C++, C, Java, Python, Assembly, Bash and CUDA; game development with Unreal, Unity and Godot.'
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
    for variant in ('network', 'compression', 'warp'):
        for theme in data['themes']:
            for mobile in (False, True):
                name = f'{variant}-{"mobile-" if mobile else ""}{theme}.svg'
                outputs[ROOT / 'assets' / 'variants' / name] = render(data, theme, mobile, variant)
    for path, value in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text() != value:
            temporary = path.with_suffix(path.suffix + '.tmp')
            temporary.write_text(value)
            temporary.replace(path)


if __name__ == '__main__':
    main()
