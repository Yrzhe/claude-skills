"""One-shot installer for chef skill dependencies.

Required:
  - PyYAML          frontmatter IO
Optional (for scraping):
  - requests        HTTP
  - beautifulsoup4  HTML parsing
  - lxml            faster parser
  - recipe-scrapers 631+ 站点内置解析器

Usage:
  python scripts/setup.py --yes          # 默认 system pip
  python scripts/setup.py --user         # pip install --user
  python scripts/setup.py --check        # 只检查
"""
from __future__ import annotations
import argparse
import subprocess
import sys

REQUIRED = ["PyYAML"]
OPTIONAL = ["requests", "beautifulsoup4", "lxml", "recipe-scrapers"]

IMPORT_NAME = {
    "PyYAML": "yaml",
    "beautifulsoup4": "bs4",
    "recipe-scrapers": "recipe_scrapers",
}


def is_installed(pkg: str) -> bool:
    try:
        __import__(IMPORT_NAME.get(pkg, pkg))
        return True
    except ImportError:
        return False


def install(pkgs: list, user: bool = False) -> bool:
    cmd = [sys.executable, "-m", "pip", "install"]
    if user:
        cmd.append("--user")
    cmd += pkgs
    print("$ " + " ".join(cmd))
    return subprocess.run(cmd).returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="不问直接装")
    ap.add_argument("--user", action="store_true", help="pip install --user")
    ap.add_argument("--check", action="store_true", help="只检查")
    args = ap.parse_args()

    print("chef skill 依赖检查：")
    for p in REQUIRED:
        print(f"  [{'✓' if is_installed(p) else '✗'}] {p}  (required)")
    for p in OPTIONAL:
        print(f"  [{'✓' if is_installed(p) else '✗'}] {p}  (optional)")

    if args.check:
        return

    missing_req = [p for p in REQUIRED if not is_installed(p)]
    if missing_req:
        if args.yes or input(f"\n安装必需 {missing_req}? [y/N] ").strip().lower() == "y":
            install(missing_req, args.user)

    missing_opt = [p for p in OPTIONAL if not is_installed(p)]
    if missing_opt:
        if args.yes or input(f"\n安装可选 {missing_opt}? [y/N] ").strip().lower() == "y":
            install(missing_opt, args.user)

    print("\n建议后续：")
    print("  python scripts/api_themealdb.py --bootstrap   # 拉 283 道种子")
    print("  python scripts/search.py --random              # 验证")


if __name__ == "__main__":
    main()
