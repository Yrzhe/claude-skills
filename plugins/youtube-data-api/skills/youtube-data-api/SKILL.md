---
name: youtube-data-api
description: YouTube Data API v3 complete wrapper - search videos, get video/channel/playlist details, get comments, download subtitles, etc. Supports filtering and sorting by time/views/rating and more.
version: 1.0.0
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - WebFetch
  - Task
---

# YouTube Data API v3 Skill

Complete wrapper based on official YouTube Data API v3 documentation.

## Configuration

### API Key Setup

```bash
# Option 1: Environment variable (recommended)
export YOUTUBE_API_KEY="YOUR_API_KEY_HERE"

# Option 2: Edit config file directly
# Edit ~/.claude/skills/youtube-data-api/scripts/config.py
```

### Getting an API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create credentials → API Key
5. (Optional) Restrict API Key to YouTube Data API only

### Quota Limits

| Operation Type | Quota Cost (units) |
|----------------|-------------------|
| Read operations (list) | 1 |
| Search requests | 100 |
| Write operations (insert/update/delete) | 50 |
| Video upload | 1600 |

**Default daily quota**: 10,000 units

---

## Core Features

### 1. Search Videos (Search)

**Quota cost**: 100 units/request

```bash
# Basic search
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "Python tutorial" \
    --max-results 25

# Filter by time (last week)
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "machine learning" \
    --published-after "7d" \
    --type video

# Sort by view count
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "React hooks" \
    --order viewCount \
    --type video

# HD videos only
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "4K nature" \
    --video-definition high \
    --type video

# Videos with captions
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "TED talk" \
    --video-caption closedCaption \
    --type video

# Live streaming videos
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "gaming" \
    --event-type live \
    --type video

# Filter by region
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "news" \
    --region-code US \
    --relevance-language en

# Filter by video duration
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "documentary" \
    --video-duration long \
    --type video
```

#### Search Parameters Reference

| Parameter | Description | Values |
|-----------|-------------|--------|
| `--query, -q` | Search keywords | Supports boolean operators (`python AND tutorial`) |
| `--type` | Resource type | `video`, `channel`, `playlist` |
| `--max-results` | Results count | 1-50, default 25 |
| `--order` | Sort order | `relevance`(default), `date`, `rating`, `viewCount`, `title` |
| `--published-after` | Published after | `1d`, `7d`, `30d`, `1y` or ISO 8601 format |
| `--published-before` | Published before | Same as above |
| `--region-code` | Region code | ISO 3166-1 (e.g., `US`, `CN`, `JP`) |
| `--relevance-language` | Language | ISO 639-1 (e.g., `en`, `zh`, `ja`) |
| `--video-duration` | Video length | `short`(<4min), `medium`(4-20min), `long`(>20min) |
| `--video-definition` | Definition | `high`(HD), `standard`(SD) |
| `--video-caption` | Captions | `closedCaption`(has captions), `none`(no captions) |
| `--video-dimension` | Dimension | `2d`, `3d` |
| `--event-type` | Live status | `live`(streaming), `completed`(ended), `upcoming`(scheduled) |
| `--channel-id` | Limit to channel | Channel ID |
| `--safe-search` | Safe search | `none`, `moderate`, `strict` |

---

### 2. Get Video Details (Videos)

**Quota cost**: 1 unit/request

```bash
# Get single video details
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py video \
    --id "dQw4w9WgXcQ" \
    --parts snippet,statistics,contentDetails

# Get multiple videos (batch)
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py video \
    --id "dQw4w9WgXcQ,jNQXAC9IVRw,9bZkp7q19f0" \
    --parts snippet,statistics

# Get trending videos
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py video \
    --chart mostPopular \
    --region-code US \
    --max-results 50

# Get trending by category
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py video \
    --chart mostPopular \
    --video-category-id 10 \
    --region-code JP
```

#### Video Parts Reference

| Part | Contains |
|------|----------|
| `snippet` | Title, description, thumbnails, channel info, publish time, tags |
| `statistics` | View count, like count, comment count |
| `contentDetails` | Duration, definition, caption info, region restrictions |
| `status` | Upload status, privacy, license |
| `player` | Embedded player HTML |
| `topicDetails` | Related topic IDs |
| `recordingDetails` | Recording location, date |
| `liveStreamingDetails` | Live info (start/end time, viewer count) |

#### Video Category IDs Reference

| ID | Category | ID | Category |
|----|----------|----|----|
| 1 | Film & Animation | 20 | Gaming |
| 2 | Autos & Vehicles | 22 | People & Blogs |
| 10 | Music | 23 | Comedy |
| 15 | Pets & Animals | 24 | Entertainment |
| 17 | Sports | 25 | News & Politics |
| 19 | Travel & Events | 26 | Howto & Style |
| 27 | Education | 28 | Science & Technology |

---

### 3. Get Channel Info (Channels)

**Quota cost**: 1 unit/request

```bash
# Get by channel ID
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py channel \
    --id "UC_x5XG1OV2P6uZZ5FSM9Ttw" \
    --parts snippet,statistics,contentDetails

# Get by username
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py channel \
    --for-username "GoogleDevelopers" \
    --parts snippet,statistics

# Get by handle (@username)
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py channel \
    --for-handle "@Google" \
    --parts snippet,statistics,brandingSettings
```

#### Channel Parts Reference

| Part | Contains |
|------|----------|
| `snippet` | Channel name, description, thumbnails, country |
| `statistics` | Subscriber count, video count, total views |
| `contentDetails` | Related playlists (uploads, likes, etc.) |
| `brandingSettings` | Channel banner, keywords, default language |
| `topicDetails` | Channel topics |
| `status` | Channel status (long video upload permission, etc.) |

---

### 4. Get Playlists (Playlists)

**Quota cost**: 1 unit/request

```bash
# Get playlist by ID
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py playlist \
    --id "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf" \
    --parts snippet,contentDetails

# Get all playlists for a channel
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py playlist \
    --channel-id "UC_x5XG1OV2P6uZZ5FSM9Ttw" \
    --max-results 50
```

---

### 5. Get Playlist Videos (PlaylistItems)

**Quota cost**: 1 unit/request

```bash
# Get all videos in a playlist
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py playlist-items \
    --playlist-id "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf" \
    --max-results 50

# Paginated retrieval
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py playlist-items \
    --playlist-id "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf" \
    --page-token "NEXT_PAGE_TOKEN"
```

---

### 6. Get Comments (Comments & CommentThreads)

**Quota cost**: 1 unit/request

```bash
# Get all comments for a video (top-level)
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py comments \
    --video-id "dQw4w9WgXcQ" \
    --max-results 100 \
    --order relevance

# Get comments for a channel
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py comments \
    --channel-id "UC_x5XG1OV2P6uZZ5FSM9Ttw" \
    --max-results 50

# Get replies to a comment
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py comment-replies \
    --parent-id "COMMENT_ID" \
    --max-results 50
```

#### Comment Sort Options

| Sort | Description |
|------|-------------|
| `relevance` | By relevance (default) |
| `time` | By time (newest first) |

---

### 7. Get Captions (Captions)

**Quota cost**: 1 unit/request (list), 50 units (download)

```bash
# List all caption tracks for a video
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py captions \
    --video-id "dQw4w9WgXcQ" \
    --list

# Download captions (requires OAuth)
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py captions \
    --video-id "dQw4w9WgXcQ" \
    --download \
    --caption-id "CAPTION_ID" \
    --format srt
```

**Note**: Downloading captions requires video owner authorization (OAuth). For public videos, use `yt-dlp` to get auto-generated captions.

#### Using yt-dlp for Subtitles (Alternative)

```bash
# Install yt-dlp
pip install yt-dlp

# List available subtitles
yt-dlp --list-subs "https://www.youtube.com/watch?v=VIDEO_ID"

# Download subtitles (skip video)
yt-dlp --write-sub --write-auto-sub --sub-lang en,zh-Hans --skip-download \
    "https://www.youtube.com/watch?v=VIDEO_ID"

# Download and convert to SRT format
yt-dlp --write-sub --write-auto-sub --sub-lang en --sub-format srt --skip-download \
    "https://www.youtube.com/watch?v=VIDEO_ID"
```

---

### 8. Get Video Categories (VideoCategories)

**Quota cost**: 1 unit/request

```bash
# Get video categories for a region
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py categories \
    --region-code US

# Get categories for China
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py categories \
    --region-code CN
```

---

### 9. Get Supported Regions and Languages

**Quota cost**: 1 unit/request

```bash
# Get supported regions list
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py regions

# Get supported languages list
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py languages
```

---

## Common Use Case Examples

### Scenario 1: Get Trending Videos on a Topic from Last Week

```bash
# Search videos about "AI" from last 7 days, sorted by view count
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "AI artificial intelligence" \
    --published-after "7d" \
    --order viewCount \
    --type video \
    --max-results 50 \
    --output ai_trending.json

# Get detailed statistics for these videos
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py video \
    --ids-from ai_trending.json \
    --parts snippet,statistics,contentDetails \
    --output ai_trending_details.json
```

### Scenario 2: Analyze All Videos from a Channel

```bash
# 1. Get channel info
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py channel \
    --for-handle "@GoogleDevelopers" \
    --parts snippet,statistics,contentDetails \
    --output channel_info.json

# 2. Get uploads playlist ID (from contentDetails.relatedPlaylists.uploads)

# 3. Get all uploaded videos
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py playlist-items \
    --playlist-id "UPLOADS_PLAYLIST_ID" \
    --max-results 50 \
    --all-pages \
    --output channel_videos.json
```

### Scenario 3: Get Videos with Subtitles

```bash
# 1. Search videos
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "TED talk motivation" \
    --video-caption closedCaption \
    --type video \
    --max-results 10 \
    --output ted_videos.json

# 2. Download subtitles using yt-dlp
for video_id in $(jq -r '.items[].id.videoId' ted_videos.json); do
    yt-dlp --write-sub --write-auto-sub --sub-lang en --skip-download \
        "https://www.youtube.com/watch?v=$video_id" \
        -o "subtitles/%(id)s.%(ext)s"
done
```

### Scenario 4: Analyze Video Comments

```bash
# Get all comments for a video
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py comments \
    --video-id "VIDEO_ID" \
    --max-results 100 \
    --all-pages \
    --output comments.json

# Comment data includes:
# - Author name
# - Comment text
# - Like count
# - Publish time
# - Reply count
```

---

## Output Formats

All commands default to JSON output, save to file with `--output` parameter.

```bash
# Output to file
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "Python" \
    --output results.json

# CSV format (tabular data)
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "Python" \
    --format csv \
    --output results.csv

# Simple output (titles and IDs only)
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "Python" \
    --format simple
```

---

## Pagination

For large datasets, API uses `pageToken` for pagination:

```bash
# Auto-fetch all pages
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "Python" \
    --all-pages \
    --max-total 500 \
    --output all_results.json

# Manual pagination
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py search \
    --query "Python" \
    --page-token "NEXT_PAGE_TOKEN"
```

---

## Error Handling

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Bad request | Check parameter format |
| 401 | Unauthorized | Check API Key |
| 403 | Quota exceeded or insufficient permissions | Check quota or request increase |
| 404 | Resource not found | Verify ID is correct |
| 429 | Too many requests | Reduce request frequency |

### Quota Optimization Tips

1. **Use `fields` parameter** to request only needed fields
2. **Batch requests** using comma-separated ID lists
3. **Cache results** to avoid duplicate requests
4. **Use ETags** to check if resource has been updated

```bash
# Only get needed fields (reduces response size)
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py video \
    --id "VIDEO_ID" \
    --fields "items(id,snippet(title,channelTitle),statistics(viewCount))"
```

---

## Operations Requiring OAuth

The following operations require user authorization (API Key alone is not sufficient):

- Upload videos
- Update video metadata
- Delete videos
- Manage playlists
- Post/delete comments
- Download captions
- Access user private data

For these operations, configure OAuth 2.0 client:

```bash
# Setup OAuth (first time use)
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py auth \
    --client-secrets client_secrets.json
```

---

## Installing Dependencies

```bash
# Install Python dependencies
pip install google-api-python-client google-auth-oauthlib

# Optional: Install yt-dlp (for subtitle downloading)
pip install yt-dlp
```

---

## Quick Check

```bash
# Check if API key is valid
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py test

# Check quota usage
python ~/.claude/skills/youtube-data-api/scripts/youtube_api.py quota
```

---

## References

- [YouTube Data API Official Documentation](https://developers.google.com/youtube/v3)
- [API Reference](https://developers.google.com/youtube/v3/docs)
- [Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- [OAuth 2.0 Guide](https://developers.google.com/youtube/v3/guides/authentication)
