---
name: intelligent-web-scraper
description: Self-learning intelligent web scraper agent - automatically analyzes page structure, handles pagination, anti-blocking, and discovers article series. No user configuration needed - AI decides everything.
version: 2.0.0
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - WebFetch
  - Task
  - mcp__plugin_playwright_playwright__browser_navigate
  - mcp__plugin_playwright_playwright__browser_snapshot
  - mcp__plugin_playwright_playwright__browser_take_screenshot
  - mcp__plugin_playwright_playwright__browser_click
  - mcp__plugin_playwright_playwright__browser_type
  - mcp__plugin_playwright_playwright__browser_evaluate
  - mcp__plugin_playwright_playwright__browser_wait_for
  - mcp__plugin_playwright_playwright__browser_console_messages
  - mcp__plugin_playwright_playwright__browser_network_requests
  - mcp__plugin_playwright_playwright__browser_close
  - mcp__plugin_playwright_playwright__browser_scroll
---

# Intelligent Web Scraper Agent

A self-aware, self-learning web scraping agent that accumulates experience over time.

## Prerequisites

> **IMPORTANT**: Before using this skill, ensure these dependencies are installed.

### One-Click Setup (Recommended)

```bash
# Navigate to skill directory and run setup
cd ~/.claude/skills/intelligent-web-scraper
chmod +x setup.sh && ./setup.sh

# Or for VPS/headless environment:
./setup.sh --headless
```

The setup script will:
- Detect your environment (macOS/Linux, GUI/headless)
- Install all Python dependencies
- Install Playwright browsers
- Set up Crawl4AI
- Create necessary directories

### Check Dependencies

```bash
# Check if everything is installed correctly
python3 ~/.claude/skills/intelligent-web-scraper/scripts/check_deps.py

# Auto-install missing dependencies
python3 ~/.claude/skills/intelligent-web-scraper/scripts/check_deps.py --install

# Output as JSON (for programmatic use)
python3 ~/.claude/skills/intelligent-web-scraper/scripts/check_deps.py --json
```

### Manual Setup (Alternative)

If you prefer manual installation:

```bash
# 1. Install Python dependencies
pip install -r ~/.claude/skills/intelligent-web-scraper/requirements.txt

# 2. Install Playwright browser
python -m playwright install chromium

# 3. Set up Crawl4AI
crawl4ai-setup

# 4. For VPS/headless Linux, also run:
python -m playwright install-deps chromium
```

### Required Tools

| Tool | Purpose | Installation |
|------|---------|--------------|
| **Playwright MCP** | Browser automation | Must be configured in Claude Code MCP settings |
| **Python 3.9+** | Script execution | `brew install python` or system package manager |
| **Crawl4AI** | Advanced crawling | Included in setup.sh |

### Verify Installation

```bash
# Quick verification
python -c "from crawl4ai import AsyncWebCrawler; print('Crawl4AI OK')"
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# Full check
python3 ~/.claude/skills/intelligent-web-scraper/scripts/check_deps.py
```

### VPS/Headless Deployment

For servers without GUI (VPS, Docker, CI):

```bash
# 1. Run setup in headless mode
./setup.sh --headless

# 2. The scraper will automatically use headless browser
# No GUI required - all scraping works via headless Chromium

# 3. Check configuration
python3 ~/.claude/skills/intelligent-web-scraper/scripts/config.py
```

**Note**: `local_browser_scraper.py` (CDP mode) requires a GUI and is not available in headless environments. Use `crawl4ai_wrapper.py` instead.

---

## Local Browser Scraping (CDP)

**Use this when the user wants to scrape using their local browser (Comet, Chrome, etc.)**

This allows scraping while preserving user's login sessions and cookies!

### Quick Start

```bash
# 1. Install websockets (one time)
pip install websockets

# 2. Launch Comet/Chrome with debugging (or use the script)
python ~/.claude/skills/intelligent-web-scraper/scripts/local_browser_scraper.py \
    --launch comet \
    --url "https://example.com"

# 3. Scrape data from current page
python ~/.claude/skills/intelligent-web-scraper/scripts/local_browser_scraper.py \
    --extract articles \
    --output data.json
```

### Using local_browser_scraper.py

**Launch browser with debugging:**
```bash
python scripts/local_browser_scraper.py --launch comet --url "https://douban.com"
python scripts/local_browser_scraper.py --launch chrome --url "https://example.com"
```

**Scrape from current tab:**
```bash
# Get page text
python scripts/local_browser_scraper.py --extract text

# Get all links
python scripts/local_browser_scraper.py --extract links

# Get articles
python scripts/local_browser_scraper.py --extract articles

# Custom JavaScript
python scripts/local_browser_scraper.py --extract "document.querySelectorAll('h1').length"
```

**Scrape specific tab (by URL pattern):**
```bash
python scripts/local_browser_scraper.py --url-pattern "douban.com" --extract articles
```

**Built-in extractors:** `text`, `html`, `title`, `links`, `images`, `tables`, `articles`, `metadata`

### Manual CDP (Alternative)

**CRITICAL: Always use user's EXISTING profile to preserve login sessions!**

```bash
# Comet - use existing profile
/Applications/Comet.app/Contents/MacOS/Comet \
    --remote-debugging-port=9222 \
    --user-data-dir="$HOME/Library/Application Support/Comet" \
    "https://example.com" &

# Chrome - use existing profile
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
    "https://example.com" &
```

### Browser Profile Locations (macOS)

| Browser | User Data Directory |
|---------|---------------------|
| Comet | `~/Library/Application Support/Comet` |
| Chrome | `~/Library/Application Support/Google/Chrome` |
| Edge | `~/Library/Application Support/Microsoft Edge` |
| Brave | `~/Library/Application Support/BraveSoftware/Brave-Browser` |

**NEVER use temp directory** like `/tmp/browser-debug` - this creates empty profile without logins!

**Why use existing profile:**
- Preserves all login sessions (no re-authentication needed)
- Browser extensions work normally
- User's bookmarks, history available

### When to Use Local Browser vs Playwright

| Use Local Browser | Use Playwright |
|-------------------|----------------|
| User requests specific browser | Automated bulk scraping |
| Need user's login session | Don't need authentication |
| User wants to see the page | Headless scraping OK |
| Site blocks headless browsers | Standard sites |

---

## Core Capabilities

### 1. Intelligent Page Analysis
- Auto-detect page type (product list, article, series, etc.)
- Identify data containers and selectors
- Recognize pagination mechanisms

### 2. Smart Pagination & Scroll Loading
- Page numbers, Next button, Infinite scroll, Load more, API pagination
- Auto-detect and handle appropriately

**CRITICAL: Scroll Loading Requirements**
- **MUST** automatically scroll down the page until all content is loaded
- Many modern websites use lazy loading/infinite scroll, initially showing only partial content
- Scroll strategy:
  1. Record current page height
  2. Scroll to bottom
  3. Wait 1-2 seconds for new content to load
  4. Check if page height increased
  5. Repeat until height stops changing (3 consecutive times)
- Use `browser_evaluate` to execute scrolling:
  ```javascript
  window.scrollTo(0, document.body.scrollHeight)
  ```

### 3. Detail Link Following

**CRITICAL: Detail Page Scraping Requirements**
- List pages may only show title/summary, full content is on detail pages
- **MUST** detect and follow detail links to get complete data
- Patterns to identify detail links:
  - "View more", "Read more", "Details", "Full article"
  - Title itself is a link
  - Arrow links like "→"
- Scraping workflow:
  1. First scrape all entries from list page
  2. Identify detail link for each entry
  3. Visit detail pages one by one to extract full content
  4. Merge data and save
- Note: Detail page scraping needs appropriate delays (2-5s) to avoid blocking

### 4. Anti-Blocking
- Adaptive delays (2-60s based on signals)
- User-Agent rotation
- Block detection and recovery

### 5. Series Discovery
- Find prev/next links
- Detect table of contents
- URL pattern analysis
- Build complete series from single article

### 6. **Self-Learning** (NEW)
- Records successful patterns for each domain
- Accumulates lessons learned
- Reuses knowledge on similar sites

---

## Self-Learning System

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    SCRAPE REQUEST                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Check Experience Database                            │
│ - Read experiences/site_patterns.json                        │
│ - Look for matching domain/URL pattern                       │
│ - If found: Use learned selectors and strategies             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Execute Scraping                                     │
│ - Use learned patterns OR discover new ones                  │
│ - Apply anti-blocking strategies                             │
│ - Extract data                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Learn & Record                                       │
│ - If successful: Save patterns to site_patterns.json         │
│ - If failed: Record lesson in lessons_learned.md             │
│ - Update success rate and timestamps                         │
└─────────────────────────────────────────────────────────────┘
```

### Experience Database Structure

**Location**: `~/.claude/skills/intelligent-web-scraper/experiences/`

```
experiences/
├── site_patterns.json    # Learned patterns for each domain
├── lessons_learned.md    # Accumulated wisdom and gotchas
└── README.md             # How the learning system works
```

### Pattern Storage Format

```json
{
  "domain.com": {
    "url_patterns": {
      "/movie/*/comments": {
        "selectors": {
          "container": ".comment-list",
          "item": ".comment-item",
          "fields": {
            "author": ".comment-info a",
            "content": ".comment-content span",
            "rating": ".rating"
          }
        },
        "pagination": {
          "type": "page_number",
          "selector": ".paginator a"
        },
        "scroll_loading": {
          "required": true,
          "max_scrolls": 20,
          "scroll_delay_ms": 1500,
          "notes": "Page uses infinite scroll loading"
        },
        "detail_links": {
          "required": true,
          "selector": "a.read-more, a:has-text('→')",
          "fields_in_detail": ["fullContent", "images", "comments"],
          "notes": "List page only has titles, need to scrape detail pages for full content"
        },
        "anti_block": {
          "min_delay": 3,
          "max_delay": 8,
          "needs_login": false
        },
        "success_count": 15,
        "last_success": "2024-01-15",
        "notes": "Rate limit after 50 requests"
      }
    }
  }
}
```

---

## Execution Guide

### When You Receive a Scraping Request:

#### Phase 1: Check Existing Knowledge

```python
# ALWAYS do this first
experiences_path = "~/.claude/skills/intelligent-web-scraper/experiences/site_patterns.json"
```

1. Read `site_patterns.json`
2. Extract domain from target URL
3. Check if matching pattern exists
4. If yes: Report to user "I have experience with this site, using learned patterns"

#### Phase 2: Analyze Page

```bash
# 1. Navigate to URL
browser_navigate(url)

# 2. Wait for load
browser_wait_for(time=3)

# 3. [IMPORTANT] Scroll to load all content
browser_evaluate('''async () => {
  let prevHeight = 0;
  let currentHeight = document.body.scrollHeight;
  let noChangeCount = 0;

  while (noChangeCount < 3) {
    prevHeight = currentHeight;
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, 1500));
    currentHeight = document.body.scrollHeight;

    if (currentHeight === prevHeight) {
      noChangeCount++;
    } else {
      noChangeCount = 0;
    }
  }
  return document.querySelectorAll('article, [class*="item"]').length;
}''')

# 4. Get snapshot (DOM structure)
browser_snapshot()

# 5. Take screenshot for visual analysis
browser_take_screenshot()
```

Analyze and identify:
- **Page Type**: product_list | article_list | article_series | single_page
- **Data Container**: Main wrapper selector
- **Data Items**: Individual item selector
- **Fields**: Specific data field selectors
- **Pagination**: Type and selectors
- **Detail Links**: Whether detail links need to be followed for more data

#### Phase 3: Confirm with User

```markdown
## Page Analysis Report

**URL**: [target]
**Domain Experience**: [Yes, used N times / No, first time]

### Structure Detected
- **Page Type**: [type]
- **Items Found**: ~[N] items on current page
- **Pagination**: [type] ([N] pages estimated)

### Extraction Plan
| Field | Selector | Sample |
|-------|----------|--------|
| title | .item-title | "Example Title" |
| price | .price | "$99.00" |

Continue scraping? [Y/n]
```

#### Phase 4: Execute Scraping

Apply appropriate strategy based on pagination type:
- **Page Numbers**: Iterate through URLs
- **Next Button**: Click and wait loop
- **Infinite Scroll**: Scroll and detect new content (see scroll code above)
- **Load More**: Click button until exhausted

#### Phase 4.5: Detail Page Scraping

**When list page content is incomplete, this step is required:**

```javascript
// 1. Extract all entries and their detail links
const entries = await browser_evaluate(() => {
  const items = document.querySelectorAll('article, .item');
  return Array.from(items).map(item => ({
    title: item.querySelector('h2, h3, .title')?.textContent,
    summary: item.querySelector('p, .desc')?.textContent,
    detailUrl: item.querySelector('a[href*="detail"], a[href*="view"], a:has-text("→")')?.href
  }));
});

// 2. Visit detail pages one by one
for (const entry of entries) {
  if (entry.detailUrl) {
    // Open new tab
    browser_tabs({ action: 'new' });
    browser_navigate(entry.detailUrl);
    browser_wait_for({ time: 2 });

    // Extract detail content
    const detail = await browser_evaluate(() => ({
      fullContent: document.querySelector('article, .content, main')?.innerText,
      images: Array.from(document.querySelectorAll('img')).map(i => i.src),
      metadata: { /* ... */ }
    }));

    entry.detail = detail;

    // Close tab, return to list
    browser_tabs({ action: 'close' });
    await sleep(2000); // Polite delay
  }
}
```

**When detail page scraping is needed:**
- List only shows title/date, content is on detail page
- Has "View more", "Read full article" links
- Data fields are obviously incomplete

#### Phase 5: Learn & Save

**CRITICAL**: After EVERY successful scrape, update the experience database.

```python
# Update site_patterns.json with:
{
  "selectors": discovered_selectors,
  "pagination": detected_pagination,
  "anti_block": {
    "min_delay": actual_delay_used,
    "max_delay": max_delay_used,
    "blocked_at": request_count_when_blocked or null
  },
  "success_count": previous_count + 1,
  "last_success": today,
  "notes": any_special_observations
}
```

**If scraping fails**, add entry to `lessons_learned.md`:
```markdown
## [Date] - domain.com - [URL Pattern]
**Issue**: [What went wrong]
**Cause**: [Why it happened]
**Solution**: [How to avoid next time]
```

---

## Anti-Blocking Strategy

### Delay Escalation Levels

| Level | Delay | Trigger |
|-------|-------|---------|
| 0 (Normal) | 2-5s | Default |
| 1 (Caution) | 5-10s | Single 429/503 |
| 2 (Careful) | 10-20s | Repeated warnings |
| 3 (Critical) | 30-60s | Multiple blocks |
| 4 (Pause) | STOP | Captcha detected |

### Block Signal Detection

```python
BLOCK_SIGNALS = [
    # HTTP Status
    (429, "rate_limited"),
    (403, "forbidden"),
    (503, "service_unavailable"),

    # Page Content
    ("captcha", "captcha_required"),
    ("verification code", "captcha_required"),
    ("access denied", "blocked"),
    ("please wait", "rate_limited"),
]
```

### Recovery Strategy

1. **Increase delay** exponentially
2. **Rotate User-Agent**
3. **Clear cookies** if needed
4. **Notify user** if captcha detected
5. **Record** in lessons_learned.md

---

## Series Discovery Algorithm

### Finding Related Articles

1. **Prev/Next Links**
   - Look for: prev, next, previous, following, «, »
   - Follow chain in both directions

2. **Table of Contents**
   - Look for: sidebar TOC, series index, chapter list
   - Extract all links

3. **URL Pattern Analysis**
   - Detect: /part-1, /chapter-2, ?id=3
   - Generate adjacent URLs

4. **Title Similarity**
   - Compare titles for series indicators
   - Look for: Part N, Chapter N, (1/10)

### Scoring Links

```python
score = (
    url_similarity * 30 +      # Same path structure
    series_indicator * 25 +    # Contains series keywords
    position_weight * 20 +     # In navigation area
    title_similarity * 15 +    # Similar to current title
    same_domain * 10           # Must be same domain
)

# Include if score >= 50
```

---

## Output Formats

| Format | Use Case | Extension |
|--------|----------|-----------|
| JSON | Structured data (products, lists) | .json |
| Markdown | Article content | .md |
| CSV | Tabular data | .csv |
| Auto | Let AI decide based on content | - |

---

## Example Scenarios

### Scenario 1: First-Time Domain

```
User: Scrape movie reviews from https://movie.douban.com/subject/1292052/comments

Agent:
1. [Check] No existing experience for douban.com/subject/*/comments
2. [Analyze] Opening page, taking screenshot...
   - Detected: Comment list with pagination
   - Container: #comments
   - Items: .comment-item
   - Pagination: Page numbers (.paginator)
3. [Confirm] Found ~20 comments per page, 500+ pages
   Continue? [Y/n]
4. [Execute] Scraping with 3-5s delays...
5. [Learn] Saved pattern to site_patterns.json
   - Next time: Will use learned selectors automatically
```

### Scenario 2: Returning to Known Domain

```
User: Scrape reviews for another movie https://movie.douban.com/subject/26363254/comments

Agent:
1. [Check] Found experience for douban.com/subject/*/comments
   - Last used: 2024-01-15 (15 successful runs)
   - Known selectors: .comment-item, .comment-content
   - Known rate limit: 3-8s delay recommended
2. [Execute] Using learned patterns directly...
3. [Update] Incremented success_count to 16
```

### Scenario 3: Article Series

```
User: This is part 3 of a tutorial, get the whole series
      https://blog.example.com/react-tutorial/part-3

Agent:
1. [Analyze] Detected series indicators:
   - Prev link: /react-tutorial/part-2
   - Next link: /react-tutorial/part-4
   - Sidebar TOC: 8 chapters found
2. [Discover] Complete series (8 articles):
   - Part 1: Introduction
   - Part 2: Components
   - Part 3: State (current)
   - ...
3. [Confirm] Scrape all 8 articles?
4. [Execute] Scraping series in order...
5. [Output] Saved to react-tutorial/ directory
```

### Scenario 4: Infinite Scroll + Detail Links

```
User: Scrape https://v0.app/changelog using Comet browser

Agent:
1. [Check] Found experience for v0.app/changelog
   - scroll_loading: required (infinite scroll)
   - detail_links: some entries have detail pages
2. [Navigate] Opening page in Comet browser...
3. [Scroll] Scrolling to load all content...
   - Scroll 1: 50 articles found
   - Scroll 2: 50 articles (no change)
   - Scroll 3: 50 articles (confirmed complete)
4. [Extract] Extracting list page data...
   - 50 changelog entries extracted
   - 12 entries have detail links (View announcement →)
5. [Detail] Scraping detail pages...
   - Entry 1: "Build with Glean via MCP" → fetching detail...
   - Entry 2: "Linear MCP Integration" → fetching detail...
   - ... (with 2s delay between each)
6. [Save] Merged data saved to v0_changelog.json
7. [Learn] Updated pattern:
   - scroll_loading.max_scrolls: 3 (sufficient)
   - detail_links: most are Twitter links (skip)
```

---

## Resume Capability

Scraping can be interrupted and resumed from where it left off.

### How It Works

```
~/.claude/skills/intelligent-web-scraper/progress/
├── example_com_abc123.json   # Progress for task
├── another_task.json         # Another task
└── ...
```

Each scraping task automatically saves:
- URLs completed/failed
- Current page number
- Scraped data (incremental)
- Configuration used

### Usage

```bash
# Start scraping (progress auto-saved)
python scripts/crawl4ai_wrapper.py https://example.com --output data.json

# If interrupted (Ctrl+C), progress is saved
# Resume by running the same command again

# List all progress files
python scripts/progress_manager.py --list

# Show resumable tasks
python scripts/progress_manager.py --resumable

# Check specific task status
python scripts/progress_manager.py --status example_com_abc123

# Delete progress file
python scripts/progress_manager.py --delete example_com_abc123

# Clean up old completed tasks
python scripts/progress_manager.py --cleanup 7  # Delete >7 days old
```

### Programmatic Usage

```python
from progress_manager import ProgressManager

# Start or resume a task
progress = ProgressManager("my_task", start_url="https://example.com")

# Check if resuming
if progress.has_progress():
    print(f"Resuming from {progress.state.completed_urls} URLs")

# During scraping
for url in urls:
    if progress.is_completed(url):
        continue  # Skip already done

    data = scrape(url)
    progress.mark_completed(url, data)

# Finish
progress.finish()
```

---

## Concurrent Scraping

Scrape multiple URLs in parallel with intelligent rate limiting.

### Features

- **Configurable concurrency**: Max parallel requests (global and per-domain)
- **Rate limiting**: Token bucket algorithm, per-domain limits
- **Auto retry**: Exponential backoff with jitter
- **Progress integration**: Automatic resume support
- **Graceful shutdown**: Ctrl+C saves progress

### Usage

```bash
# Scrape URLs from file
python scripts/concurrent_scraper.py urls.txt --output results.json

# High concurrency (10 parallel, 3 per domain)
python scripts/concurrent_scraper.py urls.txt -c 10 -d 3

# With rate limiting
python scripts/concurrent_scraper.py urls.txt --rate-limit 5 --domain-rate-limit 1

# Custom delays
python scripts/concurrent_scraper.py urls.txt --min-delay 2 --max-delay 5
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--concurrency, -c` | 5 | Max parallel requests total |
| `--per-domain, -d` | 2 | Max parallel per domain |
| `--rate-limit, -r` | 10 | Global rate limit (req/s) |
| `--domain-rate-limit` | 2 | Per-domain rate limit (req/s) |
| `--min-delay` | 1.0 | Min delay between requests |
| `--max-delay` | 3.0 | Max delay between requests |
| `--retries` | 3 | Max retries per URL |
| `--no-progress` | - | Disable resume capability |
| `--task-id` | - | Custom task ID for progress |

### Programmatic Usage

```python
from concurrent_scraper import ConcurrentScraper, ConcurrencyConfig

config = ConcurrencyConfig(
    max_concurrent=5,
    max_per_domain=2,
    global_rate_limit=10.0,
    per_domain_rate_limit=2.0,
)

scraper = ConcurrentScraper(config)
results = await scraper.scrape_urls(url_list)

# Print summary
scraper.print_summary()
```

### Rate Limiting Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Request Flow                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                 ┌────────────────────────┐
                 │   Global Rate Limiter   │  (10 req/s max)
                 │   (Token Bucket)        │
                 └────────────────────────┘
                              │
                              ▼
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
       ┌──────────┐    ┌──────────┐    ┌──────────┐
       │ Domain A │    │ Domain B │    │ Domain C │
       │ 2 req/s  │    │ 2 req/s  │    │ 2 req/s  │
       └──────────┘    └──────────┘    └──────────┘
              │               │               │
              ▼               ▼               ▼
       ┌──────────┐    ┌──────────┐    ┌──────────┐
       │ Semaphore│    │ Semaphore│    │ Semaphore│
       │ (max 2)  │    │ (max 2)  │    │ (max 2)  │
       └──────────┘    └──────────┘    └──────────┘
```

---

## Scripts & Archiving

### Built-in Scripts

**Location**: `~/.claude/skills/intelligent-web-scraper/scripts/`

| Script | Purpose | Usage |
|--------|---------|-------|
| `crawl4ai_wrapper.py` | Advanced Crawl4AI wrapper | `<url> --output file.json` |
| `concurrent_scraper.py` | Concurrent multi-URL scraping | `urls.txt -c 5 -o results.json` |
| `local_browser_scraper.py` | Local browser (Comet/Chrome) CDP scraping | `--launch comet --url URL` |
| `progress_manager.py` | Progress management (resume support) | `--list` / `--resumable` |
| `check_deps.py` | Dependency checking and installation | `--check` / `--install` |
| `config.py` | Environment configuration | (displays current config) |

### Script Archiving Rules

**CRITICAL: After each scraping task is completed, the scraping script must be saved in the data output directory!**

```
[data_output_directory]/
├── scrape_[site_name].py    # Scraping script for this site
├── [site_name]_data.json    # Scraped results
└── README.md                # Optional: data description
```

**Reasons:**
1. Scripts and data together for easy reuse and traceability
2. Each site has different structure, scripts should be customized
3. Can directly run the script next time for the same site

**Script naming convention:** `scrape_[domain_or_short_name].py`
- Example: `scrape_v0_changelog.py`
- Example: `scrape_douban_comments.py`

**Scripts should include:**
1. Target URL
2. Scroll loading logic (if needed)
3. Data extraction logic
4. Output file path

---

## Reference Documents

Detailed technical references:
- [Crawl4AI API Reference](references/crawl4ai-reference.md)
- [Pagination Patterns Guide](references/pagination-patterns.md)
- [Anti-Blocking Strategies](references/anti-block-strategies.md)
- [Link Discovery Guide](references/link-discovery-guide.md)

---

## Self-Learning Checklist

**ALWAYS follow this after every scraping task:**

- [ ] Read existing `site_patterns.json` before starting
- [ ] Use learned patterns if domain/URL pattern matches
- [ ] **Scroll check**: Does page need scroll loading? Record scroll_loading config
- [ ] **Detail check**: Is list data complete? Need to scrape detail pages? Record detail_links config
- [ ] After success: Update `site_patterns.json` with new/refined patterns
- [ ] After failure: Add entry to `lessons_learned.md`
- [ ] Note any special behaviors (rate limits, required delays, gotchas)
- [ ] Increment success_count and update last_success date

**Scroll loading fields:**
- `scroll_loading.required`: Whether scrolling is needed
- `scroll_loading.max_scrolls`: How many scrolls to reach bottom
- `scroll_loading.scroll_delay_ms`: Wait time after each scroll

**Detail link fields:**
- `detail_links.required`: Whether detail scraping is needed
- `detail_links.selector`: Detail link selector
- `detail_links.fields_in_detail`: Fields only available on detail page

---

## Important Notes

1. **Respect websites**: Follow robots.txt, don't overload servers
2. **Legal use only**: Only scrape public information
3. **Privacy**: Don't scrape personal data
4. **Self-improve**: Always record learnings
5. **Share knowledge**: Patterns help future scraping tasks
