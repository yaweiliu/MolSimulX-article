#!/usr/bin/env python3
"""
MolSimulX Markdown → WordPress 发布脚本

流程：
  1. 自动运行 sync_article_images（归档图片、转 WebP、回写 md 路径）
  2. 读取 YAML front matter（status / title / tier / wp_slug / wp_post_id）
  3. 仅 status=reviewed（新建）或 revised（更新）时同步
  4. md → HTML，上传图片，替换站内 .md 链接
  5. 克隆母版文章（默认 650）的 Kadence 区块，注入第一个 wp:html 块
  6. CREATE / UPDATE；默认 WP 状态为 draft，可用 --publish 直接上线

依赖：
  pip install markdown requests pyyaml

用法：
  cp .env.local.example .env.local    # 填写 WP 账号
  python tools/publish.py --list
  python tools/publish.py --id T01 --dry-run
  python tools/publish.py T01 --write-back-id          # positional 等同 --id
  python tools/publish.py T02 T03 T04 --publish        # 批量直接发布
  python tools/publish.py --id T02,T03 --publish --write-back-id
  python tools/publish.py --pick                       # 交互选文，不用打中文路径
  python tools/publish.py --file Git简明使用教程.md    # 仅文件名（唯一时）
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import markdown
import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from article_lookup import (  # noqa: E402
    CONTENT_ROOTS,
    find_by_ids,
    infer_series,
    iter_articles,
    resolve_article_path,
)
from sync_article_images import sync_article  # noqa: E402

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env.local"
CONFIG_FILE = SCRIPT_DIR / "publish.config.yaml"
CACHE_FILE = SCRIPT_DIR / "publish-cache.json"
TEMPLATE_CACHE = SCRIPT_DIR / ".publish-template-cache.html"
DEFAULT_TEMPLATE_FILE = SCRIPT_DIR / "templates" / "article-650.blocks.html"

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
WP_HTML_BLOCK_RE = re.compile(
    r"(<!-- wp:html -->\s*)(.*?)(\s*<!-- /wp:html -->)",
    re.DOTALL,
)
TEMPLATE_FOOTER_BLOCK_RE = re.compile(
    r"\n<!-- wp:block \{\"ref\":\d+\} /-->\s*$",
)
DEFAULT_KADENCE_META: dict[str, Any] = {
    # 与 WP 后台「文章设置」已调好的一致（见 发布与上线.md · Kadence 文章设置）
    "_kad_post_transparent": "enable",
    "_kad_post_title": "hide",
    "_kad_post_layout": "fullwidth",
    "_kad_post_content_style": "unboxed",
    "_kad_post_vertical_padding": "hide",
    "_kad_post_feature": "hide",
}

ARTICLE_BODY_CSS = """
.molsimulx-article-wrap { width: 100%; color: #111; }
.molsimulx-article-title {
  text-align: center !important;
  margin: 0 0 1.5em;
  font-weight: 700;
  line-height: 1.3;
  color: #000 !important;
}
.molsimulx-article-body {
  text-align: left !important;
  color: #111;
}
.molsimulx-article-body h2,
.molsimulx-article-body h3,
.molsimulx-article-body h4,
.molsimulx-article-body p,
.molsimulx-article-body ul,
.molsimulx-article-body ol,
.molsimulx-article-body li,
.molsimulx-article-body blockquote {
  text-align: left !important;
}
.molsimulx-article-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: 0.95em;
}
.molsimulx-article-body th,
.molsimulx-article-body td {
  border: 1px solid #b8b8b8 !important;
  padding: 0.55em 0.75em;
  vertical-align: top;
  text-align: left !important;
}
.molsimulx-article-body th {
  background: #f3f3f3;
  font-weight: 600;
}
.molsimulx-article-body tr:nth-child(even) td {
  background: #fafafa;
}
.molsimulx-article-body pre {
  position: relative;
  background: #f6f8fa;
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 2.2em 1em 1em;
  overflow-x: auto;
  margin: 1em 0;
  user-select: text !important;
  -webkit-user-select: text !important;
  cursor: text;
}
.molsimulx-article-body code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 0.9em;
  user-select: text !important;
  -webkit-user-select: text !important;
}
.molsimulx-article-body pre code {
  background: transparent;
  border: 0;
  padding: 0;
  white-space: pre;
  display: block;
}
.molsimulx-article-body :not(pre) > code {
  background: #f0f0f0;
  padding: 0.15em 0.35em;
  border-radius: 4px;
}
.molsimulx-copy-btn {
  position: absolute;
  top: 0.45em;
  right: 0.45em;
  z-index: 2;
  border: 1px solid #c9d1d9;
  background: #fff;
  color: #24292f;
  border-radius: 4px;
  padding: 0.2em 0.55em;
  font-size: 12px;
  line-height: 1.4;
  cursor: pointer;
}
.molsimulx-copy-btn:hover {
  background: #f3f4f6;
}
.molsimulx-link-pending {
  color: #666 !important;
  cursor: default;
  text-decoration: none;
  border-bottom: 1px dashed #999;
}
.molsimulx-article-body img {
  display: block;
  width: auto;
  max-width: 100%;
  height: auto;
  max-height: 420px;
  margin: 0.75em auto 1.25em;
  object-fit: contain;
}
/* 文首封面：与正文插图同一最高高度 */
.molsimulx-article-body img.molsimulx-cover {
  display: block;
  width: auto;
  max-width: 100%;
  height: auto;
  max-height: 420px;
  margin: 0.75em auto 1.25em;
  object-fit: contain;
}
/* MathJax: avoid theme line-height breaking radicals */
.molsimulx-article-body .MathJax_SVG,
.molsimulx-article-body .MathJax,
.molsimulx-article-body .MathJax_Preview {
  line-height: normal !important;
}
.molsimulx-article-body .MathJax_SVG svg {
  vertical-align: middle;
}
""".strip()

COPY_CODE_SCRIPT = """
<script>
(function () {
  var wrap = document.currentScript && document.currentScript.previousElementSibling;
  if (!wrap || !wrap.classList.contains("molsimulx-article-wrap")) {
    wrap = document.querySelector(".molsimulx-article-wrap");
  }
  if (!wrap) return;
  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
    } finally {
      document.body.removeChild(ta);
    }
    return Promise.resolve();
  }
  wrap.querySelectorAll(".molsimulx-article-body pre").forEach(function (pre) {
    if (pre.querySelector(".molsimulx-copy-btn")) return;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "molsimulx-copy-btn";
    btn.textContent = "复制";
    btn.addEventListener("click", function () {
      var code = pre.querySelector("code") || pre;
      copyText(code.innerText).then(function () {
        btn.textContent = "已复制";
        setTimeout(function () { btn.textContent = "复制"; }, 1500);
      });
    });
    pre.appendChild(btn);
  });
})();
</script>
""".strip()
PUBLISHABLE_STATUS = frozenset({"reviewed", "revised"})
SKIP_MD_NAMES = frozenset({
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
WEB_DIR_NAME = "web"


def load_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        env[key.strip()] = val.strip().strip("'\"")
    return env


def load_settings() -> dict[str, Any]:
    if not ENV_FILE.is_file():
        sys.exit(
            f"缺少 {ENV_FILE}\n请执行: cp .env.local.example .env.local 并填写 WP 账号与应用密码。"
        )

    env = load_env_file(ENV_FILE)
    site_url = env.get("WP_SITE_URL", "http://molsimulx.local/").rstrip("/")
    username = env.get("WP_USERNAME", "")
    app_password = env.get("WP_APP_PASSWORD", "").replace(" ", "")
    template_id = int(env.get("WP_TEMPLATE_POST_ID", "650"))
    post_status = env.get("WP_POST_STATUS", "draft")

    if not username or not app_password:
        sys.exit(".env.local 中需填写 WP_USERNAME 与 WP_APP_PASSWORD")

    cfg: dict[str, Any] = {
        "site": {
            "url": site_url,
            "username": username,
            "app_password": app_password,
            "template_post_id": template_id,
        },
        "paths": {
            "content_roots": [str(p) for p in CONTENT_ROOTS],
            "images_dirs": [
                str(PROJECT_ROOT / "images"),
                str(PROJECT_ROOT / "在线资源"),
                str(PROJECT_ROOT / "在线工具"),
                str(PROJECT_ROOT / "解决方案"),
                str(PROJECT_ROOT),
            ],
        },
        "publish": {
            "default_status": post_status,
            "wrap_html": True,
            "use_kadence_template": True,
            "strip_series_tags": True,
            "strip_publish_note": True,
            "comment_status": "closed",
            "ping_status": "closed",
            "assign_wp_tags": False,
            "strip_template_footer": True,
            "strip_patterns": [
                r"^> \*\*系列标签：\*\*.*$",
                r"^> \*\*发布说明：\*\*.*$",
                r"^> ⚠️.*$",
            ],
        },
        "series_catalog": {
            "在线资源": {
                "parent": "在线资源",
                "children": {
                    "知识文档": "知识文档",
                    "技术文档": "技术文档",
                    "实战案例": "实战案例",
                    "00-知识文档": "知识文档",
                    "01-技术文档": "技术文档",
                    "02-实战案例": "实战案例",
                    "实战示例": "实战案例",
                    "02-实战示例": "实战案例",
                    "基础示例": "实战案例",
                    "项目案例": "实战案例",
                    "02-基础示例": "实战案例",
                    "03-项目案例": "实战案例",
                    "04-项目案例": "实战案例",
                },
            },
            "在线工具": {
                "parent": "在线工具",
                "children": {
                    "MDStudio": "MDStudio",
                    "DataHub": "DataHub",
                    "AILab": "AILab",
                    "00-MDStudio": "MDStudio",
                    "01-DataHub": "DataHub",
                    "02-AILab": "AILab",
                },
                "default_child": "MDStudio",
            },
            "解决方案": {
                "parent": "解决方案",
                "default_child": "方案",
            },
        },
        "category_map": {},
        "slug_map": {},
    }

    if CONFIG_FILE.is_file():
        with CONFIG_FILE.open(encoding="utf-8") as f:
            file_cfg = yaml.safe_load(f) or {}
        for key in ("publish", "series_catalog", "category_map"):
            if key in file_cfg:
                if key == "publish":
                    cfg["publish"].update(file_cfg["publish"])
                elif key == "category_map":
                    cfg["category_map"].update(file_cfg.get("category_map") or {})
                else:
                    cfg["series_catalog"].update(file_cfg["series_catalog"])
        if file_cfg.get("slug_map"):
            cfg["slug_map"] = file_cfg["slug_map"]
        if file_cfg.get("strip_patterns"):
            cfg["publish"]["strip_patterns"] = file_cfg["strip_patterns"]
        if file_cfg.get("kadence_meta"):
            cfg["kadence_meta"] = file_cfg["kadence_meta"]

    cfg.setdefault("kadence_meta", dict(DEFAULT_KADENCE_META))

    return cfg


def load_cache() -> dict[str, Any]:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {"media": {}, "posts": {}, "template": {}}


def save_cache(cache: dict[str, Any]) -> None:
    # 母版仅存 .publish-template-cache.html，勿写入 json（易过期且体积大）
    slim = {k: v for k, v in cache.items() if k != "template"}
    CACHE_FILE.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8")


def wp_session(cfg: dict[str, Any]) -> tuple[str, requests.Session]:
    site = cfg["site"]["url"].rstrip("/")
    sess = requests.Session()
    sess.auth = (cfg["site"]["username"], cfg["site"]["app_password"])
    sess.headers.update({"User-Agent": "MolSimulX-Publisher/1.1"})
    return site, sess


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    block = m.group(1)
    meta: dict[str, Any] = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        if key in ("tags",):
            continue
        val = val.strip().strip("'\"")
        if val in ("null", "~", ""):
            meta[key] = None
        elif key == "wp_post_id" and val.isdigit():
            meta[key] = int(val)
        elif key == "erphpdown_blocks" and val.isdigit():
            meta[key] = int(val)
        else:
            meta[key] = val
    tags_m = re.search(r"^tags:\s*$([\s\S]*?)(?=^\w|\Z)", block, re.MULTILINE)
    if tags_m:
        tags = re.findall(r"^\s*-\s+(.+)$", tags_m.group(1), re.MULTILINE)
        if tags:
            meta["tags"] = [t.strip().strip("'\"") for t in tags]
    return meta, text[m.end() :]


def parse_series_tags(text: str) -> list[str]:
    m = re.search(r"^> \*\*系列标签：\*\* (.+)$", text, re.MULTILINE)
    if not m:
        return []
    raw = m.group(1).strip()
    parts = re.split(r"\s*·\s*", raw)
    return [p.strip().strip("`") for p in parts if p.strip()]


def count_erphpdown_pairs(text: str) -> int:
    opens = len(re.findall(r"\[erphpdown\]", text, re.IGNORECASE))
    closes = len(re.findall(r"\[/erphpdown\]", text, re.IGNORECASE))
    if opens != closes:
        raise ValueError(f"erphpdown 块未成对：打开 {opens}，关闭 {closes}")
    return opens


def normalize_paywall(raw: str | None) -> str:
    """Align with site card badges: free / vip / download-vip / download-paid."""
    v = str(raw or "").strip().lower()
    aliases = {
        "": "free",
        "none": "free",
        "free": "free",
        "vip": "vip",
        "vip-partial": "vip",
        "download-vip": "download-vip",
        "download-paid": "download-paid",
        "resource": "download-vip",
    }
    return aliases.get(v, "free")


def strip_internal_lines(text: str, patterns: list[str]) -> str:
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        if any(re.match(p, line) for p in patterns):
            continue
        out.append(line)
    return "\n".join(out).strip() + "\n"


def preprocess_obsidian(md: str) -> str:
    md = re.sub(r"!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", r"![\1](\1)", md)

    def wikilink(m: re.Match[str]) -> str:
        body = m.group(1)
        if "|" in body:
            target, label = body.split("|", 1)
        else:
            target, label = body, body
        target = target.strip()
        label = label.strip()
        if not target.endswith(".md"):
            target = f"{target}.md"
        return f"[{label}]({target})"

    return re.sub(r"\[\[([^\]]+)\]\]", wikilink, md)


def resolve_image_path(src: str, md_path: Path, cfg: dict[str, Any]) -> Path | None:
    if src.startswith(("http://", "https://", "data:")):
        return None
    candidates: list[Path] = []
    p = Path(src)
    if p.is_absolute():
        candidates.append(p)
    else:
        candidates.append((md_path.parent / p).resolve())
        for base in cfg["paths"]["images_dirs"]:
            base_path = Path(base)
            candidates.append((base_path / p.name).resolve())
            candidates.append((base_path / p).resolve())
    for c in candidates:
        if c.is_file():
            return prefer_web_image(c)
    return None


def prefer_web_image(path: Path) -> Path:
    """发布到 WP 时优先使用同级 web/*.webp，而非 original 大图。"""
    if path.suffix.lower() == ".webp" and WEB_DIR_NAME in path.parts:
        return path
    parts = list(path.parts)
    if "original" in parts:
        idx = parts.index("original")
        web_path = Path(*parts[:idx], WEB_DIR_NAME, *parts[idx + 1 :])
        web_candidate = web_path.with_suffix(".webp")
        if web_candidate.is_file():
            return web_candidate
    if path.parent.name == WEB_DIR_NAME:
        return path
    # 同目录旁路的 web/（articles/.../slug/web/）
    web_dir = path.parent.parent / WEB_DIR_NAME if path.parent.name == "original" else None
    if web_dir and web_dir.is_dir():
        web_candidate = web_dir / f"{path.stem}.webp"
        if web_candidate.is_file():
            return web_candidate
    return path


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def upload_media(
    site: str,
    sess: requests.Session,
    path: Path,
    cache: dict[str, Any],
) -> str:
    key = str(path.resolve())
    h = file_hash(path)
    if key in cache.get("media", {}):
        entry = cache["media"][key]
        if entry.get("hash") == h:
            cached_url = entry.get("url", "")
            if cached_url:
                try:
                    head = sess.head(cached_url, timeout=15, allow_redirects=True)
                    if head.status_code == 200:
                        return cached_url
                except requests.RequestException:
                    pass

    with path.open("rb") as f:
        mime = "image/webp" if path.suffix.lower() == ".webp" else "application/octet-stream"
        files = {"file": (path.name, f, mime)}
        r = sess.post(f"{site}/wp-json/wp/v2/media", files=files, timeout=120)
    r.raise_for_status()
    data = r.json()
    url = data["source_url"]
    cache["media"][key] = {"hash": h, "url": url, "id": data["id"]}
    return url


def rewrite_images(
    md: str,
    md_path: Path,
    site: str,
    sess: requests.Session,
    cfg: dict[str, Any],
    cache: dict[str, Any],
) -> str:
    def repl(m: re.Match[str]) -> str:
        alt, src = m.group(1), m.group(2).strip()
        local = resolve_image_path(src, md_path, cfg)
        if local is None:
            if src.startswith("/"):
                return f"![{alt}]({site}{src})"
            return m.group(0)
        url = upload_media(site, sess, local, cache)
        return f"![{alt}]({url})"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, md)


def slug_from_path(path: Path) -> str:
    """Derive a WordPress-like slug from the article filename (after id- prefix)."""
    stem = path.stem
    if re.match(r"^[KTECMS]\d+-", stem):
        stem = stem.split("-", 1)[1]
    # WP: spaces → hyphens; Latin letters lowercased (Chinese left as-is).
    stem = re.sub(r"[\s_]+", "-", stem.strip())
    stem = re.sub(r"-{2,}", "-", stem)
    return "".join(c.lower() if ("A" <= c <= "Z") else c for c in stem)


def collect_published_slugs() -> dict[str, str]:
    """以本地 YAML 含 wp_post_id 为准，决定站内链是否可点击。"""
    slug_map: dict[str, str] = {}
    for path in iter_articles():
        meta, _ = parse_front_matter(path.read_text(encoding="utf-8"))
        if not meta.get("wp_post_id"):
            continue
        slug = str(meta.get("wp_slug") or slug_from_path(path))
        rel = str(path.relative_to(PROJECT_ROOT))
        slug_map[rel] = slug
        slug_map[path.name] = slug
        if meta.get("id"):
            slug_map[str(meta["id"]).upper()] = slug
    return slug_map


def prune_stale_post_cache(cache: dict[str, Any]) -> bool:
    """移除 posts 缓存中已无 wp_post_id 的篇目（WP 下架后避免死链仍被当成已发布）。"""
    live = collect_published_slugs()
    posts = dict(cache.get("posts") or {})
    if not posts:
        return False
    keep: dict[str, str] = {}
    for key, slug in posts.items():
        if key.startswith("id:"):
            ok = key[3:].upper() in live
        elif key.endswith(".md"):
            ok = key in live or Path(key).name in live
        else:
            ok = key in live
        if ok:
            keep[key] = slug
    if keep == posts:
        return False
    cache["posts"] = keep
    return True


def build_published_slug_map(cache: dict[str, Any]) -> dict[str, str]:
    """构建可点击站内链映射；仅以当前 YAML wp_post_id 为准，不用过期 posts 缓存。"""
    prune_stale_post_cache(cache)
    return collect_published_slugs()


def resolve_published_slug(
    href: str,
    md_path: Path,
    slug_map: dict[str, str],
) -> str | None:
    t = href.strip()
    if t.endswith(".md"):
        t_path = (md_path.parent / t).resolve()
        try:
            rel = str(t_path.relative_to(PROJECT_ROOT))
            if rel in slug_map:
                return slug_map[rel]
        except ValueError:
            pass
        if t_path.name in slug_map:
            return slug_map[t_path.name]
    return slug_map.get(t)


def rewrite_internal_links(
    md: str,
    md_path: Path,
    cfg: dict[str, Any],
    cache: dict[str, Any],
    site: str,
    *,
    strict: bool,
    guess_unpublished: bool = False,
) -> str:
    slug_map = build_published_slug_map(cache)
    manual = dict(cfg.get("slug_map") or {})
    slug_map.update(manual)

    def repl(m: re.Match[str]) -> str:
        label, href = m.group(1), m.group(2).strip()
        if href.startswith(("mailto:", "#")):
            return m.group(0)
        if href.startswith(("http://", "https://")):
            parsed = urlparse(href)
            host = site.replace("https://", "").replace("http://", "").rstrip("/")
            if parsed.netloc and host not in parsed.netloc:
                return m.group(0)
            return m.group(0)
        if not (
            href.endswith(".md")
            or (not href.startswith("/") and "/" not in href and "." not in href)
        ):
            return m.group(0)

        slug = resolve_published_slug(href, md_path, slug_map)
        if slug:
            return f"[{label}]({site}/{slug}/)"

        if guess_unpublished:
            if href.endswith(".md"):
                t_path = (md_path.parent / href).resolve()
                return f"[{label}]({site}/{slug_from_path(t_path)}/)"
            if href in slug_map:
                return f"[{label}]({site}/{slug_map[href]}/)"

        if strict:
            return f"{label}（待发布）"
        return (
            f'<span class="molsimulx-link-pending" title="待发布">'
            f"{html.escape(label)}</span>"
        )

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, md)


A_TAG_RE = re.compile(r"<a\s[^>]*>", re.IGNORECASE)
TARGET_ATTR_RE = re.compile(
    r"""\s*\btarget\s*=\s*(["'])_blank\1""",
    re.IGNORECASE,
)
# 仅清理为新窗口配套写入的 rel；保留其它 rel 值
BLANK_REL_ONLY_RE = re.compile(
    r"""\s*\brel\s*=\s*(["'])\s*noopener(?:\s+noreferrer)?\s*\1""",
    re.IGNORECASE,
)


def normalize_link_targets(html_str: str) -> str:
    """正文链接默认当前窗口打开：去掉自动/遗留的 target=\"_blank\"。"""

    def repl(m: re.Match[str]) -> str:
        tag = m.group(0)
        if not TARGET_ATTR_RE.search(tag):
            return tag
        tag = TARGET_ATTR_RE.sub("", tag)
        tag = BLANK_REL_ONLY_RE.sub("", tag)
        return tag

    return A_TAG_RE.sub(repl, html_str)


def mark_cover_image(html_str: str) -> str:
    """给正文第一张 <img> 加上 molsimulx-cover（文首封面；与正文图同一限高）。"""
    m = re.search(r"<img\b[^>]*>", html_str, flags=re.IGNORECASE)
    if not m:
        return html_str
    tag = m.group(0)
    if "molsimulx-cover" in tag:
        return html_str
    if re.search(r"\bclass\s*=", tag, flags=re.IGNORECASE):
        new_tag = re.sub(
            r"""(\bclass\s*=\s*["'])""",
            r"\1molsimulx-cover ",
            tag,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        new_tag = re.sub(r"<img\b", '<img class="molsimulx-cover"', tag, count=1, flags=re.IGNORECASE)
    return html_str[: m.start()] + new_tag + html_str[m.end() :]


def _protect_math_segments(md: str) -> tuple[str, list[str]]:
    """Extract $...$ / $$...$$ so Markdown/nl2br cannot eat TeX backslashes (e.g. \\\\[4pt]).

    Shell-style `$HOME` / `$SCRATCH` pairs must not be treated as math: stash fenced and
    inline code first, run math extraction, then put code back before Markdown runs.
    """
    code_chunks: list[str] = []

    def _stash_fence(match: re.Match[str]) -> str:
        code_chunks.append(match.group(0))
        return f"\n\nMOLSIMULXCODE{len(code_chunks) - 1}END\n\n"

    def _stash_inline_code(match: re.Match[str]) -> str:
        code_chunks.append(match.group(0))
        return f"MOLSIMULXCODE{len(code_chunks) - 1}END"

    # Fences first, then inline `...` (not ``...``).
    out = re.sub(r"```[\s\S]*?```", _stash_fence, md)
    out = re.sub(r"(?<!`)`([^`\n]+)`(?!`)", _stash_inline_code, out)

    chunks: list[str] = []

    def _store_display(match: re.Match[str]) -> str:
        chunks.append(match.group(0))
        return f"\n\nMOLSIMULXMATH{len(chunks) - 1}END\n\n"

    def _store_inline(match: re.Match[str]) -> str:
        chunks.append(match.group(0))
        return f"MOLSIMULXMATH{len(chunks) - 1}END"

    out = re.sub(r"\$\$[\s\S]+?\$\$", _store_display, out)
    out = re.sub(
        r"(?<!\$)\$(?!\$)(?:\\.|[^\\$])+?(?<!\\)\$(?!\$)",
        _store_inline,
        out,
    )

    def _restore_code(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        if 0 <= idx < len(code_chunks):
            return code_chunks[idx]
        return match.group(0)

    out = re.sub(r"MOLSIMULXCODE(\d+)END", _restore_code, out)
    return out, chunks


def _math_chunk_for_html(tex: str) -> str:
    """Avoid raw < > in TeX so WordPress/HTML never treats them as tags (e.g. i<j)."""
    return tex.replace("<", r"\lt ").replace(">", r"\gt ")


def _restore_math_segments(html: str, chunks: list[str]) -> str:
    # Placeholder sat alone in a <p> (display math): inject TeX inside that same <p>.
    def _restore_p(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        if 0 <= idx < len(chunks):
            return f"<p>{_math_chunk_for_html(chunks[idx])}</p>"
        return match.group(0)

    html = re.sub(r"<p>\s*MOLSIMULXMATH(\d+)END\s*</p>", _restore_p, html)

    def _restore_inline(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        if 0 <= idx < len(chunks):
            return _math_chunk_for_html(chunks[idx])
        return match.group(0)

    return re.sub(r"MOLSIMULXMATH(\d+)END", _restore_inline, html)


def md_to_html(md: str, wrap: bool, title: str | None = None) -> str:
    protected, math_chunks = _protect_math_segments(md)
    body_html = markdown.markdown(
        protected,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
        output_format="html5",
    )
    body_html = _restore_math_segments(body_html, math_chunks)
    body_html = normalize_link_targets(body_html)
    body_html = mark_cover_image(body_html)
    if not wrap:
        return body_html

    title_html = ""
    if title:
        title_html = f'<h1 class="molsimulx-article-title">{html.escape(title)}</h1>\n'

    return (
        f'<div class="molsimulx-article-wrap">\n'
        f"<style>{ARTICLE_BODY_CSS}</style>\n"
        f"{title_html}"
        f'<div class="molsimulx-article-body">\n{body_html}\n</div>\n'
        f"</div>\n"
        f"{COPY_CODE_SCRIPT}"
    )


def resolve_kadence_meta(cfg: dict[str, Any]) -> dict[str, Any]:
    """读取 publish.config.yaml 中的 Kadence 文章设置（以人工调好的后台选项为准）。"""
    return dict(cfg.get("kadence_meta") or DEFAULT_KADENCE_META)


def get_or_create_category(
    site: str, sess: requests.Session, name: str, parent_id: int | None = None
) -> int:
    params: dict[str, Any] = {"search": name, "per_page": 100}
    if parent_id:
        params["parent"] = parent_id
    r = sess.get(f"{site}/wp-json/wp/v2/categories", params=params, timeout=30)
    r.raise_for_status()
    for cat in r.json():
        if cat["name"] == name and (parent_id is None or cat.get("parent") == parent_id):
            return cat["id"]
    payload: dict[str, Any] = {"name": name}
    if parent_id:
        payload["parent"] = parent_id
    r = sess.post(f"{site}/wp-json/wp/v2/categories", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["id"]


TOOL_TIER_FROM_PATH = (
    ("00-MDStudio", "MDStudio"),
    ("01-DataHub", "DataHub"),
    ("02-AILab", "AILab"),
    ("MDStudio", "MDStudio"),
    ("DataHub", "DataHub"),
    ("AILab", "AILab"),
)


def infer_online_tool_tier(md_path: Path, topic: str | None, series_tags: list[str]) -> str | None:
    """在线工具子产品：MDStudio / DataHub / AILab。"""
    rel = str(md_path).replace("\\", "/")
    for folder, name in TOOL_TIER_FROM_PATH:
        if f"/{folder}/" in rel or rel.endswith(f"/{folder}"):
            return name
    if topic in {"MDStudio", "DataHub", "AILab"}:
        return str(topic)
    for tag in series_tags:
        if tag in {"MDStudio", "DataHub", "AILab"}:
            return tag
    return None


def _child_tier_key(
    series: str,
    tier: str | None,
    series_tags: list[str],
    children: dict[str, str],
    topic: str | None = None,
) -> str:
    """Resolve WP subcategory key for a series."""
    if tier:
        return str(tier)
    if series == "在线资源":
        return series_tags[0] if series_tags else ""
    if series == "在线工具":
        # Prefer YAML topic when it is a known product subcategory.
        if topic and str(topic) in children:
            return str(topic)
        for tag in series_tags:
            if tag in children:
                return tag
        return ""
    return series_tags[0] if series_tags else ""


def resolve_categories(
    cfg: dict[str, Any],
    site: str,
    sess: requests.Session,
    series: str,
    tier: str | None,
    series_tags: list[str],
    topic: str | None = None,
) -> list[int]:
    catalog = cfg.get("series_catalog", {})
    spec = catalog.get(series, catalog.get("在线资源", {}))
    parent_name = spec.get("parent", series)
    parent_id = get_or_create_category(site, sess, parent_name)

    children = spec.get("children", {})
    if children:
        tier_key = _child_tier_key(series, tier, series_tags, children, topic=topic)
        child_name = children.get(
            tier_key,
            cfg.get("category_map", {}).get(tier_key, tier_key or None),
        )
        if not child_name:
            child_name = spec.get("default_child", "未分类")
    else:
        child_name = spec.get("default_child", "未分类")

    child_id = get_or_create_category(site, sess, child_name, parent_id=parent_id)
    return [parent_id, child_id]


def resolve_tags(
    cfg: dict[str, Any],
    site: str,
    sess: requests.Session,
    meta: dict[str, Any],
    series_tags: list[str],
) -> list[int]:
    names: list[str] = []
    topic = meta.get("topic")
    if topic:
        names.append(str(topic))
    elif meta.get("tags"):
        names.extend(str(t) for t in meta["tags"])
    elif len(series_tags) > 1:
        names.extend(series_tags[1:])
    # 去重保序
    seen: set[str] = set()
    unique = [n for n in names if n and not (n in seen or seen.add(n))]

    tag_ids: list[int] = []
    for name in unique:
        r = sess.get(f"{site}/wp-json/wp/v2/tags", params={"search": name}, timeout=30)
        r.raise_for_status()
        found = [t for t in r.json() if t["name"] == name]
        if found:
            tag_ids.append(found[0]["id"])
        else:
            r2 = sess.post(f"{site}/wp-json/wp/v2/tags", json={"name": name}, timeout=30)
            r2.raise_for_status()
            tag_ids.append(r2.json()["id"])
    return tag_ids


def find_post_by_slug(site: str, sess: requests.Session, slug: str) -> dict[str, Any] | None:
    r = sess.get(
        f"{site}/wp-json/wp/v2/posts",
        params={"slug": slug, "status": "any", "context": "edit"},
        timeout=30,
    )
    r.raise_for_status()
    posts = r.json()
    return posts[0] if posts else None


def get_post_by_id(site: str, sess: requests.Session, post_id: int) -> dict[str, Any]:
    r = sess.get(f"{site}/wp-json/wp/v2/posts/{post_id}", params={"context": "edit"}, timeout=60)
    r.raise_for_status()
    return r.json()


def post_content_raw(post: dict[str, Any], site: str, sess: requests.Session) -> str:
    """读取 Gutenberg 区块原文；列表接口有时不含 raw，则按 id 再拉一次。"""
    content = post.get("content") or {}
    raw = content.get("raw")
    if raw is not None:
        return raw
    post_id = post.get("id")
    if post_id:
        full = get_post_by_id(site, sess, int(post_id))
        raw = (full.get("content") or {}).get("raw")
        if raw is not None:
            return raw
    raise ValueError(
        f"无法读取文章 {post_id} 的 content.raw；请确认 WP 账号有编辑权限。"
    )


def strip_template_placeholder(template_content: str) -> str:
    """母版 wp:html 内只留占位，避免缓存带入旧正文。"""
    match = WP_HTML_BLOCK_RE.search(template_content)
    if not match:
        return template_content
    return (
        template_content[: match.start()]
        + match.group(1)
        + "\n<!-- molsimulx-article -->\n"
        + match.group(3)
        + template_content[match.end() :]
    )


def strip_template_footer(template_content: str) -> str:
    """去掉母版末尾的可复用页脚区块（如 wp:block ref 568）。"""
    return TEMPLATE_FOOTER_BLOCK_RE.sub("\n", template_content.rstrip()) + "\n"


def fetch_template_content(
    site: str,
    sess: requests.Session,
    template_id: int,
    *,
    dry_run: bool,
    force_refresh: bool = False,
    strip_footer: bool = True,
) -> str:
    """在线发布时每次从 WP 拉取最新母版；dry-run 默认用本地缓存。"""
    if not dry_run or force_refresh:
        post = get_post_by_id(site, sess, template_id)
        content = strip_template_placeholder(post_content_raw(post, site, sess))
        if strip_footer:
            content = strip_template_footer(content)
        if not dry_run:
            TEMPLATE_CACHE.write_text(content, encoding="utf-8")
        return content

    if TEMPLATE_CACHE.is_file():
        content = TEMPLATE_CACHE.read_text(encoding="utf-8")
        return strip_template_footer(content) if strip_footer else content

    if DEFAULT_TEMPLATE_FILE.is_file():
        content = strip_template_placeholder(DEFAULT_TEMPLATE_FILE.read_text(encoding="utf-8"))
        return strip_template_footer(content) if strip_footer else content

    raise ValueError(
        f"dry-run 需要母版缓存：先在线发布一次以生成 {TEMPLATE_CACHE.name}，"
        f"或保留 {DEFAULT_TEMPLATE_FILE}"
    )


def inject_article_html(template_content: str, article_html: str) -> str:
    match = WP_HTML_BLOCK_RE.search(template_content)
    if not match:
        raise ValueError("母版文章中未找到 <!-- wp:html --> 块，无法注入正文")
    return (
        template_content[: match.start()]
        + match.group(1)
        + "\n"
        + article_html
        + "\n"
        + match.group(3)
        + template_content[match.end() :]
    )


def replace_article_html_in_post(existing_content: str, article_html: str) -> str:
    match = WP_HTML_BLOCK_RE.search(existing_content)
    if not match:
        raise ValueError("目标文章 content 中未找到 wp:html 块；请用母版重新创建或检查版式")
    return (
        existing_content[: match.start()]
        + match.group(1)
        + "\n"
        + article_html
        + "\n"
        + match.group(3)
        + existing_content[match.end() :]
    )


def write_back_post_id(md_path: Path, post_id: int) -> None:
    text = md_path.read_text(encoding="utf-8")
    if not FRONT_MATTER_RE.match(text):
        return
    if re.search(r"^wp_post_id:\s*\d+\s*$", text, re.MULTILINE):
        text = re.sub(r"^wp_post_id:\s*.*$", f"wp_post_id: {post_id}", text, count=1, flags=re.MULTILINE)
    elif re.search(r"^wp_post_id:\s*$", text, re.MULTILINE):
        text = re.sub(r"^wp_post_id:\s*$", f"wp_post_id: {post_id}", text, count=1, flags=re.MULTILINE)
    else:
        text = text.replace("---\n", f"---\nwp_post_id: {post_id}\n", 1)
    md_path.write_text(text, encoding="utf-8")


def write_back_wp_slug(md_path: Path, slug: str) -> None:
    """Persist WordPress slug so站内链与 WP 实际 permalink 一致（含空格→连字符等）。"""
    text = md_path.read_text(encoding="utf-8")
    if not FRONT_MATTER_RE.match(text):
        return
    slug = unquote(str(slug)).strip()
    if not slug:
        return
    if re.search(r"^wp_slug:\s*.*$", text, re.MULTILINE):
        text = re.sub(r"^wp_slug:\s*.*$", f"wp_slug: {slug}", text, count=1, flags=re.MULTILINE)
    else:
        # Prefer after title if present
        if re.search(r"^title:\s*.*$", text, re.MULTILINE):
            text = re.sub(
                r"^(title:\s*.*)$",
                rf"\1\nwp_slug: {slug}",
                text,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            text = text.replace("---\n", f"---\nwp_slug: {slug}\n", 1)
    md_path.write_text(text, encoding="utf-8")


def run_image_sync(md_path: Path, *, dry_run: bool, prune_sources: bool = True) -> dict[str, Any]:
    """发布前整理配图：归档 → WebP → 回写 md（dry-run 时不写入）。"""
    report = sync_article(
        md_path,
        dry_run=dry_run,
        rewrite_md=not dry_run,
        move_from_inbox=True,
        prune_sources=prune_sources and not dry_run,
    )
    missing = [r for r in report["images"] if r["status"] == "missing"]
    if missing:
        hrefs = ", ".join(r["href"] for r in missing)
        raise ValueError(f"配图未找到，请按 md 相对路径放置图片或放入 images/inbox：{hrefs}")
    return report


def publish_file(
    md_path: Path,
    cfg: dict[str, Any],
    *,
    dry_run: bool = False,
    status_override: str | None = None,
    force: bool = False,
    strict_links: bool = False,
    write_back_id: bool = False,
    sync_images: bool = True,
    prune_image_sources: bool = True,
    refresh_template: bool = False,
    keep_layout: bool = False,
    guess_unpublished: bool = False,
) -> dict[str, Any]:
    raw = md_path.read_text(encoding="utf-8")
    meta, _ = parse_front_matter(raw)
    local_status = str(meta.get("status") or "draft").strip()

    if not force and local_status not in PUBLISHABLE_STATUS:
        return {
            "file": str(md_path),
            "skipped": True,
            "reason": f"status={local_status}，仅 reviewed / revised 可发布（加 --force 跳过）",
        }

    image_sync: dict[str, Any] | None = None
    cache = load_cache()
    if prune_stale_post_cache(cache):
        save_cache(cache)

    if sync_images:
        image_sync = run_image_sync(
            md_path,
            dry_run=dry_run,
            prune_sources=prune_image_sources,
        )
        raw = md_path.read_text(encoding="utf-8")

    meta, body = parse_front_matter(raw)

    if local_status == "revised" and not meta.get("wp_post_id"):
        # 允许用 slug 查找，但给出提示
        pass

    series_tags = parse_series_tags(body)
    strip_patterns = list(cfg["publish"].get("strip_patterns", []))
    body = strip_internal_lines(body, strip_patterns)
    body = preprocess_obsidian(body)

    erphp_count = count_erphpdown_pairs(body)
    yaml_count = meta.get("erphpdown_blocks")
    if yaml_count is not None and int(yaml_count) != erphp_count:
        print(
            f"警告: YAML erphpdown_blocks={yaml_count}，正文实际 {erphp_count} 对",
            file=sys.stderr,
        )

    title = str(meta.get("title") or slug_from_path(md_path))
    slug = str(meta.get("wp_slug") or slug_from_path(md_path))
    content_series = str(meta.get("series") or infer_series(md_path))
    tier = meta.get("tier")
    topic = meta.get("topic")
    if not tier and content_series == "在线资源":
        tier = series_tags[0] if series_tags else None
    if not tier and content_series == "在线工具":
        tier = infer_online_tool_tier(md_path, str(topic) if topic else None, series_tags)
    paywall = normalize_paywall(str(meta.get("paywall") or ""))
    post_status = status_override or cfg["publish"]["default_status"]

    site, sess = wp_session(cfg)

    if not dry_run:
        body = rewrite_images(body, md_path, site, sess, cfg, cache)
        body = rewrite_internal_links(
            body,
            md_path,
            cfg,
            cache,
            site,
            strict=strict_links,
            guess_unpublished=guess_unpublished or cfg["publish"].get("guess_unpublished_links", False),
        )

    article_html = md_to_html(body, cfg["publish"].get("wrap_html", True), title=title)
    kadence_meta = resolve_kadence_meta(cfg)

    use_template = cfg["publish"].get("use_kadence_template", True)
    full_content = article_html
    if use_template:
        template_id = int(cfg["site"]["template_post_id"])
        template_raw = fetch_template_content(
            site,
            sess,
            template_id,
            dry_run=dry_run,
            force_refresh=refresh_template,
            strip_footer=cfg["publish"].get("strip_template_footer", True),
        )
        full_content = inject_article_html(template_raw, article_html)

    result: dict[str, Any] = {
        "file": str(md_path),
        "id": meta.get("id"),
        "title": title,
        "slug": slug,
        "local_status": local_status,
        "wp_status": post_status,
        "series": content_series,
        "tier": tier,
        "paywall": paywall,
        "series_tags": series_tags,
        "erphpdown_blocks": erphp_count,
        "content_len": len(full_content),
        "kadence_meta": kadence_meta,
    }
    if image_sync is not None:
        result["image_sync"] = {
            "images": len(image_sync.get("images", [])),
            "rewrote_md": image_sync.get("rewrote_md", False),
            "dry_run": dry_run,
            "pruned": [
                p for row in image_sync.get("images", []) for p in (row.get("pruned") or [])
            ],
        }

    if dry_run:
        result["dry_run"] = True
        result["html_preview"] = article_html[:600]
        return result

    cat_ids = resolve_categories(
        cfg, site, sess, content_series, tier, series_tags, topic=str(topic) if topic else None
    )

    post_meta = dict(kadence_meta)
    post_meta["molsimulx_paywall"] = paywall

    payload: dict[str, Any] = {
        "title": title,
        "slug": slug,
        "status": post_status,
        "content": full_content,
        "categories": cat_ids,
        "format": "standard",
        "meta": post_meta,
        "comment_status": cfg["publish"].get("comment_status", "closed"),
        "ping_status": cfg["publish"].get("ping_status", "closed"),
    }
    if cfg["publish"].get("assign_wp_tags", False):
        payload["tags"] = resolve_tags(cfg, site, sess, meta, series_tags)
    else:
        payload["tags"] = []

    existing: dict[str, Any] | None = None
    wp_post_id = meta.get("wp_post_id")
    if wp_post_id:
        try:
            existing = get_post_by_id(site, sess, int(wp_post_id))
        except requests.HTTPError:
            existing = None
    if existing is None:
        existing = find_post_by_slug(site, sess, slug)

    if local_status == "revised" and existing is None:
        raise ValueError("revised 文章需要已有 wp_post_id 或同 slug 的 WP 文章")

    if existing:
        # 默认整篇套用当前母版（行宽/间距随 650 更新）；--keep-layout 则只换正文 html 块
        if use_template and keep_layout:
            try:
                existing_raw = post_content_raw(existing, site, sess)
                if WP_HTML_BLOCK_RE.search(existing_raw):
                    payload["content"] = replace_article_html_in_post(existing_raw, article_html)
            except ValueError:
                pass
        r = sess.post(f"{site}/wp-json/wp/v2/posts/{existing['id']}", json=payload, timeout=120)
        action = "update"
    else:
        r = sess.post(f"{site}/wp-json/wp/v2/posts", json=payload, timeout=120)
        action = "create"

    r.raise_for_status()
    post = r.json()
    actual_slug = unquote(str(post.get("slug") or slug))

    rel = str(md_path.resolve().relative_to(PROJECT_ROOT))
    cache.setdefault("posts", {})[rel] = actual_slug
    cache.setdefault("posts", {})[md_path.name] = actual_slug
    cache.setdefault("posts", {})[f"id:{meta.get('id')}"] = actual_slug
    save_cache(cache)

    if write_back_id:
        write_back_post_id(md_path, int(post["id"]))
    # Always persist WP slug when it differs — fixes space/case permalink drift.
    if actual_slug and actual_slug != meta.get("wp_slug"):
        write_back_wp_slug(md_path, actual_slug)

    if post_status == "publish":
        next_steps = "文章已在 WordPress 直接发布；请在后台确认 erphpdown 等设置，本地 YAML 可改 status=published"
    elif post_status == "private":
        next_steps = "文章已同步为 private；请在 WP 后台确认"
    else:
        next_steps = "WP 后台预览 draft → 配置 erphpdown → 人工发布 → 本地改 status=published"

    result.update(
        {
            "action": action,
            "wp_post_id": post["id"],
            "slug": actual_slug,
            "link": post["link"],
            "edit_link": f"{site}/wp-admin/post.php?post={post['id']}&action=edit",
            "next_steps": next_steps,
        }
    )
    return result


def collect_md_files() -> list[Path]:
    return iter_articles()


def print_batch_summary(results: list[dict[str, Any]]) -> None:
    if len(results) <= 1:
        return
    ok = [r for r in results if not r.get("skipped") and not r.get("error")]
    skipped = [r for r in results if r.get("skipped")]
    failed = [r for r in results if r.get("error")]
    print("\n=== 批量发布汇总 ===")
    print(f"成功 {len(ok)} · 跳过 {len(skipped)} · 失败 {len(failed)}")
    for r in results:
        aid = r.get("id") or "—"
        title = r.get("title") or r.get("file") or "—"
        if r.get("error"):
            status = f"失败: {r['error']}"
        elif r.get("skipped"):
            status = f"跳过: {r.get('reason', '')}"
        else:
            status = f"{r.get('action', 'ok')} · wp_status={r.get('wp_status', '—')}"
            if r.get("link"):
                status += f" · {r['link']}"
        print(f"  [{aid}] {title} — {status}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MolSimulX Markdown → WordPress")
    parser.add_argument(
        "articles",
        nargs="*",
        metavar="ID",
        help="一篇或多篇文章编号，如 T01 或 T02 T03 T04",
    )
    parser.add_argument(
        "--id",
        dest="article_ids",
        nargs="+",
        metavar="ID",
        help="文章编号（可多个），支持 T02,T03 或重复传入",
    )
    parser.add_argument("--file", help="Markdown 路径、相对路径，或唯一文件名（如 Git简明使用教程.md）")
    parser.add_argument("--list", action="store_true", help="列出文章编号与标题")
    parser.add_argument("--pick", action="store_true", help="交互式选择文章")
    parser.add_argument("--all-reviewed", action="store_true", help="发布 content_root 下全部教程（仍受 status 门禁）")
    parser.add_argument("--dry-run", action="store_true", help="只转换，不请求 WordPress（图片不上传）")
    parser.add_argument("--force", action="store_true", help="忽略 YAML status 门禁")
    parser.add_argument(
        "--strict-links",
        action="store_true",
        help="未发布站内链接改为纯文字「（待发布）」，不用灰色样式",
    )
    parser.add_argument(
        "--guess-links",
        action="store_true",
        help="未发布篇目也按文件名猜 slug 生成链接（可能 404，不推荐）",
    )
    parser.add_argument("--write-back-id", action="store_true", help="成功后回写 wp_post_id 到 md（不改 status）")
    parser.add_argument(
        "--skip-sync-images",
        action="store_true",
        help="跳过发布前的 sync_article_images（默认会自动整理配图并回写 md）",
    )
    parser.add_argument(
        "--keep-image-sources",
        action="store_true",
        help="发布后仍保留 images/ 散落源图（默认会清理重复件；original/ 归档始终保留）",
    )
    parser.add_argument(
        "--status",
        choices=["draft", "publish", "private"],
        help="覆盖 .env 默认文章状态（默认 draft；直接上线请用 --publish）",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="直接发布到 WordPress（等同 --status publish，默认仍为 draft）",
    )
    parser.add_argument(
        "--keep-layout",
        action="store_true",
        help="更新文章时保留 WP 上已有 Kadence 版式，仅替换 wp:html 正文（默认会重新套用母版 650）",
    )
    parser.add_argument(
        "--refresh-template",
        action="store_true",
        help="dry-run 时强制从 WP 拉取最新母版（在线发布默认每次已从 WP 读取）",
    )
    args = parser.parse_args()

    if args.publish and args.status:
        parser.error("--publish 与 --status 不能同时使用")
    status_override = "publish" if args.publish else args.status

    if args.list:
        resolve_article_path(list_only=True)
        sys.exit(0)

    cfg = load_settings()

    if args.all_reviewed:
        paths = collect_md_files()
    elif args.pick:
        try:
            resolved = resolve_article_path(pick=True)
        except ValueError as e:
            parser.error(str(e))
        if resolved is None:
            parser.error("未解析到文章")
        paths = [resolved]
    elif args.file:
        if args.articles or args.article_ids:
            parser.error("--file 不能与文章编号同时使用")
        try:
            resolved = resolve_article_path(file=args.file)
        except ValueError as e:
            parser.error(str(e))
        if resolved is None:
            parser.error("未解析到文章")
        paths = [resolved]
    else:
        id_tokens = list(args.articles or [])
        if args.article_ids:
            id_tokens.extend(args.article_ids)
        if not id_tokens:
            parser.error("请指定一篇或多篇文章编号、--file、--pick 或 --all-reviewed")
        try:
            paths = find_by_ids(id_tokens)
        except ValueError as e:
            parser.error(str(e))

    exit_code = 0
    batch_results: list[dict[str, Any]] = []
    for p in paths:
        if not p.exists():
            print(f"跳过（不存在）: {p}")
            batch_results.append({"file": str(p), "skipped": True, "reason": "文件不存在"})
            continue
        print(f"处理: {p}")
        try:
            res = publish_file(
                p,
                cfg,
                dry_run=args.dry_run,
                status_override=status_override,
                force=args.force,
                strict_links=args.strict_links,
                write_back_id=args.write_back_id,
                sync_images=not args.skip_sync_images,
                prune_image_sources=not args.keep_image_sources,
                refresh_template=args.refresh_template,
                keep_layout=args.keep_layout,
                guess_unpublished=args.guess_links,
            )
            print(json.dumps(res, ensure_ascii=False, indent=2))
            batch_results.append(res)
            if res.get("skipped"):
                continue
        except (requests.HTTPError, ValueError) as e:
            exit_code = 1
            err = (
                f"HTTP {e.response.status_code} {e.response.text[:800]}"
                if isinstance(e, requests.HTTPError)
                else str(e)
            )
            print(f"错误: {err}", file=sys.stderr)
            batch_results.append({"file": str(p), "error": err})

    print_batch_summary(batch_results)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
