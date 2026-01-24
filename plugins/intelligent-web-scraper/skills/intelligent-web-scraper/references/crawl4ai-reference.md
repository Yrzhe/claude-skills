# Crawl4AI API Reference

## Overview

Crawl4AI is an asynchronous web crawling framework designed for AI agents, supporting LLM integration, intelligent extraction, and deep crawling.

## Installation

```bash
# Basic installation
pip install crawl4ai

# Install browser dependencies
crawl4ai-setup

# Or manually install Playwright browsers
playwright install chromium
```

## Core Classes

### AsyncWebCrawler

The main crawler class for asynchronous web crawling.

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig

async def main():
    browser_config = BrowserConfig(
        headless=True,
        browser_type="chromium",
        # Optional: custom browser path
        # executable_path="/path/to/browser"
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=CrawlerRunConfig()
        )
        print(result.markdown)
```

### CrawlerRunConfig

Configuration class controlling single crawl behavior.

```python
from crawl4ai import CrawlerRunConfig

config = CrawlerRunConfig(
    # Basic config
    word_count_threshold=10,
    remove_overlay_elements=True,

    # Wait config
    wait_for="css:.content-loaded",
    delay_before_return_html=2.0,

    # JavaScript execution
    js_code="window.scrollTo(0, document.body.scrollHeight)",

    # Content extraction
    extraction_strategy=None,

    # Deep crawl
    deep_crawl_strategy=None,

    # Screenshots
    screenshot=True,
    pdf=False,
)
```

### BrowserConfig

Browser configuration class.

```python
from crawl4ai import BrowserConfig

browser_config = BrowserConfig(
    browser_type="chromium",        # chromium, firefox, webkit
    headless=True,

    # Viewport
    viewport_width=1920,
    viewport_height=1080,

    # Proxy
    proxy="http://proxy:port",
    proxy_config={
        "server": "http://proxy:port",
        "username": "user",
        "password": "pass"
    },

    # User data directory (maintain login state)
    user_data_dir="/path/to/user/data",

    # Custom browser path
    executable_path="/path/to/chromium",

    # User-Agent
    user_agent="Mozilla/5.0 ...",

    # Ignore HTTPS errors
    ignore_https_errors=True,
)
```

## Extraction Strategies

### LLMExtractionStrategy

Use LLM for intelligent content extraction.

```python
from crawl4ai.extraction import LLMExtractionStrategy
from pydantic import BaseModel
from typing import List

class Product(BaseModel):
    name: str
    price: float
    description: str
    image_url: str

class ProductList(BaseModel):
    products: List[Product]

strategy = LLMExtractionStrategy(
    provider="anthropic/claude-sonnet",
    api_token="your-api-key",
    schema=ProductList,
    extraction_type="schema",
    instruction="Extract all products from this e-commerce page"
)

config = CrawlerRunConfig(extraction_strategy=strategy)
```

### JsonCssExtractionStrategy

Extract JSON data using CSS selectors.

```python
from crawl4ai.extraction import JsonCssExtractionStrategy

strategy = JsonCssExtractionStrategy(
    schema={
        "name": "products",
        "baseSelector": ".product-item",
        "fields": [
            {"name": "title", "selector": ".title", "type": "text"},
            {"name": "price", "selector": ".price", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"},
            {"name": "image", "selector": "img", "type": "attribute", "attribute": "src"}
        ]
    }
)
```

### CosineStrategy

Content clustering and extraction using cosine similarity.

```python
from crawl4ai.extraction import CosineStrategy

strategy = CosineStrategy(
    semantic_filter="product information",
    word_count_threshold=10,
    sim_threshold=0.3,
    max_dist=0.2,
)
```

## Deep Crawl Strategies

### BFSDeepCrawlStrategy

Breadth-first search crawl strategy.

```python
from crawl4ai.deep_crawl import BFSDeepCrawlStrategy

strategy = BFSDeepCrawlStrategy(
    max_depth=3,
    max_pages=100,
    include_external=False,

    filter_chain=FilterChain([
        URLPatternFilter(patterns=["/article/", "/post/"]),
        DomainFilter(allowed_domains=["example.com"])
    ])
)
```

### BestFirstCrawlingStrategy

Smart priority crawl strategy, prioritizing high-relevance pages.

```python
from crawl4ai.deep_crawl import BestFirstCrawlingStrategy

strategy = BestFirstCrawlingStrategy(
    max_depth=5,
    max_pages=50,
    score_threshold=0.5,
    keywords=["tutorial", "guide"],
)
```

## Pagination Handling

### Virtual Scroll Config

Handle infinite scroll pages.

```python
from crawl4ai import VirtualScrollConfig

scroll_config = VirtualScrollConfig(
    check_interval=0.1,
    max_scrolls=20,
    scroll_delay=0.5,
    selector=".item-list",
)

config = CrawlerRunConfig(
    virtual_scroll=scroll_config,
)
```

### JavaScript Pagination

Manual pagination control.

```python
js_code = """
async () => {
    let loadMore = document.querySelector('.load-more-btn');
    while (loadMore && loadMore.offsetParent !== null) {
        loadMore.click();
        await new Promise(r => setTimeout(r, 2000));
        loadMore = document.querySelector('.load-more-btn');
    }
}
"""

config = CrawlerRunConfig(
    js_code=js_code,
    wait_for="css:.all-loaded",
)
```

## Session Management

```python
# Method 1: Use user_data_dir
browser_config = BrowserConfig(
    user_data_dir="/path/to/chrome/profile"
)

# Method 2: Use cookies
config = CrawlerRunConfig(
    cookies=[
        {"name": "session", "value": "xxx", "domain": "example.com"}
    ]
)

# Method 3: Session reuse
async with AsyncWebCrawler() as crawler:
    # First request (login)
    await crawler.arun(
        url="https://example.com/login",
        config=CrawlerRunConfig(
            js_code="document.querySelector('#login-btn').click()"
        ),
        session_id="my_session"
    )

    # Subsequent requests reuse session
    result = await crawler.arun(
        url="https://example.com/protected",
        session_id="my_session"
    )
```

## Result Object

`CrawlResult` object contains crawl results.

```python
result = await crawler.arun(url, config)

# Main properties
result.url              # Crawled URL
result.html             # Raw HTML
result.cleaned_html     # Cleaned HTML
result.markdown         # Markdown format content
result.extracted_content # Extracted structured data (JSON string)
result.links            # Page links list
result.images           # Images list
result.screenshot       # Screenshot (base64)
result.success          # Success status
result.error_message    # Error message
```

## Error Handling

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def safe_crawl(url):
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    page_timeout=30000,
                )
            )

            if not result.success:
                print(f"Crawl failed: {result.error_message}")
                return None

            return result

    except TimeoutError:
        print("Request timeout")
    except Exception as e:
        print(f"Unknown error: {e}")

    return None
```

## Proxy Configuration

```python
# Single proxy
browser_config = BrowserConfig(
    proxy="http://user:pass@proxy:port"
)

# Proxy rotation
from crawl4ai.proxy import RoundRobinProxyStrategy

proxy_strategy = RoundRobinProxyStrategy([
    "http://proxy1:port",
    "http://proxy2:port",
    "http://proxy3:port"
])

browser_config = BrowserConfig(
    proxy_rotation_strategy=proxy_strategy
)
```

## Common Patterns

### Product List Scraping

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction import JsonCssExtractionStrategy

async def crawl_products(url):
    strategy = JsonCssExtractionStrategy(
        schema={
            "name": "products",
            "baseSelector": ".product-card",
            "fields": [
                {"name": "name", "selector": ".product-name", "type": "text"},
                {"name": "price", "selector": ".product-price", "type": "text"},
                {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"}
            ]
        }
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                extraction_strategy=strategy,
                wait_for="css:.product-card"
            )
        )
        return json.loads(result.extracted_content)
```

### Article Content Scraping

```python
async def crawl_article(url):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            config=CrawlerRunConfig(
                word_count_threshold=50,
                remove_overlay_elements=True,
            )
        )
        return {
            "url": result.url,
            "markdown": result.markdown,
            "links": result.links
        }
```

### Multi-Page Scraping

```python
async def crawl_multiple_pages(base_url, max_pages=10):
    all_data = []

    async with AsyncWebCrawler() as crawler:
        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}"
            result = await crawler.arun(url, config=CrawlerRunConfig())

            if not result.success:
                break

            all_data.extend(extract_items(result))

            # Anti-blocking delay
            await asyncio.sleep(random.uniform(2, 5))

    return all_data
```

## Environment Variables

```bash
# LLM API Keys
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key

# Custom browser
CRAWL4AI_BROWSER_PATH=/path/to/chromium

# Proxy
HTTP_PROXY=http://proxy:port
HTTPS_PROXY=http://proxy:port
```

## Performance Optimization

1. **Use headless mode**: `headless=True`
2. **Disable images**: Intercept image requests via `js_code`
3. **Set reasonable timeout**: `page_timeout=30000`
4. **Use session reuse**: Avoid repeated connections
5. **CSS selectors over LLM**: Prefer CSS extraction for structured pages

## Common Issues

### Incomplete Page Load

```python
config = CrawlerRunConfig(
    wait_for="css:.content-loaded",
    delay_before_return_html=3.0,
)
```

### Dynamic Content Not Loaded

```python
config = CrawlerRunConfig(
    js_code="""
        // Trigger lazy loading
        window.scrollTo(0, document.body.scrollHeight);
    """,
    delay_before_return_html=2.0,
)
```

### Website Blocking

See [Anti-Blocking Strategies](anti-block-strategies.md) document.
