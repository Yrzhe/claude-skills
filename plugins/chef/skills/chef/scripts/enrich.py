"""诊断一个本地食谱缺什么字段，给出补全建议的命令。

用法:
  python scripts/enrich.py --file data/recipes/red-braised-pork.md
"""
from __future__ import annotations
import argparse
from pathlib import Path
from _lib import parse_frontmatter


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, required=True)
    args = ap.parse_args()

    text = args.file.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    gaps = []
    if not meta.get("ingredients"):
        gaps.append("ingredients")
    # amounts: 所有食材都有 amount 吗
    ings = meta.get("ingredients") or []
    if ings and not any(isinstance(i, dict) and i.get("amount") for i in ings):
        gaps.append("ingredient_amounts")
    if "## 步骤" not in body and "steps" not in body.lower():
        gaps.append("steps")
    if not ((meta.get("nutrition") or {}).get("calories_kcal")):
        gaps.append("nutrition")
    if not (meta.get("time") or {}).get("total_min"):
        gaps.append("time")
    if not meta.get("servings"):
        gaps.append("servings")

    print(f"文件：{args.file}")
    print(f"标题：{meta.get('title','?')}")
    print(f"缺失：{gaps or '无'}")
    print()

    if not gaps:
        return

    src = meta.get("source") or {}
    print("建议：")
    if {"ingredients", "ingredient_amounts", "steps"} & set(gaps):
        if src.get("url"):
            print(f"  重抓原页补齐：")
            print(f"    python scripts/scrape_web.py --url '{src['url']}' --source {src.get('site','')}")
        else:
            site_hint = src.get("site", "<some-source>")
            print(f"  python scripts/fetch.py --source {site_hint} --query \"{meta.get('title','')}\"")
    if "nutrition" in gaps:
        names = []
        for i in ings:
            if isinstance(i, dict) and i.get("name"):
                names.append(i["name"])
        if names:
            print(f"  逐食材查营养（按克重汇总后标 estimated: true）：")
            for n in names[:5]:
                print(f"    python scripts/api_openfoodfacts.py --query '{n}'")
    if "time" in gaps or "servings" in gaps:
        print("  Read 原页或源数据补 frontmatter.time / servings。")


if __name__ == "__main__":
    main()
