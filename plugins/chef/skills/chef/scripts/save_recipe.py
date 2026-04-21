"""Save a structured recipe to data/recipes/{slug}.md.

输入 JSON 形如：
{
  "title": "红烧肉",
  "cuisine": "中餐家常",
  "source": {"site": "xiachufang", "url": "...", "external_id": "..."},
  "servings": 4,
  "time": {"total_min": 75},
  "tags": ["猪肉","红烧"],
  "ingredients": [{"name":"五花肉","amount":500,"unit":"g"}, ...],
  "steps": ["焯水...", "炒糖色...", ...],
  "description": "...",
  "notes": "...",
  "nutrition": {"calories_kcal": 520, ...}
}
"""
from __future__ import annotations
import sys
import json
import argparse
from pathlib import Path
from _lib import write_recipe


def build_body(data: dict) -> str:
    lines: list = []
    if data.get("description"):
        lines += ["## 简介", str(data["description"]).strip(), ""]
    steps = data.get("steps") or []
    if steps:
        lines.append("## 步骤")
        for i, s in enumerate(steps, 1):
            if isinstance(s, dict):
                lines.append(f"{i}. {s.get('text', '')}")
                if s.get("note"):
                    lines.append(f"   > {s['note']}")
            else:
                lines.append(f"{i}. {s}")
        lines.append("")
    if data.get("notes"):
        lines += ["## 备注", str(data["notes"]).strip(), ""]
    src = data.get("source") or {}
    if src.get("url"):
        lines += ["## 来源", f"- 站点：{src.get('site', '')}", f"- 链接：{src['url']}"]
        if src.get("author"):
            lines.append(f"- 作者：{src['author']}")
    return "\n".join(lines).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, help="JSON 文件")
    ap.add_argument("--stdin", action="store_true", help="从 stdin 读 JSON")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    if args.stdin:
        raw = sys.stdin.read()
    elif args.json:
        raw = args.json.read_text(encoding="utf-8")
    else:
        ap.error("--json 或 --stdin 必选一个")

    data = json.loads(raw)
    body = build_body(data)
    # frontmatter 去掉只属于 body 的字段
    meta = {k: v for k, v in data.items() if k not in {"steps", "description", "notes"}}
    path = write_recipe(meta, body, overwrite=args.overwrite)
    print(path)


if __name__ == "__main__":
    main()
