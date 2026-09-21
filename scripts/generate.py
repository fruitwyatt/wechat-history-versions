"""Generate the version and package index from attributed factual records."""
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / 'data/versions.json').read_text())
source = json.loads((ROOT / 'data/source.json').read_text())
source_url = f"{source['repository']}/blob/{source['commit']}/{source['file']}"
groups = defaultdict(list)
seen = set()
for row in rows:
    version, url = row['version'], row['url']
    assert re.fullmatch(r'\d+(?:\.\d+)+', version), version
    parsed = urlparse(url)
    assert parsed.scheme == 'https' and parsed.hostname in {'dldir1.qq.com', 'dldir1v6.qq.com'}, url
    filename = Path(parsed.path).name
    assert re.fullmatch(r'[A-Za-z0-9_.-]+\.apk', filename), filename
    key = (version, filename)
    assert key not in seen, key
    seen.add(key)
    groups[version].append(row)
versions = sorted(groups, key=lambda v: tuple(map(int, v.split('.'))), reverse=True)

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

notes = '下载地址指向腾讯 qq.com 域名。本站仅整理链接，不托管 APK，也不是微信官方网站。链接可用性、安装包签名和实际版本尚未逐一验证；发布日期来自来源记录。\n'
index = ['# 微信安卓历史版本下载索引 | WeChat Android APK\n',
         f'收录 **{len(versions)} 个版本、{len(rows)} 个安装包链接**，范围为微信 {versions[-1]} 至 {versions[0]}。点击版本查看对应安装包；同一版本的不同文件分别列出，便于区分构建。\n',
         notes, '[返回平台选择](../README.md)\n', '## 按版本查找\n', '| 微信版本 | 来源记录发布日期 | 安装包数量 |', '| --- | --- | ---: |']
for i, version in enumerate(versions):
    packages = groups[version]
    dates = '、'.join(sorted({p['publish_date'] for p in packages}))
    index.append(f'| [微信 {version} 安卓版](./{version}/) | {dates} | {len(packages)} |')
    lines = [f'# 微信 {version} 安卓版下载 | WeChat {version} Android APK\n',
             f'本页整理微信 **{version}** 的 **{len(packages)} 个安装包文件**。来源记录发布日期：**{dates}**。\n',
             '[返回全部历史版本](../README.md)\n', '## 安装包列表\n',
             '| 安装包文件与详情 | 下载地址 |', '| --- | --- |']
    for p in packages:
        url = p['url']
        filename = Path(urlparse(url).path).name
        slug = filename[:-4]
        lines.append(f'| [{filename}](./{slug}/) | [下载 APK]({url}) |')
        architecture = 'ARM64（根据文件名标记，未解析 APK 验证）' if '_arm64' in filename else '文件名未标明，尚未验证'
        detail = f'''# 微信 {version} 安卓安装包下载 — {filename}

[返回微信 {version} 版本列表](../README.md) · [全部历史版本](../../README.md)

## 安装包信息

| 字段 | 内容 |
| --- | --- |
| 微信版本（来源记录） | {version} |
| 平台 | Android |
| 发布日期（来源记录） | {p['publish_date']} |
| 完整文件名 | `{filename}` |
| 架构信息 | {architecture} |
| 下载域名 | `{urlparse(url).hostname}` |

## 下载微信 {version}

[下载 {filename}]({url})

完整下载地址：<{url}>

{notes}
## 来源与核验

版本、日期和下载地址参考 [DJB-Developer 的版本记录]({source_url})，本页按安装包重新整理。未提供未经验证的文件大小、SHA-256、更新日志或系统兼容性结论。下载失败时可返回版本列表查看其他文件。
'''
        write(ROOT / 'android' / version / slug / 'README.md', detail)
    lines.extend(['', notes, '## 相邻已收录版本\n'])
    if i > 0:
        lines.append(f'- [较新版本：微信 {versions[i-1]}](../{versions[i-1]}/)')
    if i + 1 < len(versions):
        lines.append(f'- [较旧版本：微信 {versions[i+1]}](../{versions[i+1]}/)')
    lines.extend(['', f'数据来源：[原始版本记录]({source_url})。本页仅包含来源中实际存在的记录，不推测缺失版本。\n'])
    write(ROOT / 'android' / version / 'README.md', '\n'.join(lines))
index.extend(['', '## 数据来源与维护\n',
              f'感谢 [DJB-Developer/wechat-android-history-versions]({source["repository"]}) 整理版本资料。当前数据固定于 [提交 {source["commit"][:7]}]({source_url})，仅提取版本、日期和下载链接；目录、说明和生成脚本为本仓库重新编写。\n',
              '数据文件为 [data/versions.json](../data/versions.json)。更新数据后运行：\n',
              '```bash\npython3 scripts/generate.py\n```\n',
              '每个版本都有独立目录、明确标题和安装包详情链接。目录结构方便浏览与引用；搜索引擎是否收录以及排名由搜索引擎决定。\n'])
write(ROOT / 'android' / 'README.md', '\n'.join(index))
print(f'Generated {len(versions)} version pages and {len(rows)} package pages.')

# macOS records are identified by the complete upstream release tag, including dates.
macos = json.loads((ROOT / 'data/macos.json').read_text())
mac_index = ['# 微信 Mac 历史版本下载 | WeChat for macOS\n',
             '[返回平台选择](../README.md)\n',
             f'收录 **{len(macos)} 条 Release 记录**。保留完整构建号或日期标签；仅包含来源仓库收录的官网发行版，不含 App Store 版本。\n',
             '| 版本与构建记录 | 上游 Release 发布时间（UTC） | DMG 附件数 |', '| --- | --- | ---: |']
for release in macos:
    tag = release['tag']
    dmgs = [a for a in release['assets'] if a['name'].lower().endswith('.dmg')]
    mac_index.append(f"| [微信 {tag} Mac 版](./{release['slug']}/) | {release['published_at']} | {len(dmgs)} |")
    lines = [f"# 微信 {release['version']} Mac 版下载 | {tag}\n",
             '[返回 Mac 全部版本](../README.md) · [选择其他平台](../../README.md)\n',
             f"- 来源版本号：`{release['version']}`",
             f'- 完整 Release 标签：`{tag}`',
             f"- 上游 Release 发布时间：{release['published_at']}（不是独立核实的微信发布日期）",
             f"- 上游标记为预发布：{'是' if release['prerelease'] else '否'}",
             f"- [查看原始 Release]({release['release_url']})\n",
             '## 历史安装包附件\n',
             '以下附件由来源仓库保存，优先用于查找对应历史构建。本项目不存储安装包，也未独立验证附件内容。\n']
    if not dmgs:
        lines.append('该 Release 未提供 DMG 附件，请查看原始 Release。\n')
    for asset in release['assets']:
        label = '下载 DMG' if asset in dmgs else '下载校验文件或其他附件'
        lines.extend([f"### {asset['name']}\n", f"[{label}：{asset['name']}]({asset['url']})\n",
                      f"文件大小（来源 API）：{asset['size']:,} 字节。\n"])
        if asset['sha256']:
            lines.append(f"该附件 SHA-256（GitHub API 提供）：\n\n```text\n{asset['sha256']}\n```\n")
    lines.extend(['## 腾讯官方下载地址\n',
                  '官方下载地址可能被替换为较新的构建，文件名中的简短版本号不保证对应本页完整构建号。\n'])
    lines.append(f"[腾讯官方下载链接]({release['official_url']})\n" if release['official_url'] else '来源未提供可识别的腾讯 HTTPS 下载地址。\n')
    lines.append('## 来源 Release 中的校验信息\n\n以下值由上游提供，未由本项目重新下载计算；仅展示格式完整的校验值。它们不保证适用于日后被替换的腾讯下载文件。\n')
    for key, title in [('sha256', 'SHA-256'), ('md5', 'MD5')]:
        value = release[key]
        lines.append(f'{title}：\n\n```text\n{value}\n```\n' if value else f'{title}：来源未提供完整有效值。\n')
    lines.append('日期后缀是上游用于区分旧记录的标识，不据此推测缺失的完整构建号、系统要求或芯片兼容性。\n')
    write(ROOT / 'macos' / release['slug'] / 'README.md', '\n'.join(lines))
mac_index.extend(['', '数据来自 [zsbai/wechat-versions Releases](https://github.com/zsbai/wechat-versions/releases)，感谢原作者维护。每个详情页保留原 Release 链接。\n'])
write(ROOT / 'macos' / 'README.md', '\n'.join(mac_index))
write(ROOT / 'README.md', f'''# 微信历史版本下载索引 | WeChat Android & macOS

按平台、版本和构建查找微信历史安装包下载链接。本仓库仅同步上游公开元数据，不下载或托管安装包，也不是微信官方网站。

| 平台 | 已收录记录 | 版本入口 |
| --- | --- | --- |
| Android 安卓 | {len(versions)} 个版本，{len(rows)} 个 APK 链接 | [微信安卓历史版本下载](./android/) |
| macOS 苹果电脑 | {len(macos)} 条 Release 记录 | [微信 Mac 历史版本下载](./macos/) |

## 如何查找

选择平台，再选择版本。同一安卓版本下的不同 APK 分别展示；Mac 保留完整构建号或日期标签，避免混淆不同发布记录。Mac 优先提供原仓库的历史附件，腾讯直链作为补充。

## 数据来源

- Android：[DJB-Developer/wechat-android-history-versions](https://github.com/DJB-Developer/wechat-android-history-versions)，固定来源提交见 [source.json](./data/source.json)。
- macOS：[zsbai/wechat-versions](https://github.com/zsbai/wechat-versions)，通过 GitHub Releases API 分页同步，并在各页面注明原 Release。仅覆盖来源收录的官网发行版，不含 App Store 版本。
- [数据字段与整理规则](./data/README.md)。校验值、日期和文件大小均标注来源，不代表本项目独立核验。

## 自动更新

GitHub Actions 每天定时同步两处来源，也可以在 Actions 的 **Sync version indexes** 中手动运行。仅当数据有变化时提交更新。同步或校验失败时不会推送变更。

本地需要 Python 3.10+ 和已登录的 GitHub CLI：

```bash
python3 scripts/sync.py
python3 scripts/generate.py
python3 -m unittest discover -s tests
python3 scripts/validate.py
```

旧版根目录的安卓入口保留迁移导航。目录和标题方便浏览与引用，不保证搜索引擎收录或排名。
''')
print(f'Generated {len(macos)} macOS release pages and platform navigation.')
