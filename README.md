# 微信历史版本下载索引 | WeChat Android & macOS

按平台、版本和构建查找微信历史安装包下载链接。本仓库仅同步上游公开元数据，不下载或托管安装包，也不是微信官方网站。

| 平台 | 已收录记录 | 版本入口 |
| --- | --- | --- |
| Android 安卓 | 133 个版本，172 个 APK 链接 | [微信安卓历史版本下载](./android/) |
| macOS 苹果电脑 | 111 条 Release 记录 | [微信 Mac 历史版本下载](./macos/) |

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
