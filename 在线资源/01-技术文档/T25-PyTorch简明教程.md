---
id: T25
title: PyTorch简明教程
series: 在线资源
tier: 技术文档
status: draft
topic: ML与AI
paywall: vip-partial
---
> **系列标签：** `技术文档` · `工具速成` · `ML与AI` · `PyTorch` · `深度学习`

> **发布说明：** 部分 VIP 可见。WordPress 发布时自「二、」节起用 `[erphpdown]`（VIP 类型）包裹；「一、」与「学习路径」免费预览。

**PyTorch** 是 Python 主流的**深度学习框架**，支持 GPU 加速与自动求导。在分子模拟领域，它用于**神经网络势**、**图神经网络**（GNN）性质预测、以及将模拟数据拟合为复杂非线性映射等。经典表格 ML 请用 [scikit-learn简明教程](T24-scikit-learn简明教程.md)；本文介绍 PyTorch **最小必备**，便于后续 ML 势与 GNN 专题。

环境：**`myenv-ml`**（含 `torch`）；配置见 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)。

---

## 一、PyTorch 在分子模拟中的用途

| 方向 | 说明 |
|------|------|
| **拟合势能面 / 力** | 输入原子环境 → 能量、力（ML 势） |
| **GNN 性质预测** | 分子图 → 溶解度、形成能等 |
| **自定义损失** | 结合实验与模拟数据的联合训练 |
| **加速** | GPU + 集群（[集群与SLURM简明教程](T10-集群与SLURM简明教程.md)） |

入门先掌握：**Tensor、Dataset、nn.Module、训练循环**。

---

[erphpdown]

## 二、环境验证

```bash
conda activate myenv-ml
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

| 输出 | 含义 |
|------|------|
| `CUDA: False` | CPU 训练，小例子足够 |
| `CUDA: True` | 可用 GPU，`tensor.to('cuda')` |

GPU 版安装见 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md) 第二节。

---

## 三、Tensor 基础

PyTorch 的核心是 **Tensor**（类似 NumPy 数组，可放在 GPU、可求导）。

```python
import torch

x = torch.tensor([1.0, 2.0, 3.0])
A = torch.randn(3, 4)
b = torch.zeros(2, 2)

# 与 NumPy 互转
import numpy as np
arr = np.array([1., 2., 3.])
t = torch.from_numpy(arr)
back = t.numpy()

# 设备
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
x = x.to(device)
```

**常用运算：**

```python
y = torch.linspace(0.5, 3.0, 100)
z = y ** 2
mask = y > 1.5
z[mask].mean()
```

---

## 四、自动求导（为何用 PyTorch）

```python
x = torch.tensor(2.0, requires_grad=True)
y = x ** 3 + 2 * x
y.backward()
print(x.grad)   # dy/dx at x=2
```

神经网络通过反向传播更新参数；`loss.backward()` + `optimizer.step()` 即基于此。

---

## 五、示例：拟合 Lennard-Jones 势曲线

用神经网络拟合 1D 函数，对应「学习势能面」的极简版。

### 1. 生成数据

LJ 势（σ=1, ε=1）：

```python
import torch
import numpy as np
import matplotlib.pyplot as plt

r = torch.linspace(0.85, 3.0, 200).unsqueeze(1)   # shape (200, 1)
u = 4 * ((1/r)**12 - (1/r)**6)

# 加小噪声模拟「标签」
u = u + 0.02 * torch.randn_like(u)
```

### 2. Dataset 与 DataLoader

```python
from torch.utils.data import TensorDataset, DataLoader, random_split

dataset = TensorDataset(r, u)
n_train = int(0.8 * len(dataset))
n_test = len(dataset) - n_train
train_set, test_set = random_split(dataset, [n_train, n_test])

train_loader = DataLoader(train_set, batch_size=32, shuffle=True)
test_loader = DataLoader(test_set, batch_size=64)
```

### 3. 定义网络

```python
import torch.nn as nn

class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(1, 64),
            nn.Tanh(),
            nn.Linear(64, 64),
            nn.Tanh(),
            nn.Linear(64, 1),
        )

    def forward(self, x):
        return self.net(x)

model = MLP()
```

### 4. 训练循环（标准模板）

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()

epochs = 300
for epoch in range(epochs):
    model.train()
    total = 0.0
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        pred = model(xb)
        loss = loss_fn(pred, yb)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total += loss.item() * len(xb)
    if (epoch + 1) % 50 == 0:
        print(f"epoch {epoch+1}, train MSE: {total/n_train:.6f}")
```

### 5. 评估与作图

```python
model.eval()
with torch.no_grad():
    r_test = torch.linspace(0.85, 3.0, 200).unsqueeze(1).to(device)
    u_pred = model(r_test).cpu()

plt.figure(figsize=(5, 4))
plt.plot(r.numpy(), u.numpy(), "o", markersize=3, label="data")
plt.plot(r_test.cpu(), u_pred, "-", label="MLP fit")
plt.xlabel(r"$r$")
plt.ylabel(r"$U(r)$")
plt.legend()
plt.tight_layout()
plt.savefig("../figures/lj_mlp_fit.pdf", bbox_inches="tight")
plt.show()
```

---

## 六、保存与加载模型

**仅权重（推荐）：**

```python
torch.save(model.state_dict(), "models/lj_mlp.pt")

model2 = MLP()
model2.load_state_dict(torch.load("models/lj_mlp.pt", map_location="cpu"))
model2.eval()
```

**完整 checkpoint（含优化器，续训用）：**

```python
torch.save({
    "epoch": epoch,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "loss": loss.item(),
}, "models/checkpoint.pt")
```

---

## 七、训练循环模板（复制用）

```python
for epoch in range(num_epochs):
    model.train()
    for xb, yb in train_loader:
        xb, yb = xb.to(device), yb.to(device)
        pred = model(xb)
        loss = loss_fn(pred, yb)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        val_loss = 0.0
        for xb, yb in val_loader:
            xb, yb = xb.to(device), yb.to(device)
            val_loss += loss_fn(model(xb), yb).item() * len(xb)
    # 记录 val_loss / 早停等
```

[Jupyter Notebook科研使用规范](T16-Jupyter Notebook科研使用规范.md)：固定 `random_seed` 便于复现：

```python
torch.manual_seed(42)
np.random.seed(42)
```

---

## 八、与 sklearn 对比

| 维度 | sklearn | PyTorch |
|------|---------|---------|
| 数据 | NumPy 二维表 | Tensor，任意维度 |
| 模型 | 预置估计器 | 自定义 `nn.Module` |
| 训练 | `.fit()` | 手写循环 |
| GPU | 基本不用 | 常用 |
| 典型场景 | RDF 特征 + 随机森林 | ML 势、GNN |

许多工作流：**sklearn 做基线 → PyTorch 做深度模型**。

---

## 九、通向 ML 势与 GNN（预告）

| 进阶话题 | PyTorch 组件 |
|----------|--------------|
| 原子环境 → 能量 | 自定义 `forward`，力 = `-dE/dR` |
| 图神经网络 | PyG / DGL 的 `MessagePassing` |
| 批量结构 | `batch` 向量、`torch_geometric.data.Data` |
| 长训练 | 集群 GPU、`#SBATCH --gres=gpu:1` |

专题教程见 [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md) 路线图阶段 3–4。

---

## 十、常见问题

### 1. `loss` 不下降

学习率过大/过小；数据未归一化；网络太浅；标签单位错误。

### 2. `CUDA out of memory`

减小 `batch_size`；用 CPU 调试；集群申请更大显存 GPU。

### 3. `backward` 报错 graph retained

验证集用 `with torch.no_grad():`；不要对同一图多次 `backward` 不 `zero_grad`。

### 4. 与 NumPy 混用

注意 `requires_grad` 张量转 numpy 需 `.detach().cpu().numpy()`。

### 5. Apple Silicon (MPS)

```python
# device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
```

按 PyTorch 版本文档使用。

---

## 十一、API 速查

| 你想做的事 | 代码 |
|-----------|------|
| 创建 Tensor | `torch.tensor`, `torch.randn` |
| GPU | `.to(device)` |
| 数据集 | `TensorDataset`, `DataLoader` |
| 网络 | `class M(nn.Module)` + `nn.Linear` |
| 损失 | `nn.MSELoss()`, `nn.CrossEntropyLoss()` |
| 优化器 | `torch.optim.Adam(model.parameters(), lr=)` |
| 训练 | `loss.backward(); optimizer.step()` |
| 推理 | `model.eval(); torch.no_grad()` |
| 存权重 | `torch.save(model.state_dict(), path)` |

---

## 十二、小结

1. **Tensor + autograd** 是核心；**Dataset / DataLoader** 管数据.batch。  
2. **`nn.Module`** 定义模型；**训练循环** 四步：前向、损失、反向、`step`。  
3. 先用 **1D LJ 拟合** 练手，再进 ML 势 / GNN。  
4. 大训练用 **GPU + 集群**；小实验 CPU 即可。

---

[/erphpdown]

## 学习路径

**前置阅读：**

- [机器学习与分子模拟导引](T30-机器学习与分子模拟导引.md)
- [NumPy与Matplotlib简明教程](T21-NumPy与Matplotlib简明教程.md)
- [scikit-learn简明教程](T24-scikit-learn简明教程.md)（建议先读）

**下一步：**

- 待写：图神经网络入门、ML 势概念与工具概览
- [集群与SLURM简明教程](T10-集群与SLURM简明教程.md) —— GPU 作业
- `实战案例`
