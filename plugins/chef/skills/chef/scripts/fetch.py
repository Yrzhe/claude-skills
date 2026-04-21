"""按 sources/{id}.json 分派到实际抓取脚本。

用法:
  python scripts/fetch.py --list-sources
  python scripts/fetch.py --source xiachufang --query 红烧肉
  python scripts/fetch.py --source themealdb --query chicken
  python scripts/fetch.py --url https://www.allrecipes.com/recipe/...
"""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path
from _lib import load_source_config, list_sources, REPO_ROOT


SCRIPTS_DIR = REPO_ROOT / "scripts"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", help="source id（见 --list-sources）")
    ap.add_argument("--url", help="直接一个 URL（走 scrape_web.py）")
    ap.add_argument("--query", help="关键词")
    ap.add_argument("--category", help="分类 / 菜系")
    ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--list-sources", action="store_true")
    args = ap.parse_args()

    if args.list_sources:
        for cfg in list_sources(enabled_only=False):
            flag = "✓" if cfg.get("enabled", True) else "✗"
            print(f"{flag} {cfg['id']:28}  {cfg['name']:30}  [{cfg['language']}]  {cfg['access_method']}")
        return

    if args.url:
        cmd = [sys.executable, str(SCRIPTS_DIR / "scrape_web.py"), "--url", args.url]
        if args.source:
            cmd += ["--source", args.source]
        sys.exit(subprocess.run(cmd).returncode)

    if not args.source:
        ap.error("需要 --source 或 --url。用 --list-sources 查看所有 source。")

    cfg = load_source_config(args.source)
    if not cfg.get("enabled", True):
        print(f"source {args.source} 已禁用。见 sources/{args.source}.json 注解。")
        sys.exit(1)

    method = cfg["access_method"]
    print(f"→ {cfg['name']}  [{method}]")
    notes = cfg.get("usage_notes")
    if notes:
        print(f"  {notes}")

    if method == "api":
        api_script = SCRIPTS_DIR / f"api_{args.source}.py"
        if not api_script.exists():
            print(f"未找到 API 客户端：{api_script}")
            print(f"见 sources/{args.source}.json 的 access_details，手写 curl 或扩展脚本。")
            sys.exit(1)
        cmd = [sys.executable, str(api_script)]
        if args.query:
            cmd += ["--search", args.query]
        sys.exit(subprocess.run(cmd).returncode)

    if method in ("scrape_list", "scrape_with_library", "hybrid"):
        cmd = [sys.executable, str(SCRIPTS_DIR / "scrape_web.py"), "--source", args.source]
        if args.query:
            cmd += ["--query", args.query]
        if args.category:
            cmd += ["--category", args.category]
        cmd += ["--pages", str(args.pages), "--limit", str(args.limit)]
        sys.exit(subprocess.run(cmd).returncode)

    if method == "dataset":
        det = cfg.get("access_details", {})
        print(f"此 source 是数据集。下载：{det.get('download_url', '')}")
        print(f"然后：python scripts/import_dataset.py --source {args.source} --file <path>")
        return

    print(f"未知 access_method: {method}")
    sys.exit(1)


if __name__ == "__main__":
    main()
