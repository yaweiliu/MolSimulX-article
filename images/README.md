# 网站图片资源

本地源图可先**随意放置**（`images/`、`images/inbox/` 等），由脚本按文章引用自动归档并转 WebP。

## 目录结构（归档后）

```
images/
├── inbox/                    # 可选：临时丢图，整理脚本会 move 到对应文章
├── site/                     # 网站页面（首页、品牌、固定页）
│   ├── brand/original|web/
│   └── home/original|web/
└── articles/                 # 教程配图（脚本自动生成）
    └── {层级}/{文章slug}/original|web/
```

## 命名

- `hero-` 文首主图 / 首页大图
- `fig-` 正文插图
- `screenshot-` 软件截图
- `diagram-` 示意图

## 封面显示（站点）

- 导语下**不要**写「上图是……」类封面解说；若需说明，放进正文相关小节。
- 发布时正文**第一张图**视为封面；封面与正文插图均为 CSS `max-height: 420px`，比例自由（`object-fit: contain`，不裁切）。
- 源图最长边仍由转 WebP 流程限制为 ≤1920；**不必**统一宽高比。
- 后续插图只限制 `max-width: 100%`，不限高。

## 工作流

```bash
conda activate molsimulx

# 1. 把图放进 images/ 或 images/inbox/，在 md 里用任意相对路径引用（或先写占位路径）
# 2. 按文章引用整理目录 + 转 WebP + 可选回写 md 路径
python tools/sync_article_images.py --file 在线资源/01-技术文档/分子模拟工作平台搭建.md --rewrite-md

# 与发布一致：整理后删除 images/ 散落重复源图（original/ 保留）
python tools/sync_article_images.py --id T01 --rewrite-md --prune-sources

# 处理全部教程
python tools/sync_article_images.py --all --rewrite-md

# 仅预览
python tools/sync_article_images.py --all --dry-run

# 3. 若需全库重跑 WebP（已归档 original/ 目录；不删原图）
python tools/optimize_images_for_web.py
```

**发布时（`publish.py`）** 默认等同 `--prune-sources`：WebP 成功后删除 `images/` 根目录等**散落重复源图**；**`articles/.../original/` 归档原图始终保留**。若要连散落源图也不删：`publish.py T01 --keep-image-sources`。

文章 Markdown 最终引用 `web/` 下的 WebP；上传 WordPress 时使用媒体库 URL。

**Git：** `images/**/original/` 已写入仓库根 `.gitignore`，原图只留本机；建议提交 `web/*.webp`（及 `images/README.md`）。若曾误提交原图，用 `git rm -r --cached images/**/original` 后提交即可。
