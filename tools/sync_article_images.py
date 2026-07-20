#!/usr/bin/env python3
"""
按文章引用整理 images/：定位源图 → 归入 articles/{tier|系列}/{md文件名}/original/
→ 转 web/*.webp → 可选回写 md 路径。

目录名与 md 文件名一致（如 M07-MDStudio周期分子），按编号查找；不用 wp_slug 作文件夹名。

用法：
  python tools/sync_article_images.py --id T01 --rewrite-md
  python tools/sync_article_images.py --pick
  python tools/sync_article_images.py --list
  python tools/sync_article_images.py --file Git简明使用教程.md --rewrite-md
  python tools/sync_article_images.py --all

源图可放在任意位置（如 images/、images/inbox/、旧路径）；脚本按 md 引用查找并归档。
发布（publish.py）默认在生成 web/*.webp 后清理 images/ 散落重复源图；articles/.../original/ 归档原图保留。
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from article_lookup import FILENAME_ID_RE, infer_series, resolve_article_path  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = PROJECT_ROOT / "在线资源"
IMAGES_ROOT = PROJECT_ROOT / "images"
INBOX_DIR = IMAGES_ROOT / "inbox"
ORIGINAL_DIR_NAME = "original"
WEB_DIR_NAME = "web"

IMAGE_MD_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
WIKI_IMAGE_RE = re.compile(r"!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
FENCED_CODE_RE = re.compile(r"```[^\n]*\n.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SKIP_URL_PREFIX = ("http://", "https://", "data:", "#", "mailto:")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".gif"}
# 教程语法示例里的占位文件名，非真实配图
PLACEHOLDER_IMAGE_NAMES = frozenset(
    {
        "figure.png",
        "image.png",
        "example.png",
        "图片.png",
        "path",
        "url",
    }
)


def parse_front_matter(text: str) -> tuple[dict, str]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    block = m.group(1)
    meta: dict = {}
    for key in ("id", "title", "tier", "series", "wp_slug", "status"):
        km = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
        if km:
            val = km.group(1).strip().strip("'\"")
            meta[key] = None if val in ("null", "~", "") else val
    return meta, text[m.end() :]


def parse_series_tier(text: str) -> str | None:
    m = re.search(r"^> \*\*系列标签：\*\* `([^`]+)`", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def article_meta(md_path: Path, raw: str) -> dict:
    meta, body = parse_front_matter(raw)
    series = meta.get("series") or infer_series(md_path)
    tier = meta.get("tier")
    if not tier and series == "在线资源":
        tier = parse_series_tier(body)
    # Folder name = md filename stem (e.g. M07-MDStudio周期分子), easy to find by id.
    # Do not use wp_slug here — that produced unnumbered duplicate dirs.
    slug = md_path.stem
    article_id = meta.get("id")
    if not article_id:
        fn_m = FILENAME_ID_RE.match(md_path.stem)
        if fn_m:
            article_id = fn_m.group(1).upper()
    return {
        "id": article_id,
        "series": series,
        "tier": tier,
        "slug": slug,
        "title": meta.get("title") or md_path.stem,
    }


def article_image_dirs(series: str, tier: str | None, slug: str) -> tuple[Path, Path]:
    if series == "在线资源" and tier:
        base = IMAGES_ROOT / "articles" / tier / slug
    elif series == "在线资源":
        base = IMAGES_ROOT / "articles" / "未分类" / slug
    else:
        base = IMAGES_ROOT / "articles" / series / slug
    return base / "original", base / WEB_DIR_NAME


def is_image_path(href: str) -> bool:
    href = href.strip().split("?")[0].split("#")[0]
    if not href or href.startswith(SKIP_URL_PREFIX):
        return False
    name = Path(href).name
    if name.lower() in PLACEHOLDER_IMAGE_NAMES:
        return False
    return Path(href).suffix.lower() in IMAGE_EXT


def strip_code_for_image_scan(text: str) -> str:
    """去掉围栏代码块与行内代码，避免把语法示例里的 ![](figure.png) 当成真实配图。"""
    text = FENCED_CODE_RE.sub("", text)
    return INLINE_CODE_RE.sub("", text)


def extract_image_refs(body: str) -> list[tuple[str, str]]:
    scan_body = strip_code_for_image_scan(body)
    refs: list[tuple[str, str]] = []
    for alt, href in IMAGE_MD_RE.findall(scan_body):
        if is_image_path(href):
            refs.append((alt.strip(), href.strip()))
    for wiki in WIKI_IMAGE_RE.findall(scan_body):
        if is_image_path(wiki):
            refs.append((Path(wiki).stem, wiki.strip()))
    return refs


def resolve_existing(path: Path) -> Path | None:
    return path.resolve() if path.is_file() else None


def find_source_file(
    href: Path,
    md_path: Path,
    *,
    article_original_dir: Path | None = None,
    article_web_dir: Path | None = None,
) -> Path | None:
    candidates: list[Path] = []

    if href.is_absolute():
        candidates.append(href)
    else:
        candidates.append((md_path.parent / href).resolve())
        candidates.append((PROJECT_ROOT / href).resolve())
        if article_original_dir:
            candidates.append((article_original_dir / href.name).resolve())
            candidates.append((article_original_dir / href).resolve())
        if article_web_dir:
            candidates.append((article_web_dir / href.name).resolve())
            candidates.append((article_web_dir / href).resolve())
        candidates.append((IMAGES_ROOT / href.name).resolve())
        candidates.append((INBOX_DIR / href.name).resolve())

    if href.suffix.lower() == ".webp":
        stem = href.stem
        for ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"):
            candidates.append((INBOX_DIR / f"{stem}{ext}").resolve())
            for p in IMAGES_ROOT.rglob(f"{stem}{ext}"):
                if WEB_DIR_NAME not in p.parts:
                    candidates.append(p.resolve())

    for base in (INBOX_DIR, IMAGES_ROOT):
        candidates.append((base / href.name).resolve())
    for p in IMAGES_ROOT.rglob(href.name):
        if WEB_DIR_NAME not in p.parts:
            candidates.append(p.resolve())

    seen: set[Path] = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        hit = resolve_existing(c)
        if hit and not (WEB_DIR_NAME in hit.parts and hit.suffix.lower() == ".webp"):
            return hit
    for c in candidates:
        hit = resolve_existing(c)
        if hit:
            return hit
    return None


def apply_article_id_prefix(filename: str, article_id: str | None) -> str:
    """为归档文件名加上文章编号前缀，如 T01-hero-xxx.png。"""
    if not article_id:
        return filename
    aid = str(article_id).upper()
    if filename.upper().startswith(f"{aid}-"):
        return filename
    return f"{aid}-{filename}"


def target_original_name(src: Path, alt: str, index: int, article_id: str | None) -> str:
    suffix = src.suffix.lower() if src.suffix else ".png"
    name = src.name
    lower = name.lower()
    # 去掉已有编号前缀再归类，避免 T01-hero-x → T01-hero-x
    if article_id:
        aid = str(article_id).upper()
        if lower.startswith(f"{aid.lower()}-"):
            name = name[len(aid) + 1 :]
            lower = name.lower()
    if any(lower.startswith(p) for p in ("hero-", "fig-", "screenshot-", "diagram-")):
        base = name
    else:
        alt_l = alt.lower()
        if index == 0 or "hero" in alt_l or "头图" in alt:
            base = f"hero-{src.stem}{suffix}"
        elif "截图" in alt or "screenshot" in alt_l:
            base = f"screenshot-{src.stem}{suffix}"
        elif "示意" in alt or "diagram" in alt_l:
            base = f"diagram-{src.stem}{suffix}"
        else:
            base = f"fig-{src.stem}{suffix}"
    return apply_article_id_prefix(base, article_id)


def rel_web_path_from_md(md_path: Path, series: str, tier: str | None, slug: str, web_filename: str) -> str:
    depth = len(md_path.parent.relative_to(PROJECT_ROOT).parts)
    prefix = Path(*([".."] * depth))
    if series == "在线资源" and tier:
        rel = prefix / "images" / "articles" / tier / slug / WEB_DIR_NAME / web_filename
    elif series == "在线资源":
        rel = prefix / "images" / "articles" / "未分类" / slug / WEB_DIR_NAME / web_filename
    else:
        rel = prefix / "images" / "articles" / series / slug / WEB_DIR_NAME / web_filename
    return rel.as_posix()


def apply_image_path_rewrites(
    raw: str,
    replacements: dict[str, str],
    refs: list[tuple[str, str]],
) -> str:
    """回写 md：支持 `![](path)` 与 Obsidian `![[path]]` / `![[path|alt]]`。"""
    alt_by_href = {href: alt for alt, href in refs}
    new_raw = raw
    for old, new in replacements.items():
        alt = alt_by_href.get(old) or Path(old).stem
        new_raw = new_raw.replace(f"]({old})", f"]({new})")
        new_raw = re.sub(
            rf"!\[\[{re.escape(old)}(?:\|([^\]]*))?\]\]",
            lambda m, a=alt, n=new: f"![{m.group(1) or a}]({n})",
            new_raw,
        )
    return new_raw


def is_scattered_image_source(path: Path) -> bool:
    """images/ 根目录或随意路径的重复源图（归档后可删）；保留 site/、articles/.../web/。"""
    if not path.is_file() or WEB_DIR_NAME in path.parts:
        return False
    try:
        rel = path.relative_to(IMAGES_ROOT)
    except ValueError:
        return False
    if not rel.parts:
        return False
    if rel.parts[0] in ("site", "inbox"):
        return False
    if "articles" in rel.parts:
        idx = rel.parts.index("articles")
        tail = rel.parts[idx + 1 :]
        if len(tail) >= 3 and tail[2] in (ORIGINAL_DIR_NAME, WEB_DIR_NAME):
            return False
    return True


def prune_image_sources(
    *,
    src: Path,
    dest_original: Path,
    web_path: Path,
    dry_run: bool,
    prune_sources: bool,
) -> list[str]:
    """
    WebP 生成成功后清理 images/ 根目录等散落重复源图。
    归档目录 articles/.../original/ 内的大图保留，便于日后重导。
    """
    removed: list[str] = []
    if not prune_sources or dry_run or not web_path.is_file():
        return removed

    if (
        src.is_file()
        and src.resolve() != dest_original.resolve()
        and is_scattered_image_source(src)
    ):
        src.unlink()
        removed.append(str(src.relative_to(PROJECT_ROOT)) if PROJECT_ROOT in src.parents else str(src))

    return removed


def sync_article(
    md_path: Path,
    *,
    dry_run: bool = False,
    rewrite_md: bool = False,
    move_from_inbox: bool = True,
    prune_sources: bool = False,
) -> dict:
    raw = md_path.read_text(encoding="utf-8")
    _, body = parse_front_matter(raw)
    info = article_meta(md_path, raw)
    series, tier, slug = info["series"], info.get("tier"), info["slug"]
    original_dir, web_dir = article_image_dirs(series, tier, slug)

    refs = extract_image_refs(body)
    results: list[dict] = []
    replacements: dict[str, str] = {}
    article_dirs = (original_dir, web_dir)

    for i, (alt, href) in enumerate(refs):
        src = find_source_file(
            Path(href),
            md_path,
            article_original_dir=article_dirs[0],
            article_web_dir=article_dirs[1],
        )
        if src is None and info.get("id"):
            p = Path(href)
            if p.name and not p.name.upper().startswith(f"{str(info['id']).upper()}-"):
                src = find_source_file(
                    p.with_name(f"{info['id']}-{p.name}"),
                    md_path,
                    article_original_dir=article_dirs[0],
                    article_web_dir=article_dirs[1],
                )
        if src is None:
            results.append({"href": href, "status": "missing", "alt": alt})
            continue

        dest_name = target_original_name(src, alt, i, info.get("id"))
        dest_original = original_dir / dest_name

        action = "skip"
        if src.resolve() != dest_original.resolve():
            if not dest_original.exists() or src.stat().st_mtime_ns > dest_original.stat().st_mtime_ns:
                action = "move" if move_from_inbox and INBOX_DIR in src.parents else "copy"
                if not dry_run:
                    dest_original.parent.mkdir(parents=True, exist_ok=True)
                    if action == "move":
                        shutil.move(str(src), str(dest_original))
                    else:
                        shutil.copy2(src, dest_original)
            else:
                action = "exists"

        web_name = f"{dest_original.stem}.webp"
        web_path = web_dir / web_name
        optimize_row = None
        if not dry_run and dest_original.is_file():
            from optimize_images_for_web import process_one  # noqa: WPS433

            web_dir.mkdir(parents=True, exist_ok=True)
            optimize_row = process_one(
                dest_original,
                web_dir,
                max_width=1920,
                quality=92,
                force_lossless_png=False,
            )

        new_href = rel_web_path_from_md(md_path, series, tier, slug, web_name)
        replacements[href] = new_href
        pruned: list[str] = []
        if not dry_run and web_path.is_file():
            pruned = prune_image_sources(
                src=src,
                dest_original=dest_original,
                web_path=web_path,
                dry_run=dry_run,
                prune_sources=prune_sources,
            )
        results.append(
            {
                "href": href,
                "new_href": new_href,
                "source": str(src.relative_to(PROJECT_ROOT)) if PROJECT_ROOT in src.parents else str(src),
                "original": str(dest_original.relative_to(PROJECT_ROOT)),
                "web": str(web_path.relative_to(PROJECT_ROOT)),
                "action": action,
                "optimize": optimize_row,
                "pruned": pruned,
                "status": "ok",
            }
        )

    new_raw = raw
    if rewrite_md and replacements and not dry_run:
        new_raw = apply_image_path_rewrites(raw, replacements, refs)
        if new_raw != raw:
            md_path.write_text(new_raw, encoding="utf-8")

    return {
        "file": str(md_path.relative_to(PROJECT_ROOT)),
        "id": info.get("id"),
        "series": series,
        "tier": tier,
        "slug": slug,
        "images": results,
        "rewrote_md": rewrite_md and bool(replacements) and not dry_run,
    }


def collect_articles(path: Path | None) -> list[Path]:
    if path:
        return [path.resolve()]
    from article_lookup import iter_articles

    return iter_articles()


def main() -> int:
    parser = argparse.ArgumentParser(description="按文章引用整理 images 并转 WebP")
    parser.add_argument("article", nargs="?", help="文章编号，如 T01")
    parser.add_argument("--id", dest="article_id", metavar="T01", help="YAML 中的 id")
    parser.add_argument("--file", help="Markdown 路径或唯一文件名")
    parser.add_argument("--list", action="store_true", help="列出文章")
    parser.add_argument("--pick", action="store_true", help="交互式选择")
    parser.add_argument("--all", action="store_true", help="处理 在线资源 下全部教程")
    parser.add_argument("--dry-run", action="store_true", help="只报告不写入")
    parser.add_argument("--rewrite-md", action="store_true", help="回写 md 为规范 web 相对路径")
    parser.add_argument("--copy-only", action="store_true", help="始终复制，不从 inbox 移动")
    parser.add_argument(
        "--prune-sources",
        action="store_true",
        help="WebP 成功后删除 images/ 散落重复源图（保留 articles/.../original/；发布时默认开启）",
    )
    parser.add_argument(
        "--keep-sources",
        action="store_true",
        help="与 --prune-sources 相反：保留 images/ 根目录等散落源图",
    )
    args = parser.parse_args()
    if args.prune_sources and args.keep_sources:
        parser.error("--prune-sources 与 --keep-sources 不能同时使用")
    prune_sources = args.prune_sources and not args.keep_sources

    if args.list:
        resolve_article_path(list_only=True)
        return 0

    if args.all:
        paths = collect_articles(None)
    else:
        article_id = args.article_id
        file_arg = args.file
        if args.article and not article_id and not file_arg:
            article_id = args.article
        try:
            resolved = resolve_article_path(
                file=file_arg,
                article_id=article_id,
                pick=args.pick,
            )
        except ValueError as e:
            parser.error(str(e))
        if resolved is None:
            parser.error("请指定 --id、--file、--pick 或 --all")
        paths = [resolved]

    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    exit_code = 0
    for md_path in paths:
        if not md_path.exists():
            print(f"跳过（不存在）: {md_path}", file=sys.stderr)
            exit_code = 1
            continue
        print(f"\n=== {md_path.relative_to(PROJECT_ROOT)} ===")
        report = sync_article(
            md_path,
            dry_run=args.dry_run,
            rewrite_md=args.rewrite_md,
            move_from_inbox=not args.copy_only,
            prune_sources=prune_sources,
        )
        for row in report["images"]:
            if row["status"] == "missing":
                print(f"  ✗ 未找到: {row['href']} ({row.get('alt', '')})")
                exit_code = 1
            else:
                opt = row.get("optimize")
                opt_s = f" → web/{opt['output']}" if opt else ""
                print(f"  ✓ {row['action']:6} {row['source']} → {row['original']}{opt_s}")
                for p in row.get("pruned") or []:
                    print(f"      已清理: {p}")
                if row["href"] != row["new_href"]:
                    print(f"      md: {row['href']}")
                    print(f"    →    {row['new_href']}")
        if report.get("rewrote_md"):
            print("  （已回写 md 图片路径）")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
