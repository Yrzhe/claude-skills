#!/bin/bash
# YouTube Data API Skill Setup Script

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SKILL_DIR/scripts"

echo "==================================="
echo "YouTube Data API Skill Setup"
echo "==================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3.9+."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION found"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -r "$SKILL_DIR/requirements.txt" --quiet

echo "✓ Dependencies installed"

# Make scripts executable
chmod +x "$SCRIPTS_DIR/youtube_api.py"
chmod +x "$SCRIPTS_DIR/download_subtitles.py"

echo "✓ Scripts made executable"

# Check API key
echo ""
echo "==================================="
echo "API Key Configuration"
echo "==================================="
echo ""

if [ -z "$YOUTUBE_API_KEY" ]; then
    echo "YOUTUBE_API_KEY environment variable not set."
    echo ""
    echo "To set up your API key:"
    echo ""
    echo "Option 1: Set environment variable"
    echo "  export YOUTUBE_API_KEY='your-api-key'"
    echo ""
    echo "Option 2: Edit config file"
    echo "  Edit: $SCRIPTS_DIR/config.py"
    echo "  Replace YOUR_API_KEY_HERE with your actual key"
    echo ""
    echo "Get your API key at:"
    echo "  https://console.cloud.google.com/"
    echo ""
else
    echo "✓ YOUTUBE_API_KEY is set"

    # Test API key
    echo ""
    echo "Testing API key..."
    if python3 "$SCRIPTS_DIR/youtube_api.py" test 2>/dev/null | grep -q "ok"; then
        echo "✓ API key is valid"
    else
        echo "⚠ API key test failed. Please verify your key."
    fi
fi

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Usage examples:"
echo ""
echo "  # Search videos"
echo "  python3 $SCRIPTS_DIR/youtube_api.py search -q 'Python tutorial' --max-results 10"
echo ""
echo "  # Get trending videos"
echo "  python3 $SCRIPTS_DIR/youtube_api.py video --chart mostPopular --region-code US"
echo ""
echo "  # Download subtitles"
echo "  python3 $SCRIPTS_DIR/download_subtitles.py VIDEO_ID --lang en,zh-Hans"
echo ""
echo "For more options, run:"
echo "  python3 $SCRIPTS_DIR/youtube_api.py --help"
