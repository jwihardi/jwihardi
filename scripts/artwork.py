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
    """Stylized SIMT activity; lane spacing is illustrative, not a measured trace."""
    out = []
    for x, label in [(12, 'issue'), (126, 'diverge'), (277, 'join')]:
        out.append(f'<text x="{x}" y="32" class="muted" font-size="12">{label}</text>')
    # Quiet time ruler and lane-group markers give the flowing traces a fixed grid.
    for x in range(12, 349, 14):
        tall = (x-12) % 56 == 0
        out.append(f'<path d="M{x} 49v{5 if tall else 2}" stroke="var(--muted)" opacity="0.5"/>')
    for group in range(4):
        y = 68 + group*65
        out.append(f'<path d="M113 {y}h139" stroke="var(--guide)" stroke-dasharray="2 5"/>')
    # Four separated bundles fan out from a compact issue stream and reconverge.
    for lane in range(32):
        group, index = divmod(lane, 8)
        start = 107 + lane*4.4
        spread = 76 + group*65 + index*5.3
        end = 105 + lane*4.5
        bend = 68 + index*2
        arrival = 110 + index*2
        depart = 232 + (7-index)*2
        points = f'12,{start:.1f} {bend},{start:.1f} {arrival},{spread:.1f} {depart},{spread:.1f} 290,{end:.1f} 348,{end:.1f}'
        out.append(f'<polyline points="{points}" fill="none" stroke="var(--accent)" stroke-width="0.85" opacity="0.44"/>')
        # Instruction packets follow each lane; their diagonal staggering adds rhythm.
        packets = [(20+index*2, start, 9, .65),
                   (132+group*12+index*3, spread, 15, .95),
                   (193+index*2-group*5, spread, 7, .60),
                   (306+index*2, end, 13, .85)]
        for x,y,width,opacity in packets:
            out.append(f'<path d="M{x} {y:.1f}h{width}" stroke="var(--accent)" stroke-width="2.8" opacity="{opacity}"/>')
    # A visible reconvergence boundary, with open endpoints rather than a box.
    out.append('<path d="M285 84h10 M290 84v180 M285 264h10" fill="none" stroke="var(--muted)" stroke-width="0.9" stroke-dasharray="2 3"/>')
    for group, label in enumerate(['00–07', '08–15', '16–23', '24–31']):
        y = 68 + group*65
        out.append(f'<text x="113" y="{y-5}" class="muted" font-size="10">{label}</text>')
    out.append('<path d="M12 317h336m-5 -3 5 3-5 3" fill="none" stroke="var(--guide)"/>')
    return ''.join(out)
