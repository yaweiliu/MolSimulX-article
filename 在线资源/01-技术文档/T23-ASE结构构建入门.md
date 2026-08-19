---
wp_post_id: 2528
id: T23
title: ASE结构构建入门
wp_slug: ase结构构建入门
series: 在线资源
tier: 技术文档
status: reviewed
topic: 结构建模
paywall: free
---
> **系列标签：** `技术文档` · `工具速成` · `结构建模` · `ASE` · `MDStudio`

本站**搭结构的默认入口是 [MDStudio](https://mdstudio.molsimulx.com)**，不是 ASE：

| 你要什么 | 先走哪 |
|----------|--------|
| 画孤立分子、仓库取水 / 离子、力场、Packmol 装盒 | [MDStudio](https://mdstudio.molsimulx.com)（[Quickstart](../../在线工具/00-MDStudio/M01-Quickstart从画分子到测试模拟.md)、[孤立分子](../../在线工具/00-MDStudio/M06-MDStudio孤立分子.md)、[分子仓库](../../在线工具/00-MDStudio/M08-MDStudio分子仓库.md)、[力场生成](../../在线工具/00-MDStudio/M09-MDStudio力场生成.md)、[搭建盒子](../../在线工具/00-MDStudio/M11-MDStudio搭建盒子.md)） |
| 规整晶体、低指数表面、纳米管、石墨烯带、团簇 | [MDStudio周期分子](../../在线工具/00-MDStudio/M07-MDStudio周期分子.md)（底层已调 ASE，浏览器填表即可） |
| 台阶 / 空位 / 异质界面 / 不规则吸附，或 COF·MOF·GO 等填表做不出的几何 | **本机**用本文 ASE，或其它专业构建器 / 数据库 → 导出 cif/xyz → 再回 MDStudio 做力场与装盒 |

**[ASE](https://wiki.fysik.dtu.dk/ase/)**（Atomic Simulation Environment）是用 Python 操作原子结构的开源库：核心是 **`Atoms`**（元素、坐标、可选晶胞与周期性），可读写 xyz / cif、改几何，也可接 DFT 计算器。`myenv` 已安装。它**不是**动力学引擎，也**不负责** SPC/E 那种带键角、电荷、SHAKE 的全原子力场拓扑。

本文只讲：**MDStudio 够用时别先开 ASE**；复杂场景才在本地写脚本（或别的专业工具），把结构导出后再接回 MDStudio。计算器、NEB、振动不讲。轨迹后处理见 [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md)；数组与出图见 [Python科学计算简明教程](T21-Python科学计算简明教程.md)。环境见 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)。

![](../../images/articles/技术文档/T23-ASE结构构建入门/web/T23-hero-ase256.webp)

---

## 一、先 MDStudio，再 ASE（认分工）

| 工具 | 什么时候用 | 别硬用 |
|------|------------|--------|
| **MDStudio（默认）** | 日常建模：分子、晶体模板、力场、装盒、写出 `data.lmp` | — |
| **MDStudio 周期分子** | fcc / 表面 / 管 / 带 / 团簇等**规整**周期结构 | COF、GO、任意重构表面（暂请本地生成再上传） |
| **ASE（本机脚本）** | 填表做不到的可编程几何：缺陷、异质结、自定义超胞、参数扫描 | 整盒电解质、`atom_style full` 拓扑 |
| **其它专业工具** | 材料数据库 CIF、专用 COF/MOF 构建器等 | 能在 MDStudio 闭环的事不必绕开 |
| **MDAnalysis** | **轨迹**后处理 | 建初始盒子 |

ASE 模块对照（本文只用前两行写细）：

| 模块 | 典型用途 | 本篇 |
|------|----------|------|
| **`ase.build` / 改 `Atoms`** | 切面、删原子、拼界面、扩胞 | **复杂建模** |
| **`ase.io`** | 写 xyz / cif 给 MDStudio | 导出 |
| **`ase.geometry`** | 距离、体积 | 点到为止 |
| **计算器 / NEB / 振动** | DFT、过渡态 | 不讲 |

推荐工作流：

```text
多数课题
        → MDStudio（画分子 / 周期分子 / 仓库）
                ↓ 力场生成 → 搭建盒子 → data.lmp
复杂非均质 / 专用材料
        → 本机 ASE 或其它专业工具 → .cif / .xyz
                ↓ 上传 MDStudio
        → 力场生成 → 搭建盒子 → data.lmp
                ↓
        LAMMPS → dump → MDAnalysis
```

---

## 二、环境与 `Atoms`

```bash
conda activate myenv
python -c "import ase; print(ase.__version__)"
```

```python
from ase import Atoms
from ase.io import read, write
from ase.build import bulk, molecule, fcc111, add_adsorbate, surface
```

ASE 的核心是 **`Atoms`**：元素、笛卡尔坐标（Å）、可选 **cell**（3×3，Å）和 **pbc**（是否周期）。

```python
co2 = molecule("CO2")
print(co2.get_chemical_formula(), co2.positions.shape)
print(co2.cell, co2.pbc)     # 气相分子常常没有真正的周期盒
```

| 属性 / 方法 | 含义 |
|-------------|------|
| `positions` | `(N, 3)` 坐标，Å |
| `symbols` / `numbers` | 元素 / 原子序 |
| `cell` | 晶胞矩阵 |
| `pbc` | `[True, True, True]` 一类 |
| `get_chemical_formula()` | 化学式 |
| `center()` | 把质心移到盒中（须先有 cell） |
| `wrap()` | 把坐标折进当前晶胞 |
| `repeat((nx, ny, nz))` | 扩胞 |
| `extend(other)` / `+=` | 把另一份 `Atoms` 拼进来（异质结构常用） |
| `del atoms[i]` | 删原子（空位） |

气相分子要放进盒子：先 `atoms.cell = [Lx, Ly, Lz]`、`atoms.pbc = True`，再 `center()`。

---

## 三、规整模板：优先周期分子（不必先写 ASE）

下面这些，ASE 官方教程里都有，**[MDStudio周期分子](../../在线工具/00-MDStudio/M07-MDStudio周期分子.md) 已经做成填表**——日常请直接在浏览器里生成 `.cif`，不要默认先开 Notebook：

| 类别 | ASE 入口（了解即可） | 在 MDStudio |
|------|----------------------|-------------|
| 体相 Cu / Si / NaCl | `bulk("Cu", "fcc", a=3.61, cubic=True)` | 主体晶体 |
| 低指数面 | `fcc111` / `bcc110` / `miller` | 表面 |
| MoS₂ 等 | `mx2` | MX2 |
| 碳管、石墨烯带 | `nanotube`、`graphene_nanoribbon` | 纳米管 / 石墨烯带 |
| 纳米颗粒 | `cluster` | 团簇 |

界面里选类别、填 `a`、层数、真空、扩胞，预览后保存 `{name}.cif`，可一键接力场生成。参数含义以 [MDStudio周期分子](../../在线工具/00-MDStudio/M07-MDStudio周期分子.md) 为准，不必在本机再抄一套 `bulk` / `fcc111`。

若只是想在 Notebook 里看一眼 API，最小例子：

```python
cu = bulk("Cu", "fcc", a=3.61, cubic=True)
print(cu.cell.lengths(), len(cu))
write("cu_bulk.cif", cu)
```

水分子、二氧化碳这类**孤立分子**用 `molecule("H2O")` 可以，但溶液体系更稳的是从 [MDStudio分子仓库](../../在线工具/00-MDStudio/M08-MDStudio分子仓库.md) 取带力场的模板，而不是 ASE 随手造一颗水再指望自动长出 SPC/E 拓扑。

---

## 四、复杂几何：本机 ASE（或其它专业工具）

周期分子覆盖的是**规整模板**。下面这些，界面填表填不出来，再考虑本机 ASE，或材料数据库 / 专用 COF·MOF 构建器：

- 台阶 / 扭折面、缺原子的表面；  
- 两种材料拼在一起的界面（金属上石墨烯、氧化物上金属岛）；  
- 指定格点上的吸附花样，而不是「面上随便加一个 CO」；  
- 从 CIF 数据库读入后再扩胞、切斜面、挖孔。

思路都一样：**先得到一份带晶胞的 `Atoms`，改几何，写出 cif/xyz，上传工作区。**

### 1. 切面后再动手改

`fcc111` 仍可当起点——和周期分子同一套生成器——然后删原子、加吸附、拼第二层。

```python
from ase.build import fcc111, add_adsorbate
from ase.io import write

slab = fcc111("Cu", size=(4, 4, 5), vacuum=12.0, orthogonal=True)
# 表面空位：删掉最后一个原子（以你体系为准，先 print 坐标再决定下标）
del slab[-1]
add_adsorbate(slab, "O", height=1.2, position="fcc")
slab.center(axis=2)          # 真空仍沿 z 时，把 slab 摆回盒中
write("cu111_vac_O.cif", slab)
```

任意 Miller 面用 `surface(bulk_atoms, (h, k, l), layers, vacuum=...)`。切完后一样可以 `del`、`extend`、`repeat`。

### 2. 两份结构拼成异质界面

```python
from ase.build import fcc111, graphene_nanoribbon
from ase.io import write

metal = fcc111("Cu", size=(6, 6, 4), vacuum=8.0, orthogonal=True)
# 石墨烯带：先生成，再平移到金属上方（数值按晶格匹配自己调）
ribbon = graphene_nanoribbon(6, 6, type="armchair", vacuum=1.0)
ribbon.positions += [0.0, 0.0, metal.positions[:, 2].max() + 3.2]

hetero = metal.copy()
hetero.extend(ribbon)
# 必要时统一 cell / pbc，检查是否重叠
write("cu_graphene.xyz", hetero)
write("cu_graphene.cif", hetero)
```

晶格失配时不要硬塞：先各自 `repeat` 到接近公倍超胞，或接受应变并在文中写明。这正是「必须写代码」的原因——没有一张表能穷尽所有错配。

### 3. 从已有 CIF 改

```python
atoms = read("downloaded.cif")
atoms = atoms.repeat((2, 2, 1))
# 再切、再删、再吸附……
write("modified.cif", atoms)
```

COF / MOF / 氧化石墨烯这类拓扑复杂的周期材料，周期分子 Tab **暂不生成**；本地用专用构建器或数据库得到 `.cif` 后上传，后续力场 / 装盒与下面相同。

---

## 五、导出：交给 MDStudio 的是结构，不是力场

```python
write("structures/slab.xyz", slab)
write("structures/slab.cif", slab)
atoms = read("structures/slab.cif")
```

| 格式 | 用途 | 注意 |
|------|------|------|
| `.cif` | 晶体、slab、上传后接力场生成 | 带晶胞；力场生成认这个 |
| `.xyz` | 交换、VMD / 预览；力场生成也可读（须能写上晶胞注释） | **无**力场 type、电荷、键 |

> **溶液和全原子力场不要在 ASE 里收尾。** 结构用 cif / xyz 进 [MDStudio力场生成](../../在线工具/00-MDStudio/M09-MDStudio力场生成.md)，再进 [MDStudio搭建盒子](../../在线工具/00-MDStudio/M11-MDStudio搭建盒子.md) ①②③，由那边写出 `data.lmp`。

导出之后在 MDStudio 里：

1. 资源管理器上传 `*.cif` / `*.xyz`；  
2. **力场生成**得到 `{name}_ff.xyz` 与 `{name}.ff`；  
3. **搭建盒子**把它当一个物种，按个数与溶剂 / 离子一起 Packmol，写出 `data.lmp`。

墙 + 水这类受限溶液：规整墙可用 [MDStudio周期分子](../../在线工具/00-MDStudio/M07-MDStudio周期分子.md)；台阶 / 缺陷墙再本机 ASE。水与装盒不要用 ASE 手填——见 [受限溶液建模](../02-实战案例/C01-受限溶液建模.md)。

多帧：`read("traj.xyz", index=":")` 得到列表；轨迹分析仍优先 [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md)。

---

## 六、几何（点到为止）

```python
print(slab.get_volume(), len(slab) / slab.get_volume())  # 数密度 Å⁻³
# MIC 距离：atoms.get_distances(i, j, mic=True)
```

密度换成 g·cm⁻³ 需乘摩尔质量；报论文时写清。结构描述符（组分、配位）可接到 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)。计算器、结构优化、NEB 请查 [ASE 文档](https://wiki.fysik.dtu.dk/ase/)，本站主线是经典 MD。

---

## 七、Notebook 小例子（写出 cif，交给 MDStudio）

```python
from ase.build import bulk
from ase.io import write

ar = bulk("Ar", cubic=True, a=5.26).repeat((4, 4, 4))
ar.center()
write("structures/ar.cif", ar)
print(len(ar), ar.cell.lengths())
```

下一步：上传工作区 → [MDStudio力场生成](../../在线工具/00-MDStudio/M09-MDStudio力场生成.md) → [MDStudio搭建盒子](../../在线工具/00-MDStudio/M11-MDStudio搭建盒子.md)。

---

## 八、常见问题

**Q：分子飞出盒子 / 键被拉断（显示）**  
A：气相没设 cell；或显示未 wrap。分析距离用 MIC；显示用 wrap。轨迹侧见 [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md)。

**Q：ASE 和周期分子重复了？**  
A：不重复。规整模板默认用周期分子；ASE 只留给填表做不到的几何，以及需要循环扫参数（真空、层数、覆盖度）的时候。其它专业构建器 / 数据库同理：本地出 cif → 回 MDStudio。

**Q：单位**  
A：ASE 默认 Å。LAMMPS `units real` 与之一致；`metal` 仍是 Å、能量为 eV。

---

## 九、小结

1. **搭结构默认走 [MDStudio](https://mdstudio.molsimulx.com)**；规整晶体走周期分子，溶液走力场生成 + 搭建盒子。  
2. **ASE（或其它专业工具）**留给填表做不到的复杂几何；本篇核心是 **`Atoms` + 导出 cif/xyz**。  
3. 导出后仍回 MDStudio 做力场与装盒；不要在 ASE 里收尾写 `data.lmp`。  
4. 轨迹分析换 [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md)。

---

## 学习路径

**前置阅读：**

- [Quickstart：从画分子到测试模拟](../../在线工具/00-MDStudio/M01-Quickstart从画分子到测试模拟.md)（默认建模路径）
- [MDStudio周期分子](../../在线工具/00-MDStudio/M07-MDStudio周期分子.md)
- [MDStudio搭建盒子](../../在线工具/00-MDStudio/M11-MDStudio搭建盒子.md)（做溶液时）
- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)
- [Python科学计算简明教程](T21-Python科学计算简明教程.md)

**下一步：**

- [Lammps安装简明教程](T20-Lammps安装简明教程.md) —— 本机跑起来
- [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md) —— 有轨迹后再分析
- [受限溶液建模](../02-实战案例/C01-受限溶液建模.md)
- [VMD安装与高端渲染简明教程](T26-VMD安装与高端渲染简明教程.md) —— 看结构 / 出渲染图
- 做 ML 描述符时再读 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)
