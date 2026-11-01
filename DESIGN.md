# Profile design

A GitHub-code-block appearance: rounded charcoal/light-gray surface, small uniform
monospace type, tight 20-unit line spacing, dotted leaders and red labels. The
terminal heading is `jacub@genpoo`. No section headings, biography or statistics.

`profile/content.json` owns all content and palette tokens. `scripts/render.py`
owns the shared layout; desktop is 900 × 330 and mobile is 420 × 630, extended for
additional rows. The font stack is Consolas, Liberation Mono, Menlo, monospace.

Three artwork options remain in `assets/variants/`. The warp uses ASCII characters
on a fixed grid (one row per pair of lanes), explicitly labeled schematic. The
network and compression alternatives retain their original vector drawings. All
use the same text list and theme tokens. SVG title/description and meaningful
README alt text provide context; real Markdown project links sit below the panel.

The SVG resembles terminal text but remains an embedded image, not a native
copyable Markdown code fence. The main README retains the network alternative
while the user compares artwork versions.
