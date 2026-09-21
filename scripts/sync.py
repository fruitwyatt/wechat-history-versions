"""Sync upstream metadata through gh; never download installation packages."""
import base64
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
ANDROID = 'DJB-Developer/wechat-android-history-versions'
MACOS = 'zsbai/wechat-versions'


def api(endpoint, paginate=False):
    args = ['gh', 'api', endpoint]
    if paginate:
        args += ['--paginate', '--slurp']
    result = json.loads(subprocess.check_output(args, text=True))
    return [item for page in result for item in page] if paginate else result


def checksum(value, length):
    return value.lower() if value and re.fullmatch(r'[a-fA-F0-9]{%d}' % length, value) else None


def field(body, name):
    # Horizontal whitespace only: an empty field must not swallow the next line.
    match = re.search(r'^[ \t]*(?:[-*][ \t]*)?' + re.escape(name) + r':[ \t]*([^\r\n]*)', body, re.M | re.I)
    return match.group(1).strip() if match else ''


def parse_release(release):
    body = release.get('body') or ''
    tag = release['tag_name']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]*', tag):
        raise ValueError(f'Unsupported release tag: {tag!r}')
    version = field(body, 'DestVersion') or tag.removeprefix('v')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]*', version):
        raise ValueError(f'Unsupported version: {version!r}')
    official = field(body, 'DownloadFrom')
    parsed = urlparse(official)
    if parsed.scheme != 'https' or parsed.hostname not in {'dldir1.qq.com', 'dldir1v6.qq.com'}:
        official = None
    assets = []
    for asset in release.get('assets', []):
        url = asset['browser_download_url']
        if not url.startswith(f'https://github.com/{MACOS}/releases/download/'):
            raise ValueError('Unexpected asset URL')
        digest = asset.get('digest') or ''
        assets.append(dict(name=asset['name'], size=asset['size'], url=url,
                           sha256=checksum(digest.removeprefix('sha256:'), 64) if digest.startswith('sha256:') else None))
    return dict(tag=tag, slug=tag, version=version, release_url=release['html_url'],
                published_at=release['published_at'], prerelease=release.get('prerelease', False),
                official_url=official, sha256=checksum(field(body, 'Sha256'), 64),
                md5=checksum(field(body, 'Md5'), 32), assets=assets)


def normalize_android(records):
    rows = []
    seen = set()
    for record in records:
        version = record.get('version', '').strip()
        if not version:
            match = re.search(r'\d+(?:\.\d+)+', record.get('name', ''))
            if not match:
                raise ValueError('Missing Android version')
            version = match.group()
        url = record['url'].strip()
        parsed = urlparse(url)
        if not re.fullmatch(r'\d+(?:\.\d+)+', version) or parsed.scheme != 'https' or parsed.hostname not in {'dldir1.qq.com', 'dldir1v6.qq.com'}:
            raise ValueError('Invalid Android metadata')
        if (version, url) in seen:
            continue
        seen.add((version, url))
        rows.append(dict(version=version, publish_date=record['publish_date'].strip(), url=url))
    return rows


def main():
    commit = api(f'repos/{ANDROID}/commits/main')['sha']
    content = api(f'repos/{ANDROID}/contents/version.json?ref={commit}')
    android = normalize_android(json.loads(base64.b64decode(content['content'])))
    releases = api(f'repos/{MACOS}/releases?per_page=100', paginate=True)
    macos = [parse_release(r) for r in releases if not r.get('draft')]
    macos.sort(key=lambda r: (r['published_at'] or '', r['tag']), reverse=True)
    if not android or not macos:
        raise ValueError('Empty upstream data; refusing to overwrite local index')
    if len({r['slug'] for r in macos}) != len(macos):
        raise ValueError('Duplicate macOS release identifiers')
    # Fetch and validate both sources before writing any data.
    files = {'versions.json': android, 'macos.json': macos,
             'source.json': dict(repository=f'https://github.com/{ANDROID}', commit=commit, file='version.json')}
    for filename, data in files.items():
        path = ROOT / 'data' / filename
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        temporary.replace(path)
    print(f'Synced {len(android)} Android packages and {len(macos)} macOS releases.')

if __name__ == '__main__':
    main()
