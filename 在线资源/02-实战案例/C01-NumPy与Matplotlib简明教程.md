---
id: C01
title: NumPy与Matplotlib简明教程
series: 在线资源
tier: 实战案例
status: draft
topic: Python
paywall: none
---
> **系列标签：** `实战案例` · `Python` · `绘图`

**NumPy** 提供多维数组与向量化运算，是 Python 科学计算的基石；**Matplotlib** 是最常用的二维绘图库。分子模拟后处理中，径向分布函数、势能曲线、时间关联等数据都需「算得快、图画得清」。

本文结合 **JupyterLab** 交互环境，介绍 NumPy / Matplotlib 的科研常用写法与发表级出图要点。环境请先按 [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md) 配置 `myenv`；Jupyter 操作见 [JupyterLab简明教程](T11-JupyterLab简明教程.md)。

---

## 一、在 JupyterLab 中开始

```bash
conda activate myenv
jupyter lab
```

新建 Notebook，内核选 **Python (myenv)**。首格通常：

```python
import numpy as np
import matplotlib.pyplot as plt

%matplotlib inline          # 图嵌在 Notebook 输出中
# %matplotlib widget       # 交互图（需 ipympl，可选）

plt.rcParams.update({
    "font.size": 12,
    "axes.labelsize": 12,
    "figure.dpi": 120,
})
```

VSCode / Cursor 中打开 `.ipynb` 等效，见 [VSCode与Cursor简明教程](T06-VSCode与Cursor简明教程.md)。

---

## 二、NumPy 核心：数组

### 1. 创建数组

```python
a = np.array([1, 2, 3])
b = np.zeros(100)              # 100 个 0
c = np.linspace(0, 10, 101)    # 0~10 均分 101 点
d = np.arange(0, 10, 0.1)      # 步长 0.1
e = np.random.randn(1000)      # 标准正态随机数
```

### 2. 形状与重塑

```python
x = np.arange(12)
x.shape                    # (12,)
y = x.reshape(3, 4)        # 3 行 4 列
z = y.flatten()            # 拉平
```

### 3. 向量化（避免 Python 慢循环）

```python
r = np.linspace(0.5, 15, 500)
# LJ 势（σ=1, ε=1）
u = 4 * ((1/r)**12 - (1/r)**6)

# 条件筛选
mask = r > 2.0
r_far = r[mask]
```

### 4. 统计与聚合

```python
data = np.random.randn(10000)
data.mean(), data.std(), np.percentile(data, [5, 95])
```

### 5. 读取文本数据（模拟输出常用）

```python
# 假设两列：r, g(r)
data = np.loadtxt("rdf.dat", comments="#")
r = data[:, 0]
g_r = data[:, 1]
```

`np.genfromtxt` 可处理缺失值；大文件考虑 `pandas` 或 `MDAnalysis`（后续教程）。

---

## 三、Matplotlib 基础图

### 1. 折线图

```python
plt.figure(figsize=(5, 4))
plt.plot(r, g_r, label=r"$g(r)$", color="C0", linewidth=1.5)
plt.xlabel(r"$r$ (Å)")
plt.ylabel(r"$g(r)$")
plt.xlim(0, 15)
plt.ylim(0, 3)
plt.legend()
plt.tight_layout()
plt.show()
```

### 2. 散点图

```python
plt.scatter(r[::5], g_r[::5], s=10, alpha=0.7)
```

### 3. 直方图（能量分布等）

```python
energies = np.random.randn(50000) * 10 + -1000
plt.hist(energies, bins=50, density=True, alpha=0.7, edgecolor="k")
plt.xlabel("Potential energy (kcal/mol)")
plt.ylabel("Probability density")
```

### 4. 子图 layout

```python
fig, axes = plt.subplots(1, 2, figsize=(10, 4))

axes[0].plot(r, u)
axes[0].set_title("LJ potential")
axes[0].set_xlabel(r"$r$")

axes[1].plot(r, g_r)
axes[1].set_title(r"$g(r)$")
axes[1].set_xlabel(r"$r$ (Å)")

plt.tight_layout()
plt.show()
```

---

## 四、科研绘图习惯

### 1. 数学标签

轴标签用 LaTeX：`r"$g(r)$"`、`r"$\sigma$ (nm)"`。

### 2. 颜色与线型

```python
plt.plot(x, y1, "o-", label="NPT 300 K", color="C0")
plt.plot(x, y2, "s--", label="NPT 350 K", color="C1")
```

`C0`~`C9` 为默认色序；色盲友好可考虑 [colorbrewer](https://colorbrewer2.org/)。

### 3. 误差棒

```python
yerr = np.std(blocks, axis=0)   # 分块统计示例
plt.errorbar(t, mean_val, yerr=yerr, capsize=3, fmt="o-")
```

### 4. 保存图片（投稿用）

```python
fig.savefig("rdf.pdf", bbox_inches="tight")     # 矢量，推荐
fig.savefig("rdf.png", dpi=300, bbox_inches="tight")  # 预览
```

PDF 插入 [LaTeX与Overleaf简明教程](T14-LaTeX与Overleaf简明教程.md) 中的论文。

### 5. 不要在 Notebook 里堆超大图

大量高分辨率 `plt.show()` 会撑大 `.ipynb`；发表用图 `savefig` 后可在 Git 提交前清空输出（见 [Git简明使用教程](T04-Git简明使用教程.md)）。

---

## 五、完整示例：从数据到图

假设 `rdf.dat` 含两列 `r`、`g(r)`：

```python
import numpy as np
import matplotlib.pyplot as plt

%matplotlib inline

data = np.loadtxt("rdf.dat", comments="#")
r, g = data[:, 0], data[:, 1]

# 找第一峰位置
ipeak = np.argmax(g[r < 4])   # 简化：仅在 r<4 内找
r_peak = r[r < 4][ipeak]

fig, ax = plt.subplots(figsize=(5, 4))
ax.plot(r, g, lw=1.5)
ax.axvline(r_peak, color="gray", ls=":", label=rf"1st peak $\approx$ {r_peak:.2f} Å")
ax.set_xlabel(r"$r$ (Å)")
ax.set_ylabel(r"$g(r)$")
ax.set_xlim(0, 10)
ax.legend()
fig.savefig("rdf_example.pdf", bbox_inches="tight")
plt.show()
```

可在上方加 **Markdown 单元格** 记录力场、温度（见 [Markdown简明教程](T12-Markdown简明教程.md)）。

---

## 六、与 Pandas 衔接（可选）

时间序列、多列 log 可用 Pandas 再交给 Matplotlib：

```python
import pandas as pd

df = pd.read_csv("thermo.csv")   # step, temp, press, pe, ...
plt.plot(df["step"], df["pe"])
plt.xlabel("Step")
plt.ylabel("Potential energy")
```

`myenv` 已含 pandas（见平台搭建文档）。

---

## 七、常见问题

### 1. 中文坐标轴乱码

科研图建议**全英文标注**；若必须中文：

```python
plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
```

### 2. 图太小看不清

创建时指定 `figsize=(6, 4)` 或更大；保存用 `dpi=300`。

### 3. 修改图后不更新

Notebook 中重新运行定义数据的单元格；或 `plt.close("all")` 后重画。

### 4. `%matplotlib inline` 无效

检查 Jupyter 内核是否为 `myenv`；VSCode 中选对 Kernel。

---

## 八、命令/API 速查

| 任务 | 代码 |
|------|------|
| 等间距数组 | `np.linspace(a, b, n)` |
| 读文本 | `np.loadtxt(path)` |
| 折线图 | `plt.plot(x, y)` |
| 标签 | `plt.xlabel()`, `plt.ylabel()` |
| 图例 | `plt.legend()` |
| 子图 | `fig, ax = plt.subplots(nrows, ncols)` |
| 保存 | `fig.savefig("f.pdf", bbox_inches="tight")` |

---

## 九、小结

1. **NumPy** 做向量化计算；**Matplotlib** 做可视化。  
2. 在 Jupyter 中用 `%matplotlib inline` 边算边看。  
3. 轴标签用 LaTeX 格式；存 **PDF** 矢量图供论文使用。  
4. 模拟数据用 `loadtxt` / Pandas 读入，配合 Markdown 单元格记录参数。

---

## 学习路径

**前置阅读：**

- [分子模拟工作平台搭建](T01-分子模拟工作平台搭建.md) —— 安装 myenv
- [JupyterLab简明教程](T11-JupyterLab简明教程.md)
- [Conda与Mamba简明教程](T05-Conda与Mamba简明教程.md)

**下一步：**

- [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)
- [scikit-learn简明教程](C04-scikit-learn简明教程.md)
- [PyTorch简明教程](C05-PyTorch简明教程.md)
- [ASE结构构建入门](C03-ASE结构构建入门.md)
- [LaTeX与Overleaf简明教程](T14-LaTeX与Overleaf简明教程.md)
