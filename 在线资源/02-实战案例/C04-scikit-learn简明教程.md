---
id: C04
title: scikit-learn简明教程
series: 在线资源
tier: 实战案例
status: draft
topic: ML与AI
paywall: vip-partial
---
> **系列标签：** `实战案例` · `ML与AI` · `sklearn` · `统计学习`

> **发布说明：** 部分 VIP 可见。WordPress 发布时自「二、」节起用 `[erphpdown]`（VIP 类型）包裹；「一、」与「学习路径」免费预览。

**scikit-learn**（sklearn）是 Python 里最常用的**经典机器学习库**：回归、分类、聚类、降维、模型选择与流水线，API 统一、文档成熟。在分子模拟中，常用它处理**从轨迹或结构提取的特征**（RDF 峰位、RMSD 统计量、描述符等），做相态分类、性质预测或构象聚类。

本文结合分子模拟场景介绍 sklearn 核心用法；环境使用 **`myenv-ml`**（见 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)）；特征来源见 [MDAnalysis轨迹分析入门](C02-MDAnalysis轨迹分析入门.md)、[ASE结构构建入门](C03-ASE结构构建入门.md)。

---

## 一、sklearn 在 MD 工作流中的位置

```
LAMMPS 轨迹 / ASE 结构
        ↓  MDAnalysis、ASE、RDKit（后续）
   特征矩阵 X，标签 y
        ↓  sklearn
   训练 / 预测 / 聚类
        ↓
   图、表格、models/*.pkl
```

| 任务 | 常用 sklearn 模块 |
|------|-------------------|
| 物性回归（沸点、溶解度等） | `LinearRegression`, `RandomForestRegressor` |
| 相态 / 构象分类 | `LogisticRegression`, `RandomForestClassifier` |
| 构象聚类 | `KMeans`, `DBSCAN` |
| 降维可视化 | `PCA`, `TSNE`（见后续专题） |
| 标准化与流水线 | `StandardScaler`, `Pipeline` |

---

[erphpdown]

## 二、环境准备

```bash
conda activate myenv-ml
python -c "import sklearn; print(sklearn.__version__)"
```

若仅在 `myenv` 中：

```bash
conda activate myenv
mamba install scikit-learn -y
```

Jupyter / VSCode 内核选 **Python (myenv-ml)**。

---

## 三、统一范式：fit / predict

几乎所有 sklearn 估计器都遵循：

```python
model.fit(X_train, y_train)      # 训练
y_pred = model.predict(X_test)   # 预测
score = model.score(X_test, y_test)  # 默认评价指标
```

| 符号 | 含义 | 形状示例 |
|------|------|----------|
| `X` | 特征矩阵 | `(n_samples, n_features)` |
| `y` | 标签（回归为浮点，分类为整数或字符串） | `(n_samples,)` |

**分子数据注意：** 一行样本通常对应**一个独立体系/一次模拟**，不要把同一轨迹的相邻帧既当训练又当测试（信息泄漏）。

---

## 四、示例数据：模拟「描述符 → 性质」

下面用**合成数据**演示流程（无需真实实验标签）。实际项目中 `X` 来自 `data/processed/features.csv`。

```python
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 200

# 假想特征：平均密度、RDF 第一峰位 (Å)、回转半径 (Å)
density = rng.uniform(0.8, 1.2, n)
rdf_peak = rng.uniform(2.7, 3.5, n)
rg = rng.uniform(10, 25, n)

X = np.column_stack([density, rdf_peak, rg])
feature_names = ["density", "rdf_peak_A", "Rg_A"]

# 假想标签：自洽扩散系数 log10(D)（与密度、Rg 人为相关 + 噪声）
y = -2.0 * density + 0.05 * rg + rng.normal(0, 0.15, n)

df = pd.DataFrame(X, columns=feature_names)
df["log10_D"] = y
df.head()
```

---

## 五、划分训练集与测试集

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)
```

分类任务可对 `stratify=y` 保持类别比例：

```python
# y_class = ...
# train_test_split(X, y_class, stratify=y_class, ...)
```

---

## 六、特征标准化

不同特征量纲差很多时（密度 vs 峰位），建议缩放：

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)   # 只用训练集统计量！
```

---

## 七、回归：预测扩散系数

```python
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# 线性基线
ridge = Ridge(alpha=1.0)
ridge.fit(X_train_s, y_train)
y_pred = ridge.predict(X_test_s)
print("Ridge  R²:", r2_score(y_test, y_pred))
print("Ridge  MAE:", mean_absolute_error(y_test, y_pred))

# 非线性：随机森林
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train_s, y_train)
y_pred_rf = rf.predict(X_test_s)
print("RF     R²:", r2_score(y_test, y_pred_rf))
```

**特征重要性**（树模型）：

```python
import pandas as pd
pd.Series(rf.feature_importances_, index=feature_names).sort_values(ascending=False)
```

出图见 [NumPy与Matplotlib简明教程](C01-NumPy与Matplotlib简明教程.md)。

---

## 八、分类：相态识别（合成示例）

假设用 RDF 峰高、峰位区分「液态 / 固态」：

```python
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

X_c, y_c = make_classification(
    n_samples=300, n_features=4, n_informative=3, n_redundant=0,
    random_state=0, class_names=["liquid", "solid"]
)
X_tr, X_te, y_tr, y_te = train_test_split(X_c, y_c, test_size=0.3, random_state=0, stratify=y_c)

sc = StandardScaler()
X_tr_s = sc.fit_transform(X_tr)
X_te_s = sc.transform(X_te)

clf = LogisticRegression(max_iter=1000)
clf.fit(X_tr_s, y_tr)
y_hat = clf.predict(X_te_s)
print(classification_report(y_te, y_hat, target_names=["liquid", "solid"]))
print(confusion_matrix(y_te, y_hat))
```

真实项目中，`y` 来自不同温度 MD 的人工标注或序参量阈值。

---

## 九、聚类：无标签探索构象

```python
from sklearn.cluster import KMeans

# X_conf: 每行一帧的序参量或降维后坐标，例如 (n_frames, 2)
rng = np.random.default_rng(0)
X_conf = np.vstack([
    rng.normal([0, 0], 0.5, (80, 2)),
    rng.normal([4, 4], 0.6, (70, 2)),
    rng.normal([-3, 3], 0.4, (50, 2)),
])

kmeans = KMeans(n_clusters=3, random_state=42, n_init="auto")
labels = kmeans.fit_predict(X_conf)

import matplotlib.pyplot as plt
plt.scatter(X_conf[:, 0], X_conf[:, 1], c=labels, cmap="tab10", s=15)
plt.xlabel("PC1"); plt.ylabel("PC2")
plt.title("KMeans on conformational features")
plt.show()
```

从轨迹构造 `X_conf` 的完整流程见后续「构象降维与聚类」教程。

---

## 十、交叉验证

比单次划分更稳：

```python
from sklearn.model_selection import cross_val_score

rf = RandomForestRegressor(n_estimators=50, random_state=42)
scores = cross_val_score(rf, scaler.fit_transform(X), y, cv=5, scoring="r2")
print("CV R²:", scores.mean(), "+/-", scores.std())
```

---

## 十一、Pipeline：避免泄漏

把缩放与模型绑在一起，防止不小心对全数据 `fit` 缩放：

```python
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ("scale", StandardScaler()),
    ("model", RandomForestRegressor(n_estimators=100, random_state=42)),
])
pipe.fit(X_train, y_train)
print("Test R²:", pipe.score(X_test, y_test))
```

---

## 十二、保存与加载模型

```python
import joblib

joblib.dump(pipe, "models/diffusion_rf.joblib")
# 同时保存 scaler 已含在 Pipeline 中

loaded = joblib.load("models/diffusion_rf.joblib")
loaded.predict(X_test[:3])
```

`models/` 目录见 [科研项目目录结构规范](T15-科研项目目录结构规范.md)；大模型用 Git LFS 或勿提交。

---

## 十三、与 MD 特征衔接（思路）

| 特征 | 提取方式 |
|------|----------|
| RDF 峰位/峰高 | [MDAnalysis](C02-MDAnalysis轨迹分析入门.md) `InterRDF` |
| RMSD 均值/方差 | `RMSD` 分析 |
| 回转半径 | `AtomGroup.radius_of_gyration()` |
| 元素计数、键长统计 | [ASE](C03-ASE结构构建入门.md) |
| 分子指纹 | RDKit（描述符教程，待写） |

将多条模拟结果汇总为一张 `features.csv`，每行 `sample_id` 唯一，再 `pd.read_csv` → `X, y`。

---

## 十四、常见问题

### 1. 测试集 R² 很差

样本太少、特征无信息量、或训练/测试分布不同（不同温度体系混用需分组划分）。

### 2. 分类 100% 准确率

检查是否泄漏（同一轨迹帧进训练和测试）；是否标签由特征直接算出。

### 3. `n_jobs=-1` 占满 CPU

笔记本上改 `n_jobs=2`；集群上可开大。

### 4. 与 PyTorch 如何选？

| sklearn | PyTorch |
|---------|---------|
| 表格特征、样本量中小 | 大数据、神经网络、GNN、ML 势 |
| 快速基线 | 需自定义损失与架构 |

见 [PyTorch简明教程](C05-PyTorch简明教程.md)。

---

## 十五、命令/API 速查

| 你想做的事 | 代码 |
|-----------|------|
| 划分数据 | `train_test_split` |
| 标准化 | `StandardScaler().fit_transform` |
| 回归 | `Ridge`, `RandomForestRegressor` |
| 分类 | `LogisticRegression`, `RandomForestClassifier` |
| 聚类 | `KMeans`, `DBSCAN` |
| 交叉验证 | `cross_val_score` |
| 流水线 | `Pipeline([...])` |
| 保存 | `joblib.dump` |

---

## 十六、小结

1. sklearn 适合**表格化分子特征**的回归、分类、聚类。  
2. 流程：**划分 → 缩放（仅 fit 训练集）→ fit → 评估**。  
3. 用 **Pipeline** 与 **交叉验证** 提高可靠性。  
4. 注意**按独立模拟/分子划分**，避免轨迹帧泄漏。

---

[/erphpdown]

## 学习路径

**前置阅读：**

- [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)（`myenv-ml`）
- [NumPy与Matplotlib简明教程](C01-NumPy与Matplotlib简明教程.md)
- [MDAnalysis轨迹分析入门](C02-MDAnalysis轨迹分析入门.md) 或 [ASE结构构建入门](C03-ASE结构构建入门.md)

**下一步：**

- [PyTorch简明教程](C05-PyTorch简明教程.md)
- 待写：构象降维与聚类、分子描述符与特征工程
- `实战案例` —— 性质预测 / 相态分类案例
