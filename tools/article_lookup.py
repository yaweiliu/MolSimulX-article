#!/usr/bin/env python3
"""三栏内容根目录：在线资源 / 在线工具 / 解决方案（同级）。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SERIES_NAMES = ("在线资源", "在线工具", "解决方案")
CONTENT_ROOTS: tuple[Path, ...] = tuple(PROJECT_ROOT / name for name in SERIES_NAMES)

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
ID_RE = re.compile(r"^id:\s*([KTECMS]\d+)\s*$", re.MULTILINE | re.IGNORECASE)
ID_TOKEN_RE = re.compile(r"^[KTECMS]\d+$", re.IGNORECASE)
FILENAME_ID_RE = re.compile(r"^([KTECMS]\d+)-", re.IGNORECASE)

SKIP_NAMES = frozenset({
    "README.md",
    "入门导航.md",
    "资源导航.md",
    "内容写作与发布手册.md",
    "写作规范.md",
    "发布与上线.md",
    "内容规划.md",
    "文章发布指南.md",
    "内部-内容规划.md",
    "机器学习内容规划.md",
    "实战案例开篇规划.md",
    "在线工具文章规划.md",
})


def infer_series(path: Path) -> str:
    try:
        top = path.relative_to(PROJECT_ROOT).parts[0]
    except ValueError:
        return "在线资源"
    if top in SERIES_NAMES:
        return top
    return "在线资源"


def should_skip(path: Path) -> bool:
    if path.name in SKIP_NAMES or "内部" in path.name:
        return True
    if "/_templates/" in path.as_posix():
        return True
    return False


def iter_articles(content_root: Path | None = None) -> list[Path]:
    roots = [content_root] if content_root else [r for r in CONTENT_ROOTS if r.is_dir()]
    files: list[Path] = []
    for root in roots:
        files.extend(p for p in sorted(root.rglob("*.md")) if not should_skip(p))
    return files


def read_meta(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta: dict = {
        "path": path,
        "title": path.stem,
        "id": None,
        "status": None,
        "series": infer_series(path),
        "tier": None,
    }
    m = FRONT_MATTER_RE.match(text)
    block = m.group(1) if m else ""
    id_m = ID_RE.search(block)
    if id_m:
        meta["id"] = id_m.group(1).upper()
    else:
        fn_m = FILENAME_ID_RE.match(path.stem)
        if fn_m:
            meta["id"] = fn_m.group(1).upper()
    for key in ("title", "status", "series", "tier", "topic"):
        km = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
        if km:
            val = km.group(1).strip().strip("'\"")
            if val not in ("null", "~", ""):
                meta[key] = val
    if not meta.get("series"):
        meta["series"] = infer_series(path)
    meta["rel"] = str(path.relative_to(PROJECT_ROOT))
    return meta


def build_index(content_root: Path | None = None) -> list[dict]:
    return [read_meta(p) for p in iter_articles(content_root)]


def find_by_id(article_id: str, content_root: Path | None = None) -> Path:
    token = article_id.strip().upper()
    matches = [m for m in build_index(content_root) if m.get("id") == token]
    if len(matches) == 1:
        return matches[0]["path"]
    if len(matches) > 1:
        paths = ", ".join(m["rel"] for m in matches)
        raise ValueError(f"id {token} 对应多篇：{paths}")
    raise ValueError(f"未找到 id={token}；运行 --list 查看，或为文章 YAML 添加 id:")


def parse_article_id_tokens(tokens: list[str]) -> list[str]:
    """解析 T01、T02,T03、'T04 T05' 等编号输入，去重保序。"""
    ids: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        for part in re.split(r"[,，\s]+", token.strip()):
            part = part.strip().upper()
            if part and part not in seen:
                ids.append(part)
                seen.add(part)
    return ids


def find_by_ids(article_ids: list[str], content_root: Path | None = None) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for aid in parse_article_id_tokens(article_ids):
        path = find_by_id(aid, content_root)
        if path not in seen:
            paths.append(path)
            seen.add(path)
    return paths


def find_by_file_token(token: str, content_root: Path | None = None) -> Path:
    raw = token.strip()
    if not raw:
        raise ValueError("空路径")
    candidates: list[Path] = []
    p = Path(raw)
    if p.is_absolute() and p.is_file():
        return p.resolve()
    for base in (PROJECT_ROOT, *CONTENT_ROOTS):
        candidate = base / raw
        if candidate.is_file():
            return candidate.resolve()
    name = p.name if p.name.endswith(".md") else f"{p.name}.md"
    for article in iter_articles(content_root):
        if article.name == name:
            candidates.append(article)
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        paths = ", ".join(str(c.relative_to(PROJECT_ROOT)) for c in candidates)
        raise ValueError(f"文件名 {name} 不唯一：{paths}；请用 --id 或完整路径")
    raise ValueError(f"未找到文章：{raw}")


def print_article_table(rows: list[dict], *, reviewed_only: bool = False) -> None:
    shown = [r for r in rows if not reviewed_only or r.get("status") in ("reviewed", "revised")]
    if not shown:
        print("（无匹配文章）")
        return
    print(f"{'#':>3}  {'id':<4}  {'栏目':<8}  {'status':<10}  title")
    print("-" * 72)
    for i, row in enumerate(shown, 1):
        aid = row.get("id") or "—"
        series = row.get("series") or "—"
        status = row.get("status") or "—"
        print(f"{i:>3}  {aid:<4}  {series:<8}  {status:<10}  {row['title']}")
        print(f"      {row['rel']}")


def pick_article(content_root: Path | None = None, *, reviewed_only: bool = False) -> Path:
    rows = build_index(content_root)
    shown = [r for r in rows if not reviewed_only or r.get("status") in ("reviewed", "revised")]
    if not shown:
        raise ValueError("没有可选文章")
    print_article_table(shown)
    try:
        choice = input("\n请输入编号: ").strip()
        idx = int(choice) - 1
        if idx < 0 or idx >= len(shown):
            raise ValueError("编号超出范围")
    except (EOFError, KeyboardInterrupt):
        print(file=sys.stderr)
        raise SystemExit(130) from None
    except ValueError as e:
        raise ValueError(f"无效选择：{choice}") from e
    return shown[idx]["path"]


def resolve_article_path(
    *,
    file: str | Path | None = None,
    article_id: str | None = None,
    pick: bool = False,
    list_only: bool = False,
    reviewed_only: bool = False,
    content_root: Path | None = None,
) -> Path | None:
    if list_only:
        print_article_table(build_index(content_root), reviewed_only=reviewed_only)
        return None
    if pick:
        return pick_article(content_root, reviewed_only=reviewed_only)
    if article_id:
        return find_by_id(article_id, content_root)
    if file is not None:
        token = str(file)
        if ID_TOKEN_RE.match(token.strip()):
            return find_by_id(token, content_root)
        path = Path(token)
        if path.is_file():
            return path.resolve()
        return find_by_file_token(token, content_root)
    raise ValueError("请指定 --id、--file、--pick 或 --list")
