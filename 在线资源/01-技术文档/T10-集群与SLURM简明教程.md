---
wp_post_id: 1342
id: T10
title: 集群与SLURM简明教程
wp_slug: 集群与slurm简明教程
series: 在线资源
tier: 技术文档
status: reviewed
topic: 集群
paywall: vip
erphpdown_blocks: 1
---
> **系列标签：** `技术文档` · `集群` · `HPC` · `SLURM`

学校超算、课题组服务器，算力不是谁抢到谁用——得通过**作业调度系统**排队。你写好脚本、`sbatch` 交上去，调度器在空闲的**计算节点**上帮你跑 Lammps；自己别在**登录节点**上硬跑一整天的模拟，轻则慢，重则账号被限。

本文讲集群是咋回事，并以国内最常见的 **SLURM** 为主（顺带提 **PBS/Torque**）。SSH、传文件、Remote SSH 请先看 [SSH密钥与config配置简明教程](T08-SSH密钥与config配置简明教程.md)、[本地与集群文件传输](T09-本地与集群文件传输.md)、[VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md)；终端命令不熟见 [Linux终端与Shell简明教程](T03-Linux终端与Shell简明教程.md)。

学完能带走：登录节点、计算节点、调度器各干什么，`sbatch` 怎么写、队列怎么查、作业日志去哪找——够你把 Lammps 正式交上去而不是在登录节点硬跑一整天。本机先冒烟装引擎见 [Lammps安装简明教程](T20-Lammps安装简明教程.md)；钥匙在 [SSH密钥与config配置简明教程](T08-SSH密钥与config配置简明教程.md)，倒文件在 [本地与集群文件传输](T09-本地与集群文件传输.md)，远程改 in 见 [VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md)；项目目录和 runlog 怎么记，跟 [科研项目目录结构规范](T15-科研项目目录结构规范.md) 一套看。

| 阶段 | 姊妹篇 |
|------|--------|
| 能 `ssh` 上集群 | [SSH密钥与config配置简明教程](T08-SSH密钥与config配置简明教程.md) |
| 上传输入、拉回 log | [本地与集群文件传输](T09-本地与集群文件传输.md) |
| 轨迹分析、出论文图 | [从模拟到论文图的工作流](T18-从模拟到论文图的工作流.md) |

![cluster](../../images/articles/技术文档/T10-集群与SLURM简明教程/web/T10-hero-cluster.webp)

---

[erphpdown]

## 一、集群是啥结构？三个角色

可以想成饭店：**登录节点是前台**，接单、改菜单；**调度器是排号系统**；**计算节点是后厨**，真正炒菜（跑模拟）。

```
你的电脑 ──SSH──► 登录节点 ──提交作业──► 调度器 ──分配──► 计算节点
                      │                                      │
                  传文件、改 in 文件                         跑 Lammps / Python
                  git、sbatch                                吃 CPU / 内存
```

| 角色 | 干什么 | 别干什么 |
|------|--------|----------|
| **登录节点** | SSH 上来、编辑、`git`、**`sbatch` 交作业** | 长时间 Lammps、大轨迹 Python、占满核的 Jupyter |
| **计算节点** | 模拟、重分析、交互式 Jupyter（要先申请到节点） | — |
| **调度器** | 排队、分你多少核、多少内存、能跑多久 | — |

各校规矩略有差别，**用户手册一定要翻一遍**；在登录节点跑重活，账号被限不是吓唬人。

---

## 二、连上集群之后

### 1. SSH 登录

密钥和 `~/.ssh/config` 别名见 [SSH密钥与config配置简明教程](T08-SSH密钥与config配置简明教程.md)。能上去再谈交作业：

```bash
ssh username@cluster.university.edu.cn
# 配好 config 后：ssh molcluster
```

### 2. 传文件（概要）

```bash
# 上传项目（rsync，别把大轨迹塞进去）
rsync -avh --progress --exclude 'data/raw/' ./ molcluster:~/project/

# 拉回 log
scp molcluster:~/project/log.lammps ./data/raw/
```

细节见 [本地与集群文件传输](T09-本地与集群文件传输.md)。

### 3. 远程改代码

本机 VSCode / Cursor 开 **Remote - SSH**，直接编辑集群上的 `~/project`，见 [VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md)。

### 4. SSH 断了，作业还在不在？

| 情况 | SSH 断了之后 |
|------|-------------|
| 已 `sbatch` / `qsub` 交出去的 Lammps | **还在跑**——调度器接管，关电脑、断 Wi‑Fi 都不影响 |
| 登录节点**前台**命令：`tail -f`、`mamba install`、正在等的交互 `srun` | **通常会停**——进程绑在你的 SSH 会话上 |

**规矩很简单：** 真正算力走 **`sbatch`**；需要长时间占着终端（盯日志、试命令、交互进计算节点）时，先开 **`tmux`** 或 **`screen`**：

```bash
tmux new -s md                 # 进「房间」
sbatch job.slurm               # 交单后可以 detach，作业照样跑
tail -f 12345.out              # 盯日志；要关电脑：Ctrl+b 再 d

# 下次 ssh 上来
tmux attach -t md              # 回到原来的窗口，tail 还在
```

多窗口：`tmux` 里 **Ctrl+b** 再按 **`c`** 开新窗口——一个盯 `squeue`，一个跑 `srun --pty bash` 试跑，一个 `git pull`，互不挡路。Remote SSH 终端里同样适用，见 [VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md) 第六节。

老集群只有 `screen` 时：`screen -S md` → 干活 → **Ctrl+a** 再 **`d`** detach → `screen -r md` 回来。

---

## 三、集群上的环境（Lammps + Python）

### 1. 用 module 加载 Lammps（常见）

很多集群不让你自己装 Lammps，而是管理员装好，你用 `module` 切换版本。本机调试装法见 [Lammps安装简明教程](T20-Lammps安装简明教程.md)。

```bash
module avail              # 看有哪些能 load
module load gcc/11.2.0
module load openmpi
module load lammps        # 名字因集群而异
```

### 2. Python 分析环境（myenv）

轨迹分析常用自装 Conda，和本地同一套 `myenv.yml`：

```bash
# 家目录装一次 Miniconda
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
~/miniconda3/bin/conda init bash
source ~/.bashrc
mamba env create -f myenv.yml
conda activate myenv
```

> **Tips：** 登录节点能否**访问外网**装包、家目录配额多大，各校不同——见 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md) 第七节，或问管理员。

---

## 四、SLURM：怎么交作业

国内多数高校超算用 **SLURM**。日常就记四个命令：

| 你想做的事 | 命令 |
|-----------|------|
| 交作业 | `sbatch job.slurm` |
| 看自己排队没 | `squeue -u $USER` |
| 取消 | `scancel JOBID` |
| 看分区忙不忙 | `sinfo` |

历史记录用 `sacct`（查以前跑过啥、用了多久）。

### 1. 批处理脚本示例（Lammps）

把资源需求写在脚本开头的 `#SBATCH` 行里，下面才是实际要跑的命令。保存为 `job.slurm`：

```bash
#!/bin/bash
#SBATCH --job-name=lammps_npt      # 作业名（自己认）
#SBATCH --partition=cpu             # 分区名——看手册，别瞎填
#SBATCH --nodes=1
#SBATCH --ntasks=16                 # MPI 进程数
#SBATCH --cpus-per-task=1
#SBATCH --time=24:00:00             # 最长能跑多久，超了会被杀
#SBATCH --output=%j.out             # 标准输出日志，%j=作业号
#SBATCH --error=%j.err

module load lammps                  # 按本集群实际改
cd $SLURM_SUBMIT_DIR                # 回到你 sbatch 时所在目录

mpirun -np $SLURM_NTASKS lmp -in in.npt
```

交上去：

```bash
sbatch job.slurm
```

看状态和日志：

```bash
squeue -u $USER
# STATE：PD=排队中，R=正在跑
tail -f 12345.out                   # 把 12345 换成你的 JOBID
```

### 2. 交互式节点（试跑 / Jupyter）

想先进**计算节点**里调试，再交大作业：

```bash
srun --partition=cpu --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=16G --time=02:00:00 --pty bash
```

提示符变了、hostname 不是登录节点名，说明进来了。可小规模试 `lmp` 或开 Jupyter：

> **Tips：** 交互 `srun` 可能一占就是几小时，且 SSH 断了 shell 就没了。建议 **先 `tmux new -s debug` 再 `srun`**，试完 **Ctrl+b d** detach；回来 `tmux attach -t debug`。批处理 `sbatch` 则不必包 tmux。

```bash
conda activate myenv
jupyter lab --no-browser --port=8888
```

本机**另开终端**做端口转发：

```bash
ssh -L 8888:localhost:8888 molcluster
```

浏览器打开 Jupyter 吐出的 `http://127.0.0.1:8888/lab?token=...`。更完整的远程 Jupyter 说明见 [VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md) 第七节。

> 有的集群提供网页版 Jupyter 或 `salloc`，以管理员文档为准。

### 3. 常用 `#SBATCH` 参数

| 参数 | 含义 |
|------|------|
| `--partition` | 队列/分区名（手册里查） |
| `--time=HH:MM:SS` | 最长运行时间，填短了跑到一半被杀 |
| `--mem=32G` | 要多少内存 |
| `--output` / `--error` | 日志写哪 |
| `--gres=gpu:1` | 要 GPU 时 |

### 4. 数组作业（扫一串温度等）

一次交 10 个相关任务，每个用不同参数：

```bash
#SBATCH --array=1-10
TEMP=$(awk -v i=$SLURM_ARRAY_TASK_ID 'NR==i+1 {print $1}' temps.txt)
lmp -in in.template -var T $TEMP
```

---

## 五、PBS / Torque（部分老集群）

少数集群用 PBS 系，**道理一样，命令换名字**：

| 你想做的事 | SLURM | PBS / Torque |
|-----------|-------|----------------|
| 交作业 | `sbatch script` | `qsub script` |
| 看队列 | `squeue` | `qstat -u $USER` |
| 取消 | `scancel ID` | `qdel ID` |
| 交互进计算节点 | `srun --pty bash` | `qsub -I` |

**PBS 脚本示例：**

```bash
#!/bin/bash
#PBS -N lammps_job
#PBS -q normal
#PBS -l nodes=1:ppn=16
#PBS -l walltime=24:00:00
#PBS -o job.out
#PBS -e job.err

cd $PBS_O_WORKDIR
module load lammps
mpirun -np 16 lmp -in in.npt
```

提交：`qsub job.pbs`

**我家集群是哪种？**

```bash
which sbatch    # 有输出 → SLURM
which qsub      # 有输出 → PBS 系
```

拿不准就看集群首页用户手册。

---

## 六、写作业脚本的几条经验

1. **在含 `in.npt` 的目录里 `sbatch`**——别在家目录交、路径却写子目录  
2. **脚本里 `cd $SLURM_SUBMIT_DIR`**（PBS 用 `$PBS_O_WORKDIR`），别写死绝对路径  
3. **`--time` 和 `--mem` 宁松勿紧**：太短被杀，太长可能排队更久  
4. **轨迹、log、SLURM 的 `.out` 分开存**，别全糊在一个文件里  
5. **先小规模试跑**（少核、短 time），通了再放大体系  

---

## 七、登录节点 vs 计算节点（再强调一次）

| 登录节点（前台）可以 | 计算节点（后厨）才行 |
|---------------------|---------------------|
| 改 `in` 文件、VSCode 编辑 | 长时间 `lmp -in` |
| 短编译 | 大轨迹 `MDAnalysis` |
| `git`、`scp`、`rsync` | `jupyter lab` 重计算 |
| **`sbatch` / `qsub` 交单** | `mpirun` 并行跑满核 |

---

## 八、串进 MolSimulX 整条链路

```
本地：写 in、管 Git、建模
    ↓ rsync / git pull（本地与集群文件传输）
集群：sbatch 跑 Lammps
    ↓ rsync 拉回轨迹，或在计算节点分析
本地 / Jupyter：MDAnalysis 画图（NumPy与Matplotlib简明教程）
```

环境见 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)；画图见 [NumPy与Matplotlib简明教程](T21-NumPy与Matplotlib简明教程.md)。

---

## 九、常见问题

### 1. 作业一直 PD（排队）

队列满了、要的核/内存太多、`--time` 超限、分区名写错。`squeue -j JOBID` 看 `Reason`（部分集群会写原因）。

### 2. 交上去马上失败（FAILED）

先看同目录下的 `*.out` 和 `*.err`——**完整内容复制去搜**。常见：路径错、没 `module load lammps`、`mpirun -np` 和 `#SBATCH --ntasks` 对不上。

### 3. 在登录节点跑 Python 被 kill

正常，管理员在护登录节点。改成 `sbatch`，或 `srun` 申请交互计算节点再跑。

### 4. 磁盘满了写不进去

`quota -s` 或问管理员；大轨迹放 scratch，定期归档删旧的（见 [数据管理与备份](T17-数据管理与备份.md)）。

### 5. SSH 断了，模拟还在跑吗？

- **`sbatch` 已交出去** → 在，用 `squeue` / `sacct` 查，`tail -f` 看 `.out`  
- **只在终端里前台跑的 `lmp` 或 `srun` shell** → 多半没了；下次用 `sbatch`，或进 `tmux` 再跑交互任务（见第二节第 4 小节）

---

## 十、小结

1. **登录节点只交单，计算节点才跑模拟**——前台 vs 后厨，别搞反。  
2. **SLURM 三板斧**：`sbatch` 交、`squeue` 看、`scancel` 撤；PBS 对应 `qsub` / `qstat` / `qdel`。  
3. 脚本里写清 **分区、核数、时间、内存、日志路径**；先小规模试跑。  
4. Jupyter、重分析要 **`srun` 进计算节点** 或交批处理作业，别占登录节点。  
5. **`sbatch` 不依赖 SSH**；盯日志、交互调试用 **`tmux`**，断线 `attach` 回来。  
6. 分区名、`module` 名、能否外网装包——**以本校手册为准**；`.err` 看不懂就整段复制去搜。

---

[/erphpdown]

## 学习路径

**前置阅读：**

- [SSH密钥与config配置简明教程](T08-SSH密钥与config配置简明教程.md) —— 登录集群前配置密钥与别名
- [Linux终端与Shell简明教程](T03-Linux终端与Shell简明教程.md) —— 基本命令
- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md) —— 第七节集群概述
- [VSCode与Cursor简明教程](T06-VSCode与Cursor简明教程.md) —— Remote SSH
- [VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md) —— 专题详解

**下一步：**

- [本地与集群文件传输](T09-本地与集群文件传输.md) —— 轨迹怎么来回搬
- [NumPy与Matplotlib简明教程](T21-NumPy与Matplotlib简明教程.md) —— 分析跑完的数据
- `02-实战案例` 目录下的端到端案例（陆续更新）
