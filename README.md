# MolSimulX-article

MolSimulX **在线文章源仓库**：Markdown 正文、配图（WebP）、写作规范与发布到 WordPress 的脚本。面向内容作者 / 站点维护者，不是对外读者文档。

读者视角的站内入口见 [在线资源/资源导航.md](在线资源/资源导航.md)。内部约定入口：[内容写作与发布手册.md](内容写作与发布手册.md)（拆为写作 / 发布 / 规划三份；**勿上传 WordPress**）。

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
├── 内容写作与发布手册.md      # 入口索引
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
| `reviewed` | 是 → 新建 WP 草稿 |
| `revised` | 是 → 更新已有 WP 草稿（需 `wp_post_id`） |
| `published` | 否（本地标记已上线） |

---

## 常用命令

在仓库根目录、已 `conda activate molsimulx` 时执行。

### 配图

```bash
# 按文章引用归档 + 转 WebP + 回写 md 路径
python tools/sync_article_images.py --id T01 --rewrite-md

# 与发布一致：清理散落重复源图（original/ 仍保留在本地）
python tools/sync_article_images.py --id T01 --rewrite-md --prune-sources

# 仅预览
python tools/sync_article_images.py --id T01 --dry-run
```

约定：Markdown 最终引用 `images/articles/.../web/*.webp`；`images/**/original/` **不进 Git**（见 `.gitignore`）。细节见 [images/README.md](images/README.md)。

### 发布到 WordPress

```bash
python tools/publish.py --list
python tools/publish.py T01 --dry-run              # 只看转换结果，不上传
python tools/publish.py T01 --write-back-id        # 同步为 WP 草稿，并回写 wp_post_id
python tools/publish.py T02 T03 T04 --write-back-id
python tools/publish.py --pick                     # 交互选篇
```

默认写入 WP **draft**；确认无误后到后台点「发布」。加 `--publish` 才会直接上线（慎用）。更多参数与状态机见手册 **二、发布与上线**。

---

## 新文检查清单（最短版）

- [ ] YAML：`id` / `title` / `status: draft` / `paywall`  
- [ ] 导语有场景钩子；写清「讲什么 / 不讲什么 / 姊妹篇」  
- [ ] 互链用完整标题；路径相对当前目录正确  
- [ ] 封面 / 插图走 `sync_article_images`，导语下不要解说「上图是……」  
- [ ] 审完把 `status` 改为 `reviewed`（或已上线改 `revised`）再 `publish.py`  
- [ ] 后台确认分类、VIP / 附件后，本地再标 `published`

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
| `publish.py`、配图、status、paywall | [发布与上线.md](发布与上线.md) |
| 编号总表、学习路径、待写；工具 / 实战 / ML 选题 | [内容规划.md](内容规划.md) |
| 读者阅读路径 | [在线资源/资源导航.md](在线资源/资源导航.md) |
| 三份文档入口 | [内容写作与发布手册.md](内容写作与发布手册.md) |

有问题可在 Issue 里说明文章编号（如 `T19`）与本地报错全文。
