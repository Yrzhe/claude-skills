#!/usr/bin/env python3
"""
Dependency Checker for Intelligent Web Scraper

Checks if all required dependencies are installed and provides
installation instructions for missing ones.

Usage:
    python check_deps.py           # Check all dependencies
    python check_deps.py --install # Check and install missing
    python check_deps.py --json    # Output as JSON (for programmatic use)
"""

import subprocess
import sys
import json
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# ============================================================================
# Dependency Definitions
# ============================================================================

PYTHON_DEPS = {
    "crawl4ai": {
        "import_name": "crawl4ai",
        "pip_name": "crawl4ai",
        "min_version": "0.3.0",
        "required": True,
        "description": "Core web crawling library"
    },
    "playwright": {
        "import_name": "playwright",
        "pip_name": "playwright",
        "min_version": "1.40.0",
        "required": True,
        "description": "Browser automation"
    },
    "websockets": {
        "import_name": "websockets",
        "pip_name": "websockets",
        "min_version": "12.0",
        "required": True,
        "description": "WebSocket for CDP"
    },
    "pydantic": {
        "import_name": "pydantic",
        "pip_name": "pydantic",
        "min_version": "2.0",
        "required": True,
        "description": "Data validation"
    },
    "aiohttp": {
        "import_name": "aiohttp",
        "pip_name": "aiohttp",
        "min_version": "3.9.0",
        "required": False,
        "description": "Async HTTP (optional)"
    },
    "beautifulsoup4": {
        "import_name": "bs4",
        "pip_name": "beautifulsoup4",
        "min_version": "4.12.0",
        "required": False,
        "description": "HTML parsing (optional)"
    }
}


# ============================================================================
# Check Functions
# ============================================================================

def check_python_version() -> Tuple[bool, str]:
    """Check Python version >= 3.9"""
    version = sys.version_info
    ok = version >= (3, 9)
    msg = f"Python {version.major}.{version.minor}.{version.micro}"
    return ok, msg


def check_module(module_name: str) -> Tuple[bool, Optional[str]]:
    """Check if a Python module is installed and get its version"""
    try:
        module = __import__(module_name)
        version = getattr(module, "__version__", "unknown")
        return True, version
    except ImportError:
        return False, None


def check_playwright_browsers() -> Tuple[bool, str]:
    """Check if Playwright browsers are installed"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Try to get browser executable
            browser = p.chromium
            executable = browser.executable_path if hasattr(browser, 'executable_path') else None
            if executable:
                return True, f"Chromium at {executable}"
        return True, "Playwright browsers available"
    except Exception as e:
        return False, str(e)


def check_crawl4ai_setup() -> Tuple[bool, str]:
    """Check if Crawl4AI is properly set up"""
    try:
        from crawl4ai import AsyncWebCrawler
        return True, "Crawl4AI ready"
    except Exception as e:
        return False, str(e)


def detect_environment() -> Dict[str, str]:
    """Detect the runtime environment"""
    env = {
        "os": platform.system().lower(),
        "os_version": platform.release(),
        "arch": platform.machine(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "is_headless": True,  # Assume headless by default
    }

    # Check for GUI
    if env["os"] == "darwin":  # macOS always has GUI
        env["is_headless"] = False
    elif env["os"] == "linux":
        import os
        if os.environ.get("DISPLAY"):
            env["is_headless"] = False

    return env


# ============================================================================
# Main Check
# ============================================================================

def run_checks(verbose: bool = True) -> Dict:
    """Run all dependency checks"""
    results = {
        "environment": detect_environment(),
        "python": {},
        "modules": {},
        "browsers": {},
        "ready": True,
        "missing_required": [],
        "missing_optional": []
    }

    # Check Python
    ok, msg = check_python_version()
    results["python"] = {"ok": ok, "message": msg}
    if not ok:
        results["ready"] = False
    if verbose:
        status = "✓" if ok else "✗"
        print(f"{status} Python version: {msg}")

    # Check modules
    for name, info in PYTHON_DEPS.items():
        ok, version = check_module(info["import_name"])
        results["modules"][name] = {
            "ok": ok,
            "version": version,
            "required": info["required"],
            "description": info["description"]
        }

        if not ok:
            if info["required"]:
                results["ready"] = False
                results["missing_required"].append(name)
            else:
                results["missing_optional"].append(name)

        if verbose:
            status = "✓" if ok else ("✗" if info["required"] else "○")
            ver = f"v{version}" if version else "not installed"
            req = "(required)" if info["required"] else "(optional)"
            print(f"{status} {name}: {ver} {req}")

    # Check Playwright browsers
    if verbose:
        print("\nBrowser checks:")

    ok, msg = check_playwright_browsers()
    results["browsers"]["playwright"] = {"ok": ok, "message": msg}
    if not ok:
        results["ready"] = False
    if verbose:
        status = "✓" if ok else "✗"
        print(f"{status} Playwright browsers: {msg}")

    # Check Crawl4AI
    ok, msg = check_crawl4ai_setup()
    results["browsers"]["crawl4ai"] = {"ok": ok, "message": msg}
    if not ok:
        results["ready"] = False
    if verbose:
        status = "✓" if ok else "✗"
        print(f"{status} Crawl4AI setup: {msg}")

    return results


def install_missing(results: Dict) -> bool:
    """Install missing dependencies"""
    missing = results.get("missing_required", []) + results.get("missing_optional", [])

    if not missing:
        print("All dependencies are already installed!")
        return True

    print(f"\nInstalling missing packages: {', '.join(missing)}")

    # Install via pip
    pip_packages = [PYTHON_DEPS[m]["pip_name"] for m in missing if m in PYTHON_DEPS]
    if pip_packages:
        cmd = [sys.executable, "-m", "pip", "install"] + pip_packages
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False

    # Install Playwright browsers if needed
    if not results.get("browsers", {}).get("playwright", {}).get("ok", True):
        print("\nInstalling Playwright browsers...")
        cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Warning: {result.stderr}")

    # Run crawl4ai-setup if needed
    if not results.get("browsers", {}).get("crawl4ai", {}).get("ok", True):
        print("\nSetting up Crawl4AI...")
        try:
            subprocess.run(["crawl4ai-setup"], capture_output=True, timeout=120)
        except Exception as e:
            print(f"Warning: crawl4ai-setup had issues: {e}")

    print("\n✓ Installation complete!")
    return True


def print_installation_instructions(results: Dict):
    """Print manual installation instructions"""
    env = results["environment"]

    print("\n" + "=" * 50)
    print("INSTALLATION INSTRUCTIONS")
    print("=" * 50)

    # pip install
    missing = results.get("missing_required", []) + results.get("missing_optional", [])
    if missing:
        packages = [PYTHON_DEPS[m]["pip_name"] for m in missing if m in PYTHON_DEPS]
        print(f"\n1. Install Python packages:")
        print(f"   pip install {' '.join(packages)}")

    # Playwright browsers
    if not results.get("browsers", {}).get("playwright", {}).get("ok", True):
        print(f"\n2. Install Playwright browser:")
        print(f"   python -m playwright install chromium")

        if env["is_headless"] and env["os"] == "linux":
            print(f"\n   For headless Linux, also run:")
            print(f"   python -m playwright install-deps chromium")

    # Crawl4AI
    if not results.get("browsers", {}).get("crawl4ai", {}).get("ok", True):
        print(f"\n3. Set up Crawl4AI:")
        print(f"   crawl4ai-setup")

    # Linux system deps
    if env["is_headless"] and env["os"] == "linux":
        print(f"\n4. Linux system dependencies (if needed):")
        print(f"   sudo apt install libnss3 libatk1.0-0 libatk-bridge2.0-0 \\")
        print(f"       libcups2 libdrm2 libxkbcommon0 libxcomposite1 \\")
        print(f"       libxdamage1 libxfixes3 libxrandr2 libgbm1 \\")
        print(f"       libasound2 libpango-1.0-0 libcairo2")


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Check dependencies for Intelligent Web Scraper")
    parser.add_argument("--install", action="store_true", help="Install missing dependencies")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    args = parser.parse_args()

    verbose = not args.json and not args.quiet

    if verbose:
        print("=" * 50)
        print("Intelligent Web Scraper - Dependency Check")
        print("=" * 50)
        print()

    results = run_checks(verbose=verbose)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0 if results["ready"] else 1

    if verbose:
        print()
        if results["ready"]:
            print("✓ All required dependencies are installed!")
            print("  Ready to use the Intelligent Web Scraper.")
        else:
            print("✗ Some required dependencies are missing.")

            if args.install:
                install_missing(results)
            else:
                print_installation_instructions(results)
                print("\n  Or run with --install to auto-install")

    return 0 if results["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
