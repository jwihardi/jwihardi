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
    out.append('<g fill="none" stroke="var(--guide)" stroke-width="0.65" opacity="0.65">')
    for left, right in zip(columns, columns[1:]):
        for x, y in left:
            for xx, yy in right:
                out.append(f'<path d="M{x:.2f} {y:.2f} L{xx:.2f} {yy:.2f}"/>')
    out.append('</g>')
    active = set()
    routes = [[1,2,3,5,4,3,2], [3,5,6,5,6,5,3], [2,3,5,6,5,4,2]]
    out.append('<g fill="none" stroke="var(--accent)" stroke-width="1.2" opacity="0.8">')
    for route in routes:
        points = []
        for layer, row in enumerate(route):
            row = min(row, len(columns[layer]) - 1)
            active.add((layer,row))
            x,y = columns[layer][row]
            points.append(f'{x:.2f},{y:.2f}')
        out.append(f'<polyline points="{" ".join(points)}"/>')
    out.append('</g>')
    for layer, nodes in enumerate(columns):
        for row, (x,y) in enumerate(nodes):
            on = (layer,row) in active
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.6" fill="var(--{"accent" if on else "bg"})" stroke="var(--{"accent" if on else "muted"})" stroke-width="1"/>')
    return ''.join(out)
