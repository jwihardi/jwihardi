#!/usr/bin/env python3
"""Dependency-free profile generator. Fetch everything before changing any assets."""
import argparse
import json
import os
from pathlib import Path
import re
from html import escape
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def request_json(url):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-renderer',
               'X-GitHub-Api-Version': '2022-11-28'}
    if os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return json.load(response), response.headers.get('Link', '')


def fetch_stats(user, request=request_json):
    account, _ = request(f'https://api.github.com/users/{user}')
    url = f'https://api.github.com/users/{user}/repos?type=owner&per_page=100'
    owned = {}
    while url:
        repos, links = request(url)
        if not isinstance(repos, list):
            raise ValueError('Expected a repository list')
        for repo in repos:
            if not repo['fork'] and not repo['private'] and repo['owner']['login'].lower() == user.lower():
                owned[repo['id']] = repo['stargazers_count']
        next_link = re.search(r'<([^>]+)>; rel="next"', links)
        url = next_link.group(1) if next_link else None
        if url and not url.startswith('https://api.github.com/'):
            raise ValueError('Unexpected pagination host')
    stats = {'repos': len(owned), 'stars': sum(owned.values()), 'followers': account['followers']}
    if any(type(value) is not int or value < 0 for value in stats.values()):
        raise ValueError('Invalid GitHub counts')
    return stats


def text(x, y, value, color='fg', size=15, extra=''):
    return f'<text x="{x}" y="{y}" class="{color}" font-size="{size}" {extra}>{escape(str(value))}</text>'


def line(x, y, xx, yy, color='guide', width=1):
    return f'<path d="M{x} {y} L{xx} {yy}" fill="none" stroke="var(--{color})" stroke-width="{width}"/>'


def artwork(data):
    out = [text(0, 0, data['heading'], 'accent', 15)]
    for row, chars in enumerate((ROOT / 'profile/digit.txt').read_text().splitlines()):
        out.append(text(0, 67 + row * 10, chars, 'accent', 13, 'xml:space="preserve"'))
    # Three sampled columns represent input, hidden and output, not extra hidden layers.
    columns = [(137, [74, 110, 146, 182, 218]), (215, [88, 128, 168, 208]), (286, [110, 150, 190])]
    for (x, ys), (xx, yys) in zip(columns, columns[1:]):
        for i, y in enumerate(ys):
            for j, yy in enumerate(yys):
                if (i + j) % 3 == 0:
                    out.append(line(x, y, xx, yy))
    for a, b in [((104, 146), (137, 146)), ((137, 146), (215, 128)), ((137, 146), (215, 168)), ((215, 128), (286, 150)), ((215, 168), (286, 150))]:
        out.append(line(*a, *b, 'accent', 1.6))
    for x, ys in columns:
        for y in ys:
            active = (x, y) in [(137, 146), (215, 128), (215, 168), (286, 150)]
            out.append(f'<circle cx="{x}" cy="{y}" r="4" fill="var(--bg)" stroke="var(--{"accent" if active else "muted"})" stroke-width="1.5"/>')
    out += [line(290, 150, 312, 150, 'amber', 1.5), text(317, 160, data['prediction'], 'amber', 32),
            text(0, 260, '28×28', 'muted', 13), text(120, 260, 'input', 'muted', 13),
            text(193, 260, 'ReLU', 'muted', 13), text(275, 260, 'class', 'muted', 13),
            text(0, 294, data['architecture'], 'fg', 16), text(0, 317, data['note'], 'muted', 13)]
    return ''.join(out)


def render(data, stats, theme, mobile=False):
    w, h = (420, 820) if mobile else (900, 432)
    colors = data['themes'][theme]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
           '<title id="title">GPU computing, Linux and neural networks</title>',
           '<desc id="desc">ASCII digit seven passes through a schematic 784-input, one-hidden-layer EMNIST network to a predicted seven. Workstation, compute tools, projects and public GitHub statistics.</desc>',
           '<style>:root{' + ';'.join(f'--{k}:{v}' for k, v in colors.items()) + '}text{font-family:"DejaVu Sans Mono",Consolas,monospace;white-space:pre}' + ''.join(f'.{k}{{fill:var(--{k})}}' for k in colors) + '</style>',
           f'<path fill="var(--bg)" d="M0 0h{w}v{h}H0z"/>']
    ax, ay = (28, 40)
    out.append(f'<g transform="translate({ax} {ay})">{artwork(data["art"])}</g>')
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
    if stats is not None:
        y = h - 25
        out.append(line(28, y - 24, w - 28, y - 24))
        value = f"{stats['repos']} public repos  /  {stats['stars']} stars  /  {stats['followers']} followers"
        out.append(text(28, y, value, 'muted', 13 if mobile else 14))
        if not mobile:
            out.append(text(656, y, 'github · owned, non-fork', 'muted', 13))
    out.append('</svg>\n')
    return ''.join(out)


def readme(data):
    alt = 'Terminal profile: an ASCII 7 flows through an EMNIST neural network. Gentoo Linux and OpenRC; C++, C, Python and CUDA; GPU compression, neural-network benchmarking and Gentoo packaging. Public repository, star and follower counts below.'
    return f'''<picture>
  <source media="(max-width: 600px) and (prefers-color-scheme: dark)" srcset="assets/profile-mobile-dark.svg">
  <source media="(max-width: 600px)" srcset="assets/profile-mobile-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/profile-dark.svg">
  <img src="assets/profile-light.svg" width="900" alt="{alt}">
</picture>

''' + ' · '.join(f'[{label}]({url})' for label, url in data['links']) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch-stats', action='store_true')
    args = parser.parse_args()
    data = json.loads((ROOT / 'profile/content.json').read_text())
    cache = ROOT / 'profile/stats.json'
    # Network/schema errors propagate before any writes, preserving the last good files.
    stats = fetch_stats(data['user']) if args.fetch_stats else (json.loads(cache.read_text()) if cache.exists() else None)
    outputs = {ROOT / 'README.md': readme(data)}
    for theme in data['themes']:
        for mobile in (False, True):
            name = f'profile-{"mobile-" if mobile else ""}{theme}.svg'
            outputs[ROOT / 'assets' / name] = render(data, stats, theme, mobile)
    if args.fetch_stats:
        outputs[cache] = json.dumps(stats, indent=2) + '\n'
    for path, value in outputs.items():
        if not path.exists() or path.read_text() != value:
            temporary = path.with_suffix(path.suffix + '.tmp')
            temporary.write_text(value)
            temporary.replace(path)


if __name__ == '__main__':
    main()
