"""Check the actual overflow smoke-test launch boundary without starting Claude."""
import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name('input_overflow_smoke.py')


class LaunchCaptured(Exception):
    """Stop the smoke script after it constructs the subprocess arguments."""


class SmokeLaunchTests(unittest.TestCase):
    def launch_arguments(self, overrides):
        """Execute script setup in temporary storage and capture its real launch argv."""
        with tempfile.TemporaryDirectory(prefix='smoke-launch-test-') as root:
            with patch.dict(os.environ, overrides, clear=True), \
                 patch('tempfile.mkdtemp', return_value=root), \
                 patch('http.server.ThreadingHTTPServer') as server, \
                 patch('threading.Thread.start'), \
                 patch('pty.openpty', return_value=(101, 102)), \
                 patch('fcntl.ioctl'), \
                 patch('subprocess.Popen', side_effect=LaunchCaptured) as launch:
                server.return_value.server_port = 4321
                with self.assertRaises(LaunchCaptured):
                    runpy.run_path(str(SCRIPT), run_name='__main__')
                args, kwargs = launch.call_args
                self.assertFalse(kwargs.get('shell', False))
                self.assertEqual(args[0][-4:], ['--mcp-config', '{"mcpServers":{}}', '--tools', ''])
                return args[0]

    def test_unset_override_uses_claude(self):
        """Keep the documented default executable when CLAUDE_BIN is absent."""
        command = self.launch_arguments({})
        self.assertEqual(command[:2], ['claude', '--debug-file'])

    def test_override_uses_the_selected_executable(self):
        """Use an explicitly selected Claude executable instead of ignoring it."""
        command = self.launch_arguments({'CLAUDE_BIN': '/tmp/custom-claude'})
        self.assertEqual(command[:2], ['/tmp/custom-claude', '--debug-file'])

    def test_override_preserves_quoted_path_and_launcher_arguments(self):
        """Split launcher arguments while keeping quoted spaces and punctuation literal."""
        command = self.launch_arguments({'CLAUDE_BIN': '"/tmp/Claude Wrapper" --profile "test profile" "literal;value"'})
        self.assertEqual(command[:5], ['/tmp/Claude Wrapper', '--profile', 'test profile', 'literal;value', '--debug-file'])


if __name__ == '__main__':
    unittest.main()
