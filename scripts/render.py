#!/usr/bin/env python3
"""Dependency-free profile generator. Render both themes and sizes from shared content and artwork."""
import json
import hashlib
import textwrap
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
    w = 420 if mobile else 900
    x, top = (18, 410) if mobile else (430, 28)
    size, leading = 16, 22
    char_width = size * 0.6
    value_end = w - 18
    rows = []
    for row in data['rows']:
        if row is None:
            rows.append(None)
        else:
            label, value = row
            if mobile and '.' in label:
                rows.append((label, ''))
                label = ''
            label_width = max(106, (len(label) + 2) * char_width)
            row_columns = int((value_end - x - label_width) / char_width)
            wrapped = []
            current = ''
            for item in value.split(' / '):
                candidate = f'{current} / {item}' if current else item
                if current and len(candidate) > row_columns:
                    wrapped.append(current)
                    current = item
                else:
                    current = candidate
            if current:
                wrapped.extend(textwrap.wrap(current, width=row_columns, break_long_words=False, break_on_hyphens=False))
            rows.extend((label if i == 0 else '', part) for i, part in enumerate(wrapped))
    h = top + 28 + len(rows) * leading + 16
    colors = data['themes'][theme]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
           '<title id="title">GPU computing, Linux, Windows and game development</title>',
           f'<desc id="desc">{descriptions[variant]} Workstation, programming languages, compute tools, game development, hobbies, favorite games and music.</desc>',
           '<style>:root{' + ';'.join(f'--{k}:{v}' for k, v in colors.items()) + '}text{font-family:Consolas,"Liberation Mono",Menlo,monospace;white-space:pre}' + ''.join(f'.{k}{{fill:var(--{k})}}' for k in colors) + '</style>',
           f'<rect width="{w}" height="{h}" rx="12" fill="var(--bg)"/>']
    ax, ay = (18, 28)
    scale = 1.05 if mobile else 1.12
    out.append(f'<g transform="translate({ax} {ay}) scale({scale})">{drawings[variant]()}</g>')
    columns = int((w - 18 - x) / char_width)
    out.append(text(x, top, data['heading'] + ' ' + '-' * (columns - len(data['heading']) - 1), 'fg', size))
    y = top + 28
    for row in rows:
        if row is not None:
            label, value = row
            if label:
                label = {'os': 'OS', 'gpu': 'GPU', 'ide': 'IDE'}.get(label, '.'.join(part.capitalize() for part in label.split('.'))) + ':'
                out.append(text(x, y, label, 'accent', size))
                dot_x = x + (len(label) + 1) * char_width
                value_start = value_end - len(value) * char_width
                count = max(0, int((value_start - dot_x) / char_width) - 1) if value else 0
                out.append(text(dot_x, y, '.' * count, 'muted', size))
            out.append(text(value_end, y, value, 'value', size, 'text-anchor="end"'))
        y += leading
    out.append('</svg>\n')
    return ''.join(out)


def readme(data, revision):
    descriptions = {'network': 'a densely connected neural network', 'compression': 'a wireframe compression landscape', 'warp': 'a flowing GPU warp trace with 32 lanes'}
    details = '; '.join(f'{row[0]}: {row[1]}' for row in data['rows'] if row)
    alt = escape(f"Terminal profile: {descriptions[data.get('artwork', 'network')]}. {details}.", quote=True)
    return f'''<picture>
  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jwihardi/jwihardi/main/assets/rendered/profile-mobile-dark-{revision}.svg">
  <source media="(max-width: 600px)" srcset="https://raw.githubusercontent.com/jwihardi/jwihardi/main/assets/rendered/profile-mobile-light-{revision}.svg">
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jwihardi/jwihardi/main/assets/rendered/profile-dark-{revision}.svg">
  <img src="https://raw.githubusercontent.com/jwihardi/jwihardi/main/assets/rendered/profile-light-{revision}.svg" width="900" alt="{alt}">
</picture>

''' + ' · '.join(f'[{label}]({url})' for label, url in data['links']) + '\n'


def main():
    data = json.loads((ROOT / 'profile/content.json').read_text())
    outputs = {}
    for theme in data['themes']:
        for mobile in (False, True):
            name = f'profile-{"mobile-" if mobile else ""}{theme}.svg'
            outputs[ROOT / 'assets' / name] = render(data, theme, mobile, data.get('artwork', 'network'))
    revision = hashlib.sha256(''.join(outputs.values()).encode()).hexdigest()[:12]
    for path, svg in list(outputs.items()):
        outputs[ROOT / 'assets/rendered' / f'{path.stem}-{revision}.svg'] = svg
    outputs[ROOT / 'README.md'] = readme(data, revision)
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
