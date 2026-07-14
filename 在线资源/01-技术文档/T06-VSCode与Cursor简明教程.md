---
wp_post_id: 1334
id: T06
title: VSCode与Cursor简明教程
wp_slug: vscode与cursor简明教程
series: 在线资源
tier: 技术文档
status: reviewed
topic: VSCode
paywall: free
---
> **系列标签：** `技术文档` · `VSCode` · `Cursor` · `编辑器`

做分子模拟，脚本、Notebook、LAMMPS 输入文件总要有个地方写。**VSCode**（Visual Studio Code）是微软出品的免费编辑器，轻量、插件多，科研圈用得最广。**Cursor** 在 VSCode 基础上加了 AI 辅助写代码，界面和快捷键几乎一样，扩展也大多通用。

本文介绍 VSCode / Cursor 的安装、界面、常用扩展，以及与 Conda、Jupyter、Git 的配合。Mac、Ubuntu、Windows（WSL）均可按文中步骤操作。各专题细节见 [Git简明使用教程](T04-Git简明使用教程.md)、[Conda与Mamba简明教程](T05-Conda与Mamba简明教程.md)、[JupyterLab简明教程](T11-JupyterLab简明教程.md)，完整平台见 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)。

![cursor_or_vscode](../../images/articles/技术文档/T06-VSCode与Cursor简明教程/web/T06-hero-cursor_or_vscode.webp)

---

## 一、VSCode 与 Cursor 是什么关系？

可以把编辑器想成一间 **「代码工作室」**：**VSCode** 是标准版，**Cursor** 是同一间工作室里多了一位 AI 助手——桌椅摆放（界面）、工具箱（扩展）几乎一样，会用一个基本就会另一个。

| 对比项 | VSCode | Cursor |
|--------|--------|--------|
| **定位** | 通用代码编辑器 | 基于 VSCode 的 AI 编辑器 |
| **费用** | 完全免费 | 免费额度 + 付费订阅（以官网为准） |
| **界面与快捷键** | 基准 | 与 VSCode 基本相同 |
| **扩展** | VS Code Marketplace | 兼容绝大多数 VSCode 扩展 |
| **AI 能力** | 需自行装 Copilot 等扩展 | 内置 Chat、Agent、Tab 补全 |
| **适用场景** | 稳定、不依赖 AI 的纯编辑 | 希望 AI 帮忙写脚本、改 Notebook、查错 |

**怎么选？**

- 日常分子模拟开发：**两者任选其一**，配置方法几乎一样。
- 已熟悉 VSCode：换 Cursor 几乎零成本，多出来的主要是 AI 侧栏。
- 下文未特别说明时，**操作对两者通用**；Cursor 独有功能在第十节单独标出。

---

## 二、安装

### 1. VSCode

| 平台 | 方式 |
|------|------|
| **Mac** | [官网下载](https://code.visualstudio.com/) `.dmg`，拖入应用程序；或 `brew install --cask visual-studio-code` |
| **Ubuntu / Linux** | 官网下载 `.deb` / `.rpm`，或用 Snap：`sudo snap install code --classic` |
| **Windows** | 官网下载安装包；建议先完成 [WSL2安装与配置](T02-WSL2安装与配置.md) |

安装后终端可用 `code` 命令打开当前目录（安装时可选「添加到 PATH」；Mac 若提示找不到命令，打开命令面板——`Cmd + Shift + P`——执行 **Shell Command: Install 'code' command in PATH**）。

### 2. Cursor

1. 打开 [https://cursor.com](https://cursor.com) 下载对应系统安装包  
2. 按向导安装，首次启动可登录账号（使用 AI 功能时需要）  
3. 若从 VSCode 迁移：首次启动可**一键导入** VSCode 的设置、扩展和快捷键

### 3. 打开项目文件夹

分子模拟项目往往有脚本、轨迹、输入文件多个目录——**用「打开文件夹」而不是单开某个文件**，Git、搜索、相对路径读数据才都正常。

```bash
cd /path/to/your/project
code .      # VSCode
cursor .    # Cursor
```

或菜单 **File → Open Folder**，选择项目根目录。

---

## 三、界面一览

用 **File → Open Folder** 打开项目后，窗口大致分五块。下图以 VSCode 打开分子动力学脚本为例；**Cursor 布局相同**，右侧或侧边可能多出 AI 对话面板。

![vscode-MD](../../images/articles/技术文档/T06-VSCode与Cursor简明教程/web/T06-fig-vscode-MD.webp)

| 序号 | 区域 | 含义 | 分子模拟里常用来 |
|:----:|------|----------|------------------|
| **①** | **活动栏**（最左竖条） | 功能切换菜单 | 点 📁 看文件、点 Git 看改动、点 🧩 装扩展 |
| **②** | **侧栏** | 当前功能的详情面板 | 浏览项目目录、搜索代码、管理扩展 |
| **③** | **编辑区** | 写代码的「主桌面」 | 改 `.py`、`.ipynb`、LAMMPS 输入、Markdown 笔记 |
| **④** | **面板**（底部） | 终端和报错列表 | `conda activate myenv`、`python script.py`、看报错 |
| **⑤** | **状态栏**（最底一条） | 当前状态速览 | 看 Git 分支、**Python 环境是不是 myenv**、行号编码 |

> **Cursor 用户：** 除上述五块外，常见还有右侧 **Chat**（`Cmd/Ctrl + L`）或 **Agent**（`Cmd/Ctrl + I`）面板；文件树、终端、解释器选择与 VSCode 一致。

**三个建议先点熟的地方：**

1. **左侧 📁（资源管理器）** — 找脚本和轨迹目录  
2. **底部终端** — 快捷键 `` Ctrl/Cmd + ` ``，激活 Conda、跑命令  
3. **状态栏右下角 Python 版本** — 一眼确认是不是 `myenv`，不对就点进去换解释器（见第六节）


---

## 四、必装与推荐扩展

扩展就像给工作室加工具：装好一次，以后写代码、跑 Notebook、连集群都省事。打开侧栏 **扩展**（`Ctrl/Cmd + Shift + X`），搜名字安装即可。

### 分子模拟 / Python 开发必备

| 扩展名 | 含义 |
|--------|----------|
| **Python** | 语法高亮、补全、调试，还能认出 Conda 环境 |
| **Jupyter** | 在编辑器里直接打开、运行 `.ipynb` |
| **Pylance** | 通常随 Python 扩展装上，提供更聪明的代码提示 |

### 远程与协作

| 扩展名 | 含义 |
|--------|----------|
| **Remote - SSH** | 连 Linux 集群或服务器，远程文件当本地一样编辑 |
| **Remote - WSL** | Windows 用户连 WSL 里的 Linux 环境（见 [WSL2安装与配置](T02-WSL2安装与配置.md)） |

### 提升效率（可选）

| 扩展名 | 含义 |
|--------|----------|
| **Markdown All in One** | 写笔记、预览 Markdown 更方便 |
| **GitLens** | 看每一行代码是谁、什么时候改的 |
| **YAML** | 编辑 `environment.yml` 等配置文件 |

> **Tips：** Cursor 用户同样通过扩展市场安装；VSCode 的扩展名在 Cursor 里一般能直接搜到。Windows 用户连 WSL 或集群时，优先在 **WSL 内**装编辑器并配扩展，和 Linux 教程一致。

---

## 五、集成终端

菜单 **Terminal → New Terminal**，或 `` Ctrl/Cmd + ` ``。终端就是编辑器底部的「命令行窗口」——和 Mac 终端、WSL 里敲命令是一回事，装好的 Conda、Git 都在这里用。

### 1. 切换 Shell

终端右上角下拉 → 选择 **zsh**、**bash**、**Git Bash** 或 **WSL**。

| 系统 | 推荐 |
|------|------|
| Mac / Ubuntu | 默认 zsh 或 bash |
| Windows | **WSL (Ubuntu)** 或 Git Bash；纯 PowerShell 和部分科学计算工具不太合拍 |

### 2. 与 Conda 配合

终端里和外面用法一样，先激活环境再跑：

```bash
conda activate myenv
python script.py
jupyter lab
```

若新开终端提示找不到 `conda`，检查是否已运行 `conda init`（见 [Conda与Mamba简明教程](T05-Conda与Mamba简明教程.md)）。

### 3. 多终端

点击终端面板 **+** 可开多个标签——例如一个跑着 `python analyze.py`，另一个里 `git status`，互不干扰。

---

## 六、Python 与 Conda 环境

常见坑：**终端里 `conda activate myenv` 对了，编辑器还在用系统 Python**——运行就报 `ModuleNotFoundError`，或者 Notebook 和脚本用的不是同一套包。

### 1. 选择解释器

`Ctrl/Cmd + Shift + P` → **Python: Select Interpreter** → 选目标 Conda 环境，例如 `Python 3.12.x ('myenv')`。

路径通常类似：

```
~/miniconda3/envs/myenv/bin/python    # Mac / Linux
```

选对后，运行 `.py`、调试和 Jupyter Kernel 才会用对环境。状态栏右下角应显示 `myenv`（或你建的环境名）。

### 2. 运行 Python 脚本

- 打开 `.py` 文件 → 右上角 ▶ **Run Python File**
- 或右键 → **Run Python File in Terminal**
- 调试：左侧 **运行和调试** → 创建 `launch.json`（初学可先用手动运行，够日常分析用）

### 3. 项目级固定环境（可选）

在项目根目录建 `.vscode/settings.json`，团队共享时大家打开项目就自动认对环境：

```json
{
  "python.defaultInterpreterPath": "~/miniconda3/envs/myenv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

路径按本机实际修改（Windows WSL 内路径与 Linux 相同）。

---

## 七、Jupyter Notebook（.ipynb）

不必单独开浏览器，`.ipynb` 可以直接在编辑器里写、边跑边看结果——和 JupyterLab 用的是同一种文件格式，两边都能打开。操作细节见 [JupyterLab简明教程](T11-JupyterLab简明教程.md)。

### 快速步骤

1. 安装 **Jupyter** 扩展  
2. 打开 `.ipynb` 文件  
3. 右上角 **Select Kernel** → 选 `Python (myenv)`（和第六节解释器保持一致）  
4. 单元格旁 ▶ 或 `Shift + Enter` 运行  

### 常用操作

| 你想做的事 | 方式 |
|-----------|------|
| 插入单元格 | 单元格上方 `+ Code` / `+ Markdown` |
| 切换 Markdown | 单元格左上角下拉 |
| 清空输出 | 命令面板 → **Notebook: Clear All Outputs** |
| 导出为脚本 | 命令面板 → **Notebook: Export to...** |

---

## 八、Git 版本控制

左侧 **源代码管理** 图标（`Ctrl/Cmd + Shift + G`）就是图形化 Git 面板——暂存、提交、推送、拉取、切分支、看 diff，不想记命令时日常够用。可以把 Git 想成项目的「时光机」（见 [Git简明使用教程](T04-Git简明使用教程.md)）。

详细图文步骤见 [Git简明使用教程](T04-Git简明使用教程.md) 第八节「在 VSCode / Cursor 中使用 Git」。

**科研小习惯：**

- 用 `.gitignore` 排除大轨迹（`.dcd`、`.xtc` 等）、`__pycache__`、`.ipynb_checkpoints`
- 提交 Notebook 前清空无关输出，避免 diff 里全是图片和数字噪音

---

## 九、远程开发：连接集群

算大体系往往在学校集群上跑。**Remote - SSH** 让你在本机编辑器里直接操作远程文件和终端——界面还是第三节那套，只是文件和命令在集群上执行，不用来回 `scp` 代码。

**完整步骤**（SSH 配置、解释器、Notebook、登录节点 vs 计算节点、排错）见专题教程：

👉 **[VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md)**

速览：

1. 安装扩展 **Remote - SSH**、**Python**、**Jupyter**
2. 配置 `~/.ssh/config` 别名 → **Connect to Host**（见 [SSH密钥与config配置简明教程](T08-SSH密钥与config配置简明教程.md)）
3. **Open Folder** 打开 `~/project` → 终端 `conda activate myenv` → 选远程解释器
4. **别在登录节点**长时间跑重计算；交作业用 SLURM（见专题教程第七节与 [集群与SLURM简明教程](T10-集群与SLURM简明教程.md)）

> **Cursor：** 流程与 VSCode 相同；AI 功能对远程文件的支持以当前版本为准。

---

## 十、Cursor 的 AI 功能（简明）

以下为 Cursor 相对 VSCode 的主要增量；VSCode 用户可装 GitHub Copilot 等扩展获得类似能力。

> **重要：** AI 改过的代码同样会出现在 Git 面板里，**提交前务必逐文件 diff 审查**——尤其注意单位、文件路径、力场参数这类「看起来对」的细节。

### 1. Chat（对话）

侧栏或 `Ctrl/Cmd + L` 打开 AI 对话，可：

- 解释报错信息  
- 问 NumPy、MDAnalysis 等库怎么用  
- 根据自然语言生成代码片段  

**建议：** 涉及具体项目时，用 `@` 引用文件或文件夹，回答更贴你的代码上下文。

### 2. Agent / Composer（代理编辑）

`Ctrl/Cmd + I` 或 Agent 面板：描述需求，AI 可跨文件改代码。

**科研场景示例：**

- 「把这个 Notebook 里的轨迹读取改成 MDAnalysis」  
- 「给这个 LAMMPS 后处理脚本加上 RMSD 计算」  

**注意：**

- 大改动先 `git switch -c experiment/xxx` 开分支，不满意随时切回（见 [Git简明使用教程](T04-Git简明使用教程.md)）

### 3. Tab 补全

输入时出现灰色预测，按 `Tab` 接受——写重复性代码、记 API 名字时省事。

### 4. 使用原则

| 建议 | 原因 |
|------|------|
| 先自己跑通最小例子，再让 AI 扩展 | 避免不懂就复制大段代码 |
| 核对单位、边界条件、文件路径 | AI 可能语法对、物理/化学细节错 |
| 敏感数据不上传云端 | 按课题组与 Cursor 隐私政策谨慎使用 |

---

## 十一、常用快捷键

**命令面板**是编辑器里的「搜功能」入口：记不住菜单位置时，打开它、输入关键字即可。

打开方式：

- Windows / Linux：`Ctrl + Shift + P`
- Mac：`Cmd + Shift + P`
- 或菜单：**查看 (View) → 命令面板 (Command Palette)**（Cursor 同）

打开后顶部会出现输入框，直接打字搜索（如 `Python: Select Interpreter`、`Shell Command: Install`）。记不住别的快捷键也没关系——命令面板能搜到几乎所有功能。下面再记几个高频项：

| 功能 | Windows / Linux | Mac |
|------|-----------------|-----|
| 命令面板 | `Ctrl + Shift + P` | `Cmd + Shift + P` |
| 快速打开文件 | `Ctrl + P` | `Cmd + P` |
| 全局搜索 | `Ctrl + Shift + F` | `Cmd + Shift + F` |
| 保存 | `Ctrl + S` | `Cmd + S` |
| 格式化文档 | `Shift + Alt + F` | `Shift + Option + F` |
| 切换终端 | `` Ctrl + ` `` | `` Control + ` `` |
| 拆分编辑器 | `Ctrl + \` | `Cmd + \` |
| 跳转到定义 | `F12` | `F12` |
| 重命名符号 | `F2` | `F2` |
| 多光标 | `Alt + Click` | `Option + Click` |
| Cursor AI 对话 | `Ctrl + L` | `Cmd + L` |
| Cursor Agent | `Ctrl + I` | `Cmd + I` |

---

## 十二、工作区与配置文件

项目根目录下几个「小配置文件」，管的是这个项目在编辑器里怎么表现：

| 文件 / 目录 | 含义 |
|-------------|----------|
| `.vscode/settings.json` | 项目级设置：用哪个 Python、缩进几格等 |
| `.vscode/launch.json` | 调试配置（按 F5 跑脚本时用） |
| `.gitignore` | 告诉 Git 哪些文件别纳入版本（轨迹、缓存等） |
| `.cursorignore` | 告诉 Cursor AI 别索引哪些大文件（轨迹目录等） |

`.cursorignore` 语法和 `.gitignore` 一样，可避免 AI 去读几百 MB 的 `.dcd` 拖慢响应：

```gitignore
*.dcd
*.xtc
*.lammpstrj
data/
```

---

## 十三、常见问题

### 1. 找不到 Conda 环境

- 命令面板 → **Python: Select Interpreter** → **Enter interpreter path** 手动填路径  
- 或先在终端 `conda activate myenv`，再选编辑器「推荐」的解释器

### 2. Jupyter Kernel 列表为空

多半是还没把环境注册给 Jupyter：

```bash
conda activate myenv
python -m ipykernel install --user --name myenv --display-name "Python (myenv)"
```

重启编辑器后重选 Kernel。

### 3. Remote SSH 连不上

- 终端先测：`ssh cluster`（别名以你的 `config` 为准）  
- 检查 `~/.ssh/config`、密钥权限（`chmod 600`）；排错见 [SSH密钥与config配置简明教程](T08-SSH密钥与config配置简明教程.md)  
- 校园网 / VPN 是否必须先连上

### 4. 扩展在 Cursor 里不工作

看扩展页是否标了「不兼容」；可试旧版本或找替代扩展。

### 5. 保存时自动格式化乱了科学计数法

设置里搜 `format on save`，可暂时关掉，或调整 Black / autopep8 规则。

### 6. 中文路径或空格路径

项目路径尽量**英文、无空格**，部分模拟软件和脚本对路径挑剔。

---

## 十四、推荐工作流（MolSimulX）

和 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md) 里「典型一天」对应，在编辑器里可以这样串起来：

```
1. cursor . / code .          打开项目文件夹
2. conda activate myenv        终端激活环境
3. 选择 Python 解释器 / Notebook Kernel
4. 编辑 .py 或 .ipynb，终端或单元格运行
5. 源代码管理面板 git commit / push
6. 算力不够时 SSH 连集群，远程继续同一套界面
```

各工具分工（别混为一谈）：

| 工具 | 主要负责 |
|------|----------|
| **VSCode / Cursor** | 编辑、运行、调试、远程、AI 辅助 |
| **Conda / Mamba** | Python 环境与装包（「Python 小房间」） |
| **JupyterLab** | 浏览器里交互分析（与编辑器二选一或混用） |
| **Git** | 版本与协作（项目的「时光机」） |

---

## 十五、推荐学习资源

- [VSCode 官方文档](https://code.visualstudio.com/docs)
- [VSCode Python 教程](https://code.visualstudio.com/docs/python/python-tutorial)
- [Remote SSH 官方说明](https://code.visualstudio.com/docs/remote/ssh)
- [Cursor 文档](https://docs.cursor.com/)
- 本站：[Git简明使用教程](T04-Git简明使用教程.md) · [Conda与Mamba简明教程](T05-Conda与Mamba简明教程.md) · [JupyterLab简明教程](T11-JupyterLab简明教程.md) · [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)

---

## 十六、小结

1. **VSCode** 是主力编辑器，**Cursor** 在其上加了 AI，配置与扩展大体通用。  
2. **必装扩展**：Python、Jupyter；要连集群再加 Remote - SSH。  
3. **日常三板斧**：打开文件夹 → `conda activate` → 选对解释器 / Kernel。  
4. **远程**：Remote SSH 编辑集群文件；重计算交 SLURM，别占登录节点。  
5. **Cursor 用户**：AI 改动纳入 Git 审查；大轨迹用 `.cursorignore` 排除。

掌握以上内容，就具备了 MolSimulX 推荐的本地与远程开发能力。连不上环境、Kernel 为空、SSH 失败时，把终端或输出面板的**完整报错**复制去搜，往往能快速定位问题；各专题细节请继续阅读本站配套教程。

---

## 学习路径

**前置阅读：**

- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)
- [Conda与Mamba简明教程](T05-Conda与Mamba简明教程.md)
- [Git简明使用教程](T04-Git简明使用教程.md)

**下一步：**

- [JupyterLab简明教程](T11-JupyterLab简明教程.md)
- [VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md)
- [集群与SLURM简明教程](T10-集群与SLURM简明教程.md)
- [NumPy与Matplotlib简明教程](C01-NumPy与Matplotlib简明教程.md)
