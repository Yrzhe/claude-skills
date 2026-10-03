#!/usr/bin/env python3
"""Bounded local thumbnail preparation and user-triggered OS actions. No shell."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

MAX_BYTES = 64 * 1024 * 1024


def run(argv, **kwargs):
    result = subprocess.run(argv, capture_output=True, timeout=15, **kwargs)
    if result.returncode:
        raise ValueError("Preview conversion failed" if argv[0].endswith('ffmpeg') else "System action failed")
    return result


def local_path(target):
    path = Path(target).expanduser().resolve()
    if not path.is_file():
        raise ValueError("File not found")
    return path


def web_url(target):
    parsed = urllib.parse.urlsplit(target)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Unsupported URL")
    return target


class WebRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        web_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(target, destination):
    request = urllib.request.Request(web_url(target), headers={'User-Agent': 'Claude-Image-View/0.2'})
    deadline = time.monotonic() + 15
    with urllib.request.build_opener(WebRedirect).open(request, timeout=5) as response:
        if int(response.headers.get('Content-Length', 0)) > MAX_BYTES:
            raise ValueError("Media exceeds 64 MiB")
        total = 0
        with destination.open('wb') as output:
            while True:
                if time.monotonic() > deadline:
                    raise ValueError("Download timed out")
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError("Media exceeds 64 MiB")
                output.write(chunk)


def png_size(path):
    with path.open('rb') as file:
        header = file.read(24)
    if len(header) < 24 or header[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError("Not a PNG")
    width, height = struct.unpack('>II', header[16:24])
    if not (0 < width <= 100000 and 0 < height <= 100000):
        raise ValueError("Invalid image dimensions")
    return {'width': width, 'height': height}


def preview(target, cache_key, kind='image'):
    remote = target.startswith(('http://', 'https://'))
    source = None if remote else local_path(target)
    # Session/turn scope prevents a stale URL or overwritten file from retaining its old picture.
    stamp = cache_key if remote else f'{source.stat().st_mtime_ns}:{source.stat().st_size}'
    digest = hashlib.sha256(f'{target}:{stamp}'.encode()).hexdigest()
    cache = Path(tempfile.gettempdir()) / f'claude-image-view-{os.getuid()}'
    cache.mkdir(mode=0o700, exist_ok=True)
    if cache.is_symlink() or cache.stat().st_uid != os.getuid():
        raise ValueError("Invalid preview cache")
    os.chmod(cache, 0o700)
    output = cache / f'{digest}.png'
    # Prune only our generated thumbnails, never source media.
    for old in cache.glob('*.png'):
        try:
            if old.stat().st_mtime < time.time() - 7 * 86400:
                old.unlink()
        except FileNotFoundError:
            pass
    if output.exists():
        return {'path': str(output), 'size': png_size(output)}
    with tempfile.TemporaryDirectory(prefix='prepare-', dir=cache) as work:
        work = Path(work)
        if remote:
            source = work / 'input'
            download(target, source)
        converted = work / 'preview.png'
        ffmpeg = shutil.which('ffmpeg')
        if ffmpeg:
            run([ffmpeg, '-v', 'error', '-nostdin', '-y', '-protocol_whitelist', 'file,pipe',
                 '-i', str(source), '-frames:v', '1', '-vf',
                 'scale=640:400:force_original_aspect_ratio=decrease', '-threads', '1', str(converted)])
        elif kind == 'video':
            raise ValueError('Install ffmpeg for video previews')
        elif sys.platform == 'darwin' and shutil.which('sips'):
            run(['sips', '-s', 'format', 'png', '-Z', '640', str(source), '--out', str(converted)])
        else:
            # PNGs still work without a converter.
            png_size(source)
            if source.stat().st_size > MAX_BYTES:
                raise ValueError("Media exceeds 64 MiB")
            shutil.copyfile(source, converted)
        size = png_size(converted)
        os.replace(converted, output)
    return {'path': str(output), 'size': size}


def open_target(target):
    if target.startswith(('http://', 'https://')):
        target = web_url(target)
    else:
        target = str(local_path(target))
    command = ['open', target] if sys.platform == 'darwin' else ['xdg-open', target]
    run(command)


def main():
    try:
        request = json.load(sys.stdin)
        action = request['action']
        if action == 'preview':
            result = preview(request['target'], request.get('cacheKey', ''), request.get('kind', 'image'))
        elif action == 'open':
            open_target(request['target'])
            result = {'ok': True}
        else:
            raise ValueError("Unknown action")
        print(json.dumps(result))
    except Exception as error:
        # Never print URL query strings or response bodies from download errors.
        message = str(error) if isinstance(error, ValueError) else type(error).__name__
        print(json.dumps({'error': message}))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
