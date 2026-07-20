#!/usr/bin/env python3
"""One-shot: merge unnumbered wp_slug image dirs into numbered md-stem dirs, rewrite md, prune."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from sync_article_images import IMAGES_ROOT, article_image_dirs, article_meta  # noqa: E402

FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def iter_article_mds() -> list[Path]:
    out: list[Path] = []
    for base in (PROJECT_ROOT / "在线工具", PROJECT_ROOT / "在线资源"):
        if not base.is_dir():
            continue
        for p in base.rglob("*.md"):
            if p.name in {"README.md", "资源导航.md"}:
                continue
            out.append(p)
    return sorted(out)


def merge_tree(src: Path, dest: Path) -> int:
    """Copy files from src into dest; skip identical size; prefer larger on conflict."""
    n = 0
    if not src.is_dir():
        return n
    for f in src.rglob("*"):
        if not f.is_file() or f.name == ".DS_Store":
            continue
        rel = f.relative_to(src)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size >= f.stat().st_size:
            continue
        shutil.copy2(f, target)
        n += 1
    return n


def rewrite_md_paths(text: str, old_slug: str, new_slug: str) -> tuple[str, int]:
    if old_slug == new_slug:
        return text, 0
    pat = re.compile(
        rf"(images/articles/(?:[^/\s\)]+/)+){re.escape(old_slug)}/(web|original)/"
    )
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f"{m.group(1)}{new_slug}/{m.group(2)}/"

    return pat.sub(repl, text), count


def parse_wp_slug(raw: str) -> str | None:
    m = FRONT.match(raw)
    if not m:
        return None
    km = re.search(r"^wp_slug:\s*(.+)$", m.group(1), re.M)
    if not km:
        return None
    v = km.group(1).strip().strip("'\"")
    return None if v in ("null", "~", "") else v


def list_unnumbered_article_dirs() -> list[Path]:
    out: list[Path] = []
    articles = IMAGES_ROOT / "articles"
    if not articles.is_dir():
        return out
    for tier_dir in articles.iterdir():
        if not tier_dir.is_dir():
            continue
        for d in tier_dir.iterdir():
            if not d.is_dir():
                continue
            if re.match(r"^[A-Z]\d{2}-", d.name):
                continue
            out.append(d)
    return sorted(out)


def find_numbered_twin(old: Path) -> Path | None:
    parent = old.parent
    old_names = {f.name for f in old.rglob("*") if f.is_file() and f.name != ".DS_Store"}
    for sib in parent.iterdir():
        if not sib.is_dir() or sib == old:
            continue
        if not re.match(r"^[A-Z]\d{2}-", sib.name):
            continue
        sib_names = {f.name for f in sib.rglob("*") if f.is_file() and f.name != ".DS_Store"}
        if old_names & sib_names:
            return sib
    ids: set[str] = set()
    for n in old_names:
        m = re.match(r"^([A-Z]\d{2})-", n, re.I)
        if m:
            ids.add(m.group(1).upper())
    if len(ids) == 1:
        aid = ids.pop()
        for sib in parent.iterdir():
            if sib.is_dir() and sib.name.upper().startswith(f"{aid}-"):
                return sib
    return None


def main() -> int:
    dry = "--dry-run" in sys.argv
    reports: list[str] = []
    md_rewrites = 0
    merged_dirs = 0
    removed_dirs = 0

    for md_path in iter_article_mds():
        raw = md_path.read_text(encoding="utf-8")
        info = article_meta(md_path, raw)
        series, tier, stem = info["series"], info.get("tier"), info["slug"]
        wp_slug = parse_wp_slug(raw)
        target_original, _target_web = article_image_dirs(series, tier, stem)
        target_base = target_original.parent

        if wp_slug and wp_slug != stem:
            old_original, _old_web = article_image_dirs(series, tier, wp_slug)
            old_base = old_original.parent
            if old_base.is_dir() and old_base.resolve() != target_base.resolve():
                if not dry:
                    n = merge_tree(old_base, target_base)
                    shutil.rmtree(old_base)
                else:
                    n = sum(
                        1
                        for f in old_base.rglob("*")
                        if f.is_file() and f.name != ".DS_Store"
                    )
                merged_dirs += 1
                removed_dirs += 1
                reports.append(
                    f"MERGE {old_base.relative_to(PROJECT_ROOT)} → "
                    f"{target_base.relative_to(PROJECT_ROOT)} (files≈{n})"
                )

            new_text, n = rewrite_md_paths(raw, wp_slug, stem)
            if n:
                md_rewrites += n
                reports.append(
                    f"MD {md_path.relative_to(PROJECT_ROOT)}: {n} path(s) {wp_slug}→{stem}"
                )
                if not dry:
                    md_path.write_text(new_text, encoding="utf-8")

    for old in list_unnumbered_article_dirs():
        target = find_numbered_twin(old)
        if target is None:
            reports.append(f"KEEP? no numbered twin for {old.relative_to(PROJECT_ROOT)}")
            continue
        if not dry:
            merge_tree(old, target)
            shutil.rmtree(old)
        removed_dirs += 1
        reports.append(
            f"PRUNE {old.relative_to(PROJECT_ROOT)} → {target.relative_to(PROJECT_ROOT)}"
        )
        for md_path in iter_article_mds():
            text = md_path.read_text(encoding="utf-8")
            new_text, n = rewrite_md_paths(text, old.name, target.name)
            if n:
                md_rewrites += n
                reports.append(
                    f"MD {md_path.relative_to(PROJECT_ROOT)}: "
                    f"{n} path(s) {old.name}→{target.name}"
                )
                if not dry:
                    md_path.write_text(new_text, encoding="utf-8")

    print("\n".join(reports) if reports else "(no changes)")
    print(
        f"\nsummary: merged={merged_dirs} removed={removed_dirs} "
        f"md_path_rewrites={md_rewrites} dry_run={dry}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
