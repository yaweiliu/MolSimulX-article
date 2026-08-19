---
wp_post_id: 2526
id: T22
title: MDAnalysis轨迹分析入门
wp_slug: mdanalysis轨迹分析入门
series: 在线资源
tier: 技术文档
status: reviewed
topic: MD分析
paywall: free
---
> **系列标签：** `技术文档` · `工具速成` · `MD分析` · `MDAnalysis` · `轨迹`

**[MDAnalysis](https://www.mdanalysis.org/)**（常缩写 MDA）是 Python 里读、选、分析 **分子动力学轨迹** 的常用库。它不跑动力学，也不替代 VMD 那种交互看图软件：输入是「有哪些原子」的**拓扑**加上「坐标随时间变」的**轨迹**，合成一个 **Universe**，再用类似 VMD 的选择串取出原子组，算 RDF、RMSD、密度，或按帧写出子结构。LAMMPS、GROMACS、AMBER、NAMD 等引擎的常见格式它都能读。项目开源，文档在官网；MolSimulX 的 `myenv` 已预装。

和旁边工具的分工：**nglview / VMD 用来看**（转构象、出刊用图）；**MDAnalysis 用来批量、可编程、进 Notebook**。数组运算和出二维图仍用 [Python科学计算简明教程](T21-Python科学计算简明教程.md) 那一套；**搭结构默认走 [MDStudio](https://mdstudio.molsimulx.com)**，复杂几何再看 [ASE结构构建入门](T23-ASE结构构建入门.md)。概念地图见 [轨迹分析与宏观性质](../00-知识文档/K16-轨迹分析与宏观性质.md)。

本站主线是 LAMMPS：生产段往往写出一份 **data（拓扑）** 和一份 **dump（轨迹）**。本文把 **怎么读入这两份文件**，以及 **盒子中心 vs nglview 晶胞框** 写清楚。读文件、平移原点、按分子 wrap、截 nglview 图，实战案例资源包里的 `_helper_functions.py` 已经封装好，可以直接抄用。端到端例子见[计算扩散与粘度](../02-实战案例/C03-计算扩散与粘度.md)、[离子水合结构与lj1264力场](../02-实战案例/C07-离子水合结构与lj1264力场.md)。

![](../../images/articles/技术文档/T22-MDAnalysis轨迹分析入门/web/T22-hero-mda_logo.webp)

---

## 一、能做什么？

| 任务 | 入口 |
|------|------|
| 读拓扑 + 轨迹 | `MDAnalysis.Universe` |
| 选原子 | `u.select_atoms("...")` |
| 径向分布 $g(r)$ | `MDAnalysis.analysis.rdf.InterRDF` |
| 均方根偏差 RMSD | `MDAnalysis.analysis.rms.RMSD` |
| 逐帧 | `for ts in u.trajectory:` |
| 写出结构 / 子轨迹 | `AtomGroup.write(...)` |

**LAMMPS 用户先记住：**

1. 多数时候要同时给 **data** 和 **dump**。  
2. data 里常常是 **type 编号** 而不是元素名，选择串用 `type 1`；指定 `elements` 之后才能 `element Mg`。  
3. **id** 是 LAMMPS 原子号，**index** 是 MDA 从 0 起的下标，二者不必相同。  
4. 分析距离用**当前帧盒子**做周期边界（MIC）；dump 若写了 `xsu ysu zsu`（unwrap），分子不会被盒边折断，但 RDF 仍按 PBC 计。

---

## 二、核心概念

| 词 | 含义 |
|----|------|
| **Universe** | 拓扑 + 轨迹绑在一起的对象 |
| **AtomGroup** | 一组原子的视图（选择结果） |
| **Topology** | 原子 id、type、电荷、键、残基（LAMMPS 的 mol） |
| **Trajectory** | 各帧坐标 + 盒边（NPT 时盒会变） |
| **选择语言** | 类似 VMD 的字符串，如 `type 4`、`resid 1` |
| **MIC** | minimum-image convention：周期盒里取最短镜像距离 |
| **wrap / unwrap** | wrap = 折回当前盒；unwrap = 解开折叠后的连续坐标 |

---

## 三、怎么读入 LAMMPS 轨迹

### 1. 两份文件各管什么

| 文件 | 典型名字 | MDA 拿它干什么 |
|------|----------|----------------|
| **拓扑** | `data.lmp`、`result_atoms.eq.data` | 原子数、type、电荷、键、mol（resid） |
| **轨迹** | `result_atoms.lammpstrj`、`dump.lammpstrj` | 各帧坐标 + `ITEM: BOX BOUNDS` |

只给 dump、不给 data，往往没有电荷和键；只给 data、不 `load_new` dump，就只有一帧静态结构。

其它引擎对照：GROMACS 常用 `.gro` / `.tpr` + `.xtc`；AMBER 常用 `.prmtop` + `.nc`。下面只展开 LAMMPS。

### 2. `atom_style` 必须和 data 一致

MDStudio 写出的 `data.lmp` 一般是 `atom_style full`，Atoms 行是 **id mol type charge x y z**。MDA 读拓扑时写成：

```python
import MDAnalysis as mda

u = mda.Universe(
    "result_atoms.eq.data",
    atom_style="id resid type charge x y z",
)
```

这里的 `resid` 对应 LAMMPS 的 **mol**。`atomic` 只有 `id type x y z`，不要拿 `full` 的列去读。对不上时，轻则 type 错位，重则直接报错。

### 3. dump 字段：wrap 还是 unwrap

`in.lmp` 里常见：

```lammps
dump            1 all custom ${dump_every} result_atoms.lammpstrj id type xsu ysu zsu
dump_modify     1 sort id
```

| dump 列 | 含义 | 适合 |
|---------|------|------|
| `x y z` | 折在盒内的笛卡尔坐标 | 看密度、瞬时构型 |
| `xu yu zu` | **unwrap** 笛卡尔 | 扩散 MSD、分子取向 |
| `xs ys zs` | 折在盒内的约化坐标（约 $0\sim 1$） | 少用 |
| `xsu ysu zsu` | **unwrap 约化坐标** | 本站案例生产段的默认写法 |

本站案例生产段用 **`xsu ysu zsu`**：分子不会被盒边「剪断」，MSD 也不会被周期折回压平。MDA 的 `LAMMPSDUMP` 读入后得到笛卡尔坐标；RDF 仍用该帧 `ITEM: BOX BOUNDS` 做 PBC。

> **Tips：** dump 第一行附近应能看到 `ITEM: ATOMS id type xsu ysu zsu`（字段名以你写的为准）。列名和 `dump` 命令不一致时，MDA 可能把坐标读错。

### 4. 把 dump 挂到 Universe 上

推荐**两步**（拓扑与轨迹分开，方便设 `dt`）：

```python
u = mda.Universe(
    "result_atoms.eq.data",
    atom_style="id resid type charge x y z",
)
u.load_new(
    "result_atoms.lammpstrj",
    format="LAMMPSDUMP",
    timeunit="fs",
    dt=2000.0,   # dump 间隔 × timestep，单位 fs；本例 2000 步 × 1 fs
)
print(u.atoms.n_atoms, u.trajectory.n_frames, u.dimensions)
```

也可以一步写 `Universe(data, dump, atom_style=..., format="LAMMPSDUMP")`。`dt` 不对时，RMSD 的时间轴会错，RDF 一般仍能算（它按帧，不靠物理时间）。

### 5. type、元素名、残基名

```python
print(set(u.atoms.types))      # 常见：'1','2','3','4'
print(u.atoms.resids[:8])
```

LAMMPS 默认没有 `Mg`、`H2O` 这种名字。**元素**按 type 指定一份映射即可（长度必须等于原子数）：

```python
# type 编号 → 元素符号（按你的 data 改）
type_to_element = {1: "Mg", 2: "Cl", 3: "H", 4: "O"}
elements = [type_to_element[int(t)] for t in u.atoms.types]
u.add_TopologyAttr("elements", values=elements)
# 之后：u.select_atoms("element O")
```

残基名按 **mol / resid 升序** 赋（不是按原子）：

```python
u.add_TopologyAttr("resnames", values=["Mg"] * 2 + ["Cl"] * 4 + ["H2O"] * 800)
# 之后：u.select_atoms("resname H2O")
```

Masses 行尾若写了元素注释，案例资源包里的 `load_lammps_universe` 会自动补 `elements` 和 `resnames`，见 [Lammps机械控压](../02-实战案例/C02-Lammps机械控压.md)、[计算扩散与粘度](../02-实战案例/C03-计算扩散与粘度.md)、[离子水合结构与lj1264力场](../02-实战案例/C07-离子水合结构与lj1264力场.md) 的 `_helper_functions.py`。

无自己的轨迹时，可用测试包扫一眼 API（不必当分析数据）：

```python
# mamba install -c conda-forge MDAnalysisData   # 可选
from MDAnalysisData import ADK_equilibrium
u = ADK_equilibrium.adk_equilibrium()
```

---

## 四、原子选择：type、id、index

```python
print(u.atoms.types[:8])       # LAMMPS type：'1','2',...
print(u.atoms.ids[:8])         # LAMMPS atom id（data 第一列，通常从 1 起）
print(u.atoms.indices[:8])     # MDAnalysis 下标（从 0 起，按 Universe 里的顺序）
print(u.atoms.resids[:8])

ow = u.select_atoms("type 4")           # 未指定元素时用 type
ow = u.select_atoms("element O")        # 补过 elements 之后
ions = u.select_atoms("id 1 2")         # LAMMPS id
first10 = u.select_atoms("index 0:9")   # MDA 下标 0–9（含 9）
water = u.select_atoms("resid 7:806")   # 按 mol/resid（编号以你的 data 为准）
```

| 编号 | 是什么 | 选择串 | 什么时候用 |
|------|--------|--------|------------|
| **id** | 拓扑 / dump 里的 LAMMPS 原子号 | `id 12` | 和 `data.lmp`、dump 对照 |
| **index**（`atom.ix`） | Universe 里第几个原子，**从 0 起** | `index 0:9` | NumPy 切片、写 XYZ 行序、CONECT |

二者**不必相等**：id 可以不连续，dump 若未 `dump_modify sort id`，文件行序还可能和 id 对不齐。写文件、和 VMD 行号对齐时用 **index**（案例里 CONECT 用 `atom.ix + 1`），不要用 LAMMPS id 当行号。

选不到原子时，**先 print `types` / `ids` / `elements` / `resids`**，不要猜 `name O`。选择语法：[Selection Language](https://docs.mdanalysis.org/stable/documentation_pages/selections.html)。

---

## 五、盒子中心、wrap 与 nglview

这是 LAMMPS 轨迹在 Notebook 里最容易看错的地方。

### 1. 原点在盒心还是在角上

许多 LAMMPS 盒子写成 $x\in[-L_x/2,\,L_x/2]$，**原点在几何中心**，原子坐标也在 0 附近。MDAnalysis 的 `wrap` 和 nglview 的 `add_unitcell()` 却默认晶胞从 **$(0,0,0)$ 那个角** 画出边长 $L_x,L_y,L_z$ 的框。

结果：原子团在画面中间，晶胞框画在第一卦限——看起来分子「飞出盒子」。这是**显示坐标约定**问题，不是模拟跑飞了。

```text
LAMMPS 常见：          nglview 默认画框：
     ┌──────┐              ┌──────┐
     │  ·   │   原点在心    │      │  原点在角 (0,0,0)
     │ ·+·  │              │      │
     └──────┘              └──────┘
        原子在 0 附近         框在正方向，对不上
```

### 2. 显示用：先移到角上，再按分子 wrap

**另开一个 Universe** 做显示，不要改分析用的那份（扩散必须保持 unwrap）。

```python
from MDAnalysis import transformations as trans

def move_origin_to_corner(ts):
    ts.positions += ts.dimensions[:3] / 2
    return ts

u_view = mda.Universe(
    "result_atoms.eq.data",
    atom_style="id resid type charge x y z",
)
u_view.load_new("result_atoms.lammpstrj", format="LAMMPSDUMP")
u_view.trajectory.add_transformations(
    move_origin_to_corner,
    trans.wrap(u_view.atoms, compound="residues"),
)
```

顺序不要反：先把原点从盒心移到角（坐标 $+L/2$），`wrap` 才知道「主晶胞」是 $[0,L]$；再按 **residue（LAMMPS mol）** 整分子折回，避免一分子水被盒边拆成两截、licorice 画出穿盒长键。

案例里的函数名就是 `move_origin_to_corner` / `move_origin_to_center`，和上面同一句话。导出 XYZ 给 VMD 时，有的案例还会 `corner → wrap → center`，让盒子重新居中，见 [COF膜-水体系短程模拟与可视化](../02-实战案例/C06-COF膜-水体系短程模拟与可视化.md)。

### 3. nglview：扫一眼，不要当出版工具

```python
import nglview as nv

view = nv.show_mdanalysis(u_view)
view.clear_representations()
view.add_representation("licorice", selection="all")
view.add_unitcell()
view
```

| 限制 | 怎么办 |
|------|--------|
| **晶胞框不随 NPT 变** | nglview 不支持动态盒子；框只对照某一帧尺寸，验结构即可 |
| 截静帧 | 案例里的 `save_nglview_frame(view)` |
| 刊用级渲染 | [VMD安装与高端渲染简明教程](T26-VMD安装与高端渲染简明教程.md) |

`add_transformations` 会改这个 Universe 后续所有读取。**算 RDF / 扩散的 Universe 不要加这套显示变换**——再 `load_lammps_universe` 一次，或复制一份。

---

## 六、遍历帧（分析侧）

```python
import numpy as np

zs = []
for ts in u.trajectory[::10]:
    zs.append(ow.positions[:, 2].mean())
zs = np.asarray(zs)
```

分析距离用当前帧 `ts.dimensions` 做 MIC：`distance_array(..., box=ts.dimensions)`。不要为了「好看」在分析 Universe 上 wrap 掉 unwrap 轨迹。

---

## 七、径向分布与配位数

$g(r)$：距参考原子 $r$ 处，配体相对均匀体相的富集倍数。第一峰 ≈ IOD（离子–氧距离）；第一谷 $r_{\min}$ 作第一壳外缘。

$$
\mathrm{CN}(r_{\min})=4\pi\rho\int_0^{r_{\min}} r^2 g(r)\,dr
$$

$\rho$ 用**配体**（如 Ow）的平均数密度（NPT 应对各帧体积平均）。

```python
from MDAnalysis.analysis.rdf import InterRDF

g1 = u.select_atoms("type 1")
g2 = u.select_atoms("type 4")
rdf = InterRDF(g1, g2, nbins=200, range=(0.0, 10.0))
rdf.run(start=0, stop=None, step=1)

r = rdf.results.bins
g = rdf.results.rdf

vols = [ts.volume for ts in u.trajectory]
rho = len(g2) / float(np.mean(vols))
dr = float(r[1] - r[0])
cn = np.cumsum(4.0 * np.pi * rho * r**2 * g * dr)
```

长轨迹先 `step=` 稀疏试跑。双轴把 $g(r)$ 与 CN 画在一起便于对比离子，做法见 [Python科学计算简明教程](T21-Python科学计算简明教程.md) 与 [离子水合结构与lj1264力场](../02-实战案例/C07-离子水合结构与lj1264力场.md)。

---

## 八、RMSD（相对参考帧）

```python
from MDAnalysis.analysis import rms

R = rms.RMSD(u, u, select="not type 3", ref_frame=0)  # 例：去掉 Hw
R.run()
rmsd = R.results.rmsd          # 列：frame, time, RMSD, ...
```

时间单位取决于轨迹 `dt`；LAMMPS dump 间隔 × timestep 要自己设对（案例里 `dt_fs=`）。RMSD 突增常对应构象变化，可作后续聚类特征。

---

## 九、写出子结构

```python
from MDAnalysis.lib.distances import distance_array

box = u.trajectory[-1].dimensions
d = distance_array(ions.positions, ow.positions, box=box)
hit = np.where(d[0] <= 3.2)[0]
# 取整分子水再写 XYZ：按 Ow 的 resid 选，相对离子做 MIC
# 完整封装见离子水合案例资源包 `_extract_hydrated_ions.py`
```

`AtomGroup.write("frame.xyz")` 适合单帧；多帧且原子数变化时，不要硬塞进同一条 VMD 轨迹。按离子导出第一壳水的完整脚本见[离子水合结构与lj1264力场](../02-实战案例/C07-离子水合结构与lj1264力场.md) 资源包 `_extract_hydrated_ions.py`。

---

## 十、常见问题

**Q：`No module named 'MDAnalysis'`**  
A：`conda activate myenv` 后 `conda install -c conda-forge mdanalysis`。

**Q：选择串一个原子都没有**  
A：LAMMPS 默认是 type。`print(set(u.atoms.types))`。

**Q：nglview 里分子在晶胞框外面**  
A：坐标原点在盒心，框画在角上。显示 Universe 先 `move_origin_to_corner` 再 `wrap(..., compound="residues")`。案例 `_helper_functions.py` 可直接用。

**Q：RDF 第一峰位置离谱**  
A：单位（Å vs nm）、选错 type、未用当前盒 PBC、生产段未平衡。

**Q：内存爆**  
A：加大 `step`，或 `start/stop` 只分析一段；重活放计算节点（[集群与SLURM简明教程](T10-集群与SLURM简明教程.md)）。

**Q：和 SciPy 手积分的 CN 不一致**  
A：$\rho$、MIC、exclusion 不同。报论文以 `InterRDF` + 明确 $\rho$ 定义为准。

---

## 十一、小结

1. LAMMPS：**data 拓扑 + dump 轨迹**；`atom_style` 对上 data；生产段优先 `xsu ysu zsu`。  
2. 选择先看 `types` / `resids`，不要假设有元素名。  
3. **显示**把原点移到盒角再按分子 wrap；**分析**保持 unwrap，另开 Universe。  
4. nglview 晶胞框不随 NPT 更新；刊用图走 VMD。读入 / 平移 / 截图用案例里的 `_helper_functions.py`。

---

## 学习路径

**前置阅读：**

- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)
- [Python科学计算简明教程](T21-Python科学计算简明教程.md)
- [轨迹分析与宏观性质](../00-知识文档/K16-轨迹分析与宏观性质.md)
- 有本机引擎时：[Lammps安装简明教程](T20-Lammps安装简明教程.md)

**下一步：**

- [VMD安装与高端渲染简明教程](T26-VMD安装与高端渲染简明教程.md) —— 刊用级渲染（nglview 只扫一眼）
- [从模拟到论文图的工作流](T18-从模拟到论文图的工作流.md) —— 二维曲线进论文
- [计算扩散与粘度](../02-实战案例/C03-计算扩散与粘度.md)
- [离子水合结构与lj1264力场](../02-实战案例/C07-离子水合结构与lj1264力场.md)
- 搭结构默认走 [MDStudio](https://mdstudio.molsimulx.com)；复杂几何对照 [ASE结构构建入门](T23-ASE结构构建入门.md)
- 做 ML 特征时：[机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)、[scikit-learn简明教程](T31-scikit-learn简明教程.md)
