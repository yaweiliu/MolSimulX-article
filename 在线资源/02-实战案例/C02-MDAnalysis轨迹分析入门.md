---
id: C02
title: MDAnalysis轨迹分析入门
series: 在线资源
tier: 实战案例
status: draft
topic: MD分析
paywall: vip-partial
---
> **系列标签：** `实战案例` · `MD分析` · `MDAnalysis` · `轨迹`

> **发布说明：** 部分 VIP 可见。WordPress 发布时自「二、」节起用 `[erphpdown]`（VIP 类型）包裹；「一、」与「学习路径」免费预览。

**MDAnalysis** 是 Python 里常用的**分子动力学轨迹分析库**：读入 LAMMPS、GROMACS、AMBER 等格式轨迹，按原子选择、计算 RDF、RMSD、密度分布等。MolSimulX 的 `myenv` 已预装 MDAnalysis；本文介绍入门用法，为后续 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md) 中的特征提取打基础。

环境见 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)；绘图见 [NumPy与Matplotlib简明教程](C01-NumPy与Matplotlib简明教程.md)；Notebook 规范见 [Jupyter Notebook科研使用规范](T16-Jupyter Notebook科研使用规范.md)。

---

## 一、MDAnalysis 能做什么？

| 任务 | 典型函数 / 模块 |
|------|-----------------|
| 读取轨迹与拓扑 | `MDAnalysis.Universe` |
| 选择原子组 | `u.select_atoms("...")` |
| 径向分布函数 RDF | `RDF`（`MDAnalysis.analysis.rdf`） |
| 均方根偏差 RMSD | `RMSD` |
| 遍历轨迹帧 | `u.trajectory` |
| 写出子轨迹 / 结构 | `u.atoms.write()` |

与 **VMD**、**OVITO** 等可视化工具互补：MDAnalysis 适合**批量、可编程、进 Notebook** 的分析。

---

[erphpdown]

## 二、核心概念

| 概念 | 说明 |
|------|------|
| **Universe** | 拓扑（哪些原子）+ 轨迹（坐标随时间变化）的一体对象 |
| **AtomGroup** | 一组原子的视图，如「所有氧原子」 |
| **Topology** | 原子 ID、类型、键、残基等，常来自第一个数据/pdb 文件 |
| **Trajectory** | 时间序列坐标，如 dump、xtc、dcd |
| **选择语言** | 类似 VMD 的字符串，如 `name O`、`resname SOL` |

---

## 三、准备示例数据

### 已有 LAMMPS 轨迹时

确保有**拓扑文件**（如 `data` 或第一帧 `dump`）和**轨迹文件**：

```
structures/system.data      # 或 system.xyz
data/raw/traj.lammpstrj     # 或 .dcd / .xtc
```

### 快速自测（无轨迹时）

用 MDAnalysis 自带的测试文件（需安装 `MDAnalysisTests`）：

```python
import MDAnalysis as mda
from MDAnalysisData import ADK_equilibrium

# 若未装 MDAnalysisData：mamba install -c conda-forge MDAnalysisData
u = ADK_equilibrium.adk_equilibrium()
print(u)                    # 查看原子数、帧数
```

`myenv` 含 `MDAnalysisTests`；数据包可选 `mamba install -c conda-forge MDAnalysisData`。

---

## 四、加载 Universe

```python
import MDAnalysis as mda

# LAMMPS：拓扑 + 轨迹（路径按项目修改）
u = mda.Universe("structures/system.data", "data/raw/traj.lammpstrj")

# 仅单帧结构（无轨迹）
# u = mda.Universe("structures/system.xyz")

print(f"原子数: {u.atoms.n_atoms}")
print(f"帧数: {u.trajectory.n_frames}")
print(f"时间步范围: {u.trajectory[0].time} – {u.trajectory[-1].time}")
```

**格式提示：**

| 软件 | 常见扩展名 |
|------|------------|
| LAMMPS | `.data` + `.lammpstrj` / `.dcd` |
| GROMACS | `.gro` + `.xtc` / `.trr` |
| AMBER | `.prmtop` + `.nc` |

扩展名不明确时可传 `format=` 参数，见 [官方格式列表](https://docs.mdanalysis.org/stable/documentation_pages/coordinates/init.html)。

---

## 五、原子选择

```python
# 所有原子
all_atoms = u.atoms

# 按名称（LAMMPS type/name 取决于 data 文件）
ow = u.select_atoms("name O")      # 氧
hw = u.select_atoms("name H")

# 按类型（LAMMPS atom type）
type1 = u.select_atoms("type 1")

# 组合
water = u.select_atoms("name O or name H")
```

在 Notebook 里可先查看属性：

```python
print(u.atoms.names[:10])
print(u.atoms.types[:10])
```

选择串语法见 [Selection Language](https://docs.mdanalysis.org/stable/documentation_pages/selections.html)。

---

## 六、遍历轨迹

```python
import numpy as np

# 逐帧循环
for ts in u.trajectory[::10]:    # 每 10 帧取一帧
    coords = u.atoms.positions   # shape (n_atoms, 3)
    # 对 coords 做计算 ...

# 收集某一原子的 z 坐标随时间变化
zs = np.array([u.atoms.select_atoms("name O")[0].position[2]
               for _ in u.trajectory])
```

**注意：** 循环内改 `u.atoms.positions` 只影响当前帧内存；要写回磁盘需 `u.atoms.write(...)`。

---

## 七、示例：径向分布函数 RDF

```python
import MDAnalysis as mda
from MDAnalysis.analysis.rdf import InterRDF
import matplotlib.pyplot as plt

u = mda.Universe("structures/system.data", "data/raw/traj.lammpstrj")

# 两组原子，如 O-O
g1 = u.select_atoms("name O")
g2 = u.select_atoms("name O")

rdf = InterRDF(g1, g2, nbins=200, range=(0.0, 10.0))
rdf.run(start=0, stop=None, step=5)   # 每 5 帧算一次，省时间

plt.figure(figsize=(5, 4))
plt.plot(rdf.results.bins, rdf.results.rdf)
plt.xlabel(r"$r$ (Å)")
plt.ylabel(r"$g(r)$")
plt.xlim(0, 10)
plt.tight_layout()
plt.savefig("../figures/rdf_oo.pdf", bbox_inches="tight")
plt.show()
```

轨迹很长时务必 `step=` 稀疏采样；完整跑可提交集群脚本（见 [集群与SLURM简明教程](T10-集群与SLURM简明教程.md)）。

---

## 八、示例：RMSD（结构相对第一帧）

```python
from MDAnalysis.analysis import rms

ref = mda.Universe("structures/system.data", "data/raw/traj.lammpstrj")
ref.trajectory[0]    # 参考构型为第一帧

mobile = u.select_atoms("not name H")   # 常对重原子算 RMSD

R = rms.RMSD(u, ref, select="not name H", ref_frame=0)
R.run()

# R.results: 列 [frame, time, RMSD, RMSF...]
import matplotlib.pyplot as plt
plt.plot(R.results[:, 1], R.results[:, 2])
plt.xlabel("Time (ps)")
plt.ylabel("RMSD (Å)")
plt.show()
```

RMSD 突增常对应构象转变，可用于 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md) 中的**构象聚类**特征。

---

## 九、写出子结构

```python
# 写单帧 gro/xyz
protein = u.select_atoms("protein")
protein.write("data/processed/frame100.gro")

# 写子轨迹（需同名拓扑）
ow.write("data/processed/ow_traj.xtc", frames="all")
```

---

## 十、与 nglview 联动（可选）

```python
import nglview as nv
import MDAnalysis as mda

u = mda.Universe("structures/system.data", "data/raw/traj.lammpstrj")
# 取第一帧转 view（需 ase 或 mdanalysis converter）
view = nv.show_mdanalysis(u)
view
```

适合 Notebook 里快速目视检查；大批量统计仍用分析模块。

---

## 十一、常见问题

### 1. `No module named 'MDAnalysis'`

```bash
conda activate myenv
mamba install -c conda-forge MDAnalysis
```

### 2. 选择串选不到原子

`u.atoms.names` / `types` 与想象不一致；LAMMPS `data` 里常是 type 而非元素名，需 `select_atoms("type 1")` 或先在 LAMMPS 里设 `set type * name`。

### 3. 内存不足

对大体系 `step=` 加大间隔；用 `start/stop` 只分析一段；集群上跑（[VSCode与Cursor远程连接集群](T07-VSCode与Cursor远程连接集群.md)）。

### 4. 单位

LAMMPS `units real` 为 Å、fs；GROMACS 常为 nm、ps。作图轴标签与 ML 特征务必统一单位。

---

## 十二、通向机器学习

从轨迹提取的标量/向量可组成特征表，供 sklearn 等使用：

| 特征示例 | 来源 |
|----------|------|
| RDF 峰位、峰高 | `InterRDF` |
| 配位数 | RDF 积分或 `freud` |
| RMSD 时间序列统计量 | `RMSD` |
| 回转半径 | `gyration_radius` |

详见 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md) 阶段 2。

---

## 十三、小结

1. **Universe** = 拓扑 + 轨迹；**select_atoms** 选原子组。  
2. **Analysis 类**（`RDF`、`RMSD`）先 `.run()` 再读 `.results`。  
3. 长轨迹注意 **采样步长** 与单位。  
4. 结果是 ML 与论文图的常见输入。

---

[/erphpdown]

## 学习路径

**前置阅读：**

- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)
- [NumPy与Matplotlib简明教程](C01-NumPy与Matplotlib简明教程.md)
- [JupyterLab简明教程](T11-JupyterLab简明教程.md)

**下一步：**

- [ASE结构构建入门](C03-ASE结构构建入门.md)
- [scikit-learn简明教程](C04-scikit-learn简明教程.md)
- [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)
- `实战案例` —— 轨迹分析端到端案例（更新中）
