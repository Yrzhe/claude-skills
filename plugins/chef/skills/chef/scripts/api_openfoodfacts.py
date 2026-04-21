"""Open Food Facts — 查单食材/产品的营养。

用法:
  python scripts/api_openfoodfacts.py --query "鸡蛋"
  python scripts/api_openfoodfacts.py --query "chicken breast" --lang en
  python scripts/api_openfoodfacts.py --barcode 3017620422003
"""
from __future__ import annotations
import argparse
import json
import sys
from urllib.parse import quote
from _lib import load_source_config

try:
    import requests
except ImportError:
    print("缺 requests，运行 python scripts/setup.py --yes")
    sys.exit(1)


CFG = load_source_config("openfoodfacts")
UA = "chef-skill/1.0 (personal-use)"


def base_url(lang: str) -> str:
    if lang == "zh":
        return CFG["access_details"]["cn_base_url"]
    return CFG["access_details"]["base_url"]


def search(q: str, limit: int = 5, lang: str = "zh"):
    """先试 v2 Search-a-licious，503 回退 v1 cgi，都挂就返回空并打印提示。"""
    fields = "product_name,brands,code,nutriments,nutriscore_grade"
    candidates = [
        f"{base_url(lang)}/api/v2/search?search_terms={quote(q)}&page_size={limit}&fields={fields}",
        f"{base_url(lang)}/cgi/search.pl?search_terms={quote(q)}&search_simple=1&action=process&json=1&page_size={limit}",
    ]
    last_err = None
    for url in candidates:
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
            if r.status_code == 503:
                last_err = f"503 {url}"
                continue
            r.raise_for_status()
            return (r.json().get("products") or [])
        except Exception as e:
            last_err = str(e)
            continue
    print(f"  OpenFoodFacts 搜索端点都挂了（最后错误：{last_err}）", file=sys.stderr)
    print(f"  建议用条码：python scripts/api_openfoodfacts.py --barcode <code>", file=sys.stderr)
    return []


def by_barcode(code: str, lang: str = "zh"):
    url = f"{base_url(lang)}/api/v2/product/{code}.json"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
    r.raise_for_status()
    d = r.json()
    return d.get("product") or {}


def summarize(p: dict) -> dict:
    n = p.get("nutriments") or {}
    return {
        "name": (p.get("product_name") or p.get("product_name_en") or
                 p.get("product_name_zh") or p.get("generic_name") or ""),
        "brand": p.get("brands", ""),
        "barcode": p.get("code"),
        "calories_kcal_per_100g": n.get("energy-kcal_100g"),
        "protein_g_per_100g": n.get("proteins_100g"),
        "fat_g_per_100g": n.get("fat_100g"),
        "carbs_g_per_100g": n.get("carbohydrates_100g"),
        "sugar_g_per_100g": n.get("sugars_100g"),
        "sodium_g_per_100g": n.get("sodium_100g"),
        "fiber_g_per_100g": n.get("fiber_100g"),
        "nutriscore": p.get("nutriscore_grade"),
    }


def print_summary(s: dict) -> None:
    if s["calories_kcal_per_100g"] is None and not s["name"]:
        return
    print(f"- {s['name']}" + (f"  [{s['brand']}]" if s["brand"] else ""))
    if s["calories_kcal_per_100g"] is not None:
        print(f"    per 100g: {s['calories_kcal_per_100g']} kcal  "
              f"蛋白 {s['protein_g_per_100g']}g  脂肪 {s['fat_g_per_100g']}g  "
              f"碳水 {s['carbs_g_per_100g']}g")
    if s["nutriscore"]:
        print(f"    nutriscore: {s['nutriscore']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", help="食材/产品名")
    ap.add_argument("--barcode", help="条码")
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--lang", choices=["zh", "en"], default="zh")
    ap.add_argument("--fmt", choices=["list", "json"], default="list")
    args = ap.parse_args()

    if args.barcode:
        p = by_barcode(args.barcode, args.lang)
        s = summarize(p)
        if args.fmt == "json":
            print(json.dumps(s, ensure_ascii=False, indent=2))
        else:
            print_summary(s)
        return

    if args.query:
        results = [summarize(p) for p in search(args.query, args.limit, args.lang)]
        if args.fmt == "json":
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for s in results:
                print_summary(s)
        return

    ap.error("--query 或 --barcode 必选一个")


if __name__ == "__main__":
    main()
