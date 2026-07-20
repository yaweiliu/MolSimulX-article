---
wp_post_id: 1373
id: T12
title: Markdown简明教程
wp_slug: markdown简明教程
series: 在线资源
tier: 技术文档
status: reviewed
topic: 写作
paywall: free
---
> **系列标签：** `技术文档` · `写作` · `Markdown` · `文档`

写模拟笔记、README、组会记录，如果每次都开 Word，改一个字就难 diff、难进 Git。**Markdown** 用纯文本打几个符号（`#`、`-`、`` ` ``）就能排成标题、列表、代码和公式——Jupyter 单元格、GitHub、Obsidian、本站教程都是这套格式。

本文讲**够用的核心语法**，并说明在 Jupyter、VSCode、Obsidian 里怎么写；最后推荐几款常用的 Markdown 软件，按场景选就行。

![markdown](../../images/articles/技术文档/T12-Markdown简明教程/web/T12-fig-markdown.webp)

---

## 一、为啥科研党值得学 Markdown？

| 场景 | 拿来干啥 |
|------|----------|
| **Jupyter Notebook** | 代码旁边写方法、参数、结论 |
| **Git 仓库** | `README.md` 写安装步骤、目录说明 |
| **Obsidian** | 个人知识库、文献与模拟笔记 |
| **GitHub / Gitee** | Issue、PR 描述 |
| **博客 / 静态站** | 很多站点由 Markdown 生成 HTML |

和 Word 比：**纯文本进 Git，改一行 diff 看得清**；和 LaTeX 比：**上手快**，记实验、写 README 足够。  
**正式投稿排版**仍用 [LaTeX与Overleaf简明教程](T14-LaTeX与Overleaf简明教程.md) 或期刊要求的 Word 模板——Markdown 负责「记下来、说清楚」，成稿再换格式。

---

## 二、基础语法

### 1. 标题

```markdown
# 一级标题
## 二级标题
### 三级标题
```

`#` 后面空一格。一篇文档通常只有一个一级标题（就像论文只有一个总标题）。

### 2. 强调

```markdown
**粗体**
*斜体*
~~删除线~~
`行内代码`
```

### 3. 列表

```markdown
- 无序项 A
- 无序项 B
  - 嵌套项

1. 第一步
2. 第二步
```

### 4. 链接与图片

```markdown
[显示文字](https://example.com)
[Git简明使用教程](T04-Git简明使用教程.md)

![图片说明](figure.png)
```

图片路径写**相对当前 `.md` 文件**或项目里的固定目录，别写本机绝对路径（换电脑就挂了）。

### 5. 引用与分隔线

```markdown
> 注意：模拟温度 300 K，步长 1 fs。

---
```

`>` 引用适合写提醒；`---` 单独一行是横线分隔。

### 6. 表格

Markdown 表格就是「竖线画格子」：第一行表头，第二行分隔线，下面一行一行填数据。

```markdown
| 参数 | 值 | 单位 |
|------|-----|------|
| 温度 | 300 | K |
| 压强 | 1   | atm |
| 步长 | 1   | fs |
```

**记住三件事：**

| 要点 | 说明 |
|------|------|
| 第二行不能省 | `\|------\|` 这行告诉渲染器「上面是表头」；少了容易整表变纯文本 |
| 每行列数要对齐 | 三列表就每行两个 `\|` 隔开三段；某一行列多了/少了，预览会歪 |
| 单元格里少用 `\|` | 竖线本身是分隔符，内容里真要写 `\|`，部分软件要转义，能避开就避开 |

**列对齐（可选）：** 分隔行里用冒号控制（部分编辑器支持）：

```markdown
| 左对齐 | 居中 | 右对齐 |
|:-------|:----:|-------:|
| a      | b    | 100    |
```

`:---` 左对齐，`:---:` 居中，`---:` 右对齐——数字列常右对齐好看。

**科研里常拿来记模拟参数：**

```markdown
| 项目 | 设置 |
|------|------|
| 力场 | TIP3P |
| 系综 | NPT |
| 温度 | 300 K |
| 压强 | 1 atm |
| 步长 | 1 fs |
| 总步数 | 1e6 |
| 随机种子 | 12345 |
```

**从 Excel 搬数据：** 在 Excel 里选好区域复制，贴到下面任一在线工具，一键生成 Markdown，再粘进 `.md` 或 Jupyter 单元格——比手敲竖线省事得多。

#### 在线生成表格（复制粘贴即用）

| 工具                   | 网址                                                                                     | 适合干啥                                                 |
| -------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| **Tables Generator** | [tablesgenerator.com/markdown_tables](https://www.tablesgenerator.com/markdown_tables) | 最常用：网页里点格子填数，或 **从 Excel / Google 表格粘贴**，导出 Markdown |
| **Table Convert**    | [tableconvert.com](https://tableconvert.com/)                                          | Excel、CSV、JSON 等 **互转** 成 Markdown 表格                |

**推荐流程（最省事）：**

1. 在 Excel 或记事本里先把行列整理好  
2. 打开 [Tables Generator → Markdown](https://www.tablesgenerator.com/markdown_tables)  
3. **File → Paste table data**（或直接 Ctrl+V 粘贴）  
4. 点 **Generate** → **Copy to clipboard**  
5. 粘进 VSCode、Jupyter Markdown 单元格或 Obsidian  

> **Tips：** VSCode 装 **Markdown All in One** 后，在已有表格上 `Ctrl/Cmd + Shift + P` → **Markdown All in One: Format table**，可自动对齐竖线，手改过的表也能排整齐。Typora、Mark Text 里也可用菜单 **插入表格**，不用记语法。

**Jupyter / Obsidian 注意：** 生成出来的表粘进去后先 **预览一眼**；极少数复杂合并单元格在线工具不支持，那种留在 Excel 或截图即可。

### 7. 代码块

````markdown
```python
import numpy as np
x = np.linspace(0, 10, 100)
```
````

语言名写 `python`、`bash`、`json` 等，预览时会有高亮。

---

## 三、数学公式（Jupyter / Obsidian / GitHub）

**行内公式：** `$E = mc^2$`

**独立公式块：**

```markdown
$$
\int_0^1 x^2 \, dx = \frac{1}{3}
$$
```

分子模拟里常写：

```markdown
径向分布函数 $g(r)$，配位数 $N(r)$。

$$
U(r) = 4\epsilon\left[\left(\frac{\sigma}{r}\right)^{12} - \left(\frac{\sigma}{r}\right)^{6}\right]
$$
```

| 环境 | 公式支持 |
|------|----------|
| JupyterLab | 默认支持（MathJax） |
| Obsidian | 设置里开启 |
| GitHub | README 里支持 |
| VSCode 预览 | 看扩展，一般够用 |

公式显示成源码、不渲染时，先查对应软件有没有开数学支持，再查 `$` 是否成对。

---

## 四、在 JupyterLab 里写

Markdown **单元格**就是「给这段代码贴便签」。类型切换：命令模式按 `M`（详见 [JupyterLab简明教程](T11-JupyterLab简明教程.md)）。

**记一次 NPT 参数示例：**

```markdown
## 体系
- 流体：TIP3P 水，1000 分子
- 盒子：40 Å 立方周期边界

## 模拟
- 系综：NPT，300 K，1 atm
- 步长：1 fs，总步数 1e6
```

`Shift + Enter` 跑完单元格，便签变成排版好的文字。

---

## 五、在 VSCode / Cursor 里写

MolSimulX 平台线里，`.md` 和 `.py` 一样在编辑器里改：

- 新建或打开 `.md` → 预览：`Ctrl/Cmd + Shift + V`（或右上角预览图标）  
- 推荐扩展：**Markdown All in One**（目录、列表快捷键、预览增强）  
- 项目根 `README.md`：写环境怎么装、目录啥意思、怎么复现  

和 Git 一起用：`.md` 跟代码同版本提交（见 [Git简明使用教程](T04-Git简明使用教程.md)）。

---

## 六、在 Obsidian 里写

[Obsidian](https://obsidian.md/) 是**本地优先**的 Markdown 笔记库——适合文献摘录、组会、模拟参数归档。本站教程库也可以用 Obsidian 当 Vault 维护（见 [Obsidian知识库搭建](T13-Obsidian知识库搭建.md)）。

### 1. 比标准 Markdown 多出来的

| 语法 | 干啥 |
|------|------|
| `[[笔记名]]` | 链到另一篇笔记（双向链接） |
| `[[笔记名\|显示文字]]` | 自定义链接上的字 |
| `![[图片.png]]` | 嵌入图片或附件 |
| `#标签` | 按主题归类 |
| `^block-id` | 块引用（进阶） |

### 2. 模拟笔记示例

```markdown
# 2026-06 水盒子 NPT 测试

相关平台：[[分子模拟工作平台搭建]]

## 参数
- 力场：[[TIP3P 笔记]]
- 分析脚本：`analysis/rdf.ipynb`

#分子动力学 #水模型
```

### 3. 公式与代码

和标准 Markdown 一样；编辑器里「严格换行」等按自己阅读习惯在设置里调。

---

## 七、常用 Markdown 软件怎么选

语法大同小异，**会标准 Markdown 就能换软件**。按「你主要在哪儿写」选：

### 1. 平台线里已经在用的（优先熟悉）

| 软件 | 适合干啥 | 说明 |
|------|----------|------|
| **VSCode / Cursor** | 项目 README、教程、跟代码放一起的文档 | 预览 + Git 一条龙；见第五节 |
| **JupyterLab** | Notebook 里代码旁的说明 | Markdown 单元格；见 [JupyterLab简明教程](T11-JupyterLab简明教程.md) |
| **Obsidian** | 个人知识库、多篇笔记互相关联 | 双链、`#标签`；见第六节、[Obsidian知识库搭建](T13-Obsidian知识库搭建.md) |

这三样覆盖 MolSimulX 大部分场景，**不必再装一堆编辑器**。

### 2. 单篇写作、所见即所得

| 软件 | 平台 | 特点 |
|------|------|------|
| **[Typora](https://typora.io/)** | Win / Mac / Linux | 边写边排版，公式、表格友好；现多为付费，单篇长文很舒服 |
| **[Mark Text](https://marktext.app/)** | Win / Mac / Linux | 开源、免费，风格接近 Typora，轻量 |
| **[MacDown](https://macdown.uranusjr.com/)** | 仅 Mac | 免费、小巧，分栏预览，Mac 用户随手记笔记 |

适合：组会讲稿、一次性的方法说明、不想看「源码」只想看效果时。

### 3. 在线协作、共享

| 软件 | 特点 |
|------|------|
| **[HackMD](https://hackmd.io/)** | 浏览器里写 Markdown，链接分享，适合小组共改一篇文档 |
| **[语雀](https://www.yuque.com/)** | 国内访问稳，支持 Markdown 编辑与团队知识库 |
| **GitHub / Gitee** | 仓库里直接改 `.md`，PR 审阅；适合开源项目说明 |

适合：和师兄师姐共写操作手册、课题组 Wiki；定稿后可导出或同步到 Git。

### 4. 怎么选（一张表）

| 你想… | 推荐 |
|--------|------|
| 跟代码、Notebook 放一起 | **VSCode / Cursor**、**JupyterLab** |
| 长期积累、笔记互相关联 | **Obsidian** |
| 写一篇好看的说明、少折腾 | **Typora** 或 **Mark Text** |
| 多人改同一份文档 | **语雀**、**HackMD** |
| 项目对外说明 | 仓库 **README.md**（GitHub / Gitee） |

> **Tips：** 先在一个软件里写熟语法，再换别的——格式 90% 通用；Obsidian 双链、语雀专有块等是「加分项」，不是入门必学。

---

## 八、科研场景写作习惯

1. **一篇一主题**：如「某次 Lammps NPT 参数记录」，别全堆在一个文件里  
2. **代码和文档放近**：Notebook 里写参数，或 `.md` 里写脚本路径  
3. **参数表格化**：温度、步长、力场、随机种子写清楚，半年后还能复现  
4. **跟 Git 一起走**：`.md` 和 `.ipynb` 同提交  
5. **大文件别往里塞**：轨迹、大二进制用路径链接，别贴进笔记  

---

## 九、语法速查

| 元素 | 语法 |
|------|------|
| 标题 | `#` `##` `###` |
| 粗体 / 斜体 | `**` / `*` |
| 列表 | `-` 或 `1.` |
| 链接 | `[text](url)` |
| 图片 | `![alt](path)` |
| 代码 | `` ` `` 或 ` ```lang ` |
| 公式 | `$...$` 或 `$$...$$` |
| 表格 | `\| col \| col \|` + 分隔行 `\|---\|`；Excel 可经 [Tables Generator](https://www.tablesgenerator.com/markdown_tables) 转 |
| Obsidian 双链 | `[[page]]` |

---

## 十、小结

1. Markdown = **纯文本 + 少量符号**，适合 Git、Notebook、知识库。  
2. Jupyter 记实验、README 记项目、Obsidian 串笔记——**语法相通**。  
3. 公式用 `$` / `$$`；Obsidian 再加 `[[双链]]`。  
4. 软件按场景选：**VSCode / Jupyter / Obsidian** 为主；单篇用 **Typora / Mark Text**；协作用 **语雀 / HackMD**。  
5. 正式论文排版另走 LaTeX 或 Word，Markdown 管「记清楚、可复现」。

---

## 学习路径

**前置阅读：**

- [JupyterLab简明教程](T11-JupyterLab简明教程.md) —— Notebook 里的 Markdown 单元格
- [VSCode与Cursor简明教程](T06-VSCode与Cursor简明教程.md) —— 编辑与预览 `.md`

**下一步：**

- [Obsidian知识库搭建](T13-Obsidian知识库搭建.md)
- [LaTeX与Overleaf简明教程](T14-LaTeX与Overleaf简明教程.md)
- [NumPy与Matplotlib简明教程](T21-NumPy与Matplotlib简明教程.md) —— 图注可写在 Markdown 单元格
