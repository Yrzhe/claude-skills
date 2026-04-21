"""Batch-import Kaggle / HuggingFace datasets → data/recipes/*.md.

Supported sources (defined by sources/*.json):
  - food_com      (CSV：RAW_recipes.csv)
  - epicurious    (JSON：full_format_recipes.json)
  - tada_chinese  (需手写 adapter，参考 food_com)
"""
from __future__ import annotations
import argparse
import ast
import csv
import json
import sys
import time
from pathlib import Path
from _lib import write_recipe


def _py_literal(s):
    try:
        return ast.literal_eval(s) if s else []
    except Exception:
        return []


def import_food_com(file: Path, limit):
    n = 0
    with file.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if limit and n >= limit:
                break
            title = (row.get("name") or "").strip()
            if not title:
                continue
            ings = _py_literal(row.get("ingredients", "[]"))
            steps = _py_literal(row.get("steps", "[]"))
            tags = _py_literal(row.get("tags", "[]"))
            nutr = _py_literal(row.get("nutrition", "[]"))

            meta = {
                "title": title,
                "language": "en",
                "cuisine": "美式/全球",
                "source": {
                    "site": "food.com",
                    "url": f"https://www.food.com/recipe/{row.get('id')}",
                    "external_id": row.get("id"),
                    "dataset": "kaggle-food_com",
                    "imported_at": time.strftime("%Y-%m-%d"),
                },
                "tags": tags,
                "ingredients": [{"name": str(i)} for i in ings],
            }
            if row.get("minutes"):
                try:
                    meta["time"] = {"total_min": int(row["minutes"])}
                except Exception:
                    pass
            if isinstance(nutr, list) and len(nutr) == 7:
                meta["nutrition"] = {
                    "calories_kcal": nutr[0],
                    "fat_pdv": nutr[1],
                    "sugar_pdv": nutr[2],
                    "sodium_pdv": nutr[3],
                    "protein_pdv": nutr[4],
                    "saturated_fat_pdv": nutr[5],
                    "carbs_pdv": nutr[6],
                    "source": "food.com dataset (PDV = Percent Daily Value)",
                    "estimated": False,
                }

            body = ["## 简介"] if row.get("description") else []
            if row.get("description"):
                body += [row["description"].strip(), ""]
            body.append("## 步骤")
            for i, s in enumerate(steps, 1):
                body.append(f"{i}. {s}")
            body += ["", "## 来源",
                     f"- food.com (Kaggle), id={row.get('id')}",
                     f"- url: {meta['source']['url']}"]
            write_recipe(meta, "\n".join(body))
            n += 1
            if n % 200 == 0:
                print(f"  imported {n}...")
    print(f"food_com done: {n} recipes.")


def import_epicurious(file: Path, limit):
    if file.suffix.lower() != ".json":
        print("epicurious: 期望 full_format_recipes.json")
        return
    data = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print("epicurious: 期望 JSON array")
        return
    n = 0
    for row in data:
        if limit and n >= limit:
            break
        if not isinstance(row, dict):
            continue
        title = (row.get("title") or "").strip()
        if not title:
            continue
        ings = row.get("ingredients") or []
        steps = row.get("directions") or []
        cats = row.get("categories") or []
        meta = {
            "title": title,
            "language": "en",
            "cuisine": "美式精品",
            "source": {
                "site": "epicurious.com",
                "dataset": "kaggle-epicurious",
                "imported_at": time.strftime("%Y-%m-%d"),
            },
            "tags": cats,
            "ingredients": [{"name": str(i)} for i in ings],
        }
        if row.get("rating") is not None:
            meta["rating"] = row["rating"]
        nutr_keys = ("calories", "protein", "fat", "sodium")
        if any(row.get(k) is not None for k in nutr_keys):
            meta["nutrition"] = {
                "calories_kcal": row.get("calories"),
                "protein_g": row.get("protein"),
                "fat_g": row.get("fat"),
                "sodium_mg": row.get("sodium"),
                "source": "epicurious dataset",
                "estimated": False,
            }
        body = []
        if row.get("desc"):
            body += ["## 简介", row["desc"].strip(), ""]
        body.append("## 步骤")
        for i, s in enumerate(steps, 1):
            body.append(f"{i}. {s}")
        body += ["", "## 来源", "- epicurious.com (Kaggle 预爬)"]
        write_recipe(meta, "\n".join(body))
        n += 1
        if n % 200 == 0:
            print(f"  imported {n}...")
    print(f"epicurious done: {n} recipes.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True,
                    choices=["food_com", "epicurious", "tada_chinese"])
    ap.add_argument("--file", type=Path, required=True)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    if not args.file.exists():
        print(f"文件不存在：{args.file}")
        sys.exit(1)

    if args.source == "food_com":
        import_food_com(args.file, args.limit)
    elif args.source == "epicurious":
        import_epicurious(args.file, args.limit)
    elif args.source == "tada_chinese":
        print("Ta-da 仓库结构不固定。Read 文件后手写 adapter；参考 import_food_com。")


if __name__ == "__main__":
    main()
