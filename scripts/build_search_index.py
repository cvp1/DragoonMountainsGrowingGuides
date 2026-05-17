#!/usr/bin/env python3
"""
Rebuild search-index.json from the guide markdown sources.

Walks build/guide{1..15}_*.md, parses H1/H2/H3 heading hierarchy, extracts
section-body text, normalizes markdown out, emits the JSON the static
search page consumes (fields: g, gt, pdf, s, sh, b).

Run from build/:
    python3 build_search_index.py [OUTPUT_PATH]

OUTPUT_PATH defaults to search-index.json in the current directory.
"""

from __future__ import annotations
import json
import re
import sys
from pathlib import Path

BODY_CAP = 1500           # max chars in the body excerpt
GUIDE_GLOB = "guide*.md"
EXCLUDE_FILES = set()     # any source files to skip


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Strip YAML front matter from the top of the document and return (meta, rest)."""
    meta: dict = {}
    if not text.startswith("---"):
        return meta, text
    end = text.find("\n---", 3)
    if end == -1:
        return meta, text
    block = text[3:end].strip()
    rest = text[end + 4:].lstrip()
    # Minimal YAML: only need title
    for line in block.splitlines():
        m = re.match(r'^([a-zA-Z_]+):\s*"?(.*?)"?\s*$', line)
        if m:
            key, val = m.group(1), m.group(2)
            meta[key] = val.strip('"').strip("'")
    return meta, rest


def normalize_body(raw: str) -> str:
    """Strip markdown, LaTeX, callout wrappers, etc. Flatten to plain searchable prose."""
    s = raw
    # Strip fenced code blocks (raw LaTeX blocks etc.)
    s = re.sub(r'```\{?=?\w*\}?\s*\n.*?\n```', ' ', s, flags=re.DOTALL)
    s = re.sub(r'```.*?```', ' ', s, flags=re.DOTALL)
    # Strip ::: callout wrappers (keep inner text)
    s = re.sub(r'^:::\s*\w+\s*$', '', s, flags=re.MULTILINE)
    s = re.sub(r'^:::\s*$', '', s, flags=re.MULTILINE)
    # Strip images
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)\{?[^}]*\}?', ' ', s)
    # Strip raw LaTeX commands like \clearpage, \vspace{...}, \textcolor{x}{y}
    # Handle commands with braced args by replacing with the last arg's content
    s = re.sub(r'\\(?:textcolor|color)\{[^}]*\}\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\(?:textit|textbf|emph|underline|texttt)\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\[a-zA-Z]+\*?\{[^}]*\}', ' ', s)  # any other \cmd{...}
    s = re.sub(r'\\[a-zA-Z]+\*?', ' ', s)            # bare \cmd
    s = re.sub(r'\\[,;:]', ' ', s)                   # spacing macros
    # Strip inline math $...$ — keep content
    s = re.sub(r'\$([^$]+)\$', r'\1', s)
    # Strip pandoc attribute spans {.class width=...}
    s = re.sub(r'\{[^}]*\}', ' ', s)
    # Markdown emphasis to plain
    s = re.sub(r'\*\*([^*]+)\*\*', r'\1', s)
    s = re.sub(r'\*([^*]+)\*', r'\1', s)
    s = re.sub(r'_([^_]+)_', r'\1', s)
    # Markdown links [text](url) → text
    s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s)
    # Tables: convert pipe rows to space-joined; strip separator rows
    out_lines = []
    for line in s.splitlines():
        ls = line.strip()
        if re.match(r'^\|?[\s\-:|]+\|?$', ls):
            continue  # table separator
        out_lines.append(line)
    s = '\n'.join(out_lines)
    # Bullet markers
    s = re.sub(r'^\s*[-*+]\s+', '', s, flags=re.MULTILINE)
    s = re.sub(r'^\s*\d+\.\s+', '', s, flags=re.MULTILINE)
    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def cap_at_word(s: str, cap: int) -> str:
    if len(s) <= cap:
        return s
    cut = s.rfind(' ', 0, cap)
    if cut < cap * 0.7:  # very long token — hard cut
        cut = cap
    return s[:cut].rstrip(' ,;:.-') + '…'


HEADING_RE = re.compile(r'^(#{1,3})\s+(.+?)\s*$')


def extract_entries(md_text: str, meta: dict, pdf_name: str, guide_num: str):
    """Walk a markdown document and yield search-index entries."""
    lines = md_text.splitlines()
    # First, find every heading and its position
    headings = []  # (line_idx, level, title)
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            # Strip leading "N · " chapter-number prefix from H1s for cleaner sh
            title_clean = re.sub(r'^\d+\s*[·.]\s*', '', title)
            headings.append((i, level, title_clean))

    # H1 chapters get sequential §-numbers
    h1_count = 0
    # Maintain a stack of [(level, title)] to build the sh path
    path_stack: list[tuple[int, str]] = []
    h1_section_num: dict[int, str] = {}  # heading idx → §N

    # Build entries
    entries = []
    for idx, (line_i, level, title) in enumerate(headings):
        if level == 1:
            h1_count += 1
            section_num = f"§{h1_count}"
            h1_section_num[idx] = section_num
            path_stack = [(1, title)]
            sh = title
        else:
            # Find parent H1
            while path_stack and path_stack[-1][0] >= level:
                path_stack.pop()
            path_stack.append((level, title))
            sh = ' — '.join(t for _, t in path_stack)
            # Section number = the §N of the most recent H1
            parent_h1_idx = idx
            while parent_h1_idx >= 0 and headings[parent_h1_idx][1] != 1:
                parent_h1_idx -= 1
            section_num = h1_section_num.get(parent_h1_idx, '')
            if not section_num:
                continue  # heading before any H1 — skip

        # Extract body: lines from after this heading to before the next heading
        body_start = line_i + 1
        if idx + 1 < len(headings):
            body_end = headings[idx + 1][0]
        else:
            body_end = len(lines)
        body_raw = '\n'.join(lines[body_start:body_end])
        body = normalize_body(body_raw)
        body = cap_at_word(body, BODY_CAP)

        entries.append({
            'g': guide_num,
            'gt': meta.get('title', '').strip(),
            'pdf': pdf_name,
            's': section_num,
            'sh': sh,
            'b': body,
        })
    return entries


def guide_number(filename: str) -> str | None:
    m = re.match(r'guide(\d+)_', filename)
    return m.group(1) if m else None


def main(out_path: str = 'search-index.json'):
    build_dir = Path(__file__).resolve().parent
    md_files = sorted(build_dir.glob(GUIDE_GLOB),
                      key=lambda p: int(re.match(r'guide(\d+)', p.name).group(1)))
    all_entries = []
    for md_path in md_files:
        if md_path.name in EXCLUDE_FILES:
            continue
        gnum = guide_number(md_path.name)
        if not gnum:
            continue
        text = md_path.read_text(encoding='utf-8')
        meta, body_text = parse_front_matter(text)
        entries = extract_entries(body_text, meta, md_path.stem + '.pdf', gnum)
        all_entries.extend(entries)
        print(f"  guide {gnum:>2}: {len(entries):>3} entries ({md_path.name})")

    print()
    print(f"Total: {len(all_entries)} entries")

    json_text = json.dumps(all_entries, ensure_ascii=False, separators=(',', ':'))
    Path(out_path).write_text(json_text, encoding='utf-8')
    print(f"Wrote {out_path} ({len(json_text):,} bytes)")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'search-index.json')
