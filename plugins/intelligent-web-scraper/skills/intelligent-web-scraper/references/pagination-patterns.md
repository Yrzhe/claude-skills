# Pagination Patterns Recognition Guide

## Overview

Web pagination is a common content display pattern. This guide helps identify and handle various pagination mechanisms.

## Pagination Types

### 1. Page Number Pagination

**Recognition Features**:
```html
<!-- Common HTML structures -->
<div class="pagination">
    <a href="?page=1" class="active">1</a>
    <a href="?page=2">2</a>
    <a href="?page=3">3</a>
    ...
    <a href="?page=10">10</a>
</div>

<!-- Or -->
<ul class="page-list">
    <li class="page-item"><a class="page-link" href="/list/1">1</a></li>
    <li class="page-item"><a class="page-link" href="/list/2">2</a></li>
</ul>
```

**Common CSS Classes**:
- `.pagination`, `.pager`, `.page-numbers`
- `.page-item`, `.page-link`, `.page-num`
- `[class*="page"]`, `[class*="paging"]`

**URL Patterns**:
```
# Query parameters
?page=2
?p=2
?pageNum=2
?offset=20

# Path parameters
/page/2
/list/2
/articles/page-2
```

**Handling Strategy**:
```python
# Method 1: URL parameter iteration
async def crawl_by_page_param(base_url, param_name="page", max_pages=None):
    page = 1
    all_results = []

    while True:
        url = f"{base_url}?{param_name}={page}"
        result = await crawler.arun(url)

        if not result.success or is_empty_page(result):
            break

        all_results.extend(extract_items(result))
        page += 1

        if max_pages and page > max_pages:
            break

        await asyncio.sleep(random.uniform(2, 5))

    return all_results

# Method 2: Extract all page links from page
async def get_all_page_urls(result):
    js_code = """
    Array.from(document.querySelectorAll('.pagination a'))
        .map(a => a.href)
        .filter(href => href.includes('page'))
    """
    return await browser_evaluate(js_code)
```

---

### 2. Next Button

**Recognition Features**:
```html
<!-- Common structures -->
<a href="/list?page=2" class="next">Next</a>
<button class="next-page">Next →</button>
<a class="btn-next" rel="next">»</a>

<!-- Possible attributes -->
<a rel="next" href="...">
<link rel="next" href="...">
```

**Common Text/Symbols**:
- English: "Next", "Next Page", "More", "Continue"
- Symbols: `→`, `»`, `>`, `>>`, `›`
- Chinese: "下一页", "下一篇", "后一页", "继续"

**Common CSS Classes**:
- `.next`, `.next-page`, `.btn-next`
- `.nav-next`, `.pagination-next`
- `[rel="next"]`

**Handling Strategy**:
```python
async def crawl_by_next_button(start_url, next_selector=".next"):
    all_results = []
    current_url = start_url

    while True:
        await browser_navigate(current_url)
        await browser_wait_for(time=2)

        snapshot = await browser_snapshot()
        all_results.extend(extract_from_snapshot(snapshot))

        next_btn = find_element_in_snapshot(snapshot, next_selector)

        if not next_btn or is_disabled(next_btn):
            break

        if next_btn.get("href"):
            current_url = next_btn["href"]
        else:
            await browser_click(element=next_selector, ref=next_btn["ref"])
            await browser_wait_for(time=2)

        await asyncio.sleep(random.uniform(2, 5))

    return all_results
```

**End Detection**:
- Next button doesn't exist
- Next button has `disabled` attribute
- Next button has `.disabled` class
- Next button's `href` equals current URL
- Page content same as previous page

---

### 3. Infinite Scroll

**Recognition Features**:
```javascript
// Common implementations
window.addEventListener('scroll', loadMore);
new IntersectionObserver(callback).observe(sentinel);

// Possible marker elements
<div class="loading-spinner" style="display:none"></div>
<div class="load-more-trigger"></div>
<div id="sentinel"></div>
```

**Detection Methods**:
1. Page height increases with scrolling
2. `IntersectionObserver` or scroll event listeners exist
3. Loading indicator elements present
4. XHR/Fetch calls with pagination params in network requests

**Handling Strategy**:
```javascript
// Method 1: Simple scroll to bottom
async function scrollToBottom(maxScrolls = 20, delay = 2000) {
    let lastHeight = document.body.scrollHeight;
    let scrollCount = 0;

    while (scrollCount < maxScrolls) {
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, delay));

        const newHeight = document.body.scrollHeight;
        if (newHeight === lastHeight) {
            // Wait longer to confirm no new content
            await new Promise(r => setTimeout(r, delay * 2));
            if (document.body.scrollHeight === lastHeight) {
                break;
            }
        }
        lastHeight = newHeight;
        scrollCount++;
    }
}

// Method 2: Monitor content count changes
async function scrollUntilNoNewContent(containerSelector, itemSelector) {
    let lastCount = 0;
    let noChangeCount = 0;

    while (noChangeCount < 3) {
        window.scrollTo(0, document.body.scrollHeight);
        await new Promise(r => setTimeout(r, 2000));

        const currentCount = document.querySelectorAll(itemSelector).length;
        if (currentCount === lastCount) {
            noChangeCount++;
        } else {
            noChangeCount = 0;
            lastCount = currentCount;
        }
    }

    return lastCount;
}
```

**Playwright Execution**:
```python
scroll_script = """
async (page) => {
    let lastHeight = await page.evaluate('document.body.scrollHeight');
    let scrolls = 0;
    const maxScrolls = 20;

    while (scrolls < maxScrolls) {
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
        await page.waitForTimeout(2000);

        const newHeight = await page.evaluate('document.body.scrollHeight');
        if (newHeight === lastHeight) break;

        lastHeight = newHeight;
        scrolls++;
    }

    return scrolls;
}
"""
await browser_evaluate(function=scroll_script)
```

---

### 4. Load More Button

**Recognition Features**:
```html
<button class="load-more">Load More</button>
<a class="view-more" href="javascript:void(0)">View More</a>
<div class="show-more" onclick="loadMore()">Show All</div>
```

**Common Text**:
- English: "Load More", "View More", "Show More", "See More"
- Chinese: "加载更多", "查看更多", "展开全部", "显示更多"

**Common CSS Classes**:
- `.load-more`, `.loadmore`
- `.view-more`, `.show-more`
- `.btn-more`, `.more-btn`

**Handling Strategy**:
```javascript
async function clickLoadMoreUntilDone(buttonSelector) {
    let clickCount = 0;
    const maxClicks = 50;

    while (clickCount < maxClicks) {
        const button = document.querySelector(buttonSelector);

        if (!button || button.offsetParent === null) {
            break;
        }

        if (button.disabled || button.classList.contains('disabled')) {
            break;
        }

        button.click();
        clickCount++;

        await new Promise(r => setTimeout(r, 2000));
    }

    return clickCount;
}
```

---

### 5. API Pagination

**Recognition Features**:

Discovered through network request analysis:
```javascript
// Common API pagination parameters
GET /api/items?page=1&limit=20
GET /api/items?offset=0&count=20
GET /api/items?cursor=abc123
GET /api/items?after=item_id_123

// Pagination info in response
{
    "data": [...],
    "pagination": {
        "page": 1,
        "totalPages": 10,
        "nextCursor": "abc123"
    }
}
```

**Handling Strategy**:
```python
async def crawl_via_api(api_base_url):
    all_data = []
    page = 1
    has_more = True

    while has_more:
        response = await fetch_json(f"{api_base_url}?page={page}&limit=50")

        if not response or "data" not in response:
            break

        all_data.extend(response["data"])

        pagination = response.get("pagination", {})
        has_more = pagination.get("hasMore", False)
        page += 1

        await asyncio.sleep(random.uniform(1, 3))

    return all_data
```

**How to Discover API**:
```python
# Use browser_network_requests to get network requests
requests = await browser_network_requests()

# Filter XHR requests
xhr_requests = [r for r in requests if r.get("resourceType") == "xhr"]

# Analyze for pagination API
for req in xhr_requests:
    url = req.get("url", "")
    if any(param in url for param in ["page", "offset", "cursor", "limit"]):
        print(f"Found pagination API: {url}")
```

---

## Auto-Detection Flow

```
┌─────────────────────────────────────────┐
│     Get page snapshot and screenshot     │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  Check for page number elements          │
│  (.pagination etc)                       │
│  YES → Page Number Pagination            │
└─────────────────────────────────────────┘
                    │ NO
                    ▼
┌─────────────────────────────────────────┐
│  Check for next button                   │
│  (Next, →)                               │
│  YES → Next Button                       │
└─────────────────────────────────────────┘
                    │ NO
                    ▼
┌─────────────────────────────────────────┐
│  Check for load more button              │
│  (Load More)                             │
│  YES → Load More Button                  │
└─────────────────────────────────────────┘
                    │ NO
                    ▼
┌─────────────────────────────────────────┐
│  Check network requests for pagination   │
│  API                                     │
│  YES → API Pagination                    │
└─────────────────────────────────────────┘
                    │ NO
                    ▼
┌─────────────────────────────────────────┐
│  Try scrolling, check for new content    │
│  YES → Infinite Scroll                   │
│  NO  → No Pagination                     │
└─────────────────────────────────────────┘
```

---

## Best Practices

### 1. Always Add Delays

```python
await asyncio.sleep(random.uniform(2, 5))
```

### 2. Detect Duplicate Content

```python
def is_duplicate_page(current_items, previous_items):
    if not previous_items:
        return False
    return current_items == previous_items
```

### 3. Set Maximum Limits

```python
MAX_PAGES = 100
MAX_ITEMS = 1000
```

### 4. Handle Empty Pages

```python
def is_empty_page(result):
    items = extract_items(result)
    return len(items) == 0
```

### 5. Track Progress

```python
async def crawl_with_progress(urls):
    for i, url in enumerate(urls):
        print(f"Progress: {i+1}/{len(urls)}")
        # ... crawl logic
```

---

## FAQ

### Q: How to handle login-required pagination?

Login manually in browser first, ensure session is valid before pagination crawling.

### Q: Content doesn't update after pagination?

May be SPA application, need to wait for content load:
```python
await browser_wait_for(text="expected content")
```

### Q: How to know total page count?

- Find max number in page links
- Look for "Total X pages" text
- Check `totalPages` field in API response
- Continue crawling until no new content
