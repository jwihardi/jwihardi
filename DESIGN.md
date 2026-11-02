# Profile design

A GitHub-code-block appearance: rounded charcoal/light-gray surface, 15-unit monospace type, 20-unit line spacing, dotted leaders, red labels and
yellow values (darker ochre in light mode for contrast). The
terminal heading is `jacub@genpoo`. Related rows are separated by one single-dot spacer line. A Previous heading
uses a horizontal text rule; the terminal heading uses the same rule. A small public-repo/star stats block sits beneath the artwork.

`profile/content.json` owns all content and palette tokens. `scripts/render.py`
owns the shared layout; desktop width is 900 and mobile width is 420. Height follows content and
wrapped lines; mobile values wrap within their column. The font stack is Consolas, Liberation Mono, Menlo, monospace.

Three artwork options remain in `assets/variants/`. The warp retains the flowing vector trace with four lane bundles, staggered
instruction packets and a reconvergence boundary, explicitly labeled schematic.
The network and compression alternatives retain their original vector drawings. All
use the same text list and theme tokens. SVG title/description and meaningful
README alt text provide context; real Markdown project links sit below the panel.

The SVG resembles terminal text but remains an embedded image, not a native
copyable Markdown code fence. The main README uses the exploded GPU die alternative, selected by the artwork field in
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

Previous lists user-provided Leidos SWE and AWS SDE internships. Python and
Hypixel Skyblock are omitted; software hobbies read roblox dev / sys work.

The warp artwork has no title or bottom explanatory caption. Its issue/diverge/join
labels and lane markers remain. Accessibility descriptions still explain the image.

Public stats use the last successful API snapshot in profile/stats.json.
Commit and line-change rows appear only after a successful authenticated history
scan. Their snapshot date is shown below. The block and mobile panel expand to fit.

The selected live artwork is now `gpu-die`: three exploded isometric layers,
with compute blocks, interconnects and substrate contacts. No artwork captions.
