"""Check generated navigation and ensure every source record has a page."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
android = json.loads((ROOT / 'data/versions.json').read_text())
macos = json.loads((ROOT / 'data/macos.json').read_text())
count = 0
for path in ROOT.rglob('*.md'):
    if '.git' in path.parts:
        continue
    text = path.read_text()
    assert text.startswith('# '), path
    for link in re.findall(r'\]\(([^)]+)\)', text):
        if link.startswith(('https://', 'http://', '#')):
            continue
        assert (path.parent / link).exists(), (path, link)
    count += 1
for row in android:
    version = row['version']
    filename = row['url'].rsplit('/', 1)[1][:-4]
    page = ROOT / 'android' / version / filename / 'README.md'
    assert row['url'] in page.read_text(), page
    assert version in (page.parent.parent / 'README.md').read_text()
for row in macos:
    page = ROOT / 'macos' / row['slug'] / 'README.md'
    text = page.read_text()
    assert row['release_url'] in text, page
    for asset in row['assets']:
        assert asset['url'] in text, (page, asset['name'])
    for key, length in [('md5', 32), ('sha256', 64)]:
        assert row[key] is None or re.fullmatch('[a-f0-9]{%d}' % length, row[key]), row
assert len(list((ROOT / 'android').glob('*/README.md'))) == len({r['version'] for r in android})
assert len(list((ROOT / 'macos').glob('*/README.md'))) == len(macos)
print(f'Validated {count} Markdown files, all local links, {len(android)} Android packages and {len(macos)} macOS releases.')
