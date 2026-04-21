"""Web scraper: 先试 recipe-scrapers，失败回退 JSON-LD Recipe schema。

用法:
  python scripts/scrape_web.py --url https://www.allrecipes.com/recipe/...
  python scripts/scrape_web.py --source xiachufang --query 红烧肉
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from _lib import load_source_config, write_recipe

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

try:
    from recipe_scrapers import scrape_me
    _HAS_RS = True
except ImportError:
    _HAS_RS = False


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15) chef-skill/1.0"


def require_requests() -> None:
    if not _HAS_REQUESTS:
        print("缺 requests。运行：python scripts/setup.py --yes")
        sys.exit(1)


def fetch_html(url: str) -> str:
    require_requests()
    r = requests.get(url, headers={"User-Agent": UA}, timeout=20, allow_redirects=True)
    if "humancheck" in r.url.lower() or "captcha" in r.url.lower():
        raise RuntimeError(f"触发风控：重定向到 {r.url}（人机校验）——暂停该域批量，加大延迟")
    r.raise_for_status()
    return r.text


INGREDIENT_HEADING_KW = [
    "ingredients", "ingredient", "食材", "用料", "食材明細", "食材明细",
    "預備食材", "配料", "主料", "輔料", "辅料"
]
STEP_HEADING_KW = [
    "directions", "instructions", "method", "preparation",
    "步驟", "步骤", "做法", "料理步驟", "烹飪步驟", "制作步骤"
]


def via_heading_anchor(url: str) -> Optional[dict]:
    """Report 给的策略：不依赖 CSS class，靠 h1/h2/h3 文字锚点抽主字段。
    对国内/台湾社区站和所有 heading 结构规整的页面稳定。"""
    try:
        html = fetch_html(url)
    except Exception as e:
        print(f"  fetch 失败: {e}", file=sys.stderr)
        return None
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("  heading-anchor 需要 beautifulsoup4，跳过（运行 setup.py）", file=sys.stderr)
        return None
    soup = BeautifulSoup(html, "lxml" if _has_lxml() else "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(" ", strip=True) if title_tag else ""

    def _collect_after(head_tag) -> list:
        buf: list = []
        for sib in head_tag.find_all_next():
            if sib is head_tag:
                continue
            if sib.name in {"h1", "h2"}:
                break
            text = sib.get_text(" ", strip=True) if hasattr(sib, "get_text") else str(sib).strip()
            if text and len(text) < 800:  # filter boilerplate
                buf.append(text)
        return buf

    def _find_by_keywords(kws: list) -> list:
        for tag in soup.find_all(["h2", "h3"]):
            txt = tag.get_text(" ", strip=True).lower()
            for kw in kws:
                if kw.lower() in txt:
                    return _collect_after(tag)
        return []

    ingredients_raw = _find_by_keywords(INGREDIENT_HEADING_KW)
    steps_raw = _find_by_keywords(STEP_HEADING_KW)

    if not (title and (ingredients_raw or steps_raw)):
        return None

    # 粗粒度分步：过滤短噪声 + 去重
    seen = set()
    steps = []
    for s in steps_raw:
        if len(s) < 4 or s in seen:
            continue
        seen.add(s)
        steps.append(s)

    ings = []
    for i in ingredients_raw:
        if len(i) < 2 or len(i) > 200:
            continue
        ings.append({"name": i})

    return {"title": title, "ingredients": ings, "steps": steps}


def _has_lxml() -> bool:
    try:
        import lxml  # noqa
        return True
    except ImportError:
        return False


def parse_jsonld(html: str) -> Optional[dict]:
    blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.S | re.I,
    )
    for b in blocks:
        try:
            data = json.loads(b.strip())
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            t = item.get("@type")
            if t == "Recipe" or (isinstance(t, list) and "Recipe" in t):
                return item
            if isinstance(item.get("@graph"), list):
                for g in item["@graph"]:
                    if isinstance(g, dict):
                        gt = g.get("@type")
                        if gt == "Recipe" or (isinstance(gt, list) and "Recipe" in gt):
                            return g
    return None


def via_recipe_scrapers(url: str) -> Optional[dict]:
    """recipe-scrapers v15+ 自动尝试 JSON-LD 兜底，不再需要 wild_mode 参数。"""
    if not _HAS_RS:
        return None
    try:
        s = scrape_me(url)
        out = {"title": s.title()}
        try:
            out["ingredients"] = [{"name": x} for x in s.ingredients()]
        except Exception:
            out["ingredients"] = []
        try:
            out["steps"] = s.instructions_list()
        except Exception:
            try:
                out["steps"] = [l.strip() for l in s.instructions().split("\n") if l.strip()]
            except Exception:
                out["steps"] = []
        for attr, key in [
            ("total_time", "total_time"), ("yields", "servings"),
            ("image", "image"), ("author", "author"),
            ("cuisine", "cuisine"), ("category", "category"),
        ]:
            if hasattr(s, attr):
                try:
                    v = getattr(s, attr)()
                    if v:
                        out[key] = v
                except Exception:
                    pass
        try:
            out["nutrition"] = s.nutrients()
        except Exception:
            pass
        return out
    except Exception as e:
        print(f"  recipe-scrapers 失败，走 JSON-LD 兜底: {e}", file=sys.stderr)
        return None


def via_jsonld(url: str) -> Optional[dict]:
    try:
        html = fetch_html(url)
    except Exception as e:
        print(f"  fetch 失败: {e}", file=sys.stderr)
        return None
    ld = parse_jsonld(html)
    if not ld:
        return None

    ings_raw = ld.get("recipeIngredient") or []
    steps: list = []
    instr = ld.get("recipeInstructions")
    if isinstance(instr, str):
        steps = [p.strip() for p in re.split(r"[\n\.]+", instr) if p.strip()]
    elif isinstance(instr, list):
        for it in instr:
            if isinstance(it, dict):
                if it.get("@type") == "HowToSection" and isinstance(it.get("itemListElement"), list):
                    for sub in it["itemListElement"]:
                        if isinstance(sub, dict):
                            steps.append(sub.get("text") or sub.get("name") or "")
                else:
                    steps.append(it.get("text") or it.get("name") or "")
            else:
                steps.append(str(it))

    img = ld.get("image")
    if isinstance(img, list):
        img = img[0] if img else None
    elif isinstance(img, dict):
        img = img.get("url")

    out = {
        "title": ld.get("name", ""),
        "description": ld.get("description", ""),
        "ingredients": [{"name": str(i)} for i in ings_raw],
        "steps": steps,
        "servings": ld.get("recipeYield"),
        "image": img,
        "cuisine": ld.get("recipeCuisine"),
        "category": ld.get("recipeCategory"),
    }
    nutrition = ld.get("nutrition") or {}
    if isinstance(nutrition, dict):
        n = {}
        for k, v in nutrition.items():
            if k == "@type":
                continue
            n[k] = v
        if n:
            out["nutrition"] = n
    return out


def normalize(raw: dict, url: str, source_id: str) -> tuple:
    meta = {
        "title": raw.get("title", ""),
        "cuisine": raw.get("cuisine"),
        "category": raw.get("category"),
        "source": {
            "site": source_id,
            "url": url,
            "scraped_at": time.strftime("%Y-%m-%d"),
        },
        "ingredients": raw.get("ingredients", []),
    }
    if raw.get("servings"):
        meta["servings"] = raw["servings"]
    if raw.get("total_time"):
        meta["time"] = {"total_min": raw["total_time"]}
    if raw.get("image"):
        meta["image"] = raw["image"]
    if raw.get("author"):
        meta["source"]["author"] = raw["author"]
    if raw.get("nutrition"):
        meta["nutrition"] = raw["nutrition"]

    body_lines: list = []
    if raw.get("description"):
        body_lines += ["## 简介", str(raw["description"]).strip(), ""]
    steps = raw.get("steps") or []
    if steps:
        body_lines.append("## 步骤")
        for i, s in enumerate(steps, 1):
            body_lines.append(f"{i}. {s}")
        body_lines.append("")
    body_lines += ["## 来源", f"- 站点：{source_id}", f"- URL：{url}"]
    return meta, "\n".join(body_lines)


def scrape_one(url: str, source_id: str = "web") -> Optional[Path]:
    print(f"  scraping: {url}")
    raw = via_recipe_scrapers(url)
    if not raw or not raw.get("title"):
        raw = via_jsonld(url)
    if not raw or not raw.get("title"):
        raw = via_heading_anchor(url)
    if not raw or not raw.get("title"):
        print(f"  ✗ 无法解析 {url}（三层兜底全失败）", file=sys.stderr)
        return None
    meta, body = normalize(raw, url, source_id)
    path = write_recipe(meta, body)
    print(f"  ✓ {meta['title']} → {path}")
    return path


def discover_urls(source_cfg: dict, query: str, limit: int) -> list:
    det = source_cfg.get("access_details", {})
    tpl = det.get("search_url")
    if not tpl:
        for u in det.get("list_urls", []):
            if "{query}" in u:
                tpl = u
                break
    if not tpl:
        return []
    url = tpl.format(query=quote(query))
    print(f"  search: {url}")
    try:
        html = fetch_html(url)
    except Exception as e:
        print(f"  search 失败: {e}", file=sys.stderr)
        return []
    patterns = [r"/recipe/", r"/recipes/", r"/cookbook/", r"/zuofa/", r"/caipu/"]
    urls = []
    for m in re.finditer(r'href=["\'](?P<u>[^"\']+)["\']', html):
        u = m.group("u")
        if u.startswith("/"):
            from urllib.parse import urljoin
            u = urljoin(source_cfg.get("site", ""), u)
        if not u.startswith("http"):
            continue
        if any(p in u for p in patterns):
            urls.append(u)
    # dedupe keeping order
    seen, out = set(), []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
        if len(out) >= limit:
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--source", default="web")
    ap.add_argument("--query")
    ap.add_argument("--category")
    ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    if args.url:
        scrape_one(args.url, args.source)
        return

    if args.query and args.source and args.source != "web":
        cfg = load_source_config(args.source)
        urls = discover_urls(cfg, args.query, args.limit)
        if not urls:
            print("未发现候选 URL。可能 search_url 模板失败；直接用 --url 指定单个食谱。")
            return
        print(f"  发现 {len(urls)} 个候选")
        for u in urls:
            try:
                scrape_one(u, args.source)
                time.sleep(cfg.get("rate_limit_sec", 2))
            except Exception as e:
                print(f"  fail {u}: {e}", file=sys.stderr)
        return

    ap.error("给 --url，或 --source <id> --query <keyword>")


if __name__ == "__main__":
    main()
