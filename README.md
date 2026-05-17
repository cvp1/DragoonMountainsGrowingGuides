# Dragoon Mountains Growing Guides

A fifteen-guide library for growing food at 4,700 feet in Cochise
County, Arizona — written from the eastern flank of the Dragoon
Mountains, where the wild Chiltepin has grown for millennia, the
caliche runs close to the surface, and the monsoon decides whether
August is a triumph or a wash. USDA zone 8a. Sky-island country.

The guides cover peppers and grapes, brassicas and alliums, tomatoes
and tepary beans, figs and pomegranates, hydroponic nutrient
chemistry, javelina-proof fencing, monsoon-aware drip schedules, and
the dozen other things a place-anchored garden actually needs. They
are written to be useful to a beginner reading their first guide and
to an expert reaching for a specific reference — the same document
serving both, because the alternative is two libraries that drift.

This repository holds the source: markdown for every guide, the LaTeX
header and Lua filter that turn that markdown into print-ready PDFs,
a small static website that surfaces the library, and the scripts
that keep the photo gallery and the search index honest.

---

## The library at a glance

| # | Guide | What it covers |
|---|-------|----------------|
| 1 | Hydroponic Primer & Library Map | Front door · master multi-crop calendar · how to choose your starting guide |
| 2 | Peppers in the Dragoons | Soil + hydroponic + variety staking · the Rocoto protocol |
| 3 | Bato Bucket Hydroponic Systems | Build, water treatment, daily operations · the Cochise bicarbonate scrub |
| 4 | Hydroponic Nutrients | Masterblend, DIY locally-sourced, pH chemistry, indoor/LED |
| 5 | Grapes in the Dragoons | VSP trellis · late-pruning frost strategy · Cochise viticulture |
| 6 | Cool-Season Crops | Brassicas + alliums + greens + roots — October through May |
| 7 | Warm-Season Companions | Tomatoes, cucurbits, beans, corn, sweet potatoes |
| 8 | Herbs in the Dragoons | Annual + perennial · soil & hydroponic |
| 9 | Backyard Orchard | Figs, pomegranates, jujubes, stone fruits |
| 10 | Pest, Disease & Wildlife | IPM framework · javelina, gopher, deer, bird exclusion |
| 11 | Foundations: Soil & Seed | Soil-building, composting, seed-starting, propagation |
| 12 | Harvest, Preservation & Storage | Canning, fermentation, drying, ristras, root cellaring |
| 13 | Water in Cochise County | Well sourcing, testing, treatment, drip design, harvesting |
| 14 | Season Extension Structures | Cold frames, low tunnels, hoop houses, high tunnels |
| 15 | Native Food Crops of the Sonoran-Madrean Region | Tepary · Hopi Blue · Chiltepin · mesquite · agave · prickly pear · yucca · devil's claw · amaranth · native squash |

Plus a narrative companion — *First Season in the Dragoons* — six
one-page printable cheat sheets (master calendar, variety picks,
nutrients, water & pH, pests, harvest & preservation), and an 18×24
wall-poster edition of the master calendar with sow/transplant/harvest
icons designed for the garden shed wall.

---

## Repository layout

```
.
├── guide{1..14}_*.md         # source for each guide
├── first_season.md           # narrative walkthrough
├── header.tex                # shared LaTeX preamble — warm watercolor palette
├── div-to-env.lua            # pandoc filter: ::: divs → LaTeX tcolorboxes
├── build_pdf.sh              # one-file pandoc + xelatex builder
├── dragoon_mountains_cover.jpg
├── cheats/
│   └── cheat_*.md / .pdf     # six single-page printable references
├── diagrams/
│   └── *.svg / *.png         # structure & bed-type illustrations (Guide 14)
├── pictures/
│   ├── *.jpeg                # camera originals (excluded from deploy)
│   └── *.jpg                 # web-optimized variants (shipped)
├── pictures-manifest.json    # source of truth for gallery captions
├── scripts/
│   └── sync-pictures.py      # resize + regenerate gallery HTML
├── index.html                # homepage with card grid + filter pills
├── pictures.html             # gallery
├── search.html               # client-side search
├── search-index.json         # built artifact — ~1,000 entries
├── changelog.html
├── PRINCIPLES.md             # editorial north star
├── TODO.md                   # living backlog
├── CHANGELOG.md
├── MARKET_REPORT.md          # audience research
├── .dockerignore / .railwayignore
└── README.md                 # you are here
```

---

## Building from source

The build is intentionally low-magic: one bash script per PDF, a
shared LaTeX header, a small pandoc filter. No build system to learn.

### Requirements

- **pandoc** ≥ 3.0
- **xelatex** (TeX Live or MacTeX) — the LaTeX engine the header.tex
  is written for
- **bash**
- **Python 3** with `cairosvg` and `Pillow` — for the SVG → PNG
  diagram conversion and the picture-sync script

On macOS:

```sh
brew install pandoc texlive cairo
pip3 install cairosvg pillow
```

Verify:

```sh
pandoc --version
xelatex --version
```

### Build a single guide

```sh
./build_pdf.sh guide1_primer.md guide1_primer.pdf
```

The script pipes the markdown through pandoc with `header.tex` as the
LaTeX preamble and `div-to-env.lua` as a filter that converts the
custom callout divs (`::: relatedguides`, `::: keynote`, `::: localtip`,
`::: warning`) into the matching tcolorbox environments.

### Build a printer-friendly variant

```sh
./build_pdf.sh guide1_primer.md guide1_primer_print.pdf --print
```

The `--print` flag swaps the cream pagecolor for white and the
greendark/terracotta link colors for near-black — friendlier to a home
laser or inkjet, more legible photocopied.

### Build everything

```sh
for md in guide*.md first_season.md; do
  ./build_pdf.sh "$md" "${md%.md}.pdf"
done
for md in cheats/*.md; do
  ./build_pdf.sh "$md" "${md%.md}.pdf"
done
```

### Add a photo

The picture pipeline is idempotent. Drop a `.jpeg` into `pictures/`,
then:

```sh
python3 scripts/sync-pictures.py
```

The script resizes the original to a web-optimized `.jpg`, stubs an
entry in `pictures-manifest.json`, and regenerates the
`<!-- AUTOGEN-GALLERY -->` block in `pictures.html` and the
`<!-- AUTOGEN-STRIP -->` block on `index.html`. Edit the new stub in
the manifest to fill in `category`, `title`, `short`, `full`, and
`featured: true` if it should appear on the homepage strip. Re-run
the script. Commit.

### Rebuild the search index

```sh
python3 scripts/build-search-index.py
```

Walks every guide markdown, chunks by section, emits `search-index.json`
with the `g`, `gt`, `pdf`, `s`, `sh`, `b` fields the client-side
`search.html` consumes. Re-run after any guide edit; the file is small
enough (~750 KB) to commit directly.

---

## Conventions

### Front matter

Every guide opens with the same YAML block:

```yaml
---
title: "Guide Title"
author: "Guide N · Subtitle"
date: 'Subtitle · Subtitle · Subtitle `\\[0.5em] \textit{\normalsize Version 2026.05 · Revised YYYY-MM-DD}`{=latex}'
---
```

The date field carries the version string as inline LaTeX so it lands
on the title page in italics under the section subtitle.

### Callout blocks

Four pandoc fenced divs map to four tcolorbox environments, all
defined in `header.tex`:

| Markdown | Use |
|----------|-----|
| `::: relatedguides` | The library map at the front of each guide — one bullet per sibling guide. Same content across all 14, kept in sync. |
| `::: keynote` | A high-signal claim or warning the reader should not miss. Sage green box, used sparingly. |
| `::: localtip` | A Cochise- or Dragoons-specific note — calibration, timing, sourcing. Terracotta accent. |
| `::: warning` | Safety or destructive-mistake guidance. Used least often, weighted most. |

Open and close with `:::` on their own lines. The Lua filter handles
the rest.

### Cross-references

Guides cross-reference each other by number and section: *Guide 4
§3.2*. The convention is consistent so the renumber pattern below
works. Inline references should be terse — the relatedguides block
already carries the full library map; in-flow text shouldn't repeat
it.

### Renumbering

When a guide moves position, do a sentinel two-pass to avoid
double-substitution:

1. First pass: every old reference `Guide N` → `GUIDE_NEW_M`
2. Second pass: every sentinel `GUIDE_NEW_M` → `Guide M`

The same pattern applies to filenames (`GUIDEFILE_NEW_N`). A
mechanical renumber that does both substitutions in one pass will
corrupt the references it has already rewritten.

After renumbering, check three things:

- `::: relatedguides` bullet order (mechanical swap leaves them out
  of sequence)
- Guide 1's *§3 Library Map* H2 subsection order (same risk)
- Cheat sheet section pointers (e.g., master calendar references
  Guide 1 §9)

---

## Web layer

The site is plain HTML — no framework, no build step. The CSS lives
inline in each page; the masthead pattern (small photo strip + title
block + hairline rule) repeats across `index.html`, `pictures.html`,
`search.html`, and `changelog.html`.

`index.html` shows a card grid with filter pills (All / Warm-Season /
Cool-Season / Hydroponic / Soil / Reference). Cards carry file size,
page count, and last-updated date. Featured cards (currently Guide 1
and Guide 2) get a wider treatment at the top.

`search.html` does client-side full-text search against
`search-index.json` using vanilla JS — no Lunr, no service worker.
The index entries point back to specific guide sections and to the
PDF URL.

`pictures.html` is autogenerated from `pictures-manifest.json` via
`scripts/sync-pictures.py` between the `<!-- AUTOGEN-GALLERY -->`
markers. Don't hand-edit between those markers; the next sync wipes
your work.

---

## Deploy

The site deploys to Railway as a static container. Two ignore files
keep the build context honest:

- `.railwayignore` — what Railway uploads (filters the source side)
- `.dockerignore` — what the Docker build context sees (filters again
  after upload)

Both files exclude the same set: `.git`, IDE cruft, raw `.jpeg`
originals (we ship only the web-optimized `.jpg` variants — 40+ MB of
upload we don't need), the build scripts, `pictures-manifest.json`,
and superseded PDFs from earlier library structures.

After a renumber or restructure, add the stale old filenames to both
ignore files so they don't ship from the Syncthing-managed disk.

---

## Project docs

- **PRINCIPLES.md** — the editorial north star. The five-point
  evaluation checklist every guide is held to. Read this before
  starting a new guide.
- **TODO.md** — the living backlog, grouped A through F (crop gaps,
  new guides, infrastructure, editorial, web, speculative). Items get
  `[INTEGRATED in Guide X · §Y · YYYY-MM-DD]` markers when shipped.
- **CHANGELOG.md** — revision history at the project level. Per-guide
  revision dates live in each guide's front matter.
- **MARKET_REPORT.md** — audience research and partnership
  recommendations (UA Cochise Cooperative Extension at the top).

---

## A note on voice

The guides are place-anchored. The Dragoon Mountains aren't a generic
hot-dry climate; they are this climate — 4,700 ft, USDA 8a, monsoon
mid-July to mid-September, frost into early May at our elevation, the
caliche layer at eighteen inches, the south-facing slope that
extends the pepper season by three weeks, the wash that takes the
runoff every August. The writing assumes a reader who is here, or
somewhere that resembles here. Other Madrean sky-islands —
Chiricahuas, Huachucas, Santa Ritas, Patagonias, Pinaleños — fall
within useful range. Generic-temperate adaptations belong in
sidebars, not main flow.

If you contribute, write in that voice. Prefer specifics to
generalities, observations to claims, named varieties to family
labels, the date you actually transplanted to the calendar month
someone elsewhere recommends. Cut purple prose; keep the place.

---

## License

Content: © Craig Vandeputte. All guide text, photographs, and
diagrams are the author's work. The repository is published openly so
the library can be read, printed, and shared; reuse beyond that —
republication, derivative works, commercial use — is by permission.

Code (build scripts, the Lua filter, the picture-sync utility, the
search-index builder, the HTML/CSS scaffold): MIT.

---

*Pin a printed copy of the master calendar to the shed wall. Circle
the current month. Read across for what's running simultaneously,
read down for one family through the year. The library exists to be
useful in the garden, not on the screen.*
