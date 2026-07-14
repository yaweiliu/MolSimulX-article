#!/usr/bin/env python3
"""
将 images/ 下各 original/ 目录中的图片转为 WebP，输出到同级 web/。

- 自动扫描 images/**/original/（跳过 GIF、web/ 目录内文件）
- PNG：小图（≤150KB）无损 WebP；大图 q≥95
- JPEG：q=92（默认），超长边缩至 max-width

用法（molsimulx 环境）:
    conda activate molsimulx
    python tools/optimize_images_for_web.py
    python tools/optimize_images_for_web.py --root images --max-width 1920
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

SUPPORTED_INPUT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}
SKIP_EXT = {".gif"}
PNG_LOSSLESS_MAX_BYTES = 150 * 1024
ORIGINAL_DIR_NAME = "original"
WEB_DIR_NAME = "web"


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def is_source_image(path: Path) -> bool:
    if not path.is_file() or path.name.startswith("."):
        return False
    if WEB_DIR_NAME in path.parts:
        return False
    return path.suffix.lower() in SUPPORTED_INPUT and path.suffix.lower() not in SKIP_EXT


def discover_original_dirs(root: Path) -> list[Path]:
    dirs = sorted({p.parent for p in root.rglob("*") if p.is_file() and is_source_image(p)})
    named = sorted(root.rglob(ORIGINAL_DIR_NAME))
    merged: list[Path] = []
    seen: set[Path] = set()
    for d in named + dirs:
        if d.name == ORIGINAL_DIR_NAME and d not in seen:
            seen.add(d)
            merged.append(d)
    return merged


def list_images_in_original(original_dir: Path) -> list[Path]:
    return sorted(p for p in original_dir.iterdir() if is_source_image(p))


def fit_within_box(size: tuple[int, int], max_edge: int) -> tuple[int, int]:
    w, h = size
    if max(w, h) <= max_edge:
        return w, h
    if w >= h:
        new_w = max_edge
        new_h = max(1, round(h * max_edge / w))
    else:
        new_h = max_edge
        new_w = max(1, round(w * max_edge / h))
    return new_w, new_h


def load_image(path: Path) -> Image.Image:
    img = Image.open(path)
    img.load()
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        return img.convert("RGBA")
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def png_use_lossless(src: Path, force_lossless: bool) -> bool:
    if force_lossless:
        return True
    return src.stat().st_size <= PNG_LOSSLESS_MAX_BYTES


def save_webp(img: Image.Image, dest: Path, *, lossless: bool, quality: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    params: dict = {"method": 6}
    if lossless:
        params["lossless"] = True
    else:
        params["quality"] = quality
    img.save(dest, format="WEBP", **params)


def web_dir_for(original_dir: Path) -> Path:
    if original_dir.name == ORIGINAL_DIR_NAME:
        return original_dir.parent / WEB_DIR_NAME
    return original_dir / WEB_DIR_NAME


def process_one(
    src: Path,
    output_dir: Path,
    *,
    max_width: int,
    quality: int,
    force_lossless_png: bool,
) -> dict:
    img = load_image(src)
    target_w, target_h = fit_within_box(img.size, max_width)
    if (target_w, target_h) != img.size:
        img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    ext = src.suffix.lower()
    if ext == ".png":
        lossless = png_use_lossless(src, force_lossless_png)
        png_quality = max(quality, 95)
        mode_label = "lossless" if lossless else f"q={png_quality}"
        save_quality = png_quality
    else:
        lossless = False
        mode_label = f"q={quality}"
        save_quality = quality

    dest = output_dir / f"{src.stem}.webp"
    save_webp(img, dest, lossless=lossless, quality=save_quality)

    src_size = src.stat().st_size
    dest_size = dest.stat().st_size
    rel = src.relative_to(project_root() / "images") if (project_root() / "images") in src.parents else src.name
    return {
        "rel": str(rel),
        "output": dest.name,
        "size_before": src_size,
        "size_after": dest_size,
        "dimensions": f"{img.size[0]}×{img.size[1]}",
        "mode": mode_label,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    root = project_root()
    parser = argparse.ArgumentParser(
        description="扫描 images/**/original/，生成同级 web/*.webp（跳过 GIF）"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=root / "images",
        help="图片根目录（默认: 项目 images/）",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=1920,
        help="最长边上限，仅缩小不放大（默认: 1920）",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=92,
        help="JPEG 转 WebP 质量 1–100（默认: 92）",
    )
    parser.add_argument(
        "--lossless-png",
        action="store_true",
        help="所有 PNG 均用无损 WebP",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅列出待处理文件",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    images_root = args.root.resolve()
    lossless_png = args.lossless_png

    if not images_root.is_dir():
        print(f"错误：目录不存在: {images_root}", file=sys.stderr)
        return 1

    original_dirs = discover_original_dirs(images_root)
    jobs: list[tuple[Path, Path]] = []
    for original_dir in original_dirs:
        web_dir = web_dir_for(original_dir)
        for src in list_images_in_original(original_dir):
            jobs.append((src, web_dir))

    if not jobs:
        print(f"未在 {images_root} 的 original/ 目录中找到可处理图片")
        return 0

    print(f"根目录: {images_root}")
    print(
        f"最长边: {args.max_width}px | JPEG q={args.quality} | "
        f"PNG: {'全部无损' if lossless_png else '≤150KB 无损，更大图 q≥95'}\n"
    )

    total_before = 0
    total_after = 0

    for src, web_dir in jobs:
        if args.dry_run:
            print(f"  [dry-run] {src.relative_to(images_root)} → {web_dir.relative_to(images_root)}/")
            continue
        row = process_one(
            src,
            web_dir,
            max_width=args.max_width,
            quality=args.quality,
            force_lossless_png=lossless_png,
        )
        total_before += row["size_before"]
        total_after += row["size_after"]
        ratio = 100 * row["size_after"] / row["size_before"] if row["size_before"] else 0
        print(
            f"  {row['rel']} → web/{row['output']}  "
            f"{row['dimensions']}  {row['mode']}  "
            f"{row['size_before']:,} → {row['size_after']:,} B ({ratio:.1f}%)"
        )

    if not args.dry_run and total_before:
        print(
            f"\n合计: {total_before:,} → {total_after:,} B "
            f"（节省 {(1 - total_after / total_before) * 100:.1f}%）"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
