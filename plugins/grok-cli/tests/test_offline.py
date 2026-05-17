import json
import os
import tempfile
import unittest

from grok_cli.cli import _ext_from_mime, build_parser
from grok_cli.client import usd_from_ticks
from grok_cli.config import load_config, save_config
from grok_cli.sessions import SessionStore


class OfflineTests(unittest.TestCase):
    def test_parser_builds(self):
        self.assertEqual(build_parser().prog, "grok-cli")

    def test_image_video_subcommands_present(self):
        ns = build_parser().parse_args(["image", "a cat"])
        self.assertEqual(ns.command, "image")
        ns = build_parser().parse_args(["video", "--fetch", "abc"])
        self.assertEqual(ns.fetch, "abc")

    def test_session_store_isolated(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ["GROK_CLI_HOME"] = d
            store = SessionStore()
            session = store.ensure_session("unit")
            self.assertEqual(session.name, "unit")

    def test_usd_from_ticks(self):
        self.assertEqual(usd_from_ticks(200000000), 0.02)
        self.assertEqual(usd_from_ticks(4000000000), 0.4)
        self.assertIsNone(usd_from_ticks(None))

    def test_ext_from_mime(self):
        self.assertEqual(_ext_from_mime("image/png", "jpg"), "png")
        self.assertEqual(_ext_from_mime("", "jpg"), "jpg")

    def test_config_has_generation_models_and_migrates_legacy(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ["GROK_CLI_HOME"] = d
            cfg = load_config()
            self.assertTrue(cfg.image_model)
            self.assertTrue(cfg.video_model)
            cfg.search_model = "grok-4.20-reasoning"  # legacy invalid id
            save_config(cfg)
            migrated = load_config()
            self.assertEqual(migrated.search_model, "grok-4.20-0309-reasoning")


if __name__ == "__main__":
    unittest.main()
