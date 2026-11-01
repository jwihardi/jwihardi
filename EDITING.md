# Editing the profile

- **Text, project links, colors:** `profile/content.json`.
- **Network layer sizes and dimensions:** `profile/network.json`.
- **Neurons and connections:** `scripts/artwork.py`.
- **Panel spacing and responsive layout:** `scripts/render.py`.
- **Generated files:** `README.md` and `assets/profile*.svg`; do not edit by hand.

Run `python3 scripts/render.py` after editing. Python 3.10+; no packages or API
requests required. Run `python3 -m unittest discover -s tests` for verification.

The network is original abstract artwork, not a depiction of a project's actual
architecture. All adjacent layers are fully connected, with uniform red edges and outlined
neurons. Both themes share the same geometry.

Statistics and their scheduled refresh workflow have been removed.
The Neural networks link still leads to the existing neural-network repository;
ii-gentoo links to the verified Gentoo overlay. StriZ remains plain text.

## Artwork alternatives

The generator also writes all three options to `assets/variants/`, in desktop and
mobile sizes for both themes. `network-*` retains the current neural network;
`compression-*` uses a signal landscape; `warp-*` uses a schematic GPU warp trace.
The new artwork functions live in `scripts/artwork.py`. These are illustrations,
not measurements. The main README uses the variant selected by `artwork` in `profile/content.json`
(currently `warp`).

The shared panel now uses code-block typography and dotted leaders. The warp option
uses the flowing vector trace: edit `warp_artwork()` in `scripts/artwork.py`. The embedded SVG is an image, not selectable README text.
