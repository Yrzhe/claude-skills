#!/usr/bin/env python3
"""
YouTube Data API v3 CLI Tool

Usage:
    python youtube_api.py search --query "Python tutorial" --max-results 25
    python youtube_api.py video --id "dQw4w9WgXcQ" --parts snippet,statistics
    python youtube_api.py channel --for-handle "@Google" --parts snippet,statistics
"""

import argparse
import json
import os
import sys
import csv
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Error: google-api-python-client not installed.")
    print("Run: pip install google-api-python-client")
    sys.exit(1)


def get_api_key() -> str:
    """Get API key from environment or config file."""
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if api_key:
        return api_key

    # Try to read from config file
    config_path = os.path.join(os.path.dirname(__file__), "config.py")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                # Simple extraction
                for line in content.split('\n'):
                    if 'YOUTUBE_API_KEY' in line and '=' in line:
                        key = line.split('=')[1].strip().strip('"\'')
                        if key and key != "YOUR_API_KEY_HERE":
                            return key
        except Exception:
            pass

    print("Error: YOUTUBE_API_KEY not found.")
    print("Set it via: export YOUTUBE_API_KEY='your-api-key'")
    print("Or edit: ~/.claude/skills/youtube-data-api/scripts/config.py")
    sys.exit(1)


def build_youtube_client():
    """Build YouTube API client."""
    api_key = get_api_key()
    return build("youtube", "v3", developerKey=api_key)


def parse_time_delta(time_str: str) -> str:
    """Parse time delta string like '7d', '1w', '30d' to ISO 8601 format."""
    if not time_str:
        return None

    # Already ISO format
    if 'T' in time_str:
        return time_str

    now = datetime.utcnow()

    mapping = {
        'd': 'days',
        'w': 'weeks',
        'm': 'months',
        'y': 'years',
        'h': 'hours'
    }

    unit = time_str[-1].lower()
    if unit not in mapping:
        return time_str

    try:
        value = int(time_str[:-1])
    except ValueError:
        return time_str

    if unit == 'd':
        delta = timedelta(days=value)
    elif unit == 'w':
        delta = timedelta(weeks=value)
    elif unit == 'm':
        delta = timedelta(days=value * 30)
    elif unit == 'y':
        delta = timedelta(days=value * 365)
    elif unit == 'h':
        delta = timedelta(hours=value)
    else:
        return time_str

    result = now - delta
    return result.strftime("%Y-%m-%dT%H:%M:%SZ")


def search_videos(youtube, args) -> Dict[str, Any]:
    """Search for videos, channels, or playlists."""
    params = {
        "part": "snippet",
        "q": args.query,
        "maxResults": min(args.max_results, 50),
        "type": args.type if args.type else "video,channel,playlist"
    }

    # Add optional parameters
    if args.order:
        params["order"] = args.order
    if args.published_after:
        params["publishedAfter"] = parse_time_delta(args.published_after)
    if args.published_before:
        params["publishedBefore"] = parse_time_delta(args.published_before)
    if args.region_code:
        params["regionCode"] = args.region_code
    if args.relevance_language:
        params["relevanceLanguage"] = args.relevance_language
    if args.channel_id:
        params["channelId"] = args.channel_id
    if args.safe_search:
        params["safeSearch"] = args.safe_search
    if args.page_token:
        params["pageToken"] = args.page_token

    # Video-specific filters (only work with type=video)
    if args.type == "video":
        if args.video_duration:
            params["videoDuration"] = args.video_duration
        if args.video_definition:
            params["videoDefinition"] = args.video_definition
        if args.video_caption:
            params["videoCaption"] = args.video_caption
        if args.video_dimension:
            params["videoDimension"] = args.video_dimension
        if args.event_type:
            params["eventType"] = args.event_type

    if args.fields:
        params["fields"] = args.fields

    results = {"items": [], "totalResults": 0}
    page_count = 0
    max_pages = (args.max_total // 50) + 1 if args.all_pages else 1

    while True:
        response = youtube.search().list(**params).execute()

        results["items"].extend(response.get("items", []))
        results["totalResults"] = response.get("pageInfo", {}).get("totalResults", 0)

        page_count += 1

        # Check if we should continue
        if not args.all_pages:
            break
        if page_count >= max_pages:
            break
        if len(results["items"]) >= args.max_total:
            results["items"] = results["items"][:args.max_total]
            break

        next_token = response.get("nextPageToken")
        if not next_token:
            break
        params["pageToken"] = next_token

    # Add nextPageToken from last response
    if "nextPageToken" in response:
        results["nextPageToken"] = response["nextPageToken"]

    return results


def get_videos(youtube, args) -> Dict[str, Any]:
    """Get video details by ID or chart."""
    parts = args.parts if args.parts else "snippet,statistics,contentDetails"

    params = {
        "part": parts,
        "maxResults": min(args.max_results, 50)
    }

    if args.id:
        # Handle comma-separated IDs
        params["id"] = args.id
    elif args.ids_from:
        # Load IDs from JSON file
        with open(args.ids_from, 'r') as f:
            data = json.load(f)
            ids = []
            for item in data.get("items", []):
                if isinstance(item.get("id"), dict):
                    ids.append(item["id"].get("videoId", ""))
                elif isinstance(item.get("id"), str):
                    ids.append(item["id"])
            params["id"] = ",".join(filter(None, ids[:50]))
    elif args.chart:
        params["chart"] = args.chart
        if args.region_code:
            params["regionCode"] = args.region_code
        if args.video_category_id:
            params["videoCategoryId"] = args.video_category_id

    if args.fields:
        params["fields"] = args.fields

    return youtube.videos().list(**params).execute()


def get_channels(youtube, args) -> Dict[str, Any]:
    """Get channel details."""
    parts = args.parts if args.parts else "snippet,statistics,contentDetails"

    params = {
        "part": parts,
        "maxResults": min(args.max_results, 50)
    }

    if args.id:
        params["id"] = args.id
    elif args.for_username:
        params["forUsername"] = args.for_username
    elif args.for_handle:
        params["forHandle"] = args.for_handle

    if args.fields:
        params["fields"] = args.fields

    return youtube.channels().list(**params).execute()


def get_playlists(youtube, args) -> Dict[str, Any]:
    """Get playlist details."""
    parts = args.parts if args.parts else "snippet,contentDetails"

    params = {
        "part": parts,
        "maxResults": min(args.max_results, 50)
    }

    if args.id:
        params["id"] = args.id
    elif args.channel_id:
        params["channelId"] = args.channel_id

    if args.page_token:
        params["pageToken"] = args.page_token

    if args.fields:
        params["fields"] = args.fields

    return youtube.playlists().list(**params).execute()


def get_playlist_items(youtube, args) -> Dict[str, Any]:
    """Get videos in a playlist."""
    params = {
        "part": "snippet,contentDetails",
        "playlistId": args.playlist_id,
        "maxResults": min(args.max_results, 50)
    }

    if args.page_token:
        params["pageToken"] = args.page_token

    if args.fields:
        params["fields"] = args.fields

    results = {"items": [], "totalResults": 0}
    page_count = 0
    max_pages = 20 if args.all_pages else 1

    while True:
        response = youtube.playlistItems().list(**params).execute()

        results["items"].extend(response.get("items", []))
        results["totalResults"] = response.get("pageInfo", {}).get("totalResults", 0)

        page_count += 1

        if not args.all_pages:
            break
        if page_count >= max_pages:
            break

        next_token = response.get("nextPageToken")
        if not next_token:
            break
        params["pageToken"] = next_token

    if "nextPageToken" in response:
        results["nextPageToken"] = response["nextPageToken"]

    return results


def get_comments(youtube, args) -> Dict[str, Any]:
    """Get comments for a video or channel."""
    params = {
        "part": "snippet,replies",
        "maxResults": min(args.max_results, 100),
        "order": args.order if args.order else "relevance"
    }

    if args.video_id:
        params["videoId"] = args.video_id
    elif args.channel_id:
        params["channelId"] = args.channel_id

    if args.page_token:
        params["pageToken"] = args.page_token

    if args.fields:
        params["fields"] = args.fields

    results = {"items": [], "totalResults": 0}
    page_count = 0
    max_pages = 10 if args.all_pages else 1

    while True:
        response = youtube.commentThreads().list(**params).execute()

        results["items"].extend(response.get("items", []))
        results["totalResults"] = response.get("pageInfo", {}).get("totalResults", 0)

        page_count += 1

        if not args.all_pages:
            break
        if page_count >= max_pages:
            break

        next_token = response.get("nextPageToken")
        if not next_token:
            break
        params["pageToken"] = next_token

    if "nextPageToken" in response:
        results["nextPageToken"] = response["nextPageToken"]

    return results


def get_comment_replies(youtube, args) -> Dict[str, Any]:
    """Get replies to a comment."""
    params = {
        "part": "snippet",
        "parentId": args.parent_id,
        "maxResults": min(args.max_results, 100)
    }

    if args.page_token:
        params["pageToken"] = args.page_token

    return youtube.comments().list(**params).execute()


def list_captions(youtube, args) -> Dict[str, Any]:
    """List captions for a video."""
    return youtube.captions().list(
        part="snippet",
        videoId=args.video_id
    ).execute()


def get_video_categories(youtube, args) -> Dict[str, Any]:
    """Get video categories for a region."""
    return youtube.videoCategories().list(
        part="snippet",
        regionCode=args.region_code if args.region_code else "US"
    ).execute()


def get_regions(youtube, args) -> Dict[str, Any]:
    """Get supported regions."""
    return youtube.i18nRegions().list(part="snippet").execute()


def get_languages(youtube, args) -> Dict[str, Any]:
    """Get supported languages."""
    return youtube.i18nLanguages().list(part="snippet").execute()


def test_api_key(youtube, args) -> Dict[str, Any]:
    """Test if API key is valid."""
    try:
        response = youtube.videos().list(
            part="snippet",
            id="dQw4w9WgXcQ"
        ).execute()
        return {"status": "ok", "message": "API key is valid"}
    except HttpError as e:
        return {"status": "error", "message": str(e)}


def format_output(data: Dict[str, Any], format_type: str = "json") -> str:
    """Format output data."""
    if format_type == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)

    elif format_type == "simple":
        lines = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            item_id = item.get("id", {})

            if isinstance(item_id, dict):
                vid = item_id.get("videoId") or item_id.get("channelId") or item_id.get("playlistId")
            else:
                vid = item_id

            title = snippet.get("title", "N/A")
            lines.append(f"{vid}: {title}")
        return "\n".join(lines)

    elif format_type == "csv":
        if not data.get("items"):
            return ""

        # Build CSV
        output = []
        items = data["items"]

        # Flatten first item to get headers
        def flatten(d, parent_key=''):
            items_flat = []
            for k, v in d.items():
                new_key = f"{parent_key}.{k}" if parent_key else k
                if isinstance(v, dict):
                    items_flat.extend(flatten(v, new_key).items())
                elif isinstance(v, list):
                    items_flat.append((new_key, json.dumps(v)))
                else:
                    items_flat.append((new_key, v))
            return dict(items_flat)

        flat_items = [flatten(item) for item in items]
        headers = list(flat_items[0].keys())

        import io
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=headers)
        writer.writeheader()
        writer.writerows(flat_items)
        return buffer.getvalue()

    return json.dumps(data, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Data API v3 CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--output", "-o", help="Output file path")
    common_parser.add_argument("--format", "-f", choices=["json", "csv", "simple"],
                              default="json", help="Output format")
    common_parser.add_argument("--fields", help="Fields to return (for quota optimization)")
    common_parser.add_argument("--max-results", type=int, default=25, help="Max results per page")
    common_parser.add_argument("--page-token", help="Page token for pagination")
    common_parser.add_argument("--all-pages", action="store_true", help="Fetch all pages")
    common_parser.add_argument("--max-total", type=int, default=500, help="Max total results when using --all-pages")

    # Search command
    search_parser = subparsers.add_parser("search", parents=[common_parser],
                                          help="Search videos, channels, playlists")
    search_parser.add_argument("--query", "-q", required=True, help="Search query")
    search_parser.add_argument("--type", choices=["video", "channel", "playlist"], help="Resource type")
    search_parser.add_argument("--order", choices=["relevance", "date", "rating", "viewCount", "title"],
                              help="Sort order")
    search_parser.add_argument("--published-after", help="Published after (e.g., 7d, 1w, 30d or ISO 8601)")
    search_parser.add_argument("--published-before", help="Published before")
    search_parser.add_argument("--region-code", help="Region code (ISO 3166-1)")
    search_parser.add_argument("--relevance-language", help="Relevance language (ISO 639-1)")
    search_parser.add_argument("--channel-id", help="Limit to specific channel")
    search_parser.add_argument("--safe-search", choices=["none", "moderate", "strict"])
    search_parser.add_argument("--video-duration", choices=["short", "medium", "long"],
                              help="Video duration filter")
    search_parser.add_argument("--video-definition", choices=["high", "standard"],
                              help="Video definition filter")
    search_parser.add_argument("--video-caption", choices=["closedCaption", "none"],
                              help="Caption filter")
    search_parser.add_argument("--video-dimension", choices=["2d", "3d"])
    search_parser.add_argument("--event-type", choices=["live", "completed", "upcoming"],
                              help="Live streaming event type")

    # Video command
    video_parser = subparsers.add_parser("video", parents=[common_parser],
                                         help="Get video details")
    video_parser.add_argument("--id", help="Video ID(s), comma-separated")
    video_parser.add_argument("--ids-from", help="Load video IDs from JSON file")
    video_parser.add_argument("--chart", choices=["mostPopular"], help="Chart type")
    video_parser.add_argument("--region-code", help="Region code for chart")
    video_parser.add_argument("--video-category-id", help="Category ID for chart")
    video_parser.add_argument("--parts", default="snippet,statistics,contentDetails",
                             help="Parts to include")

    # Channel command
    channel_parser = subparsers.add_parser("channel", parents=[common_parser],
                                           help="Get channel details")
    channel_parser.add_argument("--id", help="Channel ID(s)")
    channel_parser.add_argument("--for-username", help="Username")
    channel_parser.add_argument("--for-handle", help="Handle (e.g., @Google)")
    channel_parser.add_argument("--parts", default="snippet,statistics,contentDetails",
                               help="Parts to include")

    # Playlist command
    playlist_parser = subparsers.add_parser("playlist", parents=[common_parser],
                                            help="Get playlist details")
    playlist_parser.add_argument("--id", help="Playlist ID(s)")
    playlist_parser.add_argument("--channel-id", help="Channel ID to get playlists from")
    playlist_parser.add_argument("--parts", default="snippet,contentDetails",
                                help="Parts to include")

    # PlaylistItems command
    items_parser = subparsers.add_parser("playlist-items", parents=[common_parser],
                                         help="Get videos in a playlist")
    items_parser.add_argument("--playlist-id", required=True, help="Playlist ID")

    # Comments command
    comments_parser = subparsers.add_parser("comments", parents=[common_parser],
                                            help="Get comments")
    comments_parser.add_argument("--video-id", help="Video ID")
    comments_parser.add_argument("--channel-id", help="Channel ID")
    comments_parser.add_argument("--order", choices=["relevance", "time"], default="relevance")

    # Comment replies command
    replies_parser = subparsers.add_parser("comment-replies", parents=[common_parser],
                                           help="Get replies to a comment")
    replies_parser.add_argument("--parent-id", required=True, help="Parent comment ID")

    # Captions command
    captions_parser = subparsers.add_parser("captions", parents=[common_parser],
                                            help="List captions for a video")
    captions_parser.add_argument("--video-id", required=True, help="Video ID")
    captions_parser.add_argument("--list", action="store_true", help="List available captions")

    # Categories command
    cat_parser = subparsers.add_parser("categories", parents=[common_parser],
                                       help="Get video categories")
    cat_parser.add_argument("--region-code", default="US", help="Region code")

    # Regions command
    subparsers.add_parser("regions", parents=[common_parser],
                          help="Get supported regions")

    # Languages command
    subparsers.add_parser("languages", parents=[common_parser],
                          help="Get supported languages")

    # Test command
    subparsers.add_parser("test", help="Test API key")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        youtube = build_youtube_client()

        # Execute command
        if args.command == "search":
            result = search_videos(youtube, args)
        elif args.command == "video":
            result = get_videos(youtube, args)
        elif args.command == "channel":
            result = get_channels(youtube, args)
        elif args.command == "playlist":
            result = get_playlists(youtube, args)
        elif args.command == "playlist-items":
            result = get_playlist_items(youtube, args)
        elif args.command == "comments":
            result = get_comments(youtube, args)
        elif args.command == "comment-replies":
            result = get_comment_replies(youtube, args)
        elif args.command == "captions":
            result = list_captions(youtube, args)
        elif args.command == "categories":
            result = get_video_categories(youtube, args)
        elif args.command == "regions":
            result = get_regions(youtube, args)
        elif args.command == "languages":
            result = get_languages(youtube, args)
        elif args.command == "test":
            result = test_api_key(youtube, args)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)

        # Format and output
        output = format_output(result, getattr(args, 'format', 'json'))

        if hasattr(args, 'output') and args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"Results saved to: {args.output}")
            print(f"Total items: {len(result.get('items', []))}")
        else:
            print(output)

    except HttpError as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
