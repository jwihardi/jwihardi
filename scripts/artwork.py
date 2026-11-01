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
    """Schematic lane activity, not a hardware trace or performance measurement."""
    out = ['<text x="0" y="0" class="accent" font-size="15">GPU warp trace</text>']
    for x, label in [(37,'load'), (153,'execute'), (290,'store')]:
        out.append(f'<text x="{x}" y="32" class="muted" font-size="12">{label}</text>')
    for x in [36, 116, 269, 346]:
        out.append(f'<path d="M{x} 44V297" stroke="var(--guide)" stroke-dasharray="2 4"/>')
    for lane in range(32):
        y = 49 + lane*7.65
        out.append(f'<path d="M36 {y:.2f}H346" stroke="var(--guide)" stroke-width="0.65"/>')
        if lane%8 == 0 or lane == 31:
            out.append(f'<text x="0" y="{y+4:.2f}" class="muted" font-size="11">{lane:02}</text>')
        # Thread groups branch into distinct execution windows then reconverge.
        group = lane//8
        spans = [(37+(lane%4)*4, 30), (88,16), (124+group*20,42), (213+(3-group)*9,18), (280,23), (316,27)]
        for index,(x,width) in enumerate(spans):
            opacity = [0.38,0.55,0.8,0.55,0.4,0.7][index]
            out.append(f'<path d="M{x} {y:.2f}h{width}" stroke="var(--accent)" stroke-width="3.1" opacity="{opacity}"/>')
    out.append('<text x="0" y="327" class="muted" font-size="13">32 lanes · schematic · time →</text>')
    return ''.join(out)
