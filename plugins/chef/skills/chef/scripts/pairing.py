"""Ingredient pairing — 基于 data/recipes/ 的共现统计。

用法:
  python scripts/pairing.py --pair 西红柿 鸡蛋       # 看共现多少
  python scripts/pairing.py --ingredient 猪肉 --top 15   # 最常搭配
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from _lib import iter_recipes, ingredient_names, _norm


def build_cooccurrence():
    """co[i][j] = recipes where normalized ingredient i co-occurs with j.
    Keys are lowercased/stripped so 'Chicken Breast' and 'chicken breast' merge."""
    co = defaultdict(Counter)
    total = 0
    for _, meta, _ in iter_recipes():
        ings = ingredient_names(meta)
        if not ings:
            continue
        total += 1
        seen = {_norm(i) for i in ings if _norm(i)}
        for i in seen:
            for j in seen:
                if i != j:
                    co[i][j] += 1
    return co, total


def fuzzy_keys(co: dict, query: str) -> list:
    q = _norm(query)
    return [k for k in co if q and (q in k or k in q)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", nargs=2, metavar=("A", "B"), help="两个食材共现")
    ap.add_argument("--ingredient", help="和 --top 配合")
    ap.add_argument("--top", type=int, help="最常搭配的 N 个")
    args = ap.parse_args()

    co, total = build_cooccurrence()
    if total == 0:
        print("（data/recipes/ 为空。先 bootstrap）")
        return

    if args.pair:
        a, b = args.pair
        ka = fuzzy_keys(co, a)
        kb = fuzzy_keys(co, b)
        if not ka or not kb:
            miss = a if not ka else b
            print(f"本地没见过 '{miss}'。查 references/ingredient_pairing.md 看理论依据。")
            return
        hits = 0
        for x in ka:
            for y in kb:
                hits += co[x].get(y, 0)
        print(f"{a} × {b}  共现 {hits} 次  (本地 {total} 道菜，aliases: {ka[:3]} / {kb[:3]})")
        if hits == 0:
            verdict = "→ 本地没见过这组。可能新搭配，或数据不够。查 references/ingredient_pairing.md。"
        elif hits < 3:
            verdict = "→ 小众搭配。"
        elif hits < 20:
            verdict = "→ 中频搭配。"
        else:
            verdict = "→ 经典搭配。"
        print(verdict)
        return

    if args.ingredient and args.top:
        keys = fuzzy_keys(co, args.ingredient)
        if not keys:
            print(f"本地没见过 '{args.ingredient}'。")
            return
        merged = Counter()
        for k in keys:
            merged.update(co[k])
        # 去掉自身 alias
        for k in keys:
            merged.pop(k, None)
        for partner, n in merged.most_common(args.top):
            print(f"- {partner}  {n} 次")
        return

    ap.error("给 --pair A B，或 --ingredient X --top N")


if __name__ == "__main__":
    main()
