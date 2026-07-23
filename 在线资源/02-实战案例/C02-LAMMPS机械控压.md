---
wp_post_id: 1982
id: C02
title: Lammps机械控压
wp_slug: lammps机械控压
series: 在线资源
tier: 实战案例
status: reviewed
topic: 压力控制
paywall: download-vip
---

> **系列标签：** `实战案例` · `机械控压` · `界面体系` · `LAMMPS`

体相模拟里控压很省心：`fix npt` 挂上，盒子自己涨缩，压力就稳在你要的值。可一旦体系里有**界面**——水夹在两块固体板之间、液滴、气液共存、电极—电解液——压力就不再是一个均匀的数：界面区的法向、切向应力和体相差很多，界面附近的压力常常明显偏低。这时候你还用全局 barostat，它调的是整个盒子的平均维里压力，会连着固体板一起缩放，结果**体相区的压力根本不是你设的那个值**。

机械控压换个思路：不去缩放盒子，而是把其中一块板当成一个**刚性活塞**，给它施加恒定外力 $F=P\cdot A$，让它只沿垂直方向（z）自由滑动。活塞压着流体，流体在体相自然就维持在目标压力 $P$；另一块板固定不动当底座。这套办法在界面 / 受限体系里很常用（相关讨论见 [J. Chem. Phys. 2018, 148, 064706](https://doi.org/10.1063/1.5011106)）。

**本文讲**：在 LAMMPS 里怎么用 `aveforce` / `setforce` / `nve` 把一块墙做成活塞、给流体单独控温、并输出局部应力与密度剖面来验证控压是否奏效。

**前置**：手上已有一个「板—溶液—板」的 `data.lmp`（怎么搭见 [受限溶液建模](C01-受限溶液建模.md)；本例可直接用文末资源包里的约 2000 SPC/E 水 + 上下墙体系）；跑过基本的 LAMMPS 输入脚本。配套输入与分析 notebook 见文末资源包（站点 **VIP 免下载**）。

![活塞控压后的体系快照](../../images/articles/实战案例/C02-Lammps机械控压/web/C02-hero-last-frame.webp)

---

## 一、为什么界面体系不能用全局 barostat

全局 barostat（`fix npt` 的 `iso` / `aniso`）盯着整个盒子的**平均**压力，通过缩放盒子边长把它调到设定值。这在均匀体相里没问题，但界面体系有两个麻烦：

| 问题 | 后果 |
|------|------|
| 压力**空间不均匀** | 界面区应力和体相差很多，「整体平均 = 1 atm」不代表体相就是 1 atm |
| 盒子缩放会**连固体板一起动** | 板的晶格被拉伸 / 压缩，界面结构失真；板本该是刚性基质 |

机械控压绕开这两点：盒子尺寸不动，压力靠**活塞的力平衡**来定义——活塞受到的外力对应目标压力，它自己找到平衡高度，压在流体上的就是你要的 $P$。

---

## 二、体系与分组

直接读入文末资源包中的 `data.lmp`（与 [受限溶液建模](C01-受限溶液建模.md) 同一类板—水—板体系：约 2000 SPC/E 水 + 上下同质碳墙）。搭盒子时已把 **z 设为 100 Å**，活塞上下滑动的空间已经留好，本例**不必再** `change_box`。

本例约定（与 Packmol 装盒顺序一致）：

| 角色 | 如何识别 | 本例 |
|------|----------|------|
| **上墙 → 活塞** | `molecule 1` | 896 个 C，约在 $z\approx +40$ Å |
| **下墙 → 底座** | `molecule 2` | 896 个 C，约在 $z\approx -40$ Å |
| **流体** | `type 2 3`（H / O） | 2000 个 SPC/E 水 |

原子类型：

| type | 元素 | 角色 |
|------|------|------|
| 1 | C | 墙（上下共用同一 type，靠 molecule 区分） |
| 2 | H | 水氢 |
| 3 | O | 水氧 |

按角色分组：

```
group   upper   molecule  1          # 上板 → 活塞
group   lower   molecule  2          # 下板 → 底座（本脚本不积分 → 固定）
group   wall    molecule  1 2
group   fluid   type      2 3        # 水（H + O）
```

> **若你的 `data.lmp` 上下墙 type 本就不同**，也可 `group upper type 1`、`group lower type 2 …`，不必依赖 molecule。同质墙时务必用 molecule 或坐标 region 区分上下，不要只写 `group wall type 1` 然后整组当活塞。

---

## 三、固定底座、最小化

先**临时冻住两墙**做一次能量最小化，消除建模带来的原子重叠，再解冻、清零步数：

```
fix freeze wall setforce 0 0 0
minimize 0.0 1.0e-8 1000 100000
unfix freeze
reset_timestep 0
```

生产段里：**下板不挂任何 time-integration**（没有 `nve` / `nvt`），坐标会停在最小化后的位置，相当于固定底座。若你更想显式锁死，也可另加 `fix lower_freeze lower setforce 0 0 0`。

> 若手里的盒子沿 z 太矮、活塞顶到边界：带电体系请保持三向周期（PPPM 要求），用 `change_box all z delta 0 50 units box` 加高上端，而不是改成 `boundary p p s`。

---

## 四、机械控压的核心

思路：把目标压力换算成活塞每个原子该受的力，用 `aveforce` 均匀加到活塞上；`setforce` 锁死活塞的 x、y 分量（只让它沿 z 动）；活塞自己用 `nve` 积分，像个能上下滑的刚性盖子。

```
variable  mytemp   equal 300.0     # 流体目标温度 [K]
variable  mypress  equal 1.0       # 目标压力 [atm]

velocity  upper set 0 0 0 units box

variable  atm2Pa  equal 101325.0
variable  A2m     equal 1.0e-10
variable  Na      equal 6.022e23
variable  convert equal ${atm2Pa}*${A2m}*${A2m}*${A2m}*${Na}/4.184/1000

# 单个活塞原子受力 = -P * 面积 / 活塞原子数（负号 = 向下压流体）
variable  force   equal -${mypress}*${convert}*lx*ly/count(upper)

fix  aveforce  upper aveforce 0 0 ${force}
fix  setforce  upper setforce 0 0 NULL
fix  upper_nve upper nve
```

逐条看：

- **`force` 的物理含义**：压力 = 力 / 面积，所以活塞总受力 $=P\cdot(l_x l_y)$，再平摊到 `count(upper)` 个活塞原子上。`convert` 把 atm·Å² 换成 LAMMPS `real` 单位下的力（kcal/mol/Å）。
- **`aveforce`**：给整组活塞叠加一个总的 z 向外力（把设定总力均分），活塞作为一个整体被「压」着。
- **`setforce ... 0 0 NULL`**：把活塞的 x、y 合力清零（不左右漂）；z 写 `NULL` 表示**不覆盖**——保留 `aveforce` 的外力与原子间作用力。
- **`nve`**：活塞只做无热浴的牛顿积分；它的「温度」没有热力学意义，所以不给它挂热浴。

---

## 五、只给流体控温 + 刚性水约束

温度只对**流体**有意义（活塞是机械件、底座固定），所以热浴只挂在 `fluid` 上，并且用**流体自己的温度**反馈，避免把墙的动能算进去：

```
compute    fluid_temp fluid temp
variable   fluid_temp equal c_fluid_temp

fix        myshake all shake 0.0001 20 0 b 1   # SPC/E：约束 O–H（bond type 1）

fix        mynvt fluid nvt temp ${mytemp} ${mytemp} 1000
fix_modify mynvt temp fluid_temp              # 用流体温度驱动热浴，排除墙

velocity   fluid create ${mytemp} ${myrand} mom yes rot yes
```

`fix_modify ... temp fluid_temp` 是关键：不加的话 NVT 会用默认全体温度，把固定的墙也算进自由度，控温就偏了。

---

## 六、输出：热力学量 + 局部应力 / 密度剖面

除了常规热力学，额外盯两样东西：**活塞高度**（看它是否平衡）和**沿 z 的局部应力 / 密度剖面**（看体相压力到底是不是目标值）。

```
variable upper_cmz equal xcm(upper,z)

thermo_style custom step time v_fluid_temp atoms &
                        pxx pyy pzz lx ly lz v_upper_cmz
thermo_modify flush yes
thermo 1000
```

热力学表写进默认的 `log.lammps`（本例分析 notebook 用 `read_result_thermo("log.lammps")` 读最后一段生产 thermo）。跑起来后，温度与活塞高度通常很快平台化：

![温度与上墙高度随时间变化](../../images/articles/实战案例/C02-Lammps机械控压/web/C02-fig-temp-wall-height.webp)

局部应力用 `stress/atom` + 沿 z 分层（`chunk/atom bin/1d`）+ 时间累积平均（`ave/chunk`）：

```
compute mystress all stress/atom NULL
compute mybins   all chunk/atom bin/1d z center 0.1 units box discard yes
fix     stress_profile all ave/chunk 1000 100 100000 mybins &
        c_mystress[1] c_mystress[2] c_mystress[3] density/number &
        norm all ave running overwrite file result_profile_stress.log

run 1000000    # 1e6 步 × 1 fs = 1 ns
```

`result_profile_stress.log` 每一层给出 $\sigma_{xx}$、$\sigma_{yy}$、$\sigma_{zz}$ 与数密度；把三个法向分量取平均、乘密度换成压力，就得到沿 z 的**局部压力剖面**。本例体相数密度约 $33\,\mathrm{nm}^{-3}$（接近 SPC/E 常温常压体相），局部压强在体相段虽然波动很大，实际上在 1 atm 附近波动：

![沿 z 的数密度与局部压强](../../images/articles/实战案例/C02-Lammps机械控压/web/C02-fig-density-pressure.webp)

---

## 七、结果怎么看

跑完后主要看四条判据（用 [轨迹分析与宏观性质](../00-知识文档/K16-轨迹分析与宏观性质.md) 的思路，或直接跑资源包里的 `simul_analysis.ipynb`）：

| 看什么                  | 期望               | 说明                            |
| -------------------- | ---------------- | ----------------------------- |
| **活塞高度 `upper_cmz`** | 很快收敛到一个平台        | 活塞找到力平衡、体系达到稳态                |
| **流体温度**             | 稳定在 300 K        | 热浴 + `fix_modify` 生效          |
| **体相密度**             | ≈ 33 nm⁻³        | 接近 300 K、1 atm 下 SPC/E 水的体相密度 |
| **局部压力剖面**           | 体相段应在 ≈ 1 atm 附近 | 界面处会剧烈振荡（界面本就应力不均），看体相平段      |

其中「体相密度对上文献值」是最直接的成功判据：如果活塞压出来的水密度和已知 SPC/E 300 K / 1 atm 的体相密度吻合，就说明这套机械控压确实在体相维持住了目标压力。

---

## 常见问题

**Q：`aveforce` 和逐原子 `addforce` 有什么区别？**  
A：`addforce` 给每个原子都加同样大小的力；`aveforce` 是把设定的**总力**平摊给整组，并抵消组内力的不均，让活塞作为一个整体受一个净外力——正是我们要的「刚性盖子」效果。

**Q：为什么活塞用 `nve` 而不是 `nvt`？**  
A：活塞是机械部件，它的动能不代表热力学温度；给它挂热浴反而会往体系里塞 / 抽能量。让它 `nve` 自由响应流体的反作用力即可。

**Q：`setforce upper 0 0 NULL` 里的 `NULL` 是什么意思？**  
A：`setforce` 把指定方向的合力**设为该值**；写数字会覆盖掉所有力，写 `NULL` 表示这个方向不动（保留 `aveforce` 的外力 + 原子间作用力）。所以 x、y 设 0（活塞不横漂），z 设 `NULL`（活塞照常沿 z 受力运动）。

**Q：下板为什么不写 `fix setforce lower 0 0 0` 也能固定？**  
A：LAMMPS 里没有挂上 time-integration 的原子默认不更新坐标。本例只给 `upper` 挂了 `nve`、给 `fluid` 挂了 `nvt`，`lower` 自然停住。显式 `setforce` 冻结也可以，效果等价、可读性更强。

**Q：局部压力剖面为什么在界面处剧烈振荡？**  
A：界面附近分子分层排布，应力张量本来就随 z 强烈起伏，这是物理现象、不是 bug。判断控压是否成功要看**体相平段**是否回到目标压力，而不是界面尖峰。

**Q：可以用它控切向压力 / 做剪切吗？**  
A：本文只在法向（z）加压。切向控制或剪切需要另配（如给活塞设切向速度、或加剪切场），不在本文范围。

---

## 小结

- 界面 / 受限体系压力**空间不均匀**，全局 `fix npt` 会连固体板一起缩放、控不住体相压力。
- 机械控压把一块墙当**刚性活塞**：`aveforce` 加 $F=P\cdot l_x l_y/N_\text{piston}$ 的外力、`setforce ... 0 0 NULL` 锁横向只放 z、`nve` 让它自由滑动；另一块墙不积分（或显式冻结）当底座。
- 控温只挂 `fluid` 且用 `fix_modify ... temp fluid_temp`，把墙排除在温度统计外；刚性水用 `shake`。
- 用 `stress/atom` + `chunk/atom` + `ave/chunk` 输出**局部应力 / 密度剖面**；体相密度对上 SPC/E 文献值即验证控压成功。

---

## 资源下载

**资源包文件名：** `Lammps机械控压.zip`

包内是本例可复现跑通的输入、短样例输出与分析 notebook：

| 文件 | 说明 |
|------|------|
| `data.lmp` | 板—水—板初始构型 |
| `in.lmp` | 机械控压生产脚本（本例完整输入） |
| `log.lammps` | 样例热力学日志（含流体温度、活塞高度） |
| `result_profile_stress.log` | 沿 z 的应力 / 数密度剖面 |
| `result_atoms.data` / `result_atoms.lammpstrj` | 样例终态与短轨迹（分析可视化用） |
| `simul_analysis.ipynb` | 轨迹可视化 + 温度 / 活塞高度 / 密度—压力出图 |
| `_helper_functions.py` | notebook 依赖的读轨迹 / 读 thermo 辅助函数 |

本地请先按 [分子模拟工作平台搭建](../01-技术文档/T01-分子模拟工作平台搭建.md) 配好 `myenv`，再按 [Lammps安装简明教程](../01-技术文档/T20-Lammps安装简明教程.md) 能跑 LAMMPS。

---

## 前置阅读 / 下一步

- **上一篇（体系从哪来）**：[受限溶液建模](C01-受限溶液建模.md)
- 局部应力、压力张量与宏观量：[轨迹分析与宏观性质](../00-知识文档/K16-轨迹分析与宏观性质.md)
- 边界与初态：[边界条件与初始条件](../00-知识文档/K07-边界条件与初始条件.md)
- 控温控压概念：[常见系综与控温控压](../00-知识文档/K11-常见系综与控温控压.md)
- 结果作图与工作流：[从模拟到论文图的工作流](../01-技术文档/T18-从模拟到论文图的工作流.md)
