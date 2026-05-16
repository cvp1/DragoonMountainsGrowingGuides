#!/usr/bin/env python3
"""
sync-pictures.py — keep gallery photos and HTML in sync.

What it does, in order:

1. Scans pictures/ for any .jpeg/.JPEG/.JPG originals and produces a
   web-optimized .jpg next to each one (max 1600px on the long edge,
   progressive JPEG at quality 82, EXIF orientation applied).

2. Updates pictures-manifest.json with stub entries for any .jpg in
   pictures/ that doesn't already have a manifest entry. Existing
   entries are preserved (won't overwrite your captions).

3. Regenerates the gallery section of pictures.html from the manifest
   (everything between the AUTOGEN-GALLERY:START and AUTOGEN-GALLERY:END
   markers).

4. Regenerates the "From the Field" strip on index.html from the
   manifest's featured photos (between AUTOGEN-STRIP:START and
   AUTOGEN-STRIP:END markers).

Workflow:
    # Drop your new photos into pictures/ (any size, .jpeg or .jpg)
    cd /path/to/DMR
    python3 scripts/sync-pictures.py

    # Then edit pictures-manifest.json to fill in captions for any
    # newly-stubbed entries (category, title, short, full). If you
    # want a photo to appear on the homepage strip, set "featured": true.

    # Re-run the sync to regenerate HTML with your captions:
    python3 scripts/sync-pictures.py

    # Commit & redeploy.

Notes:
    - You can have more than 3 photos with "featured": true; only the
      first 3 (in manifest order) show on the homepage strip.
    - The script never overwrites your manifest captions — only adds
      new entries with reasonable defaults.
    - Removing a photo: delete its manifest entry (and optionally the
      .jpg file), then re-run.
"""

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("ERROR: PIL/Pillow is not installed. Install with:")
    print("    pip3 install --user Pillow")
    sys.exit(1)


# ---------- Paths ----------
HERE = Path(__file__).resolve().parent.parent  # DMR/
PICTURES_DIR = HERE / "pictures"
MANIFEST = HERE / "pictures-manifest.json"
PICTURES_HTML = HERE / "pictures.html"
INDEX_HTML = HERE / "index.html"

# ---------- Constants ----------
MAX_DIMENSION = 1600          # long-edge in px for web-optimized .jpg
JPEG_QUALITY = 82             # subjective sweet spot
HOMEPAGE_STRIP_SIZE = 3       # number of featured photos to show on homepage


# ---------- Resize step ----------

def resize_originals():
    """Find .jpeg/.JPEG/.JPG files and produce web-optimized .jpg next to them."""
    converted = []
    if not PICTURES_DIR.is_dir():
        print(f"WARNING: {PICTURES_DIR} doesn't exist; skipping resize step")
        return converted
    for orig in sorted(PICTURES_DIR.iterdir()):
        if not orig.is_file():
            continue
        # Match .jpeg (any case) and .JPG (uppercase only — .jpg is the target)
        if orig.suffix.lower() not in {".jpeg"} and orig.suffix != ".JPG":
            continue
        target = orig.with_suffix(".jpg")
        if target.exists() and target.stat().st_mtime >= orig.stat().st_mtime:
            continue  # already resized and newer than source
        try:
            with Image.open(orig) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                w, h = img.size
                if max(w, h) > MAX_DIMENSION:
                    if w >= h:
                        new_w = MAX_DIMENSION
                        new_h = int(h * MAX_DIMENSION / w)
                    else:
                        new_h = MAX_DIMENSION
                        new_w = int(w * MAX_DIMENSION / h)
                    img = img.resize((new_w, new_h), Image.LANCZOS)
                img.save(
                    target, "JPEG",
                    quality=JPEG_QUALITY, optimize=True, progressive=True,
                )
            orig_kb = orig.stat().st_size // 1024
            new_kb = target.stat().st_size // 1024
            print(f"  resized: {orig.name:30s} {orig_kb:>5} KB  ->  "
                  f"{target.name:30s} {new_kb:>5} KB  ({img.size[0]}x{img.size[1]})")
            converted.append(target.name)
        except Exception as e:
            print(f"  ERROR resizing {orig.name}: {e}")
    return converted


# ---------- Manifest step ----------

def humanize_filename(name):
    """Turn 'Buckets3.jpg' into 'Buckets 3', 'NFT_Greens.jpg' into 'NFT Greens'."""
    stem = Path(name).stem
    # Insert space before digits and uppercase letters following lowercase
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", stem)
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)
    s = s.replace("_", " ").replace("-", " ")
    return " ".join(s.split())


def sync_manifest():
    """Stub manifest entries for any .jpg without one. Preserves existing entries."""
    if not MANIFEST.exists():
        manifest = {
            "_comment": "Single source of truth for gallery photos. Run scripts/sync-pictures.py after editing.",
            "photos": [],
        }
    else:
        with open(MANIFEST) as f:
            manifest = json.load(f)
    existing = {p["file"] for p in manifest.get("photos", [])}

    added = []
    if PICTURES_DIR.is_dir():
        for f in sorted(PICTURES_DIR.iterdir()):
            if f.suffix.lower() != ".jpg":
                continue
            if f.name in existing:
                continue
            stub = {
                "file": f.name,
                "category": "Uncategorized",
                "title": humanize_filename(f.name),
                "short": "",
                "full": "",
                "added": date.today().isoformat(),
                "featured": False,
            }
            manifest["photos"].append(stub)
            added.append(f.name)
            print(f"  stubbed: {f.name}  (title: \"{stub['title']}\" — please edit manifest to fill in captions)")

    # Warn about manifest entries pointing at missing files
    missing = []
    if PICTURES_DIR.is_dir():
        on_disk = {f.name for f in PICTURES_DIR.iterdir() if f.suffix.lower() == ".jpg"}
        for p in manifest.get("photos", []):
            if p["file"] not in on_disk:
                missing.append(p["file"])

    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return added, missing


# ---------- HTML regeneration ----------

GALLERY_START = "<!-- AUTOGEN-GALLERY:START -->"
GALLERY_END = "<!-- AUTOGEN-GALLERY:END -->"
STRIP_START = "<!-- AUTOGEN-STRIP:START -->"
STRIP_END = "<!-- AUTOGEN-STRIP:END -->"


def html_escape(s):
    """Minimal HTML escape for attribute and text values."""
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))


def gallery_card(photo):
    """Render one <figure> block for the gallery."""
    full = photo.get("full") or photo.get("short") or photo.get("title", "")
    short = photo.get("short") or full
    return (
        f'    <figure class="photo" data-full="pictures/{html_escape(photo["file"])}"\n'
        f'            data-caption="{html_escape(full)}">\n'
        f'      <div class="frame">\n'
        f'        <img src="pictures/{html_escape(photo["file"])}" '
        f'alt="{html_escape(photo.get("title", ""))}" loading="lazy" />\n'
        f'      </div>\n'
        f'      <figcaption>\n'
        f'        <div class="cap-eyebrow">{html_escape(photo.get("category", "Uncategorized"))}</div>\n'
        f'        <div class="cap-title">{html_escape(photo.get("title", ""))}</div>\n'
        f'        <div class="cap-desc">{html_escape(short)}</div>\n'
        f'      </figcaption>\n'
        f'    </figure>'
    )


def strip_tile(photo):
    """Render one photo-tile <a> for the homepage strip."""
    return (
        f'      <a class="photo-tile" href="pictures.html">\n'
        f'        <img src="pictures/{html_escape(photo["file"])}" '
        f'alt="{html_escape(photo.get("title", ""))}" loading="lazy" />\n'
        f'        <div class="tile-cap">{html_escape(photo.get("title", ""))}</div>\n'
        f'      </a>'
    )


def strip_more_tile(total):
    """Render the 'View Gallery' more-tile at the end of the homepage strip."""
    return (
        f'      <a class="photo-tile more" href="pictures.html">\n'
        f'        <div class="more-inner">\n'
        f'          <div class="more-icon">+</div>\n'
        f'          <div class="more-text">View All {total} Photos</div>\n'
        f'          <div class="more-sub">setups, plants &amp; place</div>\n'
        f'        </div>\n'
        f'      </a>'
    )


def replace_between(text, start_marker, end_marker, replacement):
    """Replace the content between two HTML comment markers."""
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    new_block = f"{start_marker}\n{replacement}\n{end_marker}"
    new_text, n = pattern.subn(new_block, text)
    return new_text, n


def regenerate_pictures_html(manifest):
    """Rewrite the gallery section of pictures.html."""
    photos = manifest.get("photos", [])
    blocks = "\n\n".join(gallery_card(p) for p in photos)
    if not PICTURES_HTML.exists():
        print(f"WARNING: {PICTURES_HTML} doesn't exist; skipping gallery regen")
        return 0
    with open(PICTURES_HTML) as f:
        text = f.read()
    if GALLERY_START not in text or GALLERY_END not in text:
        print(f"WARNING: {PICTURES_HTML} missing AUTOGEN-GALLERY markers; skipping regen")
        print(f"         expected '{GALLERY_START}' and '{GALLERY_END}' inside the gallery div")
        return 0
    new_text, n = replace_between(text, GALLERY_START, GALLERY_END, blocks)
    if new_text != text:
        with open(PICTURES_HTML, "w") as f:
            f.write(new_text)
    return n


def regenerate_index_strip(manifest):
    """Rewrite the 'From the Field' photo strip on index.html."""
    photos = manifest.get("photos", [])
    featured = [p for p in photos if p.get("featured")][:HOMEPAGE_STRIP_SIZE]
    total = len(photos)
    if not featured:
        # Fall back to the first 3 photos if none marked featured
        featured = photos[:HOMEPAGE_STRIP_SIZE]
    blocks = "\n".join(strip_tile(p) for p in featured)
    blocks = blocks + "\n" + strip_more_tile(total)
    if not INDEX_HTML.exists():
        print(f"WARNING: {INDEX_HTML} doesn't exist; skipping homepage strip regen")
        return 0
    with open(INDEX_HTML) as f:
        text = f.read()
    if STRIP_START not in text or STRIP_END not in text:
        print(f"WARNING: {INDEX_HTML} missing AUTOGEN-STRIP markers; skipping regen")
        print(f"         expected '{STRIP_START}' and '{STRIP_END}' inside the photo-strip div")
        return 0
    new_text, n = replace_between(text, STRIP_START, STRIP_END, blocks)
    if new_text != text:
        with open(INDEX_HTML, "w") as f:
            f.write(new_text)
    return n


# ---------- Main ----------

def main():
    print("=" * 60)
    print("DMR Growing Guides — sync-pictures.py")
    print("=" * 60)

    print("\n[1] Resizing any new .jpeg/.JPG originals...")
    converted = resize_originals()
    if not converted:
        print("  no new originals to resize")

    print("\n[2] Updating pictures-manifest.json...")
    added, missing = sync_manifest()
    if not added:
        print("  no new manifest entries needed")
    if missing:
        print("  WARNING: these manifest entries point to files that don't exist:")
        for m in missing:
            print(f"    - {m}")

    print("\n[3] Regenerating HTML from manifest...")
    with open(MANIFEST) as f:
        manifest = json.load(f)
    g = regenerate_pictures_html(manifest)
    print(f"  pictures.html gallery: {'regenerated' if g else 'no marker found or no change'}")
    s = regenerate_index_strip(manifest)
    print(f"  index.html 'From the Field' strip: {'regenerated' if s else 'no marker found or no change'}")

    print("\n[summary]")
    photos = manifest.get("photos", [])
    featured = [p for p in photos if p.get("featured")]
    print(f"  {len(photos)} photos in manifest")
    print(f"  {len(featured)} marked featured (first {HOMEPAGE_STRIP_SIZE} appear on homepage)")
    if added:
        print(f"\n  NEXT STEPS:")
        print(f"  Edit pictures-manifest.json and fill in captions for these new entries:")
        for f in added:
            print(f"    - {f}")
        print(f"  Then run this script again to regenerate the HTML.")


if __name__ == "__main__":
    main()
