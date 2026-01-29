#!/usr/bin/env python3
"""
YouTube Subtitle Downloader

Uses yt-dlp to download subtitles (works for public videos without OAuth).

Usage:
    python download_subtitles.py VIDEO_URL --lang en,zh-Hans --output subtitles/
    python download_subtitles.py VIDEO_ID --list  # List available subtitles
"""

import argparse
import json
import os
import sys
import subprocess
from typing import Optional, List


def check_ytdlp():
    """Check if yt-dlp is installed."""
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_video_url(video_id_or_url: str) -> str:
    """Convert video ID to URL if needed."""
    if video_id_or_url.startswith("http"):
        return video_id_or_url
    return f"https://www.youtube.com/watch?v={video_id_or_url}"


def list_subtitles(video_url: str) -> dict:
    """List available subtitles for a video."""
    result = subprocess.run(
        ["yt-dlp", "--list-subs", "--no-download", video_url],
        capture_output=True,
        text=True
    )

    # Parse output
    output = result.stdout + result.stderr
    return {"raw_output": output}


def download_subtitles(
    video_url: str,
    languages: List[str] = None,
    output_dir: str = ".",
    format: str = "srt",
    auto_sub: bool = True
) -> dict:
    """Download subtitles for a video."""

    if languages is None:
        languages = ["en"]

    # Build command
    cmd = [
        "yt-dlp",
        "--write-sub",
        "--sub-lang", ",".join(languages),
        "--skip-download",
        "-o", os.path.join(output_dir, "%(id)s.%(ext)s")
    ]

    if auto_sub:
        cmd.append("--write-auto-sub")

    if format:
        cmd.extend(["--sub-format", format])

    cmd.append(video_url)

    # Execute
    result = subprocess.run(cmd, capture_output=True, text=True)

    success = result.returncode == 0

    return {
        "success": success,
        "command": " ".join(cmd),
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def download_batch(
    video_ids: List[str],
    languages: List[str] = None,
    output_dir: str = ".",
    format: str = "srt"
) -> List[dict]:
    """Download subtitles for multiple videos."""
    results = []

    for vid in video_ids:
        url = get_video_url(vid)
        result = download_subtitles(url, languages, output_dir, format)
        result["video_id"] = vid
        results.append(result)
        print(f"{'✓' if result['success'] else '✗'} {vid}")

    return results


def main():
    parser = argparse.ArgumentParser(description="YouTube Subtitle Downloader")

    parser.add_argument("video", help="Video URL or ID")
    parser.add_argument("--list", "-l", action="store_true",
                       help="List available subtitles")
    parser.add_argument("--lang", default="en",
                       help="Languages to download (comma-separated, e.g., 'en,zh-Hans')")
    parser.add_argument("--output", "-o", default=".",
                       help="Output directory")
    parser.add_argument("--format", "-f", default="srt",
                       choices=["srt", "vtt", "ass", "json3"],
                       help="Subtitle format")
    parser.add_argument("--no-auto-sub", action="store_true",
                       help="Don't download auto-generated subtitles")
    parser.add_argument("--batch", "-b",
                       help="File with video IDs (one per line)")
    parser.add_argument("--json", action="store_true",
                       help="Output as JSON")

    args = parser.parse_args()

    # Check yt-dlp
    if not check_ytdlp():
        print("Error: yt-dlp not found. Install with: pip install yt-dlp")
        sys.exit(1)

    # Create output directory
    if args.output != ".":
        os.makedirs(args.output, exist_ok=True)

    # List subtitles
    if args.list:
        result = list_subtitles(get_video_url(args.video))
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(result["raw_output"])
        return

    # Batch download
    if args.batch:
        with open(args.batch, 'r') as f:
            video_ids = [line.strip() for line in f if line.strip()]

        results = download_batch(
            video_ids,
            args.lang.split(","),
            args.output,
            args.format
        )

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            success = sum(1 for r in results if r["success"])
            print(f"\nDownloaded: {success}/{len(results)}")
        return

    # Single video download
    result = download_subtitles(
        get_video_url(args.video),
        args.lang.split(","),
        args.output,
        args.format,
        not args.no_auto_sub
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"Subtitles downloaded to: {args.output}")
        else:
            print(f"Error: {result['stderr']}")


if __name__ == "__main__":
    main()
