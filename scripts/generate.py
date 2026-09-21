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
         notes, '## 按版本查找\n', '| 微信版本 | 来源记录发布日期 | 安装包数量 |', '| --- | --- | ---: |']
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
        write(ROOT / version / slug / 'README.md', detail)
    lines.extend(['', notes, '## 相邻已收录版本\n'])
    if i > 0:
        lines.append(f'- [较新版本：微信 {versions[i-1]}](../{versions[i-1]}/)')
    if i + 1 < len(versions):
        lines.append(f'- [较旧版本：微信 {versions[i+1]}](../{versions[i+1]}/)')
    lines.extend(['', f'数据来源：[原始版本记录]({source_url})。本页仅包含来源中实际存在的记录，不推测缺失版本。\n'])
    write(ROOT / version / 'README.md', '\n'.join(lines))
index.extend(['', '## 数据来源与维护\n',
              f'感谢 [DJB-Developer/wechat-android-history-versions]({source["repository"]}) 整理版本资料。当前数据固定于 [提交 {source["commit"][:7]}]({source_url})，仅提取版本、日期和下载链接；目录、说明和生成脚本为本仓库重新编写。\n',
              '数据文件为 [data/versions.json](./data/versions.json)。更新数据后运行：\n',
              '```bash\npython3 scripts/generate.py\n```\n',
              '每个版本都有独立目录、明确标题和安装包详情链接。目录结构方便浏览与引用；搜索引擎是否收录以及排名由搜索引擎决定。\n'])
write(ROOT / 'README.md', '\n'.join(index))
print(f'Generated {len(versions)} version pages and {len(rows)} package pages.')
