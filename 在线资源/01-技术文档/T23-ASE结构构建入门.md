---
id: T23
title: ASE结构构建入门
series: 在线资源
tier: 技术文档
status: draft
topic: 结构建模
paywall: vip-partial
---
> **系列标签：** `技术文档` · `工具速成` · `结构建模` · `ASE` · `Lammps`

> **发布说明：** 部分 VIP 可见。WordPress 发布时自「二、」节起用 `[erphpdown]`（VIP 类型）包裹；「一、」与「学习路径」免费预览。

**ASE**（Atomic Simulation Environment）是 Python 中原子结构建模与格式转换的常用库：搭建晶体、分子、表面，导出 Lammps `data`、xyz，并与多种模拟代码衔接。`myenv` 已通过 pip 安装 ASE；本文介绍入门操作，作为模拟**前处理**与 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md) 中结构特征的数据源。

平台环境见 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)；轨迹分析见 [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md)。

---

## 一、ASE 能做什么？

| 任务 | ASE 模块 / 函数 |
|------|-----------------|
| 创建晶体、分子 | `bulk`、`molecule`、`fcc111` 等 |
| 读写结构文件 | `ase.io.read` / `write` |
| 扩胞、切面、叠加 | `repeat`、`surface`、`stack` |
| 导出 Lammps 输入 | `write_lammps_data`、与 `lammps` 命令联用 |
| 几何分析 | 距离、角度、化学式 |
| 对接 DFT/MD 计算器 | `atoms.calc = ...`（进阶） |

与 **Packmol**（混合体系填充，见平台搭建文档）配合：ASE 建骨架，Packmol 填溶剂。

---

[erphpdown]

## 二、环境与验证

```bash
conda activate myenv
python -c "import ase; print(ase.__version__)"
```

Jupyter 中：

```python
import ase
from ase import Atoms
from ase.io import read, write
from ase.build import bulk, molecule, fcc111, add_adsorbate
```

---

## 三、Atoms 对象

ASE 的核心是 **`Atoms`**：元素符号、坐标、晶胞（周期性）、边界条件。

```python
from ase import Atoms

# 单个 CO2 分子（内部坐标，无晶胞）
co2 = molecule("CO2")
print(co2.get_chemical_formula())
print(co2.positions)
print(co2.get_atomic_numbers())
```

| 属性 / 方法 | 含义 |
|-------------|------|
| `positions` | (N, 3) 坐标，单位 Å |
| `symbols` / `numbers` | 元素符号 / 原子序数 |
| `cell` | 3×3 晶胞矩阵 |
| `pbc` | 周期边界 [True, True, True] |
| `get_chemical_formula()` | 化学式 |

---

## 四、创建常见结构

### 1. 体相晶体

```python
from ase.build import bulk

cu = bulk("Cu", "fcc", a=3.6)          # 面心立方铜
si = bulk("Si", "diamond", a=5.43)
print(cu.cell.lengths())
```

### 2. 分子

```python
from ase.build import molecule

h2o = molecule("H2O")
ethanol = molecule("CH3CH2OH")
```

可用 `ase.collections.g2` 等内置分子库浏览名称。

### 3. 表面与吸附（示例）

```python
from ase.build import fcc111, add_adsorbate

slab = fcc111("Cu", size=(3, 3, 4), vacuum=10.0)   # 3×3 超胞，10 Å 真空
add_adsorbate(slab, "CO", height=1.8, position="hollow")
```

### 4. 扩胞

```python
big = cu.repeat((2, 2, 2))    # 2×2×2 超胞
```

---

## 五、读写文件

```python
from ase.io import read, write

# 写 xyz（易读，适合小体系）
write("structures/water.xyz", h2o)

# 读入
atoms = read("structures/water.xyz")

# 多帧 extended xyz / 部分格式支持轨迹
# frames = read("traj.xyz", index=":")
```

**Lammps data 文件：**

```python
write("structures/system.data", slab, format="lammps-data",
      specorder=["Cu", "C", "O"])   # 按力场 atom type 顺序
```

`specorder` 需与 Lammps `pair_coeff` 类型一致；复杂体系常需手动调整 type 或使用 `atom_style full` 的专用 writer。

| 格式 | 扩展名 | 用途 |
|------|--------|------|
| xyz | `.xyz` | 交换、可视化 |
| Lammps data | `.data` | Lammps 输入 |
| cif | `.cif` | 晶体 |
| pdb | `.pdb` | 生物大分子（粗） |

完整列表：`ase.io.formats`。

---

## 六、几何与分析

```python
from ase.geometry import get_distances

d = get_distances(p1, p2, cell=atoms.cell, pbc=atoms.pbc)
print("距离 (Å):", d[1][0][0])

# 化学式与质量
print(atoms.get_chemical_formula())
print(atoms.get_masses().sum())
```

构建 ML 特征时，常用：**组分、密度、键长分布、配位** 等，可从 `Atoms` 导出（见 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)）。

---

## 七、与 Lammps 工作流衔接

推荐目录（见 [科研项目目录结构规范](T15-科研项目目录结构规范.md)）：

```
structures/system.data    ← ASE 写出
lammps/in.minimize        ← 读 data，minimize
lammps/in.npt             ← 续跑
```

**in 文件片段示例：**

```lammps
units           real
atom_style      atomic
read_data       ../structures/system.data
pair_style      lj/cut 10.0
pair_coeff      1 1 0.2381 3.405
...
```

本地或集群测试：

```bash
cd lammps
lmp -in in.minimize
```

集群提交见 [集群与SLURM简明教程](T10-集群与SLURM简明教程.md)。

---

## 八、与 Packmol 配合（混合体系）

ASE 擅长**单分子/晶体**；多分子随机填充常用 **Packmol**（`myenv` 已装）：

1. ASE 写出各组分 xyz：`water.xyz`、`ion.xyz`  
2. 写 Packmol 输入，指定盒子与数目  
3. Packmol 输出 `packed.xyz`  
4. ASE `read` 后转 `system.data`

Packmol 专题可在后续 `技术文档` 单独成篇；平台搭建文档第五节有安装说明。

---

## 九、Notebook 完整小例子

```python
from ase.build import bulk, molecule
from ase.io import write

# 氩晶体 4×4×4（LJ 流体常用起点）
ar = bulk("Ar", cubic=True, a=5.26).repeat((4, 4, 4))
write("structures/ar_liquid.data", ar, format="lammps-data")

print(f"原子数: {len(ar)}")
print(f"盒子: {ar.cell.lengths()}")
```

在 Markdown 单元格记录：力场、密度、下一步 `in` 文件名（[Jupyter Notebook科研使用规范](T16-Jupyter Notebook科研使用规范.md)）。

---

## 十、常见问题

### 1. Lammps 读 data 报 atom type 错

检查 `specorder` 与 `pair_coeff` 类型编号；`atom_style` 与 data 格式匹配（`atomic` vs `full`）。

### 2. 分子没有晶胞

气相分子 `pbc=False`；放入盒子需手动设 `cell` 和 `center()`。

### 3. 坐标单位

ASE 默认 **Å**；Lammps `units real` 一致；`units metal` 为 Å、eV。

### 4. 与 MDAnalysis 分工

- **ASE**：建初始结构、转格式  
- **MDAnalysis**：读**轨迹**做后处理  

---

## 十一、小结

1. **Atoms** 是核心；`bulk` / `molecule` / `fcc111` 快速建模。  
2. **`write(..., format="lammps-data")`** 对接 Lammps。  
3. 结构文件放 `structures/`，与 `lammps/`、`data/raw/` 分工。  
4. 结构描述符可进入 ML 管线。

---

[/erphpdown]

## 学习路径

**前置阅读：**

- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)
- [NumPy与Matplotlib简明教程](T21-NumPy与Matplotlib简明教程.md)

**下一步：**

- [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md)
- [scikit-learn简明教程](T24-scikit-learn简明教程.md)
- [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)
- [集群与SLURM简明教程](T10-集群与SLURM简明教程.md)
