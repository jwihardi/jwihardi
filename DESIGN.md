# Profile design

A GitHub-code-block appearance: rounded charcoal/light-gray surface, 16-unit monospace type, 22-unit line spacing, dotted leaders, red labels and
yellow values (darker ochre in light mode for contrast). The
terminal heading is `jacub@genpoo`. Related rows are separated by one blank line, without section headings. No statistics.

`profile/content.json` owns all content and palette tokens. `scripts/render.py`
owns the shared layout; desktop width is 900 and mobile width is 420. Height follows content and
wrapped lines; mobile values wrap within their column. The font stack is Consolas, Liberation Mono, Menlo, monospace.

Three artwork options remain in `assets/variants/`. The warp retains the flowing vector trace with four lane bundles, staggered
instruction packets and a reconvergence boundary, explicitly labeled schematic.
The network and compression alternatives retain their original vector drawings. All
use the same text list and theme tokens. SVG title/description and meaningful
README alt text provide context; real Markdown project links sit below the panel.

The SVG resembles terminal text but remains an embedded image, not a native
copyable Markdown code fence. The main README uses the warp alternative, selected by the artwork field in
profile/content.json.

User-requested personal rows include hobbies, favorite games and music. Null rows
in profile/content.json encode exactly one blank line between related groups.
Commit messages should use at most four words.

The desktop artwork is enlarged to 1.12×; the text column begins at x=430.
Values align to the right edge, with dotted leaders and a minimum 106-unit
label column. Slash-separated names stay together when wrapping. Mobile artwork
is 1.05× and retains the stacked layout.

Hobbies use Hobbies.General, Hobbies.Software and Hobbies.Videogames labels.
Desktop wrapping reserves room for each label; mobile places these long labels
on their own line so values remain readable. Music stays below the hobbies.
