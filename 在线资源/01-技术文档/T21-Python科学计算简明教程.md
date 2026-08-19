---
wp_post_id: 2524
id: T21
title: Python科学计算简明教程
wp_slug: python科学计算简明教程
series: 在线资源
tier: 技术文档
status: reviewed
topic: Python
paywall: free
---
> **系列标签：** `技术文档` · `工具速成` · `Python` · `NumPy` · `pandas` · `SciPy` · `绘图`

科学计算在 Python 里几乎都围着四套库转，合称 **SciPy 栈**（和同名的 SciPy 库不是一回事，SciPy 库只是其中一块）：

| 库 | 是什么 |
|----|--------|
| **[NumPy](https://numpy.org/)** | 多维数组（`ndarray`）和向量化运算的底座。后面三库都建立在它上面。 |
| **[pandas](https://pandas.pydata.org/)** | 带列名、带索引的表（`DataFrame`）。Excel / CSV / 实验记录那种「一行一个样本」用它，比纯数组好记。 |
| **[SciPy](https://scipy.org/)** | 在数组上的科学算法：插值、积分、FFT、优化、统计。不负责「数怎么存」，只负责「算一刀」。 |
| **[Matplotlib](https://matplotlib.org/)** | 二维绘图。论文里的折线、散点、误差棒、双轴，多半从这里出 PDF。 |

四库都是开源、文档成熟、科研默认依赖。[分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md) 的 `myenv` 已预装，Jupyter 里 `import numpy as np` 即可。本文不是四本官方文档的缩写，也不另开 Python 语言课；只讲**分子模拟后处理里什么时候用哪一个**，以及够用的写法。

LAMMPS 跑完，手里通常是三类东西：`log.lammps` 里一长串 thermo、自己写出的 `rdf.dat` / CSV，以及还没拆开的轨迹。前两类数字几乎都落在这套栈上：

| 库 | 分子模拟里什么时候用 | 典型文件 / 对象 |
|----|----------------------|-----------------|
| **NumPy** | 已经是「一列列数字」：RDF、MSD、直方图、坐标切片 | `rdf.dat`、`np.ndarray` |
| **pandas** | 有**列名**的表：thermo、多组对照、结果汇总 | `log.lammps`、`summary.csv` |
| **SciPy** | 在数组上调用算法：插值、积分配位数、VACF→谱、拟合 MSD | 已算好的 $g(r)$、$C(t)$ |
| **Matplotlib** | 二维出图：曲线、双轴、误差棒、投稿 PDF | `figures/*.pdf` |

连着用最常见：pandas / NumPy 把数备齐 → 必要时 SciPy 算一刀 → Matplotlib 出图。轨迹本身（周期边界、选原子、逐帧）不要用这四库硬扫，换 [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md)。**搭结构默认走 [MDStudio](https://mdstudio.molsimulx.com)**；复杂几何再读 [ASE结构构建入门](T23-ASE结构构建入门.md)。完整故事见 [计算扩散与粘度](../02-实战案例/C03-计算扩散与粘度.md)、[离子水合结构与lj1264力场](../02-实战案例/C07-离子水合结构与lj1264力场.md)。Jupyter 操作见 [JupyterLab简明教程](T11-JupyterLab简明教程.md)。

语法最低限度写在下面「〇」；已会写函数、读文件的人直接从第二节开始。

![](../../images/articles/技术文档/T21-Python科学计算简明教程/web/T21-hero-python.webp)

---

## 〇、Python 最低限度（可跳过）

```python
# 变量与容器
x = 1.0
names = ["Mg", "Cl", "Ow"]       # list：有序、可改
row = {"T": 298.0, "P": 1.0}     # dict：键值
T, P = row["T"], row["P"]

# 切片与推导
a = [0, 1, 2, 3, 4]
a[1:4]                           # [1, 2, 3]
squares = [i**2 for i in a if i > 0]

# 函数与 pathlib（路径别手拼字符串）
from pathlib import Path

def load_two_cols(path):
    path = Path(path)
    text = path.read_text()
    return text.splitlines()[:5]

# 脚本入口：python analysis.py
if __name__ == "__main__":
    print(Path("rdf.dat").exists())
```

| 习惯 | 说明 |
|------|------|
| Notebook vs `.py` | 探索用 Notebook；定稿的分析收成脚本（见 [Jupyter Notebook科研使用规范](T16-Jupyter Notebook科研使用规范.md)） |
| 别用 Python `for` 扫几百万个数 | 数字进 **NumPy 数组**再算 |
| 表有列名 | 用 **pandas**，不要 `data[:, 3]` 记列号 |
| 路径 | `Path("a") / "b.dat"`，跨 Windows / Linux 更稳 |

---

## 一、在 JupyterLab 中开始

```bash
conda activate myenv
jupyter lab
```

内核选 **Python (myenv)**。首格：

```python
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import interpolate, integrate, fft, optimize, stats

%matplotlib inline
# %matplotlib widget       # 交互图（需 ipympl，可选）

plt.rcParams.update({
    "font.size": 12,
    "axes.labelsize": 12,
    "figure.dpi": 120,
})
```

VSCode / Cursor 打开 `.ipynb` 等效，见 [VSCode与Cursor简明教程](T06-VSCode与Cursor简明教程.md)。

---

## 二、NumPy：数组是基本类型

**什么时候用：** 两列 `r, g(r)`、MSD 曲线、从 MDAnalysis 取出的 `positions`（`N×3`）、自己直方图的 bin。坐标还在轨迹文件里、还要考虑周期边界时，先 MDA，再把结果数组交给 NumPy。

### 1. 创建

```python
a = np.array([1.0, 2.0, 3.0])
b = np.zeros(100)
c = np.linspace(0, 10, 101)     # 含端点，均分
d = np.arange(0, 10, 0.1)       # 步长；注意浮点终点
e = np.random.default_rng(0).normal(size=1000)
```

科研里优先 `np.random.default_rng(seed)`，结果可复现。

### 2. 形状、广播、索引

```python
x = np.arange(12).reshape(3, 4)   # (3, 4)
x[:, 0]                           # 第 0 列
mask = x[:, 0] > 4
x[mask]

# 广播：r (N,) 与 (N, 1) 运算时核对形状
r = np.linspace(0.5, 12, 200)
u = 4 * ((1 / r) ** 12 - (1 / r) ** 6)   # LJ，σ=ε=1
```

### 3. 向量化（避免慢循环）

```python
# 差：for i in range(len(r)): u[i] = ...
# 好：整段数组一次算完（上一格）
```

### 4. 读纯数值文本

```python
data = np.loadtxt("rdf.dat", comments="#")
r, g = data[:, 0], data[:, 1]
```

缺列名、不规则分隔、混有非数字时改用 pandas。大轨迹不要 `loadtxt` 整文件进内存，用 [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md)。

---

## 三、pandas：带列名的表

**什么时候用：** `log.lammps` 的 Step / Temp / Press / Density、多温度对照表、`result_summary.csv`。列名比「第 3 列」可靠；和 Matplotlib 对接也更直接：`ax.plot(df["time_ps"], df["density"])`。

```python
df = pd.read_csv("result_summary.csv")
df.head()
df.columns
df["density"].mean()
df.loc[df["quantity"] == "T_prod", "value"]
```

从空白分隔的 thermo 块读（列名已知时）：

```python
thermo = pd.read_csv(
    "thermo.dat",
    sep=r"\s+",
    comment="#",
    names=["step", "temp", "press", "density"],
)
thermo["time_ps"] = thermo["step"] * 0.001   # 按你的 timestep 改
```

| 操作 | 写法 |
|------|------|
| 选列 | `df[["temp", "density"]]` |
| 条件行 | `df.query("temp > 290")` |
| 写回 | `df.to_csv("out.csv", index=False)` |
| 和 NumPy 互换 | `df["temp"].to_numpy()` / `pd.DataFrame({"r": r, "g": g})` |

**列名用小写、无空格**，后面脚本少踩坑。

> **Tips：** 整份 `log.lammps` 常有多段 thermo、中间夹 WARNING。不要一次 `read_csv` 整文件。实战案例资源包里的 `_helper_functions.read_result_thermo` 会按 `Step` 切块，例如 [离子水合结构与lj1264力场](../02-实战案例/C07-离子水合结构与lj1264力场.md)、[计算扩散与粘度](../02-实战案例/C03-计算扩散与粘度.md)。

---

## 四、SciPy：在数组上调用算法

**什么时候用：** 数已经在数组里，还要「算一刀」——稀疏 RDF 插值取值、把 $g(r)$ 积成配位数、VACF 做 FFT、指数拟合相关函数、线性拟合 MSD。周期边界、选原子、逐帧 MIC **不是** SciPy 的活。

NumPy 负责「数放哪、怎么切」；**积分、插值、FFT、拟合、统计**走 SciPy。

### 1. 插值（稀疏 RDF → 平滑取值）

```python
from scipy.interpolate import interp1d

f = interp1d(r, g, kind="cubic", fill_value="extrapolate")
g_at_2 = float(f(2.0))
```

### 2. 积分（配位数、相关函数面积）

```python
from scipy.integrate import cumulative_trapezoid

# CN(r) = 4πρ ∫ r² g(r) dr  的累积（ρ 用水氧数密度）
rho = 0.033  # 示例 Å⁻³，须用你体系的平均值
cn = cumulative_trapezoid(4 * np.pi * rho * r**2 * g, r, initial=0.0)
```

正式 RDF / CN 用 MDAnalysis 更稳（周期边界、排除），见 [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md)。SciPy 只处理「已经是 $g(r)$ 数组」的后处理。

### 3. FFT（速度自相关 → 振动谱，示意）

```python
from scipy.fft import rfft, rfftfreq

vacf = np.loadtxt("vacf.dat")[:, 1]
spec = np.abs(rfft(vacf))
freq = rfftfreq(vacf.size, d=0.002)   # d = 采样间隔（ps 等）
```

单位换算（cm⁻¹ 等）按你的 `timestep` 自己乘系数，不要抄示例数字进论文。

### 4. 拟合与统计

```python
from scipy.optimize import curve_fit
from scipy import stats

def exp_decay(t, a, tau):
    return a * np.exp(-t / tau)

popt, pcov = curve_fit(exp_decay, t, y, p0=(1.0, 10.0))
slope, intercept, r, p, se = stats.linregress(t, msd)
```

误差棒、块平均概念见 [统计误差与块平均](../00-知识文档/K17-统计误差与块平均.md)，不要只用 `std()` 当独立样本误差。

---

## 五、Matplotlib 基础图

**什么时候用：** 二维论文图和 Notebook 预览——$g(r)$、thermo、MSD、双轴 $g(r)$+CN。三维轨迹用 nglview / VMD，见 [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md) 与 [VMD安装与高端渲染简明教程](T26-VMD安装与高端渲染简明教程.md)。投稿流程见 [从模拟到论文图的工作流](T18-从模拟到论文图的工作流.md)。

### 1. 折线 / 散点 / 直方图

```python
fig, ax = plt.subplots(figsize=(5, 4))
ax.plot(r, g, lw=1.5, label=r"$g(r)$")
ax.scatter(r[::8], g[::8], s=12, alpha=0.6)
ax.set_xlabel(r"$r$ [Å]")
ax.set_ylabel(r"$g(r)$")
ax.set_xlim(0, 10)
ax.legend(frameon=False)
fig.tight_layout()
```

直方图：`ax.hist(x, bins=50, density=True, histtype="step")`。

### 2. 子图与双轴

```python
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
axes[0].plot(r, g)
axes[1].plot(r, cn)

# 左 g(r)、右 CN——离子对比常用
fig, ax = plt.subplots(figsize=(6.5, 3.6))
ax2 = ax.twinx()
ax.plot(r, g, color="C0")
ax2.plot(r, cn, color="C3", ls="--")
ax.set_ylabel(r"$g(r)$")
ax2.set_ylabel(r"CN$(r)$")
```

双轴示例见 [离子水合结构与lj1264力场](../02-实战案例/C07-离子水合结构与lj1264力场.md)。

### 3. 误差棒

```python
ax.errorbar(t, mean, yerr=sem, fmt="o-", capsize=3)
```

### 4. 保存 PDF 矢量图（投稿首选）

**PNG / JPG 是位图**：放大就糊。**PDF（以及 SVG、EPS）是矢量**：线与文字用几何描述，LaTeX / Illustrator 里放大仍清晰。分子模拟论文里的 $g(r)$、MSD、thermo 曲线，**交稿图优先存 PDF**；Notebook 里预览、网页插图再用 PNG。

```python
from pathlib import Path

fig_dir = Path("figures")
fig_dir.mkdir(exist_ok=True)

# 投稿：矢量 PDF（扩展名 .pdf 即可走矢量后端）
fig.savefig(
    fig_dir / "rdf.pdf",
    bbox_inches="tight",   # 裁掉多余白边，轴标签不易被切
    # transparent=True,    # 需要透明背景时再开
)

# 预览 / PPT：位图；dpi 决定清晰度
fig.savefig(fig_dir / "rdf.png", dpi=300, bbox_inches="tight")
```

| 参数 / 习惯 | 说明 |
|-------------|------|
| **扩展名 `.pdf`** | Matplotlib 按后缀选后端；写 `rdf.pdf` 就是矢量 PDF |
| **`bbox_inches="tight"`** | 按内容收紧画布，少切字、少大白边 |
| **`dpi=`** | 主要影响 **PNG/JPG**；PDF 里曲线本身是矢量，一般**不必**为 PDF 设很高 dpi |
| **`transparent=True`** | 背景透明，方便叠在幻灯上；期刊正文图通常不需要 |
| **同名两份** | 同一张图同时存 `.pdf`（投稿）+ `.png`（预览 / README）很常见 |

进 Overleaf 时用 `\includegraphics{figures/rdf.pdf}` 即可，见 [LaTeX与Overleaf简明教程](T14-LaTeX与Overleaf简明教程.md)。整条「分析 → 出图 → 排版」见 [从模拟到论文图的工作流](T18-从模拟到论文图的工作流.md)。

> **Tips：** 若期刊要求 **EPS**，可 `fig.savefig("rdf.eps", bbox_inches="tight")`；多数期刊接受 PDF。中文轴进 PDF 时要设好中文字体，否则可能缺字或方框——论文图尽量用英文轴标签。

---

## 六、科研绘图习惯

1. **轴标签用 LaTeX 数学**：`r"$g(r)$"`、`r"$T$ [K]"`。  
2. **色**：默认 `C0`–`C9`；色盲友好见 [ColorBrewer](https://colorbrewer2.org/)。  
3. **投稿图存 PDF（矢量）**；预览用 PNG `dpi=300`（见上一节）。  
4. **中文轴**：论文图尽量英文；必须中文时设 `font.sans-serif` 并 `axes.unicode_minus = False`。  
5. **Notebook 里少堆高清 `show()`**，`.ipynb` 会胀；Git 前提交前清输出（[Git简明使用教程](T04-Git简明使用教程.md)）。

## 七、完整示例：表 + 数组 → 图

模拟后处理的典型拼法：**pandas 读 thermo，NumPy 读 RDF，Matplotlib 两张图并排**。

```python
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 1) thermo 表
thermo = pd.read_csv("result_thermo.csv")   # 列：time_ps, density
print(thermo["density"].mean())

# 2) RDF 两列文本
rdf = np.loadtxt("rdf.dat", comments="#")
r, g = rdf[:, 0], rdf[:, 1]
ipeak = int(np.argmax(g[r < 4.0]))
r_peak = r[r < 4.0][ipeak]

fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.4))
axes[0].plot(thermo["time_ps"], thermo["density"], lw=1.0)
axes[0].set_xlabel(r"$t$ [ps]")
axes[0].set_ylabel(r"density [g\,cm$^{-3}$]")

axes[1].plot(r, g, lw=1.5)
axes[1].axvline(r_peak, color="0.4", ls=":", label=rf"peak {r_peak:.2f} Å")
axes[1].set_xlabel(r"$r$ [Å]")
axes[1].set_ylabel(r"$g(r)$")
axes[1].legend(frameon=False)
fig.tight_layout()
fig.savefig("thermo_rdf.pdf", bbox_inches="tight")
```

参数（力场、温度、截断）写在 **Markdown 单元格**，见 [Markdown简明教程](T12-Markdown简明教程.md)。

---

## 八、常见问题

**Q：`ModuleNotFoundError: numpy`**  
A：内核不是 `myenv`。终端 `which python` 应含 `envs/myenv`。

**Q：pandas 读 log 全乱**  
A：LAMMPS thermo 有多段、中间夹警告。用案例里的 `read_result_thermo` 切块，不要对整份 `log.lammps` 一次 `read_csv`。

**Q：SciPy 积分和 MDAnalysis 的 CN 差一截**  
A：RDF 的 $\rho$、是否 MIC、排除规则不同。报论文用轨迹库的定义，SciPy 只做「已是 $g(r)$ 数组」的后处理。

**Q：`%matplotlib inline` 无效**  
A：换 Kernel 后需重跑首格；VSCode 选对 Python (myenv)。

**Q：要不要学 xarray / seaborn？**  
A：表 + 二维图用本篇四件套足够。seaborn 是 Matplotlib 皮；多维标注网格再考虑 xarray。

---

## 九、命令速查

| 任务 | 入口 |
|------|------|
| 数组 | `np.linspace` / `np.loadtxt` / `arr.mean()` |
| 表 | `pd.read_csv` / `df["col"]` / `df.to_csv` |
| 插值 / 积分 / FFT | `scipy.interpolate` / `integrate` / `fft` |
| 折线 | `ax.plot(x, y)` |
| 双轴 | `ax.twinx()` |
| 矢量 PDF | `fig.savefig("f.pdf", bbox_inches="tight")` |
| 预览 PNG | `fig.savefig("f.png", dpi=300, bbox_inches="tight")` |

---

## 十、小结

1. **NumPy** 管数组，**pandas** 管带列名的表，**SciPy** 管插值 / 积分 / FFT / 拟合，**Matplotlib** 管二维图。  
2. 轨迹与周期边界不要手写三重循环，接 [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md)。  
3. 投稿图：**LaTeX 轴标签 + PDF 矢量**（`savefig(..., bbox_inches="tight")`）；预览另存 PNG。  
4. 不必再读一本 Python 语法书才能开始；数字工作从数组和表入手。

---

## 学习路径

**前置阅读：**

- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md)
- [JupyterLab简明教程](T11-JupyterLab简明教程.md)
- [Conda与Mamba简明教程](T05-Conda与Mamba简明教程.md)

**下一步：**

- [MDAnalysis轨迹分析入门](T22-MDAnalysis轨迹分析入门.md) —— 读轨迹、算 RDF
- [MDStudio](https://mdstudio.molsimulx.com) —— 搭结构默认入口（[Quickstart](../../在线工具/00-MDStudio/M01-Quickstart从画分子到测试模拟.md)）
- [ASE结构构建入门](T23-ASE结构构建入门.md) —— 仅复杂几何时本机脚本
- [从模拟到论文图的工作流](T18-从模拟到论文图的工作流.md) —— 二维图进论文
- [VMD安装与高端渲染简明教程](T26-VMD安装与高端渲染简明教程.md) —— 三维刊用图
- 做 ML 时再读 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)、[scikit-learn简明教程](T31-scikit-learn简明教程.md)
