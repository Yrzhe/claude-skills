#!/bin/bash
# ============================================================================
# Intelligent Web Scraper - Setup Script
# ============================================================================
# Automatically installs all dependencies for both local (macOS) and VPS (Linux)
# Supports both GUI and headless environments
#
# Usage:
#   chmod +x setup.sh && ./setup.sh
#
# Options:
#   --headless    Install for headless/VPS environment (skip GUI-only deps)
#   --local       Install for local environment with GUI support
#   --check       Only check dependencies, don't install
#   --help        Show this help message
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default mode: auto-detect
MODE="auto"
CHECK_ONLY=false

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is NOT installed"
        return 1
    fi
}

check_python_module() {
    if python3 -c "import $1" &> /dev/null 2>&1; then
        print_success "Python module '$1' is installed"
        return 0
    else
        print_warning "Python module '$1' is NOT installed"
        return 1
    fi
}

detect_environment() {
    # Check if we have a display (GUI)
    if [[ -n "$DISPLAY" ]] || [[ "$OSTYPE" == "darwin"* ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "macos"
        else
            echo "linux-gui"
        fi
    else
        echo "headless"
    fi
}

detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ -f /etc/debian_version ]]; then
        echo "debian"
    elif [[ -f /etc/redhat-release ]]; then
        echo "redhat"
    elif [[ -f /etc/arch-release ]]; then
        echo "arch"
    else
        echo "unknown"
    fi
}

# ============================================================================
# Parse Arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --headless)
            MODE="headless"
            shift
            ;;
        --local)
            MODE="local"
            shift
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --help|-h)
            echo "Intelligent Web Scraper - Setup Script"
            echo ""
            echo "Usage: ./setup.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --headless    Install for headless/VPS environment"
            echo "  --local       Install for local environment with GUI"
            echo "  --check       Only check dependencies, don't install"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# Main Setup
# ============================================================================

print_header "Intelligent Web Scraper Setup"

OS=$(detect_os)
ENV=$(detect_environment)

if [[ "$MODE" == "auto" ]]; then
    if [[ "$ENV" == "headless" ]]; then
        MODE="headless"
    else
        MODE="local"
    fi
fi

print_info "Operating System: $OS"
print_info "Environment: $ENV"
print_info "Mode: $MODE"

# ============================================================================
# Step 1: Check Python
# ============================================================================

print_header "Step 1: Checking Python"

if ! check_command python3; then
    if [[ "$CHECK_ONLY" == true ]]; then
        print_error "Python 3 is required but not installed"
    else
        print_info "Installing Python 3..."
        case $OS in
            macos)
                brew install python3
                ;;
            debian)
                sudo apt update && sudo apt install -y python3 python3-pip python3-venv
                ;;
            redhat)
                sudo yum install -y python3 python3-pip
                ;;
            arch)
                sudo pacman -S python python-pip
                ;;
        esac
    fi
fi

# Check pip
if ! check_command pip3; then
    if [[ "$CHECK_ONLY" == false ]]; then
        print_info "Installing pip..."
        python3 -m ensurepip --upgrade 2>/dev/null || true
    fi
fi

# ============================================================================
# Step 2: Install System Dependencies (for Playwright)
# ============================================================================

print_header "Step 2: System Dependencies"

if [[ "$MODE" == "headless" ]] && [[ "$OS" != "macos" ]]; then
    print_info "Installing system dependencies for headless browser..."

    if [[ "$CHECK_ONLY" == false ]]; then
        case $OS in
            debian)
                sudo apt update
                sudo apt install -y \
                    libnss3 \
                    libnspr4 \
                    libatk1.0-0 \
                    libatk-bridge2.0-0 \
                    libcups2 \
                    libdrm2 \
                    libxkbcommon0 \
                    libxcomposite1 \
                    libxdamage1 \
                    libxfixes3 \
                    libxrandr2 \
                    libgbm1 \
                    libasound2 \
                    libpango-1.0-0 \
                    libcairo2 \
                    libatspi2.0-0 \
                    libgtk-3-0 \
                    fonts-liberation \
                    xvfb
                print_success "System dependencies installed"
                ;;
            redhat)
                sudo yum install -y \
                    nss \
                    nspr \
                    atk \
                    at-spi2-atk \
                    cups-libs \
                    libdrm \
                    libxkbcommon \
                    libXcomposite \
                    libXdamage \
                    libXfixes \
                    libXrandr \
                    mesa-libgbm \
                    alsa-lib \
                    pango \
                    cairo \
                    gtk3 \
                    liberation-fonts \
                    xorg-x11-server-Xvfb
                print_success "System dependencies installed"
                ;;
            *)
                print_warning "Unknown OS, skipping system dependencies"
                ;;
        esac
    fi
else
    print_info "Skipping system dependencies (macOS or local mode)"
fi

# ============================================================================
# Step 3: Install Python Dependencies
# ============================================================================

print_header "Step 3: Python Dependencies"

# Check existing modules
echo "Checking Python modules..."
check_python_module "crawl4ai" || NEED_CRAWL4AI=true
check_python_module "playwright" || NEED_PLAYWRIGHT=true
check_python_module "websockets" || NEED_WEBSOCKETS=true
check_python_module "pydantic" || NEED_PYDANTIC=true
check_python_module "aiohttp" || NEED_AIOHTTP=true

if [[ "$CHECK_ONLY" == false ]]; then
    print_info "Installing Python packages from requirements.txt..."
    pip3 install -r "$SCRIPT_DIR/requirements.txt"
    print_success "Python packages installed"
fi

# ============================================================================
# Step 4: Install Browsers
# ============================================================================

print_header "Step 4: Browser Installation"

# Playwright browsers
print_info "Installing Playwright browsers..."
if [[ "$CHECK_ONLY" == false ]]; then
    python3 -m playwright install chromium

    if [[ "$MODE" == "headless" ]] && [[ "$OS" != "macos" ]]; then
        print_info "Installing Playwright system dependencies..."
        python3 -m playwright install-deps chromium 2>/dev/null || true
    fi

    print_success "Playwright Chromium installed"
fi

# Crawl4AI browser setup
print_info "Setting up Crawl4AI..."
if [[ "$CHECK_ONLY" == false ]]; then
    if command -v crawl4ai-setup &> /dev/null; then
        crawl4ai-setup 2>/dev/null || print_warning "crawl4ai-setup had issues (may be OK)"
    else
        print_warning "crawl4ai-setup not found, running via Python..."
        python3 -c "from crawl4ai import AsyncWebCrawler; print('Crawl4AI initialized')" 2>/dev/null || true
    fi
    print_success "Crawl4AI setup complete"
fi

# ============================================================================
# Step 5: Create Directories
# ============================================================================

print_header "Step 5: Directory Setup"

mkdir -p "$SCRIPT_DIR/experiences"
mkdir -p "$SCRIPT_DIR/templates"
mkdir -p "$SCRIPT_DIR/references"

# Create site_patterns.json if not exists
if [[ ! -f "$SCRIPT_DIR/experiences/site_patterns.json" ]]; then
    echo '{}' > "$SCRIPT_DIR/experiences/site_patterns.json"
    print_success "Created experiences/site_patterns.json"
fi

# Create lessons_learned.md if not exists
if [[ ! -f "$SCRIPT_DIR/experiences/lessons_learned.md" ]]; then
    cat > "$SCRIPT_DIR/experiences/lessons_learned.md" << 'EOF'
# Lessons Learned

This file records failures and lessons learned during scraping.

## Format

```markdown
## [Date] - domain.com - [URL Pattern]
**Issue**: [What went wrong]
**Cause**: [Why it happened]
**Solution**: [How to avoid next time]
```

---

EOF
    print_success "Created experiences/lessons_learned.md"
fi

print_success "Directories initialized"

# ============================================================================
# Step 6: Verification
# ============================================================================

print_header "Step 6: Verification"

echo ""
echo "Running verification tests..."

# Test Crawl4AI
echo -n "Testing Crawl4AI... "
if python3 -c "from crawl4ai import AsyncWebCrawler; print('OK')" 2>/dev/null; then
    print_success "Crawl4AI working"
else
    print_error "Crawl4AI NOT working"
fi

# Test Playwright
echo -n "Testing Playwright... "
if python3 -c "from playwright.sync_api import sync_playwright; print('OK')" 2>/dev/null; then
    print_success "Playwright working"
else
    print_error "Playwright NOT working"
fi

# Test websockets
echo -n "Testing websockets... "
if python3 -c "import websockets; print('OK')" 2>/dev/null; then
    print_success "websockets working"
else
    print_error "websockets NOT working"
fi

# ============================================================================
# Summary
# ============================================================================

print_header "Setup Complete!"

echo ""
echo "Installation Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [[ "$MODE" == "headless" ]]; then
    echo "🖥️  Mode: Headless (VPS/Server)"
    echo ""
    echo "Usage for headless scraping:"
    echo "  python3 $SCRIPT_DIR/scripts/crawl4ai_wrapper.py <url> --output data.json"
    echo ""
    echo "Note: local_browser_scraper.py is designed for GUI environments"
    echo "      and may not work in headless mode."
else
    echo "🖥️  Mode: Local (GUI)"
    echo ""
    echo "Usage:"
    echo "  # Using Crawl4AI (headless):"
    echo "  python3 $SCRIPT_DIR/scripts/crawl4ai_wrapper.py <url> --output data.json"
    echo ""
    echo "  # Using local browser (preserves login):"
    echo "  python3 $SCRIPT_DIR/scripts/local_browser_scraper.py --launch comet --url <url>"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_success "Setup completed successfully!"
