"""Given ingredients I have, suggest recipes ranked by coverage.

Examples:
  python scripts/suggest.py --have "鸡蛋,西红柿,葱"
  python scripts/suggest.py --have "eggs,tomato,scallion" --min-match 2 --max-missing 3
"""
from __future__ import annotations
import argparse
from _lib import iter_recipes, ingredient_names, ing_match


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--have", required=True, help="逗号分隔食材")
    ap.add_argument("--min-match", type=int, default=2, help="至少命中 N 个（默认 2）")
    ap.add_argument("--max-missing", type=int, default=5, help="食谱最多还缺 N 个食材")
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    have = [h.strip() for h in args.have.split(",") if h.strip()]
    if not have:
        ap.error("--have 空了")

    scored = []
    for path, meta, _ in iter_recipes():
        ings = ingredient_names(meta)
        if not ings:
            continue
        hit = []
        for i in ings:
            if any(ing_match(w, i) for w in have):
                hit.append(i)
        m = len(hit)
        missing_count = len(ings) - m
        if m < args.min_match:
            continue
        if missing_count > args.max_missing:
            continue
        ratio = m / max(len(have), 1)
        scored.append((m, -missing_count, ratio, path, meta, hit, ings))

    scored.sort(reverse=True)
    if not scored:
        print("（没有足够命中的菜。可能 data 还空，或降低 --min-match 再试）")
        return

    for m, negmiss, ratio, path, meta, hit, ings in scored[: args.limit]:
        need = [i for i in ings if i not in hit]
        need_short = ", ".join(need[:5]) + ("..." if len(need) > 5 else "")
        title = meta.get("title", "?")
        cuisine = meta.get("cuisine", "")
        print(f"- {title}  [{cuisine}]  命中 {m}/{len(have)}  还缺 {len(need)}: {need_short}")
        print(f"  走菜: python scripts/walkthrough.py --file '{path}'")


if __name__ == "__main__":
    main()
