---
id: M18
title: 配方：自定义 pack.inp（多组分 / 定密度）
series: 在线工具
tier: MDStudio
status: draft
topic: MDStudio
paywall: download-vip
erphpdown_blocks: 1
---
> **系列标签：** `MDStudio` · `配方` · `pack.inp`

> **发布说明：** paywall: download-vip — 正文免费；资源区 VIP 免下载。

界面点选覆盖不了的多组分比例、定密度边长、或触线后要本地 Packmol——这时需要**手改 `pack.inp`**。本篇写改哪些字段、备份与回传；若干成品脚本放会员包（清单发布前可再钉）。

文件面板：[MDStudio 资源管理器（工作区文件）](M04-MDStudio资源管理器.md)；装盒三步：[搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md)；超规模：[MDStudio 使用须知与限制](M02-MDStudio使用须知与限制.md)。

<!-- 配图待补：文首 hero / 文中操作截图 -->

---

## 一、案例目标

| 项 | 说明 |
|----|------|
| **目标** | 会下载 → 改关键字段 → 上传 → 续跑 Packmol / LAMMPS |
| **不算什么** | Packmol 全语法参考手册 |

---

## 二、建议工作流（免费）

1. 用 [搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md) 先生成一版「接近目标」的 `pack.inp`。
2. 下载到本地；必要时在工作区留副本（或依赖产品 `.bak` 提示）。
3. 用文本编辑器改：
   - 各 `structure … number …` 的分子数
   - `inside box`（或等价）边长，以靠近目标密度
   - 多组分追加 / 删减 structure 块（保持与工作区坐标文件名一致）
4. 上传覆盖（确认对话框见 [MDStudio 资源管理器（工作区文件）](M04-MDStudio资源管理器.md)）。
5. 再跑 Packmol；若提示超过在线上限（约 **10 万** 原子），缩小体系，或见须知走 [联系我们](https://www.molsimulx.com/contact_us/) 线下定制。
6. 生成 LAMMPS。

---

## 三、字段含义表（无完整可复制脚本）

| 概念 | 你在改什么 |
|------|------------|
| 分子数 | 浓度、化学计量、总原子 |
| 盒子边长 | 密度；过小易重叠失败 |
| structure 文件名 | 必须对上工作区真实文件 |
| tolerance 等 | 过严可能装不进；以界面默认为基线微调 |

完整多组分范例脚本见会员包；正文刻意不贴整段，避免未门禁复制。

---

## 四、大体系与 `run_packmol.sh`

当界面要求下载脚本：

1. 本机安装 Packmol（或用课题环境）。
2. 按脚本说明放到含坐标文件的目录运行。
3. 将得到的 `simbox.xyz` 传回工作区。
4. 再回 MDStudio 生成 `data.lmp`/`in.lmp`。

配额与阈值数字：[MDStudio 使用须知与限制](M02-MDStudio使用须知与限制.md)。

---

## 五、注意点

- 改完又在界面「重新生成 pack」会盖掉手工修改——先备份。
- 文件名与 `pack.inp` 内字符串必须一致（大小写敏感视环境而定）。

---

## 资源下载

以下为会员资源包占位（初稿阶段文件未上传媒体库；正式发布前换成 zip 绝对 URL，并在 WP 后台把短代码设为 VIP 免费下载）。

[erphpdown]
**会员资源包（待补）：** 多组分 / 定密度示例 `pack.inp` 与配套坐标、可选 `run_packmol.sh` 说明（清单待钉）
<!-- 发布时替换为媒体库绝对链接，例如：
https://www.molsimulx.com/wp-content/uploads/molsimulx/downloads/Mxx-….zip
-->
[/erphpdown]

---

## 小结

1. 高级装盒 = 界面生成底稿 + 手改关键字段 + 回传。
2. 超限走本地 Packmol 再回传 simbox。
3. 成品脚本在会员包；注意备份防覆盖。

---

## 学习路径

**前置阅读：**

- [搭建模拟盒子（Packmol 三步）](M11-搭建模拟盒子.md)
- [MDStudio 资源管理器（工作区文件）](M04-MDStudio资源管理器.md)
- [MDStudio 使用须知与限制](M02-MDStudio使用须知与限制.md)

**下一步：**

- [配方：乙醇水溶液（溶质 + TIP3P）](M13-配方乙醇水溶液.md)
- [配方：CIF 框架材料装溶剂 / 客体](M16-配方CIF框架装溶剂.md)
- [测试模拟（LAMMPS 冒烟）](M12-测试模拟.md)
