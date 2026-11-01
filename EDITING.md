# Editing the profile

- **Text, project links, colors:** `profile/content.json`.
- **ASCII digit:** `profile/digit.txt` (spaces matter).
- **Network drawing, spacing, responsive layout:** `scripts/render.py`, especially
  `artwork()` and `render()`. Coordinates are shared across both themes.
- **Generated files:** `README.md` and `assets/profile*.svg`; do not edit by hand.

Run `python3 scripts/render.py` after editing. This uses the last successful
`profile/stats.json`; if no cache exists the stats line is omitted.
Run `python3 scripts/render.py --fetch-stats` to refresh from GitHub. Optionally set
`GITHUB_TOKEN` for authenticated API limits. Python 3.10+; no packages required.
Run `python3 -m unittest discover -s tests` for pagination, filtering, theme parity,
valid SVG and failed-request preservation checks.

The scheduled workflow runs Mondays at 08:17 UTC and supports **Actions → Refresh
profile → Run workflow**. It uses the built-in token and commits only changed
outputs. GitHub Actions must be enabled and repository policy must allow that token
to write contents. API failures stop generation before any output is written; the
last good SVGs stay in place. Public repositories means owned, public, non-forks;
stars are summed over exactly that set. Followers are the account's public count.
All repository pages are followed, and duplicate IDs are counted once. Counts are
snapshots, not a live widget. The cache deliberately has no changing timestamp.

Verified project destinations:
- https://github.com/jwihardi/neural-network-EMNIST
- https://github.com/jwihardi/illogical-impulse-gentoo-overlay (displayed as ii-gentoo)

No public StriZ repository was found among the account's public repositories; it
remains plain text. Architecture source:
https://github.com/jwihardi/neural-network-EMNIST/blob/main/README.md

For a browser preview, serve the repository with `python3 -m http.server` and embed
the README picture HTML in a page with `img { max-width:100%; height:auto }`.
Inspect light/dark at 760 px and 375 px, plus 320 px for text clipping. The same
picture media queries select the compact variant; GitHub owns link/focus styling.
