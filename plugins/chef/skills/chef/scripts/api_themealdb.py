"""TheMealDB free API client. Saves to data/recipes/.

Usage:
  python scripts/api_themealdb.py --search 'chicken'
  python scripts/api_themealdb.py --random
  python scripts/api_themealdb.py --area Chinese
  python scripts/api_themealdb.py --bootstrap
"""
from __future__ import annotations
import argparse
import string
import sys
import time
from urllib.parse import quote
from _lib import load_source_config, write_recipe

try:
    import requests
except ImportError:
    print("缺 requests，运行：python scripts/setup.py --yes")
    sys.exit(1)


CFG = load_source_config("themealdb")
BASE = CFG["access_details"]["base_url"]
UA = "chef-skill/1.0"


def get_json(path: str) -> dict:
    r = requests.get(BASE + path, headers={"User-Agent": UA}, timeout=20)
    r.raise_for_status()
    return r.json()


def meal_to_recipe(m: dict):
    ings: list = []
    for i in range(1, 21):
        n = (m.get(f"strIngredient{i}") or "").strip()
        q = (m.get(f"strMeasure{i}") or "").strip()
        if not n:
            continue
        ing = {"name": n}
        if q:
            ing["amount"] = q
        ings.append(ing)

    instr = m.get("strInstructions", "") or ""
    steps = [s.strip() for s in instr.split("\r\n") if s.strip()]
    if len(steps) < 2:
        steps = [s.strip() for s in instr.split("\n") if s.strip()]
    if len(steps) < 2 and instr:
        steps = [s.strip() + "." for s in instr.split(".") if s.strip()]

    meta = {
        "title": m.get("strMeal", ""),
        "language": "en",
        "cuisine": m.get("strArea"),
        "category": m.get("strCategory"),
        "tags": [t.strip() for t in (m.get("strTags") or "").split(",") if t.strip()],
        "source": {
            "site": "themealdb",
            "url": m.get("strSource") or f"https://www.themealdb.com/meal/{m.get('idMeal')}",
            "external_id": m.get("idMeal"),
            "scraped_at": time.strftime("%Y-%m-%d"),
        },
        "image": m.get("strMealThumb"),
        "ingredients": ings,
    }
    if m.get("strYoutube"):
        meta["video"] = m["strYoutube"]

    body_lines = ["## 步骤"]
    for i, s in enumerate(steps, 1):
        body_lines.append(f"{i}. {s}")
    body_lines += ["", "## 来源", f"- TheMealDB: {meta['source']['url']}"]
    if meta.get("video"):
        body_lines.append(f"- 视频：{meta['video']}")
    return meta, "\n".join(body_lines)


def save_meal(m: dict):
    meta, body = meal_to_recipe(m)
    return write_recipe(meta, body)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--search", help="按名字搜")
    ap.add_argument("--random", action="store_true")
    ap.add_argument("--lookup", help="按 id 查单菜")
    ap.add_argument("--ingredient", help="按食材过滤")
    ap.add_argument("--area", help="按地区/菜系（Chinese/Italian/Mexican...）")
    ap.add_argument("--category", help="按分类（Beef/Chicken/Seafood/Dessert/...）")
    ap.add_argument("--bootstrap", action="store_true", help="按首字母 a-z 拉全量（~283）")
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    if args.search:
        data = get_json(f"/search.php?s={quote(args.search)}")
        for m in (data.get("meals") or [])[: args.limit]:
            p = save_meal(m)
            print(f"- {m.get('strMeal')} → {p}")
        return

    if args.random:
        data = get_json("/random.php")
        for m in (data.get("meals") or []):
            p = save_meal(m)
            print(f"- {m.get('strMeal')} → {p}")
        return

    if args.lookup:
        data = get_json(f"/lookup.php?i={args.lookup}")
        for m in (data.get("meals") or []):
            p = save_meal(m)
            print(f"- {m.get('strMeal')} → {p}")
        return

    def _filter_then_lookup(endpoint: str):
        data = get_json(endpoint)
        ids = [m.get("idMeal") for m in (data.get("meals") or []) if m.get("idMeal")]
        print(f"命中 {len(ids)} 道。逐个拉详情...")
        for mid in ids[: args.limit]:
            d = get_json(f"/lookup.php?i={mid}")
            for m in (d.get("meals") or []):
                save_meal(m)
            time.sleep(1)

    if args.ingredient:
        _filter_then_lookup(f"/filter.php?i={quote(args.ingredient)}")
        return
    if args.area:
        _filter_then_lookup(f"/filter.php?a={quote(args.area)}")
        return
    if args.category:
        _filter_then_lookup(f"/filter.php?c={quote(args.category)}")
        return

    if args.bootstrap:
        seen = set()
        total = 0
        for ch in string.ascii_lowercase:
            try:
                data = get_json(f"/search.php?f={ch}")
            except Exception as e:
                print(f"  letter {ch} failed: {e}", file=sys.stderr)
                continue
            for m in (data.get("meals") or []):
                mid = m.get("idMeal")
                if mid in seen:
                    continue
                seen.add(mid)
                save_meal(m)
                total += 1
            print(f"  {ch}: cumulative {total}")
            time.sleep(1)
        print(f"bootstrap 完成，共 {total} 道。")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
