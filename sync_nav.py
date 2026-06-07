#!/usr/bin/env python3
"""
Sync the nav CSS block from index.html into every other HTML page.

'Nav block' = everything in <style> from the opening tag up to (but not
including) the first non-NAV section comment (/* ── SOMETHING ── */ where
SOMETHING is not NAV).  Post pages that have no section comments use the
'.container {' rule as the boundary instead.
"""
import re, os, glob

ROOT = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(ROOT, 'index.html'), encoding='utf-8') as f:
    index_src = f.read()

STYLE_OPEN = '  <style>\n'

# Section comments look like:  /* ── SOMETHING ── */
# The ── are two non-ASCII chars (box-drawing or similar).
# Match any section comment whose name is NOT 'NAV' (covers both
# /* ── NAV ── */ and /* ── NAV DROPDOWN ── */).
SECTION_RE    = re.compile(r'/\* [^\x00-\x7f]{2} (?!NAV)')
NAV_SECTION_RE = re.compile(r'/\* [^\x00-\x7f]{2} NAV ')

# --- Extract nav block from index.html ---
idx = index_src.index(STYLE_OPEN)
after_index = index_src[idx:]
m = SECTION_RE.search(after_index)
if not m:
    raise RuntimeError('Could not find page-specific section boundary in index.html')
nav_block = after_index[:m.start()]   # e.g. '  <style>\n...\n\n'
print(f'Nav block: {nav_block.count(chr(10))} lines extracted from index.html\n')

# --- Process every non-index HTML file ---
html_files = sorted(
    p for p in glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True)
    if os.path.normcase(os.path.relpath(p, ROOT)) != 'index.html'
)

changed = 0
skipped = 0

for path in html_files:
    rel = os.path.relpath(path, ROOT)
    with open(path, encoding='utf-8') as f:
        content = f.read()

    s = content.find(STYLE_OPEN)
    if s == -1:
        print(f'  SKIP  (no <style>): {rel}')
        skipped += 1
        continue

    after = content[s:]

    if NAV_SECTION_RE.search(content):
        # Root-level page: find first non-NAV section comment as the boundary
        m2 = SECTION_RE.search(after)
        if not m2:
            print(f'  SKIP  (no page boundary): {rel}')
            skipped += 1
            continue
        end = s + m2.start()
    else:
        # Post / compact page: nav CSS ends just before the .container rule
        m2 = re.search(r'\n    \.container [\{]', after)
        if not m2:
            m2 = re.search(r'\n    \.container\{', after)
        if not m2:
            print(f'  SKIP  (no .container boundary): {rel}')
            skipped += 1
            continue
        end = s + m2.start() + 1   # +1 skips the leading \n; points to '    .container'

    new_content = nav_block + content[end:]

    if new_content == content:
        print(f'  OK    (already current): {rel}')
        continue

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'  UPDATED: {rel}')
    changed += 1

print(f'\nDone — {changed} files updated, {skipped} skipped.')
