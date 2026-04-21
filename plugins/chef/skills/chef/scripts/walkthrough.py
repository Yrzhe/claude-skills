"""Render a recipe md as a cooking-class walkthrough (食材 + 步骤 + 营养 + 来源)."""
from __future__ import annotations
import argparse
from pathlib import Path
from _lib import parse_frontmatter


def render(meta: dict, body: str) -> str:
    out: list = []
    out.append(f"# {meta.get('title', '未命名')}")
    if meta.get("title_en"):
        out.append(f"*{meta['title_en']}*")
    out.append("")

    bits = []
    if meta.get("cuisine"):
        bits.append(f"菜系：{meta['cuisine']}")
    if meta.get("category"):
        bits.append(f"类别：{meta['category']}")
    t = meta.get("time") or {}
    if t.get("total_min"):
        bits.append(f"总耗时：{t['total_min']} 分钟")
    elif t.get("cook_min"):
        bits.append(f"烹饪：{t['cook_min']} 分钟")
    if meta.get("servings"):
        bits.append(f"份量：{meta['servings']} 人")
    if meta.get("difficulty"):
        bits.append(f"难度：{meta['difficulty']}")
    if bits:
        out.append(" · ".join(bits))
        out.append("")

    ings = meta.get("ingredients") or []
    if ings:
        out.append("## 食材")
        by_group: dict = {}
        for i in ings:
            if isinstance(i, dict):
                by_group.setdefault(i.get("group") or "", []).append(i)
            else:
                by_group.setdefault("", []).append({"name": str(i)})
        for group, items in by_group.items():
            if group:
                out.append(f"**{group}**")
            for i in items:
                name = i.get("name", "")
                amt = i.get("amount")
                unit = i.get("unit", "")
                line = f"- {name}"
                if amt not in (None, ""):
                    line += f"  {amt}{unit}".rstrip()
                if i.get("note"):
                    line += f"  （{i['note']}）"
                out.append(line)
        out.append("")

    out.append(body.strip())
    out.append("")

    n = meta.get("nutrition") or {}
    if n:
        out.append("## 营养（每份估算）")
        for key, label, unit in [
            ("calories_kcal", "热量", "kcal"),
            ("protein_g", "蛋白质", "g"),
            ("fat_g", "脂肪", "g"),
            ("carbs_g", "碳水", "g"),
            ("sodium_mg", "钠", "mg"),
        ]:
            if n.get(key) not in (None, ""):
                out.append(f"- {label}：{n[key]} {unit}")
        if n.get("estimated"):
            out.append(f"> 数据为估算，来源：{n.get('source', 'unknown')}")
        out.append("")

    src = meta.get("source") or {}
    if src.get("url") or src.get("site"):
        label = src.get("site", "")
        url = src.get("url", "")
        if url:
            out.append(f"> 来源：{label} · {url}")
        else:
            out.append(f"> 来源：{label}")

    return "\n".join(out).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, required=True)
    args = ap.parse_args()
    text = args.file.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    print(render(meta, body))


if __name__ == "__main__":
    main()
