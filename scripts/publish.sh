#!/usr/bin/env bash
# publish.sh — build the deployable tree and push it to Cloudflare Pages.
#
# Replaces `railway up --detach` (the library moved off Railway 2026-07-25).
# Usage:
#   scripts/publish.sh            # deploy to production
#   scripts/publish.sh --dry-run  # build + check the tree, deploy nothing
#
# WHY A BUILD STEP AT ALL — the repo root is NOT the doc root. The old Railway
# Dockerfile (deleted with the rest of that setup) used an explicit COPY
# allow-list, so MARKET_REPORT.md, TODO.md, AGENT.md, PRINCIPLES.md, and
# scripts/ were never served. Deploying the repo root to Pages would publish
# all of them. This script is now the only thing standing between the repo and
# the public site, so it verifies its own output rather than trusting the copy.
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
# Everything shipped must be TRACKED IN GIT. That is what makes the deployed
# site reproducible from a clone, and it replaces two hand-maintained exclusion
# lists the Railway setup needed:
#   - stale renumbered PDFs (guide1_peppers.pdf and friends) that linger on the
#     Syncthing-managed disk but were never committed
#   - the raw .jpeg/.JPG camera originals, which are gitignored
# A plain `cp *.pdf` or `cp -r pictures` would ship both. Git already knows the
# difference, so there is no list to keep in sync.
ship() {  # ship <git-pathspec>...
  git ls-files -z -- "$@" | while IFS= read -r -d '' f; do
    mkdir -p "$OUT/$(dirname "$f")"
    cp "$f" "$OUT/$f"
  done
}
ship 'index.html' 'pictures.html' 'changelog.html' 'search.html' 'cheats.html' \
     '404.html' 'search-index.json'
# All guide PDFs EXCEPT the 16.5 MB bound volume, which index.html links from
# the GitHub raw URL rather than shipping.
ship '*.pdf' ':!library_volume1.pdf'
ship 'pictures/*' 'cheats/*' 'diagrams/*'

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

# The old Dockerfile listed each HTML page by hand, so adding a page and
# forgetting to list it silently shipped a site without it. Catch that here
# instead of leaving it as a note in AGENT.md for someone to remember.
import subprocess
tracked = subprocess.run(["git", "ls-files", "*.html"], capture_output=True,
                         text=True).stdout.split()
unshipped = [h for h in tracked if "/" not in h and not os.path.exists(os.path.join(out, h))]
if unshipped:
    sys.exit("ABORT: top-level pages tracked in git but not shipped: "
             f"{unshipped}\n  Add them to the `ship` list in scripts/publish.sh.")

n = len([f for r, _, fs in os.walk(out) for f in fs])
print(f"publish tree OK: {n} files, no broken local links, nothing private, "
      "every tracked page shipped")
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
