# Profile design

A continuous terminal surface with a large, dense neural network on the left and
an aligned workstation/compute/work grid on the right. Seven layers and many fine
connections form the main visual; cyan paths and filled neurons trace activations.
The network is abstract, not a claim about any project's architecture. No digit,
EMNIST label, statistics, biography, badges, decorative cards, gradients or animation.

`profile/content.json` owns text and theme tokens. `profile/network.json` owns the
artwork dimensions and layer sizes; `scripts/artwork.py` draws it. Both themes and
layouts use these same sources through `scripts/render.py`.

DejaVu Sans Mono, Consolas, monospace maintain the terminal grid. Desktop is
900 × 406; below 600 px the picture selects a 420 × 770 stacked panel. Meaningful
alt text and SVG descriptions accompany real Markdown project links.
