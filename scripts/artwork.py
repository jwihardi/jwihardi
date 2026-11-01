"""Original abstract neural-network artwork; no claim about a project's architecture."""
from html import escape


def artwork(config):
    layers = config['layers']
    width, height = config['width'], config['height']
    columns = []
    for layer, count in enumerate(layers):
        span = height * (0.45 + 0.55 * count / max(layers))
        columns.append([(12 + layer * width / (len(layers) - 1), 38 + (height - span) / 2 + row * span / (count - 1)) for row in range(count)])
    out = [f'<text x="0" y="0" class="accent" font-size="15">{escape(config["heading"])}</text>']
    # Full connectivity between adjacent layers, held behind the signal paths.
    out.append('<g fill="none" stroke="var(--accent)" stroke-width="0.65" opacity="0.23">')
    for left, right in zip(columns, columns[1:]):
        for x, y in left:
            for xx, yy in right:
                out.append(f'<path d="M{x:.2f} {y:.2f} L{xx:.2f} {yy:.2f}"/>')
    out.append('</g>')
    for layer, nodes in enumerate(columns):
        for row, (x,y) in enumerate(nodes):
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.6" fill="var(--bg)" stroke="var(--accent)" stroke-width="1"/>')
    return ''.join(out)


def compression_artwork():
    """An illustrative signal landscape; not measured compression results."""
    from math import sin, exp
    out = ['<text x="0" y="0" class="accent" font-size="15">compression landscape</text>']

    def project(u, v):
        # A smooth signal is progressively quantized into terraces on the right.
        height = (95 * exp(-((u-.35)**2/.035 + (v-.58)**2/.12))
                  + 65 * exp(-((u-.78)**2/.025 + (v-.35)**2/.06))
                  + 9 * sin(u*16 + v*5))
        blend = max(0, (u - .48) / .52)
        height = height * (1-blend) + round(height/16)*16 * blend
        return 9 + u*246 + v*91, 174 + v*119 - u*42 - height

    out.append('<g fill="none" stroke="var(--accent)" stroke-width="0.85">')
    for j in range(19):
        pts = [project(i/36, j/18) for i in range(37)]
        out.append('<polyline opacity="0.72" points="' + ' '.join(f'{x:.1f},{y:.1f}' for x,y in pts) + '"/>')
    for i in range(37):
        pts = [project(i/36, j/18) for j in range(19)]
        out.append('<polyline opacity="0.30" points="' + ' '.join(f'{x:.1f},{y:.1f}' for x,y in pts) + '"/>')
    out.append('</g>')
    out += ['<text x="0" y="327" class="muted" font-size="13">signal → quantize → pack</text>']
    return ''.join(out)


def warp_artwork():
    """ASCII SIMT illustration. Each displayed row represents two lanes."""
    out = ['<text x="0" y="0" class="fg" font-size="14">warp / SIMT ----------------------------</text>',
           '<text x="0" y="26" class="muted" font-size="13">      issue       execute       join</text>']
    for pair in range(16):
        group, lane = divmod(pair, 4)
        cells = list('  :....:.....................:....:')
        first = 4 + lane
        middle = 12 + group*3 + lane
        last = 29 + lane
        for pos in [first, middle, last]:
            cells[pos:pos+2] = ['#', '#']
        # Slash marks outline staggered execution boundaries on a character grid.
        if middle > 10:
            cells[middle-2] = '/'
        chars = f'{pair*2:02} ' + ''.join(cells)
        pieces = []
        for char in chars:
            color = 'accent' if char == '#' else 'muted'
            pieces.append(f'<tspan class="{color}">{escape(char)}</tspan>')
        out.append(f'<text x="0" y="{49+pair*13}" font-size="13" xml:space="preserve">{"".join(pieces)}</text>')
    out.append('<text x="0" y="273" class="muted" font-size="13">32 lanes / paired / schematic</text>')
    return ''.join(out)
