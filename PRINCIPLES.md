# DMR Growing Guides — Editorial Principles

The north-star objective for the library:

> **A well-rounded series of guides that are easy to adopt and learn from
> — instructional enough for a beginner to follow, deep enough to answer
> expert-level questions.**

Everything below is in service of that objective. Reference this file
when writing new content, refactoring existing guides, or evaluating
whether a draft is ready to ship.

---

## What "beginner to expert" means in practice

The reader you're writing for varies. The same guide should support all
three of these uses without forcing any of them to read material meant
for the others:

1. **The first-timer skimming the page** wants to know: am I in the
   right place, and what should I actually do first?
2. **The competent practitioner returning for a reminder** wants the
   specific number, the table, the recipe — fast.
3. **The expert troubleshooting an edge case** wants the full reasoning
   chain, the variables, the exceptions.

A guide that only serves one of these is incomplete.

---

## Structural patterns that achieve this

**Layered information architecture.** Each guide should be readable at
multiple depths:

- *Skim depth* — table of contents, section headings, and callouts tell
  the story alone. A reader who only reads these should understand what
  the guide covers and where to dig deeper.
- *Mid depth* — short intros + reference tables. A reader who reads the
  intro paragraph + the table for the relevant chapter has enough to act.
- *Full depth* — the prose explains the why behind each table value and
  walks through edge cases.

**Decision matrices early, reference tables late.** Every guide should
have at least one "choose your path" table near the start (e.g., "soil
vs hydroponic", "this crop vs that crop"). The deep reference tables
(variety SHU/days/height, EC/pH by stage, etc.) come later and are
denser.

**Procedural recipes are step-numbered.** Anything a reader needs to do
in a specific order — bicarbonate water treatment, stock-solution
mixing, transplant — is numbered, not paragraph prose.

**Callouts surface what matters most.** The four callout types each
play a distinct role:

- `::: relatedguides` — orient the reader at the top of every guide.
- `::: keynote` — the single thing the reader should remember from this
  section. Use sparingly so they retain weight.
- `::: localtip` — Dragoons-specific knowledge a generic guide wouldn't
  have. This is our voice / unique value.
- `::: warning` — failure modes and safety. Save for material harm.

**Cross-references over duplication** (the hybrid rule, established
during the 10→6 consolidation). Procedural recipes have one canonical
home; everywhere else cross-refs. Context paragraphs (climate, "the
Dragoons" framing) can repeat across guides so each guide stays
standalone-readable.

---

## Voice

- Warm and factual. Like a knowledgeable neighbor walking the bed with
  you. Not academic, not breezy, not condescending.
- Direct. "Plant May 15," not "you may wish to consider planting around
  the middle of May."
- Specific. Numbers, varieties, dimensions. If you can quantify it, do.
- Honest about uncertainty. "Often" / "usually" / "in most years" when
  the answer genuinely varies. Don't fake precision.
- "The Dragoons" as the unit of place, not "your area" or "in this
  climate." Place-anchored writing is more memorable.
- Italicize *species* and *variety* names on first use in a section.
- Use en-dashes for ranges (50–60 days, not 50-60).
- No emojis in body prose. (The web cards use them; the PDF guides do
  not.)

---

## Onramps for beginners

The library should make it easy for someone new to find their feet:

- **Guide 4** is the front door. It exists to orient newcomers. Any
  major change to the library should prompt a check that Guide 4 still
  works for someone reading it cold.
- **Every guide opens with `::: relatedguides`** listing the other 5,
  one line each. A reader who picked up the wrong guide should
  immediately see which one they actually want.
- **Decision matrices in early chapters** of each crop guide.
- **Glossary terms explained on first use.** Don't assume the reader
  knows what EC, VPD, PPFD, or VSP mean — define them the first time
  they appear in each guide, even if defined elsewhere in the library.
- **"If you're new here" callouts** where appropriate — a `::: keynote`
  that gives a 1-line recommendation for the unsure reader.

---

## Depth for experts

The library should reward the reader who wants to go deep:

- **Variety reference tables** with SHU/days/height/Dragoon-fit rating.
- **Per-stage protocols** (EC, pH, irrigation gal/day, light hours) —
  not just averages.
- **Specific brand or source recommendations** where they matter
  (Masterblend 4-18-38, RAINPOINT timer, specific oak species for
  potash).
- **Failure modes named and diagnosed** — buttoning, tipburn, hollow
  stem, bolt-before-set, etc. Each gets a row in the troubleshooting
  table with cause + fix.
- **Exceptions and edge cases** acknowledged — "this usually works,
  except when X" — not glossed over.
- **The reasoning behind the rule**, not just the rule. A reader who
  understands *why* the bicarbonate routine works can adapt it when
  conditions change.

---

## How to evaluate a draft

Before any new content ships, walk through this checklist:

1. Could a beginner who's never grown this crop read the first
   chapter and know what to do first? If not, the onramp is missing.
2. Could a competent grower find the variety table, the EC chart, the
   month-by-month calendar without reading the prose? If not, the
   reference layer is buried.
3. If an expert asked "why does X happen," does the guide answer that
   somewhere (or point to where it's answered)? If not, the depth
   isn't there.
4. Are the `::: relatedguides` block, cross-references, and date stamps
   consistent with the rest of the library?
5. Is every place-specific claim actually Dragoons-specific, or have
   you imported generic horticultural advice that drifts from the
   voice?

If all five pass, ship it. If any fail, fix that one thing before
shipping.
