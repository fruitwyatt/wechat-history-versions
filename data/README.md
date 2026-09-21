# 数据字段与整理规则

## Android

[versions.json](./versions.json) 保存版本号、来源发布日期和腾讯下载链接。[source.json](./source.json) 固定每次同步所依据的上游提交。

移除字段首尾空白。版本号为空时从同条记录的名称提取，例如原记录中的 6.6 和 6.2。不从文件名猜测未知版本。

## macOS

[macos.json](./macos.json) 通过 zsbai/wechat-versions 的 GitHub Releases API 完整分页读取公开 Release。

- `tag` / `slug`：完整原始标签，也是目录名；保留 v 前缀、构建号和日期后缀。
- `version`：Release 的 DestVersion 字段，缺失时使用标签。
- `published_at`：GitHub Release 发布时间，不等同于微信官方发布日期。
- `official_url`：上游 DownloadFrom 字段中的腾讯 HTTPS 链接；可能被上游替换内容。
- `sha256` / `md5`：Release 正文中的完整校验值，空值或长度不符时记为 null，不跨行读取。
- `assets`：Release 附件名称、下载地址、字节数与 GitHub API 提供的 SHA-256。每个附件的摘要单独保存，校验文件本身的摘要不会当作 DMG 摘要。
- `prerelease`：保留上游预发布标记，页面明确展示。

不同日期标签可能具有相同 DestVersion，不能仅按版本号去重。所有下载链接和校验值来自上游，未由本项目独立下载核验。仅同步事实字段，不复制上游抓包脚本或 Release 正文。

## 更新规则

运行 `python3 scripts/sync.py` 获取两处来源，全部解析成功后才写入数据；随后生成并校验页面。自动流程中任一步失败均不会提交或推送。元数据不含每次运行时间，未变更的数据不会导致无意义提交。
