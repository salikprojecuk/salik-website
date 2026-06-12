import os
import sys

TRACKING_ID = 'G-MLWQZHT65N'
SNIPPET = '''<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-MLWQZHT65N"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-MLWQZHT65N');
</script>'''

modified = []
skipped = []

root = os.path.dirname(os.path.abspath(__file__))

for dirpath, dirnames, filenames in os.walk(root):
    for filename in filenames:
        if not filename.endswith('.html'):
            continue
        filepath = os.path.join(dirpath, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if TRACKING_ID in content:
            skipped.append(filepath)
            continue
        # Find the <head> tag (case-insensitive, handles attributes)
        lower = content.lower()
        idx = lower.find('<head')
        if idx == -1:
            skipped.append(filepath)
            continue
        # Find the end of the opening <head...> tag
        close = content.find('>', idx)
        if close == -1:
            skipped.append(filepath)
            continue
        insert_at = close + 1
        new_content = content[:insert_at] + '\n' + SNIPPET + '\n' + content[insert_at:]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        modified.append(filepath)

print(f"\nModified ({len(modified)} files):")
for p in modified:
    print(f"  {p}")

print(f"\nSkipped ({len(skipped)} files):")
for p in skipped:
    print(f"  {p}")
