# MolSimulX-article

MolSimulX **在线文章源仓库**：Markdown 正文、配图（WebP）、写作规范与发布到 WordPress 的脚本。面向内容作者 / 站点维护者，不是对外读者文档。

读者视角的站内入口见 [在线资源/资源导航.md](在线资源/资源导航.md)。内部约定：[写作规范.md](写作规范.md) · [发布与上线.md](发布与上线.md) · [内容规划.md](内容规划.md)（**勿上传 WordPress**）。

---

## 仓库里有什么

```
MolSimulX-article/
├── 在线资源/                 # 对外主内容（知识 K / 技术 T / 实战 C）
│   ├── 00-知识文档/
│   ├── 01-技术文档/
│   ├── 02-实战案例/
│   └── 资源导航.md
├── 在线工具/ · 解决方案/     # 其它栏目源稿
├── images/                   # 配图：归档后 …/original|web/（原图默认不入库）
├── downloads/                # 附件包（如 myenv.yml）
├── tools/                    # 配图整理、Markdown → WP 发布
├── 写作规范.md · 发布与上线.md · 内容规划.md
└── .env.local.example        # WP 账号模板（复制为 .env.local）
```

编号习惯：`K##` 知识、`T##` 技术、`C##` 实战、`M##` 在线工具、`S##` 解决方案。正文互链用**完整文章标题**，不要写 `T01` 这类编号当锚文字。

---

## 5 分钟上手

### 1. 克隆

```bash
git clone git@github.com:yaweiliu/MolSimulX-article.git
cd MolSimulX-article
```

### 2. Conda 环境（发布 / 配图）

需要已安装 Miniconda / Anaconda（有 `conda` 命令）。本仓库发布工具使用名为 **`molsimulx`** 的环境：

```bash
# 若尚未创建
conda create -n molsimulx python=3.12 -y
conda activate molsimulx
pip install -r tools/requirements-publish.txt
```

之后每次开终端先：

```bash
conda activate molsimulx
```

（有 Mamba 时可用 `mamba create -n molsimulx python=3.12 -y` 创建，激活仍用 `conda activate`。）

### 3. 配置 WordPress（要发布时再做）

```bash
cp .env.local.example .env.local
# 编辑 .env.local：WP_SITE_URL、WP_USERNAME、WP_APP_PASSWORD、母版文章 ID
```

- 应用密码：WP 后台 → 用户 → 个人资料 → **应用密码**  
- `.env.local` **不要提交**  
- 非敏感项可看 `tools/publish.config.yaml`

### 4. 写文章（只改文、不发站）

1. 在对应目录新建或编辑 `T19-标题.md` 等文件。  
2. 文首 YAML 至少包含：`id`、`title`、`series`、`tier`、`status`、`topic`、`paywall`。  
3. 写作规范、导语厚度、互链规则 → 打开 [写作规范.md](写作规范.md)。  
4. 本地用 Obsidian / VS Code / Cursor 预览即可；不必先配 WP。

`status` 门禁（同步到 WP 时）：

| 本地 `status` | 能否跑发布脚本 |
|---------------|----------------|
| `draft` | 否（除非 `--force`） |
| `reviewed` | 是 → CREATE / UPDATE（有 `wp_post_id` 则更新） |

本地只有这两种状态；**不要**写 `published` / `revised`。是否已上线看 WordPress。

日常复制命令见 [发布与上线.md](发布与上线.md)；下文「发布详解」是完整说明。

---

## 常用命令

在仓库根目录、已 `conda activate molsimulx` 时执行。

### 配图

`sync_article_images.py`：按 md 引用找源图 → 归档 `…/original/` → 转 `…/web/*.webp`。常用：

```bash
python tools/sync_article_images.py T01 --rewrite-md --prune-sources
python tools/sync_article_images.py T01 --dry-run
```

| 参数 | 作用 |
|------|------|
| `T01` / `--id` / `--file` / `--pick` / `--all` | 选文章 |
| `--rewrite-md` | 回写 md 为 `web/*.webp` 相对路径 |
| `--prune-sources` | 删散落重复源图（保留 original/web） |
| `--keep-sources` | 保留散落源图 |
| `--dry-run` | 只报告不写入 |

约定：最终引用 `images/articles/.../web/*.webp`；`images/**/original/` **不进 Git**。详见 [images/README.md](images/README.md)、[发布与上线.md](发布与上线.md)。

### 发布到 WordPress

```bash
python tools/publish.py --list
python tools/publish.py T01 --dry-run
python tools/publish.py T01 --write-back-id
python tools/publish.py T02 T03 T04 --write-back-id
python tools/publish.py --sync --write-back-id     # 日常增量
python tools/publish.py --pick
```

默认写入 WP **draft**；确认无误后到后台点「发布」。加 `--publish` 才会直接上线（慎用）。

---

## 新文检查清单（最短版）

- [ ] YAML：`id` / `title` / `status: draft` / `paywall`  
- [ ] 导语有场景钩子；写清「讲什么 / 不讲什么 / 姊妹篇」  
- [ ] 互链用完整标题；路径相对当前目录正确  
- [ ] 封面 / 插图走 `sync_article_images`，导语下不要解说「上图是……」  
- [ ] 审完把 `status` 改为 `reviewed`，再 `publish.py`  
- [ ] 后台确认分类、VIP / 附件后点「发布」；本地保持 `reviewed`

---

<a id="发布详解"></a>

## 发布详解

> 从原 [发布与上线.md](发布与上线.md) 迁出的完整约定；日常发文请优先复制该文件里的命令。

### 状态工作流

```text
draft ──审完──► reviewed ── publish.py ──► WP（默认 draft，可 --publish）
                 ▲                              │
                 └──── 改稿后仍用 reviewed，再推 ──┘
```

| 阶段 | 本地 YAML | WordPress |
|------|-----------|-----------|
| 写作审阅 | `draft` | （无或旧版） |
| 可同步 | `reviewed` | 脚本写入 **draft**（或 `--publish`） |
| 正式上线 | 仍为 `reviewed` | 后台点「发布」或脚本已 `--publish` |
| 改稿再推 | 仍为 `reviewed` | UPDATE 同 `wp_post_id` |

有 `wp_post_id` 时脚本 **UPDATE**；没有则 **CREATE**。`--sync` 会挑：新 `reviewed`、正文相对上次推送有变、互链目标新近上线、以及引用方回填。

### 文首 YAML

新建请复制 [在线资源/_templates/新文章模板.md](在线资源/_templates/新文章模板.md)。

```yaml
---
id: T01
title: 分子模拟工作平台搭建
series: 在线资源
tier: 01-技术文档
status: draft          # 审完改为 reviewed
topic: 平台搭建
paywall: free
---
```

同步成功后可有（由 `--write-back-id` 写入）：

```yaml
wp_post_id: 1234
wp_slug: 分子模拟工作平台搭建
```

旧字段 `published_at` / `revised_at` / `revision_note` 可删；脚本会忽略它们对内容指纹的影响。

### paywall（四种，互斥）

| YAML | 站点展示名 | 适用 |
|------|------------|------|
| `free` | 免费 | 全文公开 |
| `vip` | VIP | 主体用 `[erphpdown]` 包全文 |
| `download-vip` | VIP下载 | 正文免费；资源包 VIP 免下 |
| `download-paid` | 付费下载 | 正文免费；资源包单独购，会员折扣 |

勿在 WP 整篇勾「VIP 可见」；门禁只放在 `erphpdown` 块内。00/01 默认 `free`（少数进阶 `vip`）；02 有资源包用 `download-vip` / `download-paid`。

### 站内互链

- 源稿只用相对路径 `.md`；**不要**写 WordPress URL。  
- 无 `wp_post_id` 的目标在线上显示为灰色「待发布」。  
- 目标首次写入 `wp_post_id` 后，用 `--sync` 回填引用方，或重推引用文。  
- 批量首发建议：被引文先发，或发完一轮后再 `--sync`。

### 母版 650 与配图

- 每次从 WP **实时读**母版 650 再注入正文；默认整篇重套母版（`--keep-layout` 则只换 HTML 块）。  
- `publish.py` 默认跑配图同步并清理散落源图；保留散落源图用 `--keep-image-sources`。  
- `images/**/original/` 不进 Git；线上用 `web/*.webp`。

### 配置文件

| 文件 | 用途 |
|------|------|
| `.env.local` | 站点 URL、账号、母版 ID（不进 git） |
| `tools/publish.config.yaml` | 分类映射、Kadence meta、是否用母版 |
| `tools/publish-cache.json` | 媒体 / slug / sync 指纹（自动生成） |

### 检查清单

- [ ] `status: reviewed`；YAML `id` / `paywall` 齐全  
- [ ] `--write-back-id` 后确认有 `wp_post_id`  
- [ ] WP 预览：母版、图片、erphpdown  
- [ ] 人工发布或已用 `--publish`  
- [ ] 改稿后仍 `reviewed`，`--sync` 或单篇重推  
- [ ] VIP 资格不因 UPDATE 丢失；勿删文新建换 post ID；勿写坏 `[erphpdown]`

### 栏目 → WP 分类

| YAML `series` + `tier` | WP |
|------------------------|-----|
| `在线资源` + `00-知识文档` / `01-技术文档` / `02-实战案例` | 在线资源 → 对应二级 |
| `在线工具` + `MDStudio` 等 | 在线工具 → 产品名 |
| `解决方案` | 解决方案 |

erphpdown 价格 / VIP 类型每篇在 WP 后台人工配置，脚本只保留短代码。

---

## 相关仓库（可选）

| 仓库 | 用途 |
|------|------|
| 本仓库 | 文章 Markdown + 配图源 |
| [MolSimulX-web](https://github.com/yaweiliu/MolSimulX-web)（若已开源） | 站点主题 / mu-plugins |
| 其它核心库 | 模拟引擎与 Web 工具，与本仓库独立 |

站点插件里的展示逻辑、会员门禁等在 **web** 侧；**本仓库只负责内容真源与发布脚本**。

---

## 需要深入时读哪份

| 问题 | 文档 |
|------|------|
| 文风、禁止套话、互链、YAML | [写作规范.md](写作规范.md) |
| 复制命令、快速部署 | [发布与上线.md](发布与上线.md) |
| status / paywall / 互链 / 母版细节 | 本文「发布详解」 |
| 编号总表、学习路径、待写 | [内容规划.md](内容规划.md) |
| 读者阅读路径 | [在线资源/资源导航.md](在线资源/资源导航.md) |

有问题可在 Issue 里说明文章编号（如 `T19`）与本地报错全文。
