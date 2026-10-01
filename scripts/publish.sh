#!/usr/bin/env bash
# Build the deployable tree from an allow-list, verify it, and deploy to Cloudflare Pages.
# Usage:
#   scripts/publish.sh            # deploy to production
#   scripts/publish.sh --dry-run  # build + check the tree, deploy nothing
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

# Ship only git-tracked files, so untracked PDFs and gitignored camera originals stay out.
ship() {  # ship <git-pathspec>...
  git ls-files -z -- "$@" | while IFS= read -r -d '' f; do
    mkdir -p "$OUT/$(dirname "$f")"
    cp "$f" "$OUT/$f"
  done
}
ship 'index.html' 'pictures.html' 'changelog.html' 'search.html' 'cheats.html' \
     '404.html' 'search-index.json'
# The bound volume is linked from GitHub, not shipped.
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
        # Strip the leading slash so os.path.join resolves against the publish root.
        rel = m.split("?")[0].lstrip("/")
        if rel in ("", "."):
            continue
        if not os.path.exists(os.path.join(out, rel)):
            missing.add(f"{os.path.basename(h)} -> {m}")
if missing:
    sys.exit("ABORT: broken local links:\n  " + "\n  ".join(sorted(missing)))

# Every tracked top-level page must be in the ship list.
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
