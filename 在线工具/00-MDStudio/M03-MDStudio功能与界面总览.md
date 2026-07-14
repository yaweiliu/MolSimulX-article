---
id: M03
title: MDStudio 功能与界面总览
series: 在线工具
tier: MDStudio
status: draft
topic: MDStudio
paywall: free
---
> **系列标签：** `MDStudio` · `总览` · `界面`

第一次进 MDStudio，中间一排 Tab、左边一堆文件、右边还会转 3D——如果不先认清「三条主路径」和「左边是工作区」，很容易在力场转换和力场生成之间来回迷路。

本文是**功能与界面总览**：分区、八个 Tab 一句话地图、免费与 VIP 门面。不逐步代操（那是 Quickstart 与各 Tab 文）；细限额见 [MDStudio 使用须知与限制](M02-MDStudio使用须知与限制.md)；文件怎么管见 [MDStudio 资源管理器（工作区文件）](M04-MDStudio资源管理器.md)。

<!-- 配图待补：文首 hero / 文中操作截图 -->

---

## 一、MDStudio 是什么？

浏览器里完成：**结构来源 → 力场参数 → Packmol 装盒 → LAMMPS 输入（`data.lmp` / `in.lmp`）→ 可选短测试模拟**。命令行用户可把它当成同一流水线的图形入口；本系列**不写**部署与 CLI 全参数。

入口：[https://mdstudio.molsimulx.com](https://mdstudio.molsimulx.com)

---

## 二、界面分区

| 区域 | 作用 |
|------|------|
| **左：资源管理器 / 工作区** | 当前项目文件的上传、下载、预览入口；详解见 [MDStudio 资源管理器（工作区文件）](M04-MDStudio资源管理器.md) |
| **中：功能 Tab** | 力场转换 → … → 测试模拟（见下表） |
| **右：3D 预览** | 点选结构后可视化（能否预览取决于格式与规模） |

---

## 三、八个 Tab 地图

| Tab | 一句话 | 详解 |
|-----|--------|------|
| 力场转换 | 外部 LigParGen 等 gro/itp → 工作区 xyz+ff | [力场转换（LigParGen / 外部力场）](M05-力场转换LigParGen.md) |
| 孤立分子 | Ketcher 绘制 → `.mol` / SMILES | [孤立分子（Ketcher 绘制）](M06-孤立分子Ketcher绘制.md) |
| 周期分子 | ASE 模板晶体/表面/管等 → `.cif` | [周期分子（晶体 / 表面 / 纳米结构）](M07-周期分子.md) |
| 分子仓库 | 浏览库内结构；导入到工作区 | [分子仓库（浏览、预览与导入）](M08-分子仓库.md) |
| 力场生成 | 结构或 SMILES → `_ff.xyz` + `.ff` | [力场生成（结构 / SMILES → .ff）](M09-力场生成.md) |
| 超胞变换 | 扩胞/平移/旋转 → `*_trans.xyz` | [超胞与几何变换](M10-超胞与几何变换.md) |
| 搭建盒子 | pack.inp → Packmol → data/in.lmp | [搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md) |
| 测试模拟 | 对 `in.lmp` 短冒烟 | [测试模拟（LAMMPS 冒烟）](M12-测试模拟.md) |

---

## 四、两条主路径

1. **绘制 / SMILES → 力场 → 装盒 → 测试**（最短闭环，跟 [MDStudio Quickstart：从画分子到测试模拟](M01-Quickstart从画分子到测试模拟.md)）
2. **仓库导入 / LigParGen / CIF →（可选超胞）→ 力场 → 装盒 → 测试**

配方级「水溶液 / IL / 电解质…」见 [配方：乙醇水溶液（溶质 + TIP3P）](M13-配方乙醇水溶液.md) 起各篇。

---

## 五、免费与 VIP（门面）

| | 常见情况 |
|--|----------|
| 免费 | 登录、仓库浏览与预览等 |
| VIP | 绘制、力场、装盒、测试、仓库导入、转换等生成类能力 |

完整限制与超时表：[MDStudio 使用须知与限制](M02-MDStudio使用须知与限制.md)。官网开通：[VIP](https://www.molsimulx.com/vip/)。

---

## 小结

1. 左工作区、中 Tab、右预览：先认分区再点功能。
2. 八个 Tab 各有一篇详解；两条主路径覆盖大多数用法。
3. 限额与 VIP 细节只维护在使用须知，避免各处重复。

---

## 学习路径

**前置阅读：**

- [MDStudio Quickstart：从画分子到测试模拟](M01-Quickstart从画分子到测试模拟.md)
- [MDStudio 使用须知与限制](M02-MDStudio使用须知与限制.md)

**下一步：**

- [MDStudio 资源管理器（工作区文件）](M04-MDStudio资源管理器.md)
- [孤立分子（Ketcher 绘制）](M06-孤立分子Ketcher绘制.md)
- [力场生成（结构 / SMILES → .ff）](M09-力场生成.md)
- [搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md)
