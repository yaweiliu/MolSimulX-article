#!/usr/bin/env python3
"""为教程文章写入/更新 YAML front matter，并将 status 设为 draft。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from article_lookup import FRONT_MATTER_RE, iter_articles, should_skip  # noqa: E402

# 与 内容规划.md 编号表一致
ID_BY_REL: dict[str, dict[str, str]] = {
    # 00-知识（按模拟流程；排除已并入 K03）
    "在线资源/00-知识文档/K01-分子模拟方法概述.md": {"id": "K01", "paywall": "free"},
    "在线资源/00-知识文档/K02-分子动力学模拟概述.md": {"id": "K02", "paywall": "free"},
    "在线资源/00-知识文档/K03-经典全原子力场.md": {"id": "K03", "paywall": "free"},
    "在线资源/00-知识文档/K04-粗粒化与加速模型.md": {"id": "K04", "paywall": "vip"},
    "在线资源/00-知识文档/K05-高精度力场与机器学习势.md": {"id": "K05", "paywall": "vip"},
    "在线资源/00-知识文档/K30-粗粒化动力学加速与耗散.md": {"id": "K30", "paywall": "none"},
    "在线资源/00-知识文档/K31-全原子与粗粒化能不能混用.md": {"id": "K31", "paywall": "none"},
    "在线资源/00-知识文档/K06-力场怎么选.md": {"id": "K06", "paywall": "free"},
    "在线资源/00-知识文档/K07-边界条件与初始条件.md": {"id": "K07", "paywall": "free"},
    "在线资源/00-知识文档/K08-截断长程力与近邻列表.md": {"id": "K08", "paywall": "free"},
    "在线资源/00-知识文档/K09-积分算法与时间步长.md": {"id": "K09", "paywall": "free"},
    "在线资源/00-知识文档/K10-键长键角约束与刚性.md": {"id": "K10", "paywall": "free"},
    "在线资源/00-知识文档/K11-常见系综与控温控压.md": {"id": "K11", "paywall": "free"},
    "在线资源/00-知识文档/K12-能量最小化与预平衡.md": {"id": "K12", "paywall": "free"},
    "在线资源/00-知识文档/K13-平衡判据与收敛.md": {"id": "K13", "paywall": "free"},
    "在线资源/00-知识文档/K14-增强采样与自由能.md": {"id": "K14", "paywall": "vip"},
    "在线资源/00-知识文档/K15-对比单位与无量纲化.md": {"id": "K15", "paywall": "vip"},
    "在线资源/00-知识文档/K16-轨迹分析与宏观性质.md": {"id": "K16", "paywall": "free"},
    "在线资源/00-知识文档/K17-统计误差与块平均.md": {"id": "K17", "paywall": "vip"},
    "在线资源/00-知识文档/K18-有限尺寸效应.md": {"id": "K18", "paywall": "vip"},
    "在线资源/00-知识文档/K19-温度压强与表面张力.md": {"id": "K19", "paywall": "vip"},
    "在线资源/00-知识文档/K20-序参量与相变.md": {"id": "K20", "paywall": "vip"},
    "在线资源/00-知识文档/K21-输运系数谱系.md": {"id": "K21", "paywall": "vip"},
    "在线资源/00-知识文档/K22-非平衡分子动力学概述.md": {"id": "K22", "paywall": "vip"},
    "在线资源/00-知识文档/K23-统计力学基础与系综.md": {"id": "K23", "paywall": "vip"},
    "在线资源/00-知识文档/K24-分子动力学与蒙特卡洛.md": {"id": "K24", "paywall": "vip"},
    "在线资源/00-知识文档/K25-朗之万布朗与溶剂介质方法.md": {"id": "K25", "paywall": "vip"},
    "在线资源/00-知识文档/K26-第一性原理分子动力学与核量子效应.md": {"id": "K26", "paywall": "vip"},
    "在线资源/00-知识文档/K27-QM-MM思想.md": {"id": "K27", "paywall": "vip"},
    "在线资源/00-知识文档/K28-机器学习数据基础.md": {"id": "K28", "paywall": "none"},
    "在线资源/00-知识文档/K29-神经网络与深度学习基础.md": {"id": "K29", "paywall": "none"},
    # 01-技术 T01–T18
    "在线资源/01-技术文档/T01-分子模拟工作平台搭建.md": {"id": "T01", "paywall": "resource"},
    "在线资源/01-技术文档/T02-WSL2安装与配置.md": {"id": "T02", "paywall": "none"},
    "在线资源/01-技术文档/T03-Linux终端与Shell简明教程.md": {"id": "T03", "paywall": "none"},
    "在线资源/01-技术文档/T04-Git简明使用教程.md": {"id": "T04", "paywall": "none"},
    "在线资源/01-技术文档/T05-Conda与Mamba简明教程.md": {"id": "T05", "paywall": "none"},
    "在线资源/01-技术文档/T06-VSCode与Cursor简明教程.md": {"id": "T06", "paywall": "none"},
    "在线资源/01-技术文档/T07-VSCode与Cursor远程连接集群.md": {"id": "T07", "paywall": "none"},
    "在线资源/01-技术文档/T08-SSH密钥与config配置简明教程.md": {"id": "T08", "paywall": "none"},
    "在线资源/01-技术文档/T09-本地与集群文件传输.md": {"id": "T09", "paywall": "none"},
    "在线资源/01-技术文档/T10-集群与SLURM简明教程.md": {"id": "T10", "paywall": "none"},
    "在线资源/01-技术文档/T11-JupyterLab简明教程.md": {"id": "T11", "paywall": "none"},
    "在线资源/01-技术文档/T12-Markdown简明教程.md": {"id": "T12", "paywall": "none"},
    "在线资源/01-技术文档/T13-Obsidian知识库搭建.md": {"id": "T13", "paywall": "none"},
    "在线资源/01-技术文档/T14-LaTeX与Overleaf简明教程.md": {"id": "T14", "paywall": "none"},
    "在线资源/01-技术文档/T15-科研项目目录结构规范.md": {"id": "T15", "paywall": "none"},
    "在线资源/01-技术文档/T16-Jupyter Notebook科研使用规范.md": {"id": "T16", "paywall": "none"},
    "在线资源/01-技术文档/T17-数据管理与备份.md": {"id": "T17", "paywall": "none"},
    "在线资源/01-技术文档/T18-从模拟到论文图的工作流.md": {"id": "T18", "paywall": "none"},
    "在线资源/01-技术文档/T29-Docker与Apptainer入门.md": {"id": "T29", "paywall": "none"},
    "在线资源/01-技术文档/T30-机器学习与分子模拟导引.md": {"id": "T30", "paywall": "none"},
    # 01-技术 · 工具速成 T21–T25（原 C01–C05，已从实战案例迁入）
    "在线资源/01-技术文档/T21-NumPy与Matplotlib简明教程.md": {"id": "T21", "paywall": "none"},
    "在线资源/01-技术文档/T22-MDAnalysis轨迹分析入门.md": {"id": "T22", "paywall": "vip-partial"},
    "在线资源/01-技术文档/T23-ASE结构构建入门.md": {"id": "T23", "paywall": "vip-partial"},
    "在线资源/01-技术文档/T24-scikit-learn简明教程.md": {"id": "T24", "paywall": "vip-partial"},
    "在线资源/01-技术文档/T25-PyTorch简明教程.md": {"id": "T25", "paywall": "vip-partial"},
}

SERIES_TAG_RE = re.compile(r"系列标签：\*\*\s*`([^`]+)`\s*·\s*`([^`]+)`")
TIER_FROM_PATH = {
    "00-知识文档": "知识文档",
    "01-技术文档": "技术文档",
    "02-实战案例": "实战案例",
    "00-MDStudio": "MDStudio",
    "01-DataHub": "DataHub",
    "02-AILab": "AILab",
}


def infer_tier(rel: str) -> str | None:
    for key, tier in TIER_FROM_PATH.items():
        if f"/{key}/" in rel:
            return tier
    return None


def infer_topic(body: str) -> str:
    m = SERIES_TAG_RE.search(body)
    if m:
        return m.group(2).strip()
    return ""


def strip_front_matter(text: str) -> str:
    m = FRONT_MATTER_RE.match(text)
    if m:
        return text[m.end() :]
    return text


def build_yaml(
    *,
    article_id: str,
    title: str,
    series: str,
    tier: str | None,
    topic: str,
    paywall: str,
) -> str:
    lines = [
        "---",
        f"id: {article_id}",
        f"title: {title}",
        f"series: {series}",
    ]
    if tier:
        lines.append(f"tier: {tier}")
    lines.extend(
        [
            "status: draft",
            f"topic: {topic or title}",
            f"paywall: {paywall}",
            "---",
            "",
        ]
    )
    return "\n".join(lines)


def process(path: Path) -> bool:
    rel = str(path.relative_to(PROJECT_ROOT))
    spec = ID_BY_REL.get(rel)
    if not spec:
        return False

    text = path.read_text(encoding="utf-8")
    body = strip_front_matter(text)
    title = path.stem
    topic = infer_topic(body)
    tier = infer_tier(rel)
    yaml_block = build_yaml(
        article_id=spec["id"],
        title=title,
        series="在线资源",
        tier=tier,
        topic=topic,
        paywall=spec["paywall"],
    )
    path.write_text(yaml_block + body.lstrip("\n"), encoding="utf-8")
    return True


def main() -> int:
    updated = 0
    for path in iter_articles():
        if process(path):
            updated += 1
            print(f"draft  {path.relative_to(PROJECT_ROOT)}")
    print(f"\n共 {updated} 篇 → status: draft")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
