# Agent Handoff — Working with This Repo

Instructions for recreating the Claude agent instance that built this
library, or for handing the workflow to a different collaborator (human
or AI). Read this file at the start of any new session before touching
the guides. The 17 guides are the product; this file is the operating
manual that produced them.

The earlier sections describe the environment to set up. The later
sections describe what the agent should *know* — the voice, the
conventions, the gotchas that don't live in any single guide.

---

## 1. Environment

### 1.1 Tooling

The agent runs inside Anthropic's **Cowork mode** (Claude desktop app),
which provides:

- A sandboxed Linux VM (Ubuntu) with pandoc, xelatex/TeX Live, ghostscript,
  Python 3, and standard CLI tools preinstalled
- File tools (Read, Write, Edit) with access to a mounted host folder
- A bash shell scoped to the sandbox
- A `request_cowork_directory` MCP tool that mounts host folders into the VM
- Subagent dispatch (general-purpose, Explore, Plan, claude-code-guide)
- A scheduled-tasks MCP for cron-style runs
- A pdf-viewer MCP for in-conversation PDF rendering

Equivalent setups outside Cowork: Claude Code (CLI) plus a local Linux
environment with the same toolchain. Claude.ai web doesn't have file
access so it can't run this workflow directly.

### 1.2 Required CLI tools (verify on first session)

```sh
pandoc --version     # ≥ 3.0
xelatex --version    # any TeX Live
gs --version         # ≥ 9.50 for PDF compression
python3 --version    # ≥ 3.9
python3 -c "import pypdf, cairosvg, PIL"   # picture-sync and bundle build
```

The Cowork VM ships with all of these. If recreating outside Cowork,
install pandoc, TeX Live (full or `xetex` + `texlive-fonts-extra`),
ghostscript, and `pip install pypdf cairosvg pillow`.

### 1.3 Mounting the project folder

In a new Cowork session, the working folder is not mounted by default.
Have the agent call `request_cowork_directory` with the host path:

```
/Users/craigvandeputte/data/GitHub/DragoonMountainsGrowingGuides
```

The VM path it surfaces at is
`/sessions/<session-id>/mnt/DragoonMountainsGrowingGuides`.

**The mount has one critical limitation: `unlink` is blocked.** The
VirtioFS bridge passes write operations through to the host but rejects
file deletions. `rm`, `mv` (because `mv` is copy+delete), and `git
checkout -- file` all fail with "Operation not permitted." Workarounds:

- To overwrite an existing file with new content: `cat new_content >
  existing_file` works (truncate + write, no unlink)
- To delete a file: the user must run `rm` themselves in their Mac
  Terminal; the agent cannot do this
- To restore a file the agent accidentally truncated: `git show HEAD:path
  > path` (same redirect trick)

This is the #1 footgun. If the agent tries to delete or mv anything on
the mount, it will fail. The agent should always work via overwrite, and
when deletion is truly needed, write a copy-paste shell snippet for the
user to run on the Mac.

The session's scratch folder (`/sessions/<session-id>/build/` if present,
or the agent's working directory) is a real ext4 filesystem and supports
unlink normally. Use it for intermediate work.

### 1.4 Plugins active in this workspace

The agent that built this library had these Cowork plugins loaded
(visible in the agent's `<available_skills>` listing):

- `engineering` (debug, code-review, testing-strategy, architecture,
  incident-response, system-design, standup, documentation,
  deploy-checklist, tech-debt) — not heavily used but available
- `productivity` (start, update, task-management, memory-management) —
  not used directly; the agent uses its own TaskCreate/TaskUpdate tools
- `cowork-plugin-management` — plugin authoring tools, not used here
- Default Cowork skills: doc-coauthoring, internal-comms, schedule,
  theme-factory, setup-cowork, xlsx, pdf, docx, pptx, mcp-builder,
  web-artifacts-builder, skill-creator

For this project specifically, the only skills regularly used are **pdf**
(for PDF reading and manipulation) and the **schedule** skill if the user
wants cron-style runs. The rest are noise that can be ignored.

### 1.5 Git workflow

The user pushes git from their Mac, not from the Cowork session. The
agent's job is to make changes in the working tree; the user reviews
`git status`, stages, commits, pushes. The agent should never run `git
push`, and should be careful with `git commit` — only commit when the
user explicitly says so.

Deploy goes through Railway (`railway up` from the Mac terminal, or
git-triggered deploy from the GitHub repo). The agent doesn't deploy;
the user does. See §5.3.

---

## 2. Project map

```
DragoonMountainsGrowingGuides/
├── guide{1..17}_*.pdf       # the 17 deployed guides (compressed)
├── first_season.pdf         # narrative companion
├── library_volume1.pdf      # bound-volume (excluded from Railway deploy)
├── README.md                # front-of-repo doc, also linked from GitHub
├── AGENT.md                 # this file
├── PRINCIPLES.md            # editorial north star — read before drafting
├── TODO.md                  # backlog with [INTEGRATED] markers
├── CHANGELOG.md             # project-level revision log
├── MARKET_REPORT.md         # audience research
├── index.html               # homepage
├── cheats.html              # cheat sheet listing
├── search.html              # client-side search UI
├── changelog.html           # rendered changelog page
├── pictures.html            # photo gallery
├── search-index.json        # built search index (~1.6 MB)
├── pictures-manifest.json   # source of truth for gallery (excluded)
├── Dockerfile               # nginx:alpine static deploy
├── nginx.conf               # serving config
├── .dockerignore / .railwayignore
├── cheats/
│   └── cheat_*.pdf          # 6 letter-size + 1 wall poster
├── pictures/
│   ├── *.jpeg               # raw originals (excluded from deploy)
│   └── *.jpg                # web-optimized variants (shipped)
├── diagrams/
│   └── *.svg / *.png        # Guide 14 structure illustrations
├── scripts/
│   ├── sync-pictures.py     # gallery sync (excluded from deploy)
│   └── build_search_index.py # search index builder (excluded)
└── .git, .stfolder          # housekeeping (excluded)
```

**Source markdown does not live in this repo.** The agent works on
`.md` source files in a separate `build/` scratch folder inside the
Cowork session (not on the mount). Built PDFs are written back to the
repo via the cat-redirect trick (§1.3). The deployed repo only ships
PDFs and HTML; the markdown source is the agent's workspace.

If recreating this project from scratch, the markdown source files
would need to be checked into a separate `src/` folder or kept in
parallel to the repo. The current arrangement (markdown in session
scratch, PDFs in git) is a consequence of how the Cowork sessions
incrementally built up the project.

---

## 3. Build pipeline

The pipeline is intentionally low-magic: one bash script per PDF, a
shared LaTeX header, one pandoc Lua filter. No npm, no make, no CI.

### 3.1 Standard guide build

```sh
./build_pdf.sh guide5_grapes.md guide5_grapes.pdf --print
```

`build_pdf.sh` (in the session scratch folder, not in the repo) wraps
pandoc with these flags:

- `--pdf-engine=xelatex`
- `--lua-filter=div-to-env.lua` (converts `:::` divs to tcolorboxes)
- `-V geometry:margin=1in -V papersize=letter` (standard letter size)
- `-V mainfont="DejaVu Serif" -V monofont="DejaVu Sans Mono"`
- `--toc --toc-depth=2`
- `-H header.tex` (the shared LaTeX preamble — warm watercolor palette
  in cream mode; near-black in `--print` mode)

The `--print` flag swaps cream pagecolor for white, darkens accent
colors (greendark, terracotta, gold, slate, textmuted) to near-black
variants, strips callout box backgrounds. Used for every deployed PDF
in the library. The cream/colored mode exists but is not currently used.

### 3.2 Cheat sheet build — bypass build_pdf.sh

Cheats use **custom YAML geometry** (0.3" margins, paper-specific size)
and **no TOC**. `build_pdf.sh` hardcodes geometry and TOC, which overrides
the YAML and breaks the layout. Build cheats with direct pandoc:

```sh
PRINT_HEADER=$(mktemp --suffix=.tex) && cat > "$PRINT_HEADER" << 'TEX'
\pagecolor{white}
\color{black}
\definecolor{greendark}{HTML}{1F3A20}
\definecolor{greenmid}{HTML}{2F4A2C}
\definecolor{terracotta}{HTML}{5A2C1E}
\definecolor{terracottasoft}{HTML}{6B3624}
\definecolor{gold}{HTML}{5A4828}
\definecolor{textmuted}{HTML}{4A4A4A}
\definecolor{slate}{HTML}{2A2A2A}
\definecolor{bodytext}{HTML}{000000}
\definecolor{hairline}{HTML}{888888}
\tcbset{enhanced jigsaw,colback=white}
TEX

pandoc cheats/cheat_NAME.md \
  -o cheats/cheat_NAME.pdf \
  --pdf-engine=xelatex \
  --lua-filter=div-to-env.lua \
  -V mainfont="DejaVu Serif" \
  -V monofont="DejaVu Sans Mono" \
  -V linestretch=1.05 \
  -V colorlinks=true \
  -V linkcolor=black \
  -V urlcolor=black \
  -H header.tex \
  -H "$PRINT_HEADER" \
  -H cheats/cheat_overrides.tex     # density overrides — see §3.4
rm -f "$PRINT_HEADER"
```

`cheats/cheat_overrides.tex` shrinks tcolorbox padding and tightens
inter-paragraph spacing so the bottom callouts don't overflow off the
single page.

### 3.3 Wall poster build — also bypass build_pdf.sh

The 24×18 poster needs landscape paper size, no TOC, and pifont icons.
Same direct-pandoc invocation as cheats, but **without**
`cheats/cheat_overrides.tex` (the poster has its own density baked in).

### 3.4 PDF compression

After build, run ghostscript on every guide before deploy:

```sh
gs -sDEVICE=pdfwrite \
   -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=guide_tmp.pdf \
   guide_in.pdf
mv guide_tmp.pdf guide_in.pdf       # in build/ folder, mv works
```

Typically 50–65% size reduction with no visible quality loss. Don't
compress cheats (already small) or the wall poster (icons can lose
sharpness). DO compress the bundle if you regenerate it.

### 3.5 Bundle build (`library_volume1.pdf`)

The 1,139-page bound volume uses Python `pypdf` to concatenate:

1. Build a frontmatter PDF (`volume1_frontmatter.md` — cover + master
   TOC + "how to use this volume")
2. Build all 17 guides + first_season individually
3. Run a Python script that reads each PDF, captures page count,
   concatenates with `PdfWriter`, adds PDF bookmarks for every guide,
   and writes `library_volume1.pdf`

The script is in the session's prior transcript (inline Python — never
saved to a file). The master TOC's starting-page numbers are calibrated
to a 4-page frontmatter; if you change the frontmatter length, update
the TOC numbers.

**Vol. 1 does not ship to Railway.** It's listed in `.dockerignore` and
`.railwayignore`. The homepage link points to a GitHub raw URL so the
download comes from GitHub's CDN. After regenerating Vol. 1, the user
must `git push` for the new version to surface.

### 3.6 Search index rebuild

```sh
python3 scripts/build_search_index.py /path/to/repo/search-index.json
```

The script walks every `guide*.md` source, parses H1/H2/H3 hierarchy,
extracts body excerpts (capped at 1500 chars at word boundary),
normalizes markdown out, and emits the JSON the static search page
consumes. Rerun after any guide edit. The output file ships to Railway
and is served gzipped by nginx.

### 3.7 Picture sync

```sh
python3 scripts/sync-pictures.py
```

Drop `.jpeg` originals into `pictures/`. The script resizes to
web-optimized `.jpg`, stubs a manifest entry, regenerates the
AUTOGEN blocks in `pictures.html` and the homepage strip. Manifest
caption fields (`title`, `short`, `full`) are hand-edited after the
first run. Re-run after editing the manifest.

---

## 4. Conventions

### 4.1 Voice

Place-anchored, specific, lightly literary, treats the reader as
competent, prefers observation to claim. Real measurements (°F, sq ft,
gal/wk, days to maturity). Named varieties. Em-dashes liberally. No
exclamations. No emojis. No rhetorical questions.

The single best voice exemplars are Guide 1's opening, Guide 8's herb
chapter intros, and Guide 15's framing chapters (§1 and §2). When
writing a new chapter, read at least one of those first.

PRINCIPLES.md is the codified version of the voice — read it before
starting any new guide.

### 4.2 Front matter (every guide)

```yaml
---
title: "Guide Title"
author: "Guide N · Subtitle"
date: 'Subtitle · Subtitle · Subtitle `\\[0.5em] \textit{\normalsize Version 2026.05 · Revised YYYY-MM-DD}`{=latex}'
---

![](dragoon_mountains_cover.jpg){width=100%}

\clearpage
```

Followed by the `::: relatedguides` block (the library map — see §4.4).

### 4.3 Callout blocks

Four `:::` divs converted to LaTeX tcolorboxes by `div-to-env.lua`:

- `::: relatedguides` — the library map at the start (and sometimes end)
  of each guide; one bullet per sibling guide. Same content across all 17.
- `::: keynote` — a high-signal claim the reader should not miss.
- `::: localtip` — Cochise- or Dragoons-specific note.
- `::: warning` — safety or destructive-mistake guidance. Used least often.

Open and close with `:::` on their own lines.

### 4.4 Cross-references

Format: `*Guide 5 §3.2*` (italicized, em-dash optional). Always italics.
Always with §. The renumber cascade depends on this format being
consistent.

### 4.5 Renumber cascade

When a guide moves position (e.g., Primer was Guide 4, renamed Guide 1),
do a sentinel two-pass on every source file:

1. First pass: every `Guide N` → `GUIDE_NEW_M` (sentinel)
2. Second pass: every `GUIDE_NEW_M` → `Guide M`

Same for filenames (`GUIDEFILE_NEW_N`). A one-pass renumber will corrupt
already-rewritten references.

After renumber, three things to check:

- `::: relatedguides` bullet order (mechanical swap leaves bullets out
  of sequence; sort them with a regex pass)
- Guide 1's "N-guide map" chapter — H2 subsections need reordering with
  the same approach
- Cheat sheets that reference specific guide sections (e.g., master
  calendar pointing back to Guide 1 §9)

### 4.6 Adding a new guide (the library cascade)

When a new guide ships:

1. Update **every** existing guide's `::: relatedguides` block to add
   the new guide line. Some guides have two relatedguides blocks (front +
   back) — update both.
2. Bump the count in opening prose: "one of fifteen" → "one of sixteen",
   "fifteen-guide library" → "sixteen-guide library", "15-guide map" →
   "16-guide map" (Guide 1 only).
3. Add a new H2 subsection to Guide 1's N-guide map chapter (Guide 1's
   §3) describing the new guide.
4. Add a homepage card with an SVG icon, eyebrow tag, description, and
   page-count meta line.
5. Update README's library-at-a-glance table.
6. Rebuild ALL guides (relatedguides changed in all of them) and deploy.
7. Rebuild search index.

If using `sed` to insert the new relatedguides line, **watch for false
matches** in Guide 1's N-guide map chapter where guide names appear as
H2 headers. Use Edit tool for Guide 1 instead of sed.

---

## 5. User defaults and preferences

These reflect the choices the user made over many sessions and should
be assumed in similar future questions unless the user redirects.

### 5.1 Scope

When asked to scope a new guide, **prefer comprehensive over lean**. The
user has consistently chosen "equal-weight, full coverage" over focused
options. ~60-100 page guides are the norm.

### 5.2 Tone

When asked about cultural framing (especially for native crops), the
user picked "acknowledge + attribute, light hand" — substantive but not
the lead. Treat indigenous knowledge with respect but stay
cultivation-grounded; don't center the cultural piece as primary.

### 5.3 Deploy / commit

The user pushes from their Mac after reviewing `git status`. Don't `git
push` from the Cowork session. Don't `git commit` unless explicitly
asked. After making changes, leave the working tree dirty and let the
user commit.

When changes can't be made on the FUSE mount (deletions), provide a
copy-paste shell snippet for the user's Mac terminal.

### 5.4 Print mode

All deployed PDFs use `--print` mode (white paper, near-black accents).
The cream-paper variant is not currently shipped. Don't switch back
without asking.

### 5.5 Cheat sheet philosophy

Cheats are single-page references. If a cheat overflows to page 2, the
fix order is: (1) apply `cheat_overrides.tex` density adjustments, (2)
trim text by a sentence or two, (3) shrink the font half a point. Don't
let a cheat ship as 2 pages — the whole point of a cheat is print-and-tape.

### 5.6 Voice anchor strategy

For substantial guides (~60+ pages), the working pattern is:

1. Agent writes front matter + About + §1 + §2 directly (the voice anchor)
2. Agent commissions a subagent to draft §3 through §N with the voice
   anchor + research scaffolding + tight format specs
3. Agent writes closing chapters (sources, closing) directly
4. Agent does a light integration edit — voice consistency, cross-refs

The subagent path saves substantial conversation length without
sacrificing voice quality, provided the specs are detailed enough.

---

## 6. Operational gotchas (in priority order)

1. **FUSE mount rejects `unlink`.** Use overwrite via `cat new > old`.
   Never `rm` or `mv` on the mount. (§1.3)
2. **`build_pdf.sh` overrides YAML geometry and forces a TOC.** Cheats
   and the wall poster must use direct pandoc. (§3.2, §3.3)
3. **Library cascade is mechanical and error-prone.** When sed-inserting
   a new relatedguides bullet after the highest-numbered guide, double-check
   Guide 1 doesn't have the same string as an H2 header. (§4.6)
4. **`library_volume1.pdf` is 16.5 MB and excluded from Railway.** The
   homepage link points to a GitHub raw URL. After regenerating, the
   user must push for the link to serve the new version. (§3.5)
5. **PDFs compressed with `gs -dPDFSETTINGS=/ebook` are ~50% smaller**
   with no visible loss. Always compress before deploy. (§3.4)
6. **The Dockerfile lists each HTML file explicitly.** When you add a
   new top-level HTML page (e.g., the `cheats.html` listing), add it to
   the Dockerfile COPY list or it won't ship.
7. **Stale renumbered PDFs.** After the May 2026 renumber, stale
   filenames (`guide1_peppers.pdf`, etc.) lingered on the Syncthing-managed
   disk. Both `.dockerignore` and `.railwayignore` carry exclusion lines
   for them so they don't deploy. Don't remove those lines.
8. **`pifont` and DejaVu Sans Mono** are in the build pipeline because
   the wall poster uses `\ding{}` icons and code blocks (Guide 16's guild
   diagrams) need Unicode box-drawing chars. Don't remove from
   `header.tex` or `build_pdf.sh`.
9. **search-index.json bodies are capped at 1,500 chars.** Increasing
   the cap inflates the file size linearly; decreasing it loses search
   recall. 1500 is the current balance. (§3.6)
10. **Picture pipeline is idempotent.** `sync-pictures.py` is safe to
    re-run as many times as needed; it only does work when new originals
    appear or the manifest changes.

---

## 7. First-hour checklist for a new session

If you're picking up this work in a new Cowork session:

```
[ ] Verify Cowork has mounted the project folder
    (request_cowork_directory /Users/craigvandeputte/data/GitHub/DragoonMountainsGrowingGuides
     if not already mounted)
[ ] Read AGENT.md (this file) — you're here
[ ] Read README.md — repo layout, build conventions, library map
[ ] Read PRINCIPLES.md — the editorial north star (voice)
[ ] Skim TODO.md — backlog state, what's integrated, what's open
[ ] Skim CHANGELOG.md — recent revisions, current version
[ ] git log -10 — last few commits to see what's just landed
[ ] Verify tooling: pandoc, xelatex, gs, python3+pypdf
[ ] If editing a guide, read at least one chapter of an adjacent
    guide first to absorb the voice
[ ] If writing a new guide, read Guide 15 (§1, §2) or Guide 16 (§1) —
    those are the strongest voice exemplars
[ ] If touching the build pipeline, read §3 of this file carefully
```

If the user asks "where are we?", the typical answer at any given moment
is: 17 guides + first_season + cheats + wall poster + Vol. 1 bundle all
deployed; the backlog state lives in `TODO.md` with `[INTEGRATED]`
markers for closed items.

---

## 8. Things this agent did *not* know to do, in case the next one
   needs to

A short list of things that were learned only through this session,
worth capturing for the future:

- The FUSE unlink restriction was discovered by trying to `rm` files
  during the cleanup pass. The workaround (`cat > file` to overwrite)
  came from observing that `truncate -s 0` worked while `rm` didn't.
- The wall poster wouldn't render box-drawing chars until `pifont` and
  `monofont="DejaVu Sans Mono"` were added. The default xelatex math
  font (Latin Modern Math) lacks ★ ▲ ─ etc.
- The cheat sheets' YAML geometry was being overridden by
  `build_pdf.sh`'s hardcoded `-V geometry:margin=1in` until I bypassed
  the script. This was the same root cause as the wall-poster geometry
  problem.
- Guide 1's "N-guide map" chapter has H2 section headings that look
  identical to the relatedguides bullets, so naive sed insertion
  duplicates content in the wrong place. Use Edit, not sed, for Guide 1.

Add new items here as you learn them. This is the institutional memory
of the workflow.

---

\textit{— AGENT.md, last revised 2026-05-17, Dragoon Mountains.}
