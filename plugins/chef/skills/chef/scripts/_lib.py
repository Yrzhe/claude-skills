"""Shared helpers for chef scripts.

Paths, frontmatter IO, slug, source-config loading, ingredient helpers.
其它脚本 `from _lib import ...`。
"""
from __future__ import annotations
from pathlib import Path
import re
import json
import hashlib
from typing import Iterator, Optional, Tuple

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "recipes"
SOURCES_DIR = REPO_ROOT / "sources"
TEMPLATES_DIR = REPO_ROOT / "templates"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)


def ensure_yaml() -> None:
    if not _HAS_YAML:
        raise RuntimeError(
            "PyYAML 未安装。运行：python scripts/setup.py --yes"
        )


def load_source_config(source_id: str) -> dict:
    path = SOURCES_DIR / f"{source_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"未找到 source 配置: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def list_sources(enabled_only: bool = True) -> list:
    configs = []
    for p in sorted(SOURCES_DIR.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            cfg = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if enabled_only and not cfg.get("enabled", True):
            continue
        configs.append(cfg)
    return configs


def parse_frontmatter(md_text: str) -> Tuple[dict, str]:
    m = FRONTMATTER_RE.match(md_text)
    if not m:
        return {}, md_text
    ensure_yaml()
    front, body = m.group(1), m.group(2)
    meta = yaml.safe_load(front) or {}
    return meta, body


def serialize_frontmatter(meta: dict) -> str:
    ensure_yaml()
    return yaml.safe_dump(
        meta, allow_unicode=True, sort_keys=False, default_flow_style=False
    ).strip()


def slugify(text: str, max_len: int = 60) -> str:
    """保留中日韩字符；空格/标点转 '-'；兜底 md5。"""
    s = (text or "").strip().lower()
    s = re.sub(r"[\s/\\]+", "-", s)
    s = re.sub(r"[^\w\u4e00-\u9fff\u3400-\u4dbf\-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        s = "recipe-" + hashlib.md5((text or "").encode("utf-8")).hexdigest()[:8]
    return s[:max_len]


def make_slug(title: str, source_id: str = "", external_id: str = "") -> str:
    parts = [slugify(title)]
    if source_id:
        parts.append(slugify(source_id, 20))
    if external_id:
        parts.append(slugify(str(external_id), 20))
    return "-".join(p for p in parts if p)


def recipe_path(slug: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"{slug}.md"


def write_recipe(meta: dict, body: str, slug: Optional[str] = None, overwrite: bool = False) -> Path:
    if slug is None:
        src = meta.get("source", {}) or {}
        slug = make_slug(
            meta.get("title", "untitled"),
            src.get("site", ""),
            src.get("external_id", ""),
        )
    path = recipe_path(slug)
    if path.exists() and not overwrite:
        return path
    front = serialize_frontmatter(meta)
    text = f"---\n{front}\n---\n\n{body.strip()}\n"
    path.write_text(text, encoding="utf-8")
    return path


def iter_recipes() -> Iterator[Tuple[Path, dict, str]]:
    for p in sorted(DATA_DIR.glob("*.md")):
        try:
            text = p.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(text)
        except Exception:
            continue
        yield p, meta, body


def ingredient_names(meta: dict) -> list:
    out = []
    for ing in meta.get("ingredients") or []:
        if isinstance(ing, dict):
            name = (ing.get("name") or "").strip()
        else:
            name = str(ing).strip()
        if name:
            out.append(name)
    return out


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def ing_match(want: str, recipe_ing: str) -> bool:
    """单个食材模糊匹配：大小写不敏感，子串双向。"""
    w, r = _norm(want), _norm(recipe_ing)
    if not w or not r:
        return False
    return w in r or r in w


def match_count(recipe_ings: list, want: list) -> int:
    """want 里每个词命中 recipe_ings 某一项就 +1。大小写不敏感，子串双向。"""
    count = 0
    for w in want:
        if any(ing_match(w, r) for r in recipe_ings):
            count += 1
    return count
