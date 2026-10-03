"""Real conversion/download checks; desktop actions are captured, never launched."""
import functools
import http.server
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'media.py'
spec = importlib.util.spec_from_file_location('media', SCRIPT)
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class MediaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('ffmpeg'):
            raise unittest.SkipTest('Install ffmpeg for real image/video checks')
        cls.temp = tempfile.TemporaryDirectory(prefix='image-view-test-')
        cls.root = Path(cls.temp.name)
        # A filename deliberately containing spaces and shell syntax.
        cls.picture = cls.root / 'cover $(touch SHOULD_NOT_EXIST).png'
        cls.movie = cls.root / 'clip.mp4'
        for output, options in [(cls.picture, ['-frames:v', '1']), (cls.movie, ['-t', '0.2', '-pix_fmt', 'yuv420p'])]:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=160x90:rate=10', *options, str(output)], check=True)
        cls.jpeg = cls.root / 'cover.jpg'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(cls.picture), str(cls.jpeg)], check=True)
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(cls.root)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def test_real_local_png_jpeg_and_video_posters(self):
        for path in [self.picture, self.jpeg, self.movie]:
            with self.subTest(path=path.name):
                result = media.preview(str(path), 'local')
                self.assertTrue(Path(result['path']).is_file())
                self.assertEqual(result['size']['width'] * 9, result['size']['height'] * 16)
                self.assertEqual(media.png_size(Path(result['path'])), result['size'])

    def test_real_http_image_and_video_downloads_and_query_strings(self):
        port = self.server.server_address[1]
        for name in ['cover.jpg', 'clip.mp4']:
            with self.subTest(name=name):
                result = media.preview(f'http://127.0.0.1:{port}/{name}?token=a&b=c', self.temp.name)
                self.assertTrue(Path(result['path']).is_file())
                self.assertGreater(result['size']['width'], 0)

    def test_stdin_protocol_and_no_shell_expansion(self):
        result = subprocess.run(['python3', str(SCRIPT)], input=json.dumps({'action': 'preview', 'target': str(self.picture)}), text=True, capture_output=True, check=True)
        self.assertIn('path', json.loads(result.stdout))
        self.assertFalse((Path.cwd() / 'SHOULD_NOT_EXIST').exists())

    def test_failure_and_download_size_limit(self):
        with self.assertRaisesRegex(ValueError, 'File not found'):
            media.preview(str(self.root / 'gone.mp4'), 'test')
        with patch.object(media, 'MAX_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'exceeds'):
                media.preview(f'http://127.0.0.1:{self.server.server_address[1]}/cover.jpg', 'limit-test')

    def test_open_preserves_exact_paths_and_metacharacters(self):
        with patch.object(media.sys, 'platform', 'darwin'), patch.object(media, 'run') as run:
            media.open_target(str(self.picture))
            run.assert_called_with(['open', str(self.picture.resolve())])
            media.open_target('http://localhost:3000/?a=1&b=2')
            run.assert_called_with(['open', 'http://localhost:3000/?a=1&b=2'])

    def test_unsafe_schemes_and_redirects_are_rejected(self):
        for target in ['javascript:alert(1)', 'file:///etc/passwd', 'https://user:pass@example.com/']:
            with self.assertRaises(ValueError):
                media.web_url(target)


if __name__ == '__main__':
    unittest.main()
