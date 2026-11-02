#!/usr/bin/env python3
"""Dependency-free profile generator. Render both themes and sizes from shared content and artwork."""
import json
import hashlib
import textwrap
from pathlib import Path
from html import escape
from artwork import artwork, compression_artwork, warp_artwork, fourier_artwork, gpu_die_artwork

ROOT = Path(__file__).resolve().parents[1]


def text(x, y, value, color='fg', size=15, extra=''):
    return f'<text x="{x}" y="{y}" class="{color}" font-size="{size}" {extra}>{escape(str(value))}</text>'


def line(x, y, xx, yy, color='guide', width=1):
    return f'<path d="M{x} {y} L{xx} {yy}" fill="none" stroke="var(--{color})" stroke-width="{width}"/>'


def render(data, theme, mobile=False, variant="network"):
    descriptions = {"network": "A densely connected multilayer neural network.", "compression": "A wireframe signal landscape transitioning into quantized terraces.", "warp": "A schematic GPU warp trace with 32 lanes, branching execution and reconvergence.", "fourier": "Elliptical Fourier harmonics with epicycles and a traced orbit.", "gpu-die": "An exploded isometric GPU package with compute blocks, interconnects and substrate."}
    drawings = {"network": lambda: artwork(json.loads((ROOT / "profile/network.json").read_text())), "compression": compression_artwork, "warp": warp_artwork, "fourier": fourier_artwork, "gpu-die": gpu_die_artwork}
    w = 420 if mobile else 900
    stats = data.get('stats')
    history_ready = bool(stats and all(key in stats for key in ('commits', 'additions', 'deletions')))
    x, top = (18, (580 if history_ready else 500) if stats else 410) if mobile else (430, 28)
    size, leading = 15, 20
    char_width = size * 0.6
    label_x = x + 2 * char_width
    value_end = w - 18
    rows = []
    for row in data['rows']:
        if row is None:
            rows.append(None)
        elif isinstance(row, dict):
            rows.append(row)
        else:
            label, value = row
            if mobile and '.' in label:
                rows.append((label, ''))
                label = ''
            label_width = max(106, (len(label) + 2) * char_width)
            row_columns = int((value_end - label_x - label_width) / char_width)
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
    if history_ready and not mobile:
        h = max(h, 572)
    colors = data['themes'][theme]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
           '<title id="title">GPU computing, Linux, Windows and game development</title>',
           f'<desc id="desc">{descriptions[variant]} Workstation, programming languages, compute tools, game development, hobbies, favorite games, music and previous internships.</desc>',
           '<style>:root{' + ';'.join(f'--{k}:{v}' for k, v in colors.items()) + '}text{font-family:Consolas,"Liberation Mono",Menlo,monospace;white-space:pre}' + ''.join(f'.{k}{{fill:var(--{k})}}' for k in colors) + '</style>',
           f'<rect width="{w}" height="{h}" rx="12" fill="var(--bg)"/>']
    ax, ay = (18, 28)
    scale = 1.05 if mobile else 1.12
    out.append(f'<g transform="translate({ax} {ay}) scale({scale})">{drawings[variant]()}</g>')
    if stats:
        sx, sy = 18, 394 if mobile else 418
        end = 400
        out.append(text(sx, sy, '- GitHub ' + '─' * 33, 'fg', 15))
        entries = [('Public repos', 'repos'), ('Stars', 'stars')]
        if history_ready:
            entries += [('Commits', 'commits'), ('Lines +', 'additions'), ('Lines −', 'deletions')]
        for i, (label, key) in enumerate(entries):
            value = f"{stats[key]:,}"
            y = sy + 24 + i * 20
            out.append(text(sx, y, '. ' + label + ':', 'accent', 15))
            dot_x = sx + (len(label) + 4) * 9
            count = max(0, int((end - len(value) * 9 - dot_x) / 9) - 1)
            out.append(text(dot_x, y, '.' * count, 'muted', 15))
            out.append(text(end, y, value, 'value', 15, 'text-anchor="end"'))
        if history_ready:
            out.append(text(sx, sy + 132, 'history as of ' + stats.get('history_as_of', 'unknown'), 'muted', 13))
    columns = int((w - 18 - x) / char_width)
    out.append(text(x, top, data['heading'] + ' ' + '─' * (columns - len(data['heading']) - 1), 'fg', size))
    y = top + 28
    for row in rows:
        if isinstance(row, dict):
            heading = '- ' + row['section'] + ' '
            out.append(text(x, y, heading + '─' * (columns - len(heading)), 'fg', size))
        elif row is None:
            out.append(text(x, y, '.', 'muted', size))
        else:
            label, value = row
            if label:
                out.append(text(x, y, '.', 'muted', size))
                label = {'os': 'OS', 'gpu': 'GPU', 'ide': 'IDE', 'aws': 'AWS'}.get(label, '.'.join(part.capitalize() for part in label.split('.'))) + ':'
                out.append(text(label_x, y, label, 'accent', size))
                dot_x = label_x + (len(label) + 1) * char_width
                value_start = value_end - len(value) * char_width
                count = max(0, int((value_start - dot_x) / char_width) - 1) if value else 0
                out.append(text(dot_x, y, '.' * count, 'muted', size))
            out.append(text(value_end, y, value, 'value', size, 'text-anchor="end"'))
        y += leading
    out.append('</svg>\n')
    return ''.join(out)


def readme(data, revision):
    descriptions = {'network': 'a densely connected neural network', 'compression': 'a wireframe compression landscape', 'warp': 'a flowing GPU warp trace with 32 lanes', 'fourier': 'elliptical Fourier harmonics', 'gpu-die': 'an exploded GPU package'}
    details = '; '.join((row['section'] if isinstance(row, dict) else f'{row[0]}: {row[1]}') for row in data['rows'] if row)
    if data.get('stats'):
        details += f"; public owned non-fork repos: {data['stats']['repos']}; stars received: {data['stats']['stars']}"
    if data.get('stats') and 'commits' in data['stats']:
        details += f"; all-time authored commits in accessible default branches: {data['stats']['commits']}; lines added: {data['stats']['additions']}; lines deleted: {data['stats']['deletions']}"
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
    cache = ROOT / 'profile/stats.json'
    if cache.exists():
        data['stats'] = json.loads(cache.read_text())
    outputs = {}
    for theme in data['themes']:
        for mobile in (False, True):
            name = f'profile-{"mobile-" if mobile else ""}{theme}.svg'
            outputs[ROOT / 'assets' / name] = render(data, theme, mobile, data.get('artwork', 'network'))
    revision = hashlib.sha256(''.join(outputs.values()).encode()).hexdigest()[:12]
    for path, svg in list(outputs.items()):
        outputs[ROOT / 'assets/rendered' / f'{path.stem}-{revision}.svg'] = svg
    outputs[ROOT / 'README.md'] = readme(data, revision).rstrip() + '\n'
    for variant in ('network', 'compression', 'warp', 'fourier', 'gpu-die'):
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
