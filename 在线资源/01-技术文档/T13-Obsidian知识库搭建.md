---
wp_post_id: 1375
id: T13
title: Obsidian知识库搭建
wp_slug: obsidian知识库搭建
series: 在线资源
tier: 技术文档
status: reviewed
topic: 写作
paywall: vip
erphpdown_blocks: 1
---
> **系列标签：** `技术文档` · `写作` · `Obsidian` · `知识库`

文献看了就忘、模拟参数散在聊天记录里、组会想法没地方串——**Obsidian** 能把这些都收成**本地 Markdown 笔记**，用 `[[双向链接]]` 和图谱把「这篇论文 ↔ 这个力场 ↔ 那次 NPT」连起来。文件在你硬盘上，不依赖某家云笔记；和 Git、Jupyter 也能分工协作。

本文讲怎么装、怎么建库（Vault）、日常怎么记模拟日志。`.md` 语法请先过一遍 [Markdown简明教程](T12-Markdown简明教程.md)。

学完能带走：一套能直接复制的 Vault 目录、模拟日志该记哪些字段（力场、JOBID、轨迹路径）、以及把本站 `在线资源` 当本地知识库用 `[[双向链接]]` 读教程。只补 `.md` 写法看 [Markdown简明教程](T12-Markdown简明教程.md)；跑数出图还在 Jupyter，规范见 [Jupyter Notebook科研使用规范](T16-Jupyter Notebook科研使用规范.md)；成稿投稿走 [LaTeX与Overleaf简明教程](T14-LaTeX与Overleaf简明教程.md)。

| 你要… | 姊妹篇 |
|--------|--------|
| 学 Markdown 语法 | [Markdown简明教程](T12-Markdown简明教程.md) |
| Notebook 怎么写才可复现 | [Jupyter Notebook科研使用规范](T16-Jupyter Notebook科研使用规范.md) |
| 论文排版、参考文献 | [LaTeX与Overleaf简明教程](T14-LaTeX与Overleaf简明教程.md) |

![obsidian](../../images/articles/技术文档/T13-Obsidian知识库搭建/web/T13-hero-obsidian.webp)

---

[erphpdown]

## 一、Obsidian 适合干啥？

| 场景 | 举例 |
|------|------|
| **文献笔记** | 一篇论文一个文件，`[[经典全原子力场]]` 链到概念文 |
| **模拟日志** | 记 in 参数、JOBID、轨迹路径、当时为啥这么设 |
| **教程知识库** | 把整个 `在线资源` 当 Vault，本地双链读 K/T/E 教程 |
| **组会 / 灵感** | 快速记下待验证假设，以后链到具体项目 |

**不适合替代：** 跑 Python、交 SLURM 作业、正式论文排版——那些交给 Jupyter、集群、[LaTeX与Overleaf简明教程](T14-LaTeX与Overleaf简明教程.md)。

**和 Jupyter 分工：** Notebook 算数和出图；Obsidian 记「**为什么**用这个温度、力场、步长」。

---

## 二、安装

| 平台 | 方式 |
|------|------|
| **Mac** | [obsidian.md](https://obsidian.md) 下 `.dmg`；或 `brew install --cask obsidian` |
| **Windows** | 官网安装包 |
| **Linux** | AppImage / Snap / Flatpak（见官网） |

基础功能免费；官方同步、发布等服务可选付费，**用 Git 或网盘同步整个文件夹**也能多台电脑共用。

---

## 三、建知识库（Vault）

1. 打开 Obsidian → **Create new vault**（创建新库）  
2. 选一个**专题目录**，别把整个硬盘当库：

| 用途 | 文件夹示例 |
|------|------------|
| 个人科研笔记 | `~/Documents/MolSimulX笔记` |
| 阅读本站教程 | 选 `MolSimulX-article/在线资源` 或再上一级 |

> **Tips：** **Vault = 一个根文件夹**，里面的 `.md` 都会被索引。教程、笔记、附件分目录放，别和系统目录搅在一起。

### 用 MolSimulX 教程当 Vault

本地克隆或下载教程仓后，可直接打开：

```
MolSimulX-article/
└── 在线资源/
    ├── 00-知识文档/     # 概念：MD、力场、ML 等
    ├── 01-技术文档/     # 平台、集群、写作教程
    └── 02-实战案例/     # 技能教程与端到端案例
```

在 Obsidian 里能看到各篇之间的 `[[链接]]`；**知识文档**讲原理，**技术文档**讲操作——图谱里常从 `[[分子动力学模拟概述]]` 链到 `[[集群与SLURM简明教程]]`。栏目说明见 [知识文档栏目](../00-知识文档/README.md)。

---

## 四、界面与顺手操作

```
┌──────────┬─────────────────────┬──────────┐
│ 文件列表  │   当前笔记编辑区      │ 反向链接  │
│          │                     │ 大纲     │
│          │                     │ 标签     │
└──────────┴─────────────────────┴──────────┘
```

| 操作 | 干啥 |
|------|------|
| `Ctrl/Cmd + N` | 新建笔记 |
| `Ctrl/Cmd + O` | 快速打开某篇 |
| `Ctrl/Cmd + P` | 命令面板（啥都能搜） |
| 输入 `[[` | 插入链到另一篇笔记 |
| `#标签` | 给笔记打主题签 |
| 右侧边栏 | 看「谁链到本篇」 |

**图谱视图：** 命令面板 → **Graph view**，整张笔记关系网一眼扫过——适合整理力场、体系、项目之间的关联。

---

## 五、推荐设置（科研向）

**设置 → 编辑器：**

- **Strict line break**：按习惯开或关（一行到底要不要换行）  
- **默认编辑模式**：熟悉 Markdown 用「源码」；想要边写边看效果选 **Live Preview**  

**设置 → 文件与链接：**

- **新建链接格式**：相对路径（跟 Git 搬家不炸）  
- **附件目录**：如 `attachments/`，图片统一扔这里  

**设置 → 核心插件（自带，打开即可）：**

- **Templates**：笔记模板  
- **Daily notes**：每日实验流水账（可选）  
- **Outline**：按标题折叠大纲  

**公式：** 设置 → 编辑器 → 打开数学公式；写法见 [Markdown简明教程](T12-Markdown简明教程.md)。

---

## 六、模拟日志模板

在 Vault 里建 `templates/sim-log.md`：

```markdown
# {{title}}

日期：{{date}}
项目：[[项目名称]]

## 目的


## 模拟参数
| 项 | 值 |
|----|-----|
| 力场 | |
| 温度 | |
| 系综 | |

## 文件路径
- 输入：`lammps/in.npt`
- 轨迹：
- 集群 JOBID：

## 结果与下一步

#模拟日志
```

**设置 → Templates** → 模板文件夹指到 `templates/`；新建笔记时插入，省得每次重抄表头。

**和知识文档联动示例：**

```markdown
力场选用 TIP3P，概念见 [[经典全原子力场]]。
NPT 参数参考 [[分子动力学模拟概述]] 里的系综说明。
```

---

## 七、和 Git 一起用

Vault 就是普通文件夹，可以 `git init`：

```bash
cd ~/Documents/MolSimulX笔记
git init
```

`.gitignore` 示例：

```gitignore
.obsidian/workspace.json
.obsidian/cache
.trash/
```

`workspace.json` 记的是窗口布局，各人不同，常忽略；插件列表 `community-plugins.json` 团队要统一再提交。详见 [Git简明使用教程](T04-Git简明使用教程.md)。

---

## 八、社区插件（可选，初学可跳过）

**设置 → 社区插件** → 先关「安全模式」再浏览安装：

| 插件 | 干啥 |
|------|------|
| **Excalidraw** | 手绘示意图、流程图 |
| **Dataview** | 用查询汇总笔记（如列出所有 `#模拟日志`） |
| **Citations** | 接 BibTeX 文献库 |
| **Latex Suite** | 公式输入快一点 |

核心功能够记一年日志；插件按需加，别一上来装一堆。

---

## 九、和其他工具怎么分活

| 工具 | 更擅长 |
|------|--------|
| **Obsidian** | 长期文字、双链、概念与参数归档 |
| **JupyterLab** | 可执行代码、图表、轨迹分析 |
| **VSCode / Cursor** | 写 `.py`、调试、Remote SSH、Git |
| **LaTeX / Overleaf** | 投稿排版 |

一条常见链路：**Obsidian 写实验设计** → **Jupyter 跑分析** → **Obsidian 记结论和待办** → **LaTeX 写论文**。

---

## 十、常见问题

### 1. 公式不显示

设置里开数学渲染；检查 `$...$` 是否成对（见 [Markdown简明教程](T12-Markdown简明教程.md)）。

### 2. 图片路径乱了

用 `![[attachments/fig.png]]` 或相对路径；附件集中一个目录。

### 3. 和 VSCode 同时改同一文件

两边别同时开着未保存的同一篇；**代码以 VSCode 为主，笔记以 Obsidian 为主**。

### 4. 多台电脑同步

官方 Sync（付费）、**Git 推送**、或 iCloud / 网盘同步整个 Vault（注意冲突，别两边同时改同一篇）。

### 5. 打开教程 Vault 链接是红的

红色表示还没建对应文件名的笔记；链到本站 `.md` 时，文件名要和 `[[链接名]]` 一致，或用 `[[显示名|实际文件名]]`。

---

## 十一、小结

1. Obsidian = **本地文件夹** + Markdown + `[[双链]]` + 图谱。  
2. Vault 选专题目录；`在线资源` 可当教程库，**知识文档** 与 **技术文档** 分文件夹放。  
3. 用模板记模拟日志；`#标签` 和双链把项目、力场、文献串起来。  
4. 与 Git、Jupyter、LaTeX 分工，不替代代码和集群环境。

---

[/erphpdown]

## 学习路径

**前置阅读：**

- [Markdown简明教程](T12-Markdown简明教程.md)

**下一步：**

- [LaTeX与Overleaf简明教程](T14-LaTeX与Overleaf简明教程.md) —— 从笔记到论文
- [Git简明使用教程](T04-Git简明使用教程.md) —— 版本管理 Vault
