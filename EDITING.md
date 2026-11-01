# Editing the profile

- **Text, project links, colors:** `profile/content.json`.
- **Network layer sizes and dimensions:** `profile/network.json`.
- **Neurons, connections and highlighted paths:** `scripts/artwork.py`.
- **Panel spacing and responsive layout:** `scripts/render.py`.
- **Generated files:** `README.md` and `assets/profile*.svg`; do not edit by hand.

Run `python3 scripts/render.py` after editing. Python 3.10+; no packages or API
requests required. Run `python3 -m unittest discover -s tests` for verification.

The network is original abstract artwork, not a depiction of a project's actual
architecture. All adjacent layers are fully connected; three highlighted routes
carry the eye through the diagram. Both themes share the same geometry.

Statistics and their scheduled refresh workflow have been removed.
The Neural networks link still leads to the existing neural-network repository;
ii-gentoo links to the verified Gentoo overlay. StriZ remains plain text.
