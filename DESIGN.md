# Profile design

One continuous terminal surface: original ASCII handwriting and a sparse neural
network occupy approximately 40%; an aligned workstation/compute/work grid occupies
60%. The only strong color is ice cyan, with amber reserved for the prediction.
No personal biography, decorative cards, badges, gradients or animation.

`profile/content.json` owns all text and theme tokens. `scripts/render.py` consumes
those tokens directly for every SVG. `profile/digit.txt` owns the original digit.
DejaVu Sans Mono, Consolas, monospace keep text and ASCII on a fixed grid. Desktop
is 900 × 432; below a 600 px viewport the picture selects a 420 × 820 stacked panel.
Meaningful image alt text and SVG title/description accompany real Markdown links.

The forward pass is an illustrative digit-7 schematic, not an inference result or
accuracy claim. Architecture comes from neural-network-EMNIST: 784 inputs, one
configurable hidden layer, 10 classes for digits. Circles sample the layers; cyan
edges illustrate activation, not measured weights. The ReLU label follows the CUDA
implementation. Reference principles: Andrew6rant's fixed grid and picture theme
selection; no reference artwork or source code reused.
