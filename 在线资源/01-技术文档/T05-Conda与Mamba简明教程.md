---
wp_post_id: 1331
id: T05
title: Conda与Mamba简明教程
wp_slug: conda与mamba简明教程
series: 在线资源
tier: 技术文档
status: reviewed
topic: Conda
paywall: free
---
> **系列标签：** `技术文档` · `Conda` · `Python环境` · `myenv`

在 Python 科研里，项目 A 要 NumPy 1.x，项目 B 要 NumPy 2.x——全塞进系统自带的 Python，很容易「装一个坏一个」。**Conda** 和 **Mamba** 就是帮你给每个项目单独隔一间 **「Python 小房间」**（虚拟环境），互不打架。

本文讲 Conda / Mamba 怎么装、怎么建环境、怎么装包。分子模拟的一键环境 `myenv` 见 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)；本文侧重**日常环境管理**本身。

![conda_mamba](../../images/articles/技术文档/T05-Conda与Mamba简明教程/web/T05-hero-conda_mamba.webp)

---

## 一、核心概念：为什么要用虚拟环境？

| 概念 | 含义 |
|------|----------|
| **虚拟环境 (Environment)** | 一个独立的「Python 小房间」，有自己的 Python 版本和包 |
| **base 环境** | Conda 安装后自带的默认环境，**不建议在 base 里装项目依赖** |
| **激活 (activate)** | 进入某个环境，此后 `python`、`pip` 命令都指向该环境 |
| **通道 (Channel)** | 软件包的下载源，如 `conda-forge`、官方 `defaults` |
| **environment.yml** | 环境配置文件，可一键复现整套依赖 |

**典型场景：**

- 项目 A 用 Python 3.10 + NumPy 1.x
- 项目 B 用 Python 3.12 + NumPy 2.x  
→ 各建一个环境，切换即可，不必来回卸载重装。

---

## 二、Conda 与 Mamba 是什么关系？

可以这么记：**Conda 是管家，Mamba 是同一个管家的「快跑模式」**——命令几乎一样，但创建环境、装包时 Mamba 快很多。

| 工具 | 含义 |
|------|----------|
| **Conda** | 包与环境管理器，功能全；解析依赖时偶尔较慢 |
| **Mamba** | Conda 的加速版，**命令与 Conda 兼容**，日常装包首选 |
| **Miniconda** | 精简版安装器（不带一大堆预装包），**日常推荐** |
| **Miniforge** | 类似 Miniconda，默认走 `conda-forge` 源，开源社区常用 |
| **pip** | Python 官方装包工具；Conda 环境里也能用，但**优先 mamba install** |

**推荐组合：Miniconda（或 Miniforge）+ Mamba**

- 用 **mamba** 创建环境、安装包（快）
- 用 **conda** 激活 / 退出环境（`conda activate` 是标准写法）

后文命令以 `mamba` 为例；若未安装 Mamba，把 `mamba` 换成 `conda` 即可，语法相同。

---

## 三、各平台安装

### 1. Mac

**方式一：Miniconda（官方）**

1. 打开 [Miniconda 安装页](https://www.anaconda.com/docs/getting-started/miniconda/install/overview)，下载 macOS 安装包（Apple Silicon 选 arm64，Intel 选 x86_64）
2. 按向导安装，或终端执行（以 arm64 为例，版本号以官网为准）：

```bash
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh
```

3. 安装结束后**重新打开终端**，验证：

```bash
conda --version
```

**方式二：Homebrew**

```bash
brew install --cask miniconda
conda init zsh   # 若使用 Zsh（Mac 默认）
```

### 2. Ubuntu / Linux

```bash
# 下载（Linux x86_64 示例，其他架构见官网）
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
# 按提示安装，完成后重新打开终端
conda --version
```

**Miniforge 替代方案（默认 conda-forge）：**

```bash
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh
```

### 3. Windows

1. 从 [Miniconda 官网](https://www.anaconda.com/docs/getting-started/miniconda/install/overview) 下载 `.exe` 安装包
2. 安装时建议勾选 **「Add Miniconda3 to my PATH environment variable」**（或安装后用「Anaconda Prompt」）
3. 打开 **Anaconda Prompt**、**Git Bash** 或 **WSL**，验证：

```bash
conda --version
```

> **Tips：** 分子模拟用户若已配置 WSL，建议在 WSL 内安装 Miniconda，与 Linux 教程一致。参见 [WSL2安装与配置](T02-WSL2安装与配置.md) 与 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)。

---

## 四、安装后初始化

### 1. 让终端识别 conda 命令

安装程序通常会问是否运行 `conda init`；若未执行，手动运行：

```bash
conda init zsh         # Mac / Ubuntu（Zsh）
conda init bash        # Ubuntu（Bash）
conda init powershell  # Windows PowerShell
```

然后**关掉终端再打开**（或执行 `source ~/.zshrc`）。若提示符前出现 `(base)`，说明 conda 已生效。

### 2. 安装 Mamba（强烈推荐）

`(base)` 是 conda 自带的默认环境，**只用来装 mamba 本身**，别往里面堆项目包。在 base 里执行一次：

```bash
conda install mamba -n base -c conda-forge
mamba --version
```

### 3. 可选：加快 conda-forge 访问

国内用户可配置镜像（以清华镜像为例，按需选用）：

```bash
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge
conda config --set show_channel_urls yes
```

---

## 五、环境管理：最常用的命令

日常就记这一套：**建环境 → 激活 → 装包 → 用完退出**。

### 1. 创建环境

```bash
# 指定 Python 版本创建名为 myproject 的环境
mamba create -n myproject python=3.12 -y

# 创建时直接安装常用包
mamba create -n dataanalysis python=3.11 numpy pandas matplotlib -y
```

`-n` 表示环境名称（name）；`-y` 表示自动确认，跳过交互提示。

### 2. 激活与退出

```bash
conda activate myproject    # 进入环境（提示符前会出现环境名）
conda deactivate            # 退出当前环境，回到 base
```

> **注意：** 激活 / 退出统一用 `conda activate` / `conda deactivate`，即使用 Mamba 安装包也是如此。

### 3. 查看环境列表

```bash
mamba env list
# 或
conda env list
```

带 `*` 的为当前激活的环境；`base` 为默认环境。

### 4. 删除环境

```bash
mamba env remove -n myproject
```

### 5. 克隆环境（复制一份）

```bash
mamba create -n myproject-copy --clone myproject
```

---

## 六、安装与管理软件包

**进入目标环境后再安装：**

```bash
conda activate myproject
```

### 1. 用 mamba 安装（首选）

```bash
mamba install numpy scipy matplotlib
mamba install -c conda-forge rdkit    # 指定通道
```

### 2. 用 pip 安装（mamba 里没有的包）

Conda 环境里可以混用 pip，但**建议先 mamba 后 pip**，且装完不要再对该环境大量 `mamba install`，以免依赖冲突：

```bash
pip install some-pypi-only-package
```

### 3. 查看已安装的包

```bash
mamba list
# 或查看某个包
mamba list numpy
```

### 4. 更新 / 卸载包

```bash
mamba update numpy          # 更新单个包
mamba update --all          # 更新环境中所有包（慎用，可能牵动依赖）
mamba remove numpy          # 卸载包
```

### 5. 搜索包

```bash
mamba search mdanalysis
```

---

## 七、导出与复现环境（environment.yml）

团队协作或换机器时，用配置文件一键复现环境。

### 1. 从当前环境导出

```bash
conda activate myproject
mamba env export > environment.yml
```

精简版（只保留你手动安装过的包，体积更小）：

```bash
mamba env export --from-history > environment.yml
```

### 2. 从 yml 文件创建环境

```bash
mamba env create -f environment.yml
conda activate myproject   # 名称以 yml 里 name: 字段为准
```

### 3. yml 文件长什么样？

```yaml
name: myproject
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - numpy
  - pandas
  - pip
  - pip:
      - some-pypi-package
```

分子模拟预置环境可直接使用 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md) 中的 `myenv.yml` 一键部署。

### 4. 更新已有环境

修改 `environment.yml` 后：

```bash
mamba env update -n myproject -f environment.yml --prune
```

`--prune` 会移除 yml 中不再列出的包。

---

## 八、通道 (Channel) 是什么？

**通道**就是「去哪个仓库下载安装包」。装不上、版本不对时，常和通道有关。

| 通道 | 含义 |
|------|----------|
| **defaults** | Anaconda 官方默认仓库 |
| **conda-forge** | 社区维护，包全、更新快，**科研用户首选** |
| **bioconda** | 生物信息学相关包 |

临时指定通道：

```bash
mamba install -c conda-forge packmol
```

永久添加（写入配置）：

```bash
conda config --add channels conda-forge
conda config --set channel_priority strict
```

---

## 九、在 VSCode / Cursor 与 Jupyter 中使用

### 1. 选择 Python 解释器

1. `Command/Ctrl + Shift + P` → 输入 `Python: Select Interpreter`
2. 选择对应 Conda 环境，路径通常含 `envs/环境名/bin/python`

### 2. Jupyter Notebook / JupyterLab

```bash
conda activate myproject
mamba install jupyterlab ipykernel
python -m ipykernel install --user --name myproject --display-name "Python (myproject)"
```

之后在 VSCode / Cursor 或 JupyterLab 的 Kernel 列表里选择 **Python (myproject)** 即可。

### 3. 终端里确认当前环境

```bash
which python      # Mac / Linux
where python      # Windows
python --version
```

路径应指向 `.../envs/环境名/...`，而不是系统 Python。

---

## 十、常见问题与最佳实践

### 1. 不要滥用 base 环境

`base` 只用来管理 Conda/Mamba 本身。每个项目单独建环境，避免把所有包装在一起。

### 2. `conda activate` 报错：command not found

运行 `conda init <你的shell>` 后重开终端；WSL / 远程集群需在**对应终端**里初始化。

### 3. 环境激活后 VSCode 仍用错 Python

手动 `Python: Select Interpreter` 选一次；或在项目根目录建 `.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": "~/miniconda3/envs/myproject/bin/python"
}
```

路径按实际安装位置修改。

### 4. Solving environment 很慢或失败

- 优先用 **mamba** 代替 `conda install`
- 尽量在**新环境**里安装，而不是往旧环境里硬塞
- 指定版本范围，减少求解空间：`python=3.12`、`numpy>=1.26,<2`
- 冲突严重时，新建环境往往比修复旧环境更省时

### 5. mamba 与 pip 混用原则

1. 先 `mamba install` 能装的
2. 再用 `pip install` 补 PyPI 独有的包
3. 同一环境里避免反复交替大量安装

### 6. 清理磁盘空间

```bash
mamba clean --all        # 清理下载缓存与索引
mamba env remove -n 旧环境名
```

### 7. 开机自动进入某环境（可选）

在 `~/.zshrc` 或 `~/.bashrc` 末尾添加：

```bash
conda activate myenv
```

仅当你几乎只用一个环境时推荐；多项目用户建议每次手动切换。

---

## 十一、命令速查表

| 你想做的事 | 命令 |
|-----------|------|
| 创建环境 | `mamba create -n 环境名 python=3.12 -y` |
| 激活环境 | `conda activate 环境名` |
| 退出环境 | `conda deactivate` |
| 查看所有环境 | `mamba env list` |
| 删除环境 | `mamba env remove -n 环境名` |
| 安装包 | `mamba install 包名` |
| 卸载包 | `mamba remove 包名` |
| 查看已装包 | `mamba list` |
| 导出环境 | `mamba env export > environment.yml` |
| 从 yml 创建 | `mamba env create -f environment.yml` |
| 更新环境 | `mamba env update -n 环境名 -f environment.yml` |
| 清理缓存 | `mamba clean --all` |

---

## 十二、推荐学习资源

- [Conda 官方文档](https://docs.conda.io/projects/conda/en/stable/user-guide/getting-started.html)
- [Mamba 文档](https://mamba.readthedocs.io/)
- [conda-forge 包搜索](https://anaconda.org/conda-forge)
- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md) —— MolSimulX 预置 Python 环境与分子模拟库安装

---

## 十三、小结

1. **一个项目一个环境**，尽量别在 `base` 里堆包。  
2. **Miniconda + Mamba**：创建和安装用 mamba，激活用 conda。  
3. **日常三板斧**：`mamba create` → `conda activate` → `mamba install`。  
4. **复现与分享**：`environment.yml` 是团队协作的标配。  
5. **编辑器**：在 VSCode / Cursor 里选对解释器和 Jupyter Kernel，避免「终端对了、Notebook 错了」。

掌握以上内容，就足以应对日常 Python 科研开发中的环境管理需求；分子模拟方向的完整依赖清单与一键部署，请继续参考本站[分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md) 教程。`Solving environment` 卡住或报错时，把终端**完整输出**复制去搜，往往能找到具体解决办法。

---

## 学习路径

**前置阅读：**

- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)（第三节步骤 3）
- [Linux终端与Shell简明教程](T03-Linux终端与Shell简明教程.md)

**下一步：**

- [JupyterLab简明教程](T11-JupyterLab简明教程.md)
- [VSCode与Cursor简明教程](T06-VSCode与Cursor简明教程.md) —— 选择解释器
