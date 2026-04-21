"""Search data/recipes/*.md by name/ingredient/tag/cuisine/random."""
from __future__ import annotations
import argparse
import json
import random
from _lib import iter_recipes, ingredient_names, ing_match


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", help="标题包含（模糊）")
    ap.add_argument("--ingredient", action="append", default=[], help="食材含（可多次, AND）")
    ap.add_argument("--tag", action="append", default=[], help="tag（可多次, AND）")
    ap.add_argument("--cuisine", help="菜系过滤")
    ap.add_argument("--random", action="store_true", help="随机返回 1 道")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--fmt", choices=["list", "json", "paths"], default="list")
    args = ap.parse_args()

    hits = []
    for path, meta, _ in iter_recipes():
        title = (meta.get("title") or "") + " " + str(meta.get("title_en") or "")
        if args.name and args.name.lower() not in title.lower():
            continue
        tags = [str(t).lower() for t in (meta.get("tags") or [])]
        if args.tag and not all(t.lower() in " ".join(tags) for t in args.tag):
            continue
        if args.cuisine and args.cuisine not in str(meta.get("cuisine") or ""):
            continue
        if args.ingredient:
            ings = ingredient_names(meta)
            if not all(any(ing_match(w, i) for i in ings) for w in args.ingredient):
                continue
        hits.append((path, meta))

    if args.random and hits:
        hits = [random.choice(hits)]
    hits = hits[: args.limit]

    if not hits:
        print("（无命中。data/recipes/ 可能为空——试试 api_themealdb.py --bootstrap）")
        return

    if args.fmt == "json":
        print(json.dumps(
            [{"path": str(p), "title": m.get("title"), "cuisine": m.get("cuisine"),
              "tags": m.get("tags"), "source": (m.get("source") or {}).get("site")}
             for p, m in hits],
            ensure_ascii=False, indent=2))
    elif args.fmt == "paths":
        for p, _ in hits:
            print(p)
    else:
        for p, m in hits:
            src = (m.get("source") or {}).get("site", "")
            tags = ",".join(str(t) for t in (m.get("tags") or [])[:3])
            print(f"- {m.get('title','?')}  [{m.get('cuisine','')}]  源:{src}  tag:{tags}  {p}")


if __name__ == "__main__":
    main()
