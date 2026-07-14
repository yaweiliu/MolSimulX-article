---
id: M05
title: 力场转换（LigParGen / 外部力场）
series: 在线工具
tier: MDStudio
status: draft
topic: MDStudio
paywall: free
---
> **系列标签：** `MDStudio` · `LigParGen` · `力场转换`

已经在 LigParGen（或同类工具）上拿到了 OPLS-AA 的 `.gro`/`.pdb` + `.itp`，却卡在「怎么塞进 MDStudio 装盒」——**力场转换** Tab 就是为这个配对口。

本文讲：准备哪些文件、点哪里、产物名是什么、配对失败怎么查。限额见 [MDStudio 使用须知与限制](M02-MDStudio使用须知与限制.md)；装进盒子见 [搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md)；整条配方见 [配方：LigParGen 外部力场进盒子](M17-配方LigParGen进盒子.md)。**不讲** LigParGen 网站怎么注册、OPLS 参数推导。

<!-- 配图待补：文首 hero / 文中操作截图 -->

---

## 一、目标与前提

| 项 | 说明 |
|----|------|
| **目标** | 把外部力场坐标 + topology 转成工作区可用的 `*.xyz` + `*.ff` |
| **前提** | 本地已有**成对**的结构文件（`.gro` 或 `.pdb`）与 `.itp`；建议 VIP 已开通（见须知） |
| **本 Tab 最易踩** | 只上传其中一个，或 gro 与 itp 不是同一分子版本 |

---

## 二、操作步骤

1. 左侧工作区**上传**结构与 `.itp`（文件名尽量清晰，如 `ligand.gro` + `ligand.itp`）。
2. 打开 **力场转换** Tab。
3. 按界面选择成对文件（或勾选配对）。
4. 提交转换，等待任务完成。
5. 刷新工作区，确认出现坐标与 `.ff`。

---

## 三、产物一览

| 产物（举例） | 用途 |
|--------------|------|
| `*.xyz`（或转换后的坐标名） | 后续装盒 / 可视化 |
| `*.ff` | 与坐标成对，供搭建盒子写 LAMMPS |

装盒时务必选**本次转换得到的一对**，不要混入仓库另一套同名分子。

---

## 四、接着做

- 直接装盒：[搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md)
- 配方串联：[配方：LigParGen 外部力场进盒子](M17-配方LigParGen进盒子.md)
- 自己本机也没有 gro/itp：改走 [孤立分子（Ketcher 绘制）](M06-孤立分子Ketcher绘制.md) → [力场生成（结构 / SMILES → .ff）](M09-力场生成.md)

---

## 五、常见问题

| 问题 | 处理 |
|------|------|
| 配对失败 / 原子数对不上 | 重新从 LigParGen 一次导出；确认没改过坐标却沿用旧 itp |
| 转换红了 | 看任务日志；检查上传是否完整 |
| 装盒找不到力场 | 刷新工作区；确认 `.ff` 与 xyz 文件名对应 |

---

## 小结

1. LigParGen 进 MDStudio，先保证 gro/pdb 与 itp 成对。
2. 产物是 xyz + ff，再交给搭建盒子。
3. 整条装盒配方见 LigParGen 进盒子篇。

---

## 学习路径

**前置阅读：**

- [MDStudio 使用须知与限制](M02-MDStudio使用须知与限制.md)
- [MDStudio 功能与界面总览](M03-MDStudio功能与界面总览.md)
- [MDStudio 资源管理器（工作区文件）](M04-MDStudio资源管理器.md)

**下一步：**

- [搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md)
- [配方：LigParGen 外部力场进盒子](M17-配方LigParGen进盒子.md)
- [力场生成（结构 / SMILES → .ff）](M09-力场生成.md)
