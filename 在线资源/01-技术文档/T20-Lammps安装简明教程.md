---
wp_post_id: 1803
id: T20
title: Lammps安装简明教程
wp_slug: lammps安装简明教程
series: 在线资源
tier: 技术文档
status: reviewed
topic: Lammps
paywall: free
---
> **系列标签：** `技术文档` · `Lammps` · `安装` · `package` · `GPU` · `macOS` · `Linux`

平台和 Python 环境有了，下一步往往是：本机能不能先跑通一小段 **Lammps**？笔记本上短跑冒烟、调试 `in` 文件，比每次改两行就 `rsync` 上集群排队省事得多。

本文讲 **Mac** 与 **Linux（含 Ubuntu / WSL）** 上安装可执行程序的常用路径：**Homebrew**、**apt**，以及 **CMake 自编译**——含开启常见 / 特殊 **package**、编 **GPU** 版（GPU package 与 KOKKOS）。目标是装出能敲的命令（如 `lmp` / `lammps_serial`），跑通冒烟，搞清本机安装和集群 `module load` 的关系。

细节跟 [官方 Build extras](https://docs.lammps.org/Build_extras.html) 与集群环境走。装本机底座仍看 [Mac与Ubuntu开发环境配置](T19-Mac与Ubuntu开发环境配置.md)；平台总览见 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)；正式生产多在集群，见 [集群与SLURM简明教程](T10-集群与SLURM简明教程.md)。

| 你在哪 | 读哪篇 |
|--------|--------|
| 新 Mac / 新 Ubuntu 还没 CLT / Homebrew / apt 基础 | [Mac与Ubuntu开发环境配置](T19-Mac与Ubuntu开发环境配置.md) |
| Windows 原生 | 先 [WSL2安装与配置](T02-WSL2安装与配置.md)，再按本文 **Ubuntu** 节 |
| **本机装发行版 Lammps** | 下文第三～四节 |
| **有改写 / 新增源码，要自己编** | 下文第五节 |
| **要开特殊 package / 编 GPU 版** | 下文第六～七节 |
| 交作业、登录节点别硬跑 | [集群与SLURM简明教程](T10-集群与SLURM简明教程.md) |

官方总览：[Lammps 安装文档](https://docs.lammps.org/Install.html)（版本与包名偶有变动，以官网与包管理器为准）。

![lammps](../../images/articles/技术文档/T20-Lammps安装简明教程/web/T20-hero-lammps.webp)

---

## 一、先选一条安装路线

| 路线                              | 适合谁                                                    | 优点                         | 注意                                        |
| ------------------------------- | ------------------------------------------------------ | -------------------------- | ----------------------------------------- |
| **Mac：Homebrew**                | 已按 [Mac与Ubuntu开发环境配置](T19-Mac与Ubuntu开发环境配置.md) 装好 brew | 一行安装；自带 serial / MPI 可执行文件 | 预编译包未必含你要的全部 Lammps package               |
| **Ubuntu / Debian / WSL：`apt`** | 系统较新                                                   | 简单；随系统更新                   | 发行版仓库版本可能略落后于官网最新 stable                  |
| **源码 CMake 自编译**                | 要开特定 package、GPU，或**手里有改写 / 新增的 `.cpp/.h`**            | 版本与代码完全可控；改完可反复重编          | 要准备编译器 + CMake；别和 brew/apt 的 `lmp` 抢 PATH |

入门推荐：**Mac 用 brew；Ubuntu / WSL 用 apt**。先冒烟通过，再决定要不要为某个 `pair_style`、或自写势函数去源码编译。

> **Tips：** 集群上常见是 `module load lammps` 或管理员编好的路径，**不必**在登录节点再 brew/apt 一份生产构建。本机安装主要服务「短跑调试」；自编译二进制再 `rsync` / 按集群规矩安装时，版本与 package 要和生产一致。

---

## 二、安装前确认底座

在终端执行（Mac / Linux / WSL 通用思路）：

```bash
# Mac
brew --version
clang --version

# Ubuntu / WSL
sudo apt update
gcc --version
```

若 `brew` / 编译器都没有，先完成 [Mac与Ubuntu开发环境配置](T19-Mac与Ubuntu开发环境配置.md)。Windows 用户所有命令都在 **WSL** 里敲。

---

## 三、Mac：用 Homebrew 安装

1. 确保 [Homebrew](https://brew.sh/) 可用（步骤见 [Mac与Ubuntu开发环境配置](T19-Mac与Ubuntu开发环境配置.md)）。  
2. 安装：

```bash
brew install lammps
```

3. 按 brew 结束时的提示确认 PATH。常见可执行文件名（以你机器为准）：

```bash
which lammps_serial
which lammps_mpi
lammps_serial -h
```

官方说明：Homebrew 安装后通常提供 **`lammps_serial`** 与 **`lammps_mpi`**，并附带部分 potentials / examples 等资源目录（见 [Install for macOS](https://docs.lammps.org/Install_mac.html)）。可用：

```bash
brew test lammps -v
```

做一次包管理器侧的快速自检（需联网与 brew 测试权限，视环境而定）。

**可选：** 需要 OpenKIM 模型时：

```bash
brew install openkim-models
```

> **Tips：** 预编译缺某个 package（`Unrecognized … style`）时，按下文第五、六节用 CMake 开启对应 `PKG_…`（或挂上自写代码）再编——Homebrew 默认配方不一定覆盖你课题的全部包。

---

## 四、Ubuntu / Debian / WSL：用 apt 安装

```bash
sudo apt update
sudo apt install -y lammps
```

常见可执行文件名为 **`lmp`**（部分环境也可能提供带后缀的变体）：

```bash
which lmp
lmp -h
```

需要 OpenKIM 模型时可再装（包名以发行版为准）：

```bash
sudo apt install -y openkim-models
```

更新仓库后的 Lammps 包：

```bash
sudo apt update
sudo apt upgrade lammps
```

说明见 [Install for Linux](https://docs.lammps.org/Install_linux.html)。Fedora / RHEL / openSUSE 等用各自的 `dnf` / `yum` / `zypper`，包名多为 `lammps`，本文不一一展开。

---

## 五、自己改写 / 新增源码：CMake 编译

发行版装的是「别人编好的二进制」。下面这些情况通常要**拿源码自己编**（Mac、Ubuntu、WSL 流程相同；Windows 仍建议在 WSL 里做）：

| 情况 | 为什么包管理器不够 |
|------|-------------------|
| 改了现有 `pair_*` / `fix_*` / `fix_*` 等 | brew / apt 装不到你的补丁 |
| 新加了一个 style（自定义势、新 fix） | 必须把 `.cpp/.h` 编进可执行文件 |
| 课题要开特定 [package](https://docs.lammps.org/Packages.html)，预编译没开 | 用 `-D PKG_xxx=on` 重开再编 |
| 要对齐论文 / 集群上的某个 git commit | 固定源码树再构建，便于复现 |

官方入口：[Build with CMake](https://docs.lammps.org/Build_cmake.html) · [Adding your own code](https://docs.lammps.org/Modify.html)（旧作文与新版路径名偶有差异，以当前文档为准）。

### 1. 编译依赖

```bash
# Ubuntu / WSL
sudo apt update
sudo apt install -y build-essential cmake git
# 需要 MPI 并行时再装，例如：
# sudo apt install -y libopenmpi-dev openmpi-bin

# Mac（CLT + Homebrew，见「Mac与Ubuntu开发环境配置」）
brew install cmake
# 需要 MPI 时：brew install open-mpi
```

核对：

```bash
cmake --version
c++ --version    # 或 g++ / clang++
```

### 2. 准备源码树（含你的改写）

常见两种来源——**以你实际手里的目录为准**：

```bash
# A. 官方源码再改（举例）
git clone --depth 1 https://github.com/lammps/lammps.git
cd lammps
# 在 src/ 或自建 package 目录里改 / 加文件……

# B. 课题组已给你改过的完整树（zip / git 仓库）
cd /path/to/your-lammps-fork
```

**放自定义代码的习惯（择一，别两边各抄一份）：**

1. **改现有文件**：直接改 `src/` 里对应源文件，保存后重编即可。  
2. **新增 style**：按官方「自建 package」做法，把文件放进例如 `src/MYPKG/`（目录名与 package 名约定见文档），构建时打开对应 `PKG_…`；或按 Modify 文档把文件挂进现有 package。  
3. **务必**随可执行文件记下：**基于哪个 upstream 版本 / commit、你自己的补丁清单**，否则半年后 Methods 写不清「跑的是哪一版引擎」。

用 [Git简明使用教程](T04-Git简明使用教程.md) 给 fork 开分支；大轨迹仍不要塞进同一仓库（见 [数据管理与备份](T17-数据管理与备份.md)）。

### 3. 标准构建（装到用户目录，避开系统包）

**不要** overlap 覆盖 brew / apt 的全局 `lmp`——装到家目录前缀，用绝对路径或单独改 PATH：

```bash
cd /path/to/your-lammps-fork
mkdir -p build && cd build

# 串行入门示例；需要的 package 按课题打开（名称见官方 Packages 列表）
# Lammps_MACHINE 可给可执行文件起名：装出 lmp_<名字>（不设则多为 lmp）
cmake ../cmake \
  -D CMAKE_INSTALL_PREFIX=$HOME/opt/lammps-custom \
  -D Lammps_MACHINE=custom \
  -D BUILD_MPI=no \
  -D PKG_MOLECULE=yes \
  -D PKG_KSPACE=yes
  # 若你建了 MYPKG：再加 -D PKG_MYPKG=yes

cmake --build . -j "$(sysctl -n hw.ncpu 2>/dev/null || nproc)"
cmake --install .
```

装完后二进制通常在 `$HOME/opt/lammps-custom/bin/`。上面例子会得到 **`lmp_custom`**（未设 `Lammps_MACHINE` 时多为 `lmp`，以 `ls` 为准）：

```bash
export PATH="$HOME/opt/lammps-custom/bin:$PATH"
which lmp_custom
lmp_custom -h
```

**给可执行文件起名（推荐多版本并存时用）：** CMake 选项 `-D Lammps_MACHINE=名字` 会生成 `lmp_名字`（共享库则多为 `liblammps_名字…`）。名字自定，例如 `serial`、`mpi`、`gpu`、`reax-gpu`、课题组简称。本机可同时保留：

| 场景 | 示例 |
|------|------|
| 日常串行调试 | `-D Lammps_MACHINE=serial -D BUILD_MPI=no` → `lmp_serial` |
| MPI 生产构建 | `-D Lammps_MACHINE=mpi -D BUILD_MPI=yes` → `lmp_mpi` |
| GPU / 自改源码 | `-D Lammps_MACHINE=gpu` 或 `mycustom` → `lmp_gpu` / `lmp_mycustom` |

作业脚本、`which`、Methods 里都写 **`lmp_名字` 的绝对路径**，就不会和 brew / apt 的 `lammps_serial`、系统 `lmp` 撞车。说明见 [Basic build options](https://docs.lammps.org/Build_basics.html)。

需要 MPI 时，在本机装好 OpenMPI / MPICH 后改为例如 `-D BUILD_MPI=yes`，并用 `mpirun -np … lmp_mpi -in …` 试跑（核数别占满整机，见第九节）。

> **Tips：** 第一次配置错了（忘开 package、装错前缀），删掉 `build/` 重建往往比在旧缓存上硬改省心：`rm -rf build && mkdir build && cd build && cmake …`。

### 4. 改完代码怎么重编

日常开发循环：

```bash
# 1. 改 src/… 或你的 package 目录
# 2. 回到当初的 build 目录
cd /path/to/your-lammps-fork/build
cmake --build . -j "$(sysctl -n hw.ncpu 2>/dev/null || nproc)"
cmake --install .    # 若之前装过前缀，再同步一次 bin
```

只改了少量 `.cpp` 时增量编译通常很快。若 CMake 选项（package、MPI）有变，重新跑一遍 `cmake ../cmake …` 再 build。

冒烟时**刻意**调用自编路径，确认不是 brew/apt 的旧二进制：

```bash
type -a lmp_custom
$HOME/opt/lammps-custom/bin/lmp_custom -in in.your_test
```

### 5. 和发行版、集群怎么并存

| 场景                               | 建议                                                                                          |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| 本机既有 `brew install lammps` 又有自编译 | 自编译用 `Lammps_MACHINE` 起不同名（如 `lmp_custom`），脚本写死 `$HOME/opt/…/bin/lmp_custom` |
| 集群跑你改过的引擎                        | 一般不能指望 `module load` 带你的补丁；把编好的二进制或整个 `prefix` 按课题组规矩放到 `$HOME` / `$SCRATCH`，作业脚本里写**绝对路径** |
| 提交论文                             | 写明 upstream 标签 / commit + 自写 package 名；仓库里保留可复现的 CMake 命令或小脚本                               |

开启更多 **package**、编 **GPU** 见第六、七节。改完选项记得重新 `cmake`（或清掉 `build/` 再建）。

---

## 六、特殊 / 常用 package 怎么开

Lammps 的「package」决定二进制里有没有某类 `pair_style` / `fix` / `compute`。发行版 brew / apt **默认只开一部分**；缺了就会报 `Unrecognized … style`——这时用 CMake 打开对应 `PKG_名字=yes` 再编（见第五节）。

官方总表：[Packages](https://docs.lammps.org/Packages.html) · 开法：[Build package](https://docs.lammps.org/Build_package.html) · 额外依赖：[Build extras](https://docs.lammps.org/Build_extras.html)。

### 1. 怎么知道自己缺哪个包

1. 查文档：该 `pair_style` / `fix` 页面通常写明隶属哪个 package。  
2. 看当前二进制：`lmp -h`（或部分版本打印 Installed Packages）。  
3. 报错 `Unrecognized pair style 'lj/class2'` 之类 → 打开含 CLASS2 的包后再编。

### 2. CMake 开包与 preset

单个打开：

```bash
cmake ../cmake -D PKG_MOLECULE=yes -D PKG_KSPACE=yes -D PKG_MANYBODY=yes
# 名字与 Packages 页面一致，例如 PKG_REAXFF、PKG_MEAM、PKG_PYTHON
```

常用 **preset**（在源码树 `cmake/presets/`，用 `-C` 加载；可叠多个）：

```bash
# 核心几包：MOLECULE、KSPACE、MANYBODY、RIGID、GRAPHICS 等
cmake -C ../cmake/presets/basic.cmake ../cmake

# 多数常用包（更全，体积与编译时间也更大）
cmake -C ../cmake/presets/most.cmake ../cmake

# most 后再去掉依赖重库的包，并自己加 GPU 等（官方示例思路）
cmake -C ../cmake/presets/most.cmake \
      -C ../cmake/presets/nolib.cmake \
      -D PKG_GPU=on -D GPU_API=cuda \
      ../cmake
```

已有 `build/` 时也可增量加包：

```bash
cd build
cmake -D PKG_BODY=yes .
cmake --build . -j "$(sysctl -n hw.ncpu 2>/dev/null || nproc)"
```

### 3. 分子模拟里常碰到的包（示例）

| 需求方向                  | 常见 package（名称以官网为准）            | 备注                                                     |
| --------------------- | ------------------------------ | ------------------------------------------------------ |
| 分子拓扑、键角、简单 LJ/电荷      | `MOLECULE`、`KSPACE`、`RIGID`    | `basic` preset 大致覆盖                                    |
| 金属多体势、AIREBO 等        | `MANYBODY` 等                   | 缺势多从这里找                                                |
| Class2 / 部分商品力场风格     | `CLASS2` 等                     | 输入里出现 `lj/class2` 就对一下                                 |
| ReaxFF、MEAM 等         | `REAXFF`、`MEAM` 等              | 各自文档有额外提示                                              |
| OpenMP 线程加速（CPU）      | `OPENMP`（`-D PKG_OPENMP=yes`）  | 运行用 `-sf omp` 等；见速度文档                                  |
| 嵌 Python、调外部库         | `PYTHON`                       | 需本机 Python 开发头文件；见 Build extras                        |
| OpenKIM 模型            | `KIM`                          | 另装 kim-api / openkim-models；发行版有时另有 `openkim-models` 包 |
| 机器学习势（SNAP、IAP、PACE…） | `ML-SNAP`、`ML-IAP`、`ML-PACE` 等 | 部分要额外库；跟 Build extras 逐步开                              |
| GPU 加速                | `GPU` 或 `KOKKOS`               | **见第七节**；不要一次全开                                        |

> **Tips：** `most.cmake` 省事，但编译久、依赖多；课题只缺两三个 style 时，**按需 `-D PKG_…=yes`** 更干净，也更容易对齐集群上的构建。

### 4. 「特殊」包：多出来的依赖

下面这些打开后常要**额外软件**，CMake 会找库；找不到就配置失败——对照 [Build extras](https://docs.lammps.org/Build_extras.html) 装好再编：

| 包（示例） | 常要额外准备什么 |
|------------|------------------|
| `PYTHON` | Python 3 + 开发头文件（如 `python3-dev`） |
| `KIM` | kim-api；模型侧常配 OpenKIM |
| `VORONOI` | voro++ |
| `NETCDF` / `H5MD` / `COMPRESS` | netcdf、HDF5、zlib 等 |
| `ML-*` 系列 | 依官方说明（部分要单独源码或库） |
| `GPU` / `KOKKOS` | CUDA（NVIDIA）或对应 GPU 工具链；见第七节 |

Ubuntu 举例（仅示意，包名随发行版变）：

```bash
sudo apt install -y python3-dev zlib1g-dev libpng-dev
# kim-api、fftw、netcdf 等按你打开的 PKG 再装
```

Mac 上优先用 Homebrew 装同名依赖，再把前缀告诉 CMake（必要时 `-D CMAKE_PREFIX_PATH=$(brew --prefix)`）。

---

## 七、GPU 版本怎么装

GPU 不是 brew / apt 「换个开关」就能得到的——一般要在 **Linux + NVIDIA（或集群模块）** 上用源码编。消费级 **Mac（含 Apple Silicon）基本没有 NVIDIA CUDA 路线**，本机 GPU 版 Lammps 不现实；调试用 CPU，生产把作业交到有 GPU 的集群。

两条主流加速包（**二选一为主**，勿混用同一套输入里的两套约定）：

| | **GPU package** | **KOKKOS package** |
|--|-----------------|---------------------|
| 定位 | 经典「力和邻居上 GPU」加速包 | 更统一的 Kokkos 后端（CUDA / HIP / OpenMP…） |
| CMake | `-D PKG_GPU=yes` + `GPU_API` / `GPU_ARCH` | `-D PKG_KOKKOS=yes`，常用 `kokkos-cuda.cmake` preset |
| 运行 | 常用 `-sf gpu`，并设 GPU 数等 | 须 `-k on`，常用 `-sf kk` |
| 文档 | [GPU package](https://docs.lammps.org/Speed_gpu.html) · [Build extras · GPU](https://docs.lammps.org/Build_extras.html#gpu-package) | [KOKKOS](https://docs.lammps.org/Speed_kokkos.html) · [Build extras · KOKKOS](https://docs.lammps.org/Build_extras.html#kokkos-package) |

课题论文、集群 `module` 写的是哪条，你就跟哪条；两边都编通再在自家 `in` 里试。

### 1. 编译前确认硬件与工具链

```bash
nvidia-smi                  # 有驱动、能看到卡
nvcc --version              # CUDA toolkit（版本要与驱动匹配）
```

集群上常见是 `module load cuda` / `module load gcc` 等，**以机房说明为准**。无卡的登录节点可以「交叉」编出二进制，但链接时常需要 CUDA stub（`libcuda.so`）；最终仍须在**计算节点**冒烟。

### 2. 示例：GPU package + CUDA

架构代号（`GPU_ARCH`）按卡型选，例如 Ampere 常用 `sm_80` / `sm_86`，完整表见 [Build extras · GPU](https://docs.lammps.org/Build_extras.html#gpu-package)。可与 `most` + `nolib` 组合：

```bash
cd /path/to/lammps
mkdir -p build-gpu && cd build-gpu

cmake -C ../cmake/presets/most.cmake \
      -C ../cmake/presets/nolib.cmake \
      -D CMAKE_INSTALL_PREFIX=$HOME/opt/lammps-gpu \
      -D Lammps_MACHINE=gpu \
      -D BUILD_MPI=yes \
      -D PKG_GPU=yes \
      -D GPU_API=cuda \
      -D GPU_ARCH=sm_80 \
      ../cmake

cmake --build . -j "$(nproc)"
cmake --install .
```

冒烟（单卡、小例子）：

```bash
export PATH="$HOME/opt/lammps-gpu/bin:$PATH"
# 具体 -sf / -pk 参数以当前文档为准
mpirun -np 1 lmp_gpu -sf gpu -pk gpu 1 -in in.lj
```

OpenCL / HIP 把 `GPU_API` 换成 `opencl` 或 `hip`，并装好对应 runtime（细节见官方）。

### 3. 示例：KOKKOS + CUDA

优先用官方 preset，再按卡改架构变量（preset 内注释会写 `Kokkos_ARCH_…`）：

```bash
mkdir -p build-kk && cd build-kk

cmake -C ../cmake/presets/most.cmake \
      -C ../cmake/presets/kokkos-cuda.cmake \
      -D CMAKE_INSTALL_PREFIX=$HOME/opt/lammps-kk \
      -D Lammps_MACHINE=kk \
      ../cmake

cmake --build . -j "$(nproc)"
cmake --install .
```

运行要点（摘自官方速度文档，参数名随版本微调）：

```bash
export PATH="$HOME/opt/lammps-kk/bin:$PATH"
# 必须打开 Kokkos；g / t 等为 GPU 数与 OpenMP 线程数示例
mpirun -np 1 lmp_kk -k on g 1 -sf kk -in in.lj
```

多 MPI 秩且 MPI **非** GPU-aware 时，可能要加 `package kokkos gpu/aware off` 或命令行等价选项，否则会段错误——见 [Speed_kokkos](https://docs.lammps.org/Speed_kokkos.html)。

### 4. 使用与排错注意

| 现象 | 先检查 |
|------|--------|
| 编得过、跑却像纯 CPU | 是否加了 `-sf gpu` / `-k on -sf kk`；是否误用了 brew/apt 的旧 `lmp` |
| `CUDA not found` / 链接 `libcuda` | `nvcc`、`CUDA_HOME`、驱动；登录节点缺库时用 toolkit 自带 stub |
| 小体系 GPU 更慢 | 正常：传输开销大；GPU 适合**足够大**的体系 |
| Mac / 无 NVIDIA 笔记本 | 不要死磕本机 GPU 版；CPU 调通 `in`，GPU 放到集群 |

> **Tips：** 第一次编 GPU，先固定 **一套**（GPU package **或** KOKKOS）+ 一两个本征 package，确认 `nvidia-smi` 有占用后再往 `most` 里堆。集群作业脚本里写清模块、绝对路径与 `-sf`/`-k` 参数，和 [集群与SLURM简明教程](T10-集群与SLURM简明教程.md) 一起用。

---

## 八、冒烟：跑一个最短例子

装好后任选本机二进制（下面以 `lmp` 为例；Mac Homebrew 请换成 `lammps_serial`；自编译用你的 `prefix/bin/lmp`）：

```bash
# 找 examples（路径因安装方式而异，可用 locate / mdfind / brew --prefix）
# apt / brew 常把示例放在 share 或 Cellar 下；也可从官网 tarball 取 bench/examples

# 最小自检：能打印帮助即说明二进制正常
lmp -h
```

若已找到 Lammps 自带的 Lennard-Jones 示例目录（名称常含 `lj` / `bench`），进入后：

```bash
lmp -in in.lj
# Mac Homebrew 常为：
# lammps_serial -in in.lj
```

看到开始刷 thermo、结束无立即段错误，一般就算通过。细节以当前版本文档与 `examples` 里的 README 为准。

本项目目录习惯是把输入放在 `lammps/`（见 [科研项目目录结构规范](T15-科研项目目录结构规范.md)）：

```bash
mkdir -p myproject/lammps
# 把调试用的 in.* 放进 myproject/lammps/
cd myproject/lammps
lmp -in in.minimize
```

---

## 九、MPI、核数与「本机别跑太凶」

| 场景 | 建议 |
|------|------|
| 改 `in`、核对单位、几十步 minimize | **串行**即可（`lmp` / `lammps_serial` / 自编译 `lmp`） |
| 本机并行试跑 | `mpirun -np 4 lammps_mpi -in in.npt`（核数别占满整机） |
| GPU 节点 | 一个作业绑清 GPU 数与 MPI 秩；别在登录节点占卡 |
| 正式长时间、大体系 | **集群** `sbatch`（见 [集群与SLURM简明教程](T10-集群与SLURM简明教程.md)） |

笔记本风扇狂转、散热报警时，把生产迁到集群比死磕本机更合理。

---

## 十、常见问题

**Q：提示 `command not found: lmp`？**  
A：Mac 先试 `lammps_serial`；自编译是否把 `$HOME/opt/…/bin` 写进 PATH。`echo $PATH`、`type -a lmp` 先看清楚。重新开一个终端再试。

**Q：`Unrecognized atom style / pair style`？**  
A：当前二进制没编进对应 package，或你的自定义 style 没进这次构建。查看文档隶属哪个包，按第六节 `-D PKG_…=yes`（或第五节挂自写代码）再编。

**Q：改完源码，运行仍像旧版行为？**  
A：多半 PATH 命中了 brew/apt 的旧 `lmp`。用 `type -a lmp` 和**绝对路径**调用自编译二进制；确认 `cmake --install` 已装到你以为的前缀。

**Q：本机和集群结果差一截？**  
A：先对齐**同一份源码 / commit**、包集合（含 GPU/KOKKOS）、精度与热浴；本机冒烟通过 ≠ 和生产构建比特级一致。Methods 里写清可执行文件来源与版本。

**Q：自编译出来的还叫 `lmp`，和系统装的撞名？**  
A：CMake 加 `-D Lammps_MACHINE=名字`，可执行文件会变成 `lmp_名字`（第五节）。Homebrew 自带的一般是 `lammps_serial` / `lammps_mpi`，命名空间本来就和 `lmp` 错开。

**Q：一定要装 GPU 版吗？**  
A：不必。小体系与调 `in` 用 CPU 往往更省事；GPU 适合集群上的大体系。有 NVIDIA + CUDA 时按第七节编；Mac 本机一般走 CPU。

**Q：GPU package 和 KOKKOS 要不要一起开？**  
A：可以编进同一二进制，但**同一套生产输入**建议主用一条加速路径，避免 style 后缀与 `package` 命令打架。跟课题 / 集群文档保持一致。

**Q：Windows 不装 WSL 行不行？**  
A：可以找社区/官方的 Windows 构建，但与集群 Linux 环境不一致，路径与脚本容易分叉；**自编译与 GPU 尤其别在原生 Windows 硬刚**。MolSimulX 推荐 **WSL → 按 Ubuntu 安装 / 编译**（GPU 仍需 Linux 主机或带 GPU 的远程节点）。

---

## 十一、小结

1. **Mac：** `brew install lammps` → 常用 `lammps_serial` / `lammps_mpi`。  
2. **Ubuntu / WSL：** `sudo apt install lammps` → 常用 `lmp`。  
3. **改写 / 新增源码：** CMake 编到 `$HOME/opt/…`，用 `-D Lammps_MACHINE=…` 生成 `lmp_名字`；改完增量 `cmake --build`；作业脚本写绝对路径。  
4. **特殊 / 常用 package：** `-D PKG_…=yes` 或 `basic` / `most` preset；有额外库的对照 Build extras。  
5. **GPU：** Linux + CUDA（或集群模块）；`PKG_GPU` 或 `PKG_KOKKOS`（preset），运行加 `-sf gpu` 或 `-k on -sf kk`。  
6. 先 `-h` 与短 `in` 冒烟，再谈 MPI、GPU 与集群。  
7. 长时间生产放到集群；本机安装与自编译主要服务调试和复现。

---

## 学习路径

**前置阅读：**

- [Mac与Ubuntu开发环境配置](T19-Mac与Ubuntu开发环境配置.md)
- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)
- Windows：[WSL2安装与配置](T02-WSL2安装与配置.md)
- 自编译 / fork 管理：[Git简明使用教程](T04-Git简明使用教程.md)

**下一步：**

- [集群与SLURM简明教程](T10-集群与SLURM简明教程.md) —— 正式提交作业；自编 / GPU 引擎用绝对路径与模块  
- [科研项目目录结构规范](T15-科研项目目录结构规范.md) —— `lammps/` 放哪  
- [本地与集群文件传输](T09-本地与集群文件传输.md) —— 同步 `in`、自编 `bin` 与拉回 `log`  
- [分子动力学模拟概述](../00-知识文档/K02-分子动力学模拟概述.md) —— 概念侧巩固  
- [ASE结构构建入门](../01-技术文档/T23-ASE结构构建入门.md) —— 生成结构对接 Lammps  

官方手册：[docs.lammps.org](https://docs.lammps.org/) · [Build](https://docs.lammps.org/Build.html) · [Packages](https://docs.lammps.org/Packages.html) · [Build extras](https://docs.lammps.org/Build_extras.html) · [Modify](https://docs.lammps.org/Modify.html) · [GPU](https://docs.lammps.org/Speed_gpu.html) · [KOKKOS](https://docs.lammps.org/Speed_kokkos.html)
