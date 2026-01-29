"""
YouTube Data API Configuration

Replace YOUR_API_KEY_HERE with your actual API key from Google Cloud Console.
Or set the YOUTUBE_API_KEY environment variable.
"""

# YouTube Data API Key
# Get your API key at: https://console.cloud.google.com/
# 1. Create a new project or select existing
# 2. Enable YouTube Data API v3
# 3. Create credentials -> API Key
YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"

# Optional: Restrict by region (ISO 3166-1 alpha-2)
DEFAULT_REGION_CODE = "US"

# Optional: Default language (ISO 639-1)
DEFAULT_LANGUAGE = "en"

# Quota settings
# Default daily quota: 10,000 units
# Search: 100 units per request
# Read: 1 unit per request
# Write: 50 units per request
QUOTA_WARNING_THRESHOLD = 8000  # Warn when usage exceeds this
