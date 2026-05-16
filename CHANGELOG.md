# Changelog — Dragoon Mountains Growing Guides

Developer-facing change log for the library. Reader-facing version at
[changelog.html](changelog.html).

Version stamps follow the pattern `YYYY.MM` (the month a revision
batch shipped). Each guide's title page carries its own version +
last-revised date.

## 2026.05 — May 2026

### Major: First Season narrative companion

- **New: `first_season.pdf`** — 34-page narrative walkthrough
  (October through September) for someone new to Cochise County.
  Different voice from the reference guides: first-person-plural,
  conversational, sensory-anchored. End-of-chapter cross-references
  route into the deep reference library. Closes backlog F1.

### Major: 6 cross-cutting cheat sheets

- **New: `cheats/cheat_master_calendar.pdf`** — 12 months × 6 crop
  families on one page.
- **New: `cheats/cheat_variety_picks.pdf`** — best 1–2 variety picks
  per major crop across warm, cool, and orchard categories.
- **New: `cheats/cheat_water_ph.pdf`** — 5-step Cochise bicarbonate
  protocol + pH targets + common acid choices.
- **New: `cheats/cheat_nutrients.pdf`** — Masterblend per-stage chart
  for pepper and tomato.
- **New: `cheats/cheat_pests.pdf`** — 12-row pest catalog + universal
  spray decision tree.
- **New: `cheats/cheat_harvest_preservation.pdf`** — harvest indicators
  + best preservation method per crop, altitude-adjusted.

All cheat sheets verified single-page, density-optimized for printing
on letter paper. Closes backlog C4.

### Major: "Beyond the Dragoons" sky-island adaptation chapter

- **Guide 4** gains a new chapter (§ between Sources & References and
  Glossary) documenting how the library transfers across the Madrean
  Sky Islands archipelago. Close-fits table (Mules, Huachucas,
  Whetstones, Chiricahuas, Animas/Peloncillo). Partial-fits table with
  adjustment notes (Santa Ritas, Santa Catalinas, Pinaleños, Galiuros,
  Patagonia/Canelo). Poor-fits table (Tucson basin, Phoenix, Mt.
  Lemmon, Flagstaff). The ±1 week per 500 ft rule of thumb. Guide 4
  grew from 60 to 71 pages.

### Major: Five reference guides ship — library reaches 14

- **Guide 10 — Pest, Disease & Wildlife** (74 pp) — IPM master
  reference + Cochise wildlife exclusion.
- **Guide 11 — Foundations: Soil & Seed** (81 pp) — soil-building +
  seed-starting + propagation.
- **Guide 12 — Harvest, Preservation & Storage** (80 pp) — closes the
  growing-to-eating loop.
- **Guide 13 — Water in Cochise County** (61 pp) — canonical home for
  water topics, including the 5-step bicarbonate protocol.
- **Guide 14 — Season Extension Structures** (61 pp) — cold frames,
  low tunnels, hoop houses, high tunnels.

Homepage reorganized into four sections: Start Here · Crop Guides ·
Foundations & Systems · Protection & Yield. Two new filter pills
(Foundations, Reference). Existing 9 guides updated to reference all
14 in their `::: relatedguides` blocks. Search index expanded to
1,044 sections. Closes backlog B2 through B8.

### Major: Library editorial overhaul

- Glossary appendix added to Guide 4 (50+ terms with cross-references)
- Variety Index appendix added to Guide 4 (130+ named varieties by
  crop family)
- Sources & References appendix added to all 14 guides
- Inline glossary first-use definitions added across the library
- 14 field photos embedded across 8 guides where they teach more than
  prose
- "If you're new here" callouts added at the top of long/complex
  chapters
- "Where do I start?" decision matrix added to Guide 3
- Version + revision date on every guide's title page
- Related-guides blocks consistent across all 14 guides

Closes backlog C1, C2, C6, D0, D1, D2, D3, D4, D5.

### Feature: Search across all guides

- **New: `search.html`** with `search-index.json` — client-side static
  search over all 1,044 indexed sections. Quick-jump pills,
  match-highlight snippets, `?q=foo` deep-link support.

### Feature: Picture sync workflow

- **New: `pictures-manifest.json`** as single source of truth for
  gallery photos.
- **New: `scripts/sync-pictures.py`** — one-command pipeline: resize
  new originals, stub manifest entries, regenerate HTML.
- Auto-generation markers in `pictures.html` and `index.html`.

### Polish

- Homepage redesigned with side-by-side masthead, refined typography,
  thin SVG line icons, hairline borders, dashed dividers replaced.
- Featured-card treatment for Guide 4 (Start Here) and Guide 1
  (Peppers).
- Tag-style filters above the guide grid.
- "Last updated" date stamps per card.
- New mobile breakpoints at 720px and 480px.
- `changelog.html` reader-facing release-notes page.
- `pictures.html` matches the new masthead pattern.

## 2026.04 — April 2026

### Major: Library consolidated from 10 guides to 6

The pepper trilogy (A + C + I), nutrient trio (E + F + G), and bato
bucket pair (B + I) collapsed into single authoritative guides.

- **Guide 1 — Peppers in the Dragoons** (merges old A + C + I)
- **Guide 2 — Bato Bucket Hydroponic Systems** (refresh of old B)
- **Guide 3 — Hydroponic Nutrients** (merges old E + F + G)
- **Guide 4 — Hydroponic Primer & Library Map** (repurposes old D)
- **Guide 5 — Grapes in the Dragoons** (light refresh of old H)
- **Guide 6 — Cool-Season Crops** (expanded from old J brassicas
  to brassicas + alliums + greens + roots)

Established the hybrid repetition rule and codified editorial
principles in `PRINCIPLES.md`. Resolved the 1.5 vs 2.4 g/gal Epsom
conflict between guides B and E.

### Polish: Warm watercolor design system

Replaced the original stark-green palette with a warmer
watercolor-inspired theme across all PDFs and the website: cream
paper (`#FBF5E6`), warm charcoal body text, sage green headings,
terracotta accents. Side-by-side masthead introduced. Thin SVG icons
replaced emoji bullets. Gallery page came online.

## Project conventions

- **Versioning:** `YYYY.MM` for the library, e.g., `Version 2026.05`.
  Bump on substantive content additions or restructures.
- **Date format:** ISO `YYYY-MM-DD` for revision stamps; "Month Year"
  for prose.
- **Editorial principles:** see [PRINCIPLES.md](PRINCIPLES.md). The
  5-point evaluation checklist gates new content.
- **Workflow tooling:** [scripts/sync-pictures.py](scripts/sync-pictures.py)
  for gallery updates; manual rebuild via `build_pdf.sh` for guide
  edits.
- **Backlog:** see [TODO.md](TODO.md). Items get an `[INTEGRATED ...]`
  tag when folded into a guide.
