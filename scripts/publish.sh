#!/usr/bin/env bash
# publish.sh — build the deployable tree and push it to Cloudflare Pages.
#
# Replaces `railway up --detach` (the library moved off Railway 2026-07-25).
# Usage:
#   scripts/publish.sh            # deploy to production
#   scripts/publish.sh --dry-run  # build + check the tree, deploy nothing
#
# WHY A BUILD STEP AT ALL — the repo root is NOT the doc root. Railway's
# Dockerfile used an explicit COPY allow-list, so MARKET_REPORT.md, TODO.md,
# AGENT.md, PRINCIPLES.md, and scripts/ were never served. Deploying the repo
# root to Pages would publish all of them. This script reproduces that
# allow-list and then *verifies* the result rather than trusting it.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO/.publish"
PROJECT="dmr-guides"
ACCOUNT_ID="aed2b4225c65aeed23c87533667d3b16"
TOKEN_FILE="$HOME/.key/cloudflare-pages.token"
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

cd "$REPO"
rm -rf "$OUT"; mkdir -p "$OUT"

# --- the allow-list ----------------------------------------------------------
cp index.html pictures.html changelog.html search.html cheats.html 404.html \
   search-index.json "$OUT/"
# All guide PDFs EXCEPT the 16.5 MB bound volume, which is linked from GitHub
# raw instead of shipped (index.html points at the raw URL, not a local path).
for p in *.pdf; do
  [ "$p" = "library_volume1.pdf" ] && continue
  cp "$p" "$OUT/"
done
cp -r pictures cheats diagrams "$OUT/"

# --- refuse to ship anything that was never meant to be public ---------------
LEAKED=$(find "$OUT" -type f \( -name '*.md' -o -name '*.py' -o -name 'Dockerfile*' \
         -o -name '*.conf' -o -name '.env*' \) 2>/dev/null || true)
if [ -n "$LEAKED" ]; then
  echo "ABORT: the publish tree contains files that must not be served:"
  echo "$LEAKED"
  exit 1
fi

# --- refuse to ship a broken site --------------------------------------------
/usr/bin/python3 - "$OUT" <<'PY'
import glob, os, re, sys
out = sys.argv[1]
missing = set()
for h in glob.glob(os.path.join(out, "*.html")):
    for m in re.findall(r'(?:href|src)="([^"#]+)"', open(h, encoding="utf-8", errors="replace").read()):
        if m.startswith(("http://", "https://", "mailto:", "data:", "javascript:")):
            continue
        # Root-relative ("/search.html") and document-relative ("search.html")
        # both resolve against the publish root here. os.path.join would
        # silently discard `out` for the leading-slash form and then "find"
        # the file on the real filesystem — a checker that passes by accident.
        rel = m.split("?")[0].lstrip("/")
        if rel in ("", "."):
            continue
        if not os.path.exists(os.path.join(out, rel)):
            missing.add(f"{os.path.basename(h)} -> {m}")
if missing:
    sys.exit("ABORT: broken local links:\n  " + "\n  ".join(sorted(missing)))
n = len([f for r, _, fs in os.walk(out) for f in fs])
print(f"publish tree OK: {n} files, no broken local links, nothing private")
PY

if [ "$DRY_RUN" = 1 ]; then
  echo "--dry-run: built $OUT, deployed nothing."
  exit 0
fi

[ -f "$TOKEN_FILE" ] || { echo "🔒 ~/.key locked or token missing — run keyvault/unlock.sh"; exit 1; }
export CLOUDFLARE_API_TOKEN="$(cat "$TOKEN_FILE")"
export CLOUDFLARE_ACCOUNT_ID="$ACCOUNT_ID"
npx --yes wrangler@latest pages deploy "$OUT" --project-name "$PROJECT" --branch main

echo
echo "Deployed. Spot-checking the live site..."
for p in "" search.html cheats.html guide1_primer.pdf pictures/Herbs.jpg; do
  printf '  %s  /%s\n' "$(curl -sSL -o /dev/null -w '%{http_code}' --max-time 60 "https://dmr-guides.pages.dev/$p")" "$p"
done
printf '  %s  /this-should-404 (expect 404)\n' \
  "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 30 "https://dmr-guides.pages.dev/this-should-404?cb=$$")"
