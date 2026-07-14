---
id: M17
title: 配方：LigParGen 外部力场进盒子
series: 在线工具
tier: MDStudio
status: draft
topic: MDStudio
paywall: download-vip
erphpdown_blocks: 1
---
> **系列标签：** `MDStudio` · `配方` · `LigParGen`

> **发布说明：** paywall: download-vip — 正文免费；资源区 VIP 免下载。

外部已有 LigParGen 结果时，不必重画分子——**转换 Tab → 装盒 →（可选）测试**即可闭环。本篇串路径；转换结果与 pack/LAMMPS 成品在会员包。

转换细节：[力场转换（LigParGen / 外部力场）](M05-力场转换LigParGen.md)；装盒：[搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md)；限额：[MDStudio 使用须知与限制](M02-MDStudio使用须知与限制.md)。

<!-- 配图待补：文首 hero / 文中操作截图 -->

---

## 一、案例目标

| 项 | 建议 |
|----|------|
| **输入** | 一对 `.gro`/`.pdb` + `.itp`（演示可用小配体） |
| **目标** | 转换后装成纯液或溶液盒子 |
| **不算什么** | 重做 LigParGen 网页全流程教学 |

---

## 二、点击路径（免费）

1. 工作区上传 gro/pdb + itp（[MDStudio 资源管理器（工作区文件）](M04-MDStudio资源管理器.md)）。
2. [力场转换（LigParGen / 外部力场）](M05-力场转换LigParGen.md) 完成转换 → 得到 xyz + `.ff`。
3. （可选）仓库加水做成溶液，或纯液多分子复制装盒。
4. [搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md) 三步生成 `data.lmp`/`in.lmp`。
5. 可选 [测试模拟（LAMMPS 冒烟）](M12-测试模拟.md)。

---

## 三、文件名与参数含义

| 阶段 | 文件 |
|------|------|
| 外部 | `ligand.gro` + `ligand.itp`（名自定） |
| 转换后 | `*.xyz`、`*.ff` |
| 装盒 | `pack.inp`、`simbox.xyz` |
| LAMMPS | `data.lmp`、`in.lmp` |

勿把转换前的 gro 直接丢进装盒当「已有 ff」——走转换产物。

---

## 四、注意点

- 配对失败先回 [力场转换（LigParGen / 外部力场）](M05-力场转换LigParGen.md) FAQ。
- 与 GAFF 路径产物不要混用同名文件。

---

## 资源下载

以下为会员资源包占位（初稿阶段文件未上传媒体库；正式发布前换成 zip 绝对 URL，并在 WP 后台把短代码设为 VIP 免费下载）。

[erphpdown]
**会员资源包（待补）：** LigParGen 转换示例 + pack/LAMMPS 成品 zip
<!-- 发布时替换为媒体库绝对链接，例如：
https://www.molsimulx.com/wp-content/uploads/molsimulx/downloads/Mxx-….zip
-->
[/erphpdown]

---

## 小结

1. 外部力场：先转换，再装盒。
2. 正文串路径；zip 在会员区。
3. 文件成对与命名清晰可少踩坑。

---

## 学习路径

**前置阅读：**

- [力场转换（LigParGen / 外部力场）](M05-力场转换LigParGen.md)
- [搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md)
- [MDStudio 使用须知与限制](M02-MDStudio使用须知与限制.md)

**下一步：**

- [配方：乙醇水溶液（溶质 + TIP3P）](M13-配方乙醇水溶液.md)
- [配方：自定义 pack.inp（多组分 / 定密度）](M18-配方自定义pack.inp.md)
- [测试模拟（LAMMPS 冒烟）](M12-测试模拟.md)
