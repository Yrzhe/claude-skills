"""Offline smoke test for grok-cli packaging."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from grok_cli.cli import build_parser
from grok_cli.config import load_config
from grok_cli.sessions import SessionStore

parser = build_parser()
assert parser.prog == "grok-cli"
cfg = load_config()
store = SessionStore()
session = store.ensure_session("smoke-test")
assert session.name == "smoke-test"
print("offline smoke test passed")
