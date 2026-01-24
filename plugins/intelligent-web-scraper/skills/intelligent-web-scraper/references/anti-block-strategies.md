# Anti-Blocking Strategies Guide

## Overview

Websites typically implement various measures to prevent automated scraping. This guide covers identifying block signals and response strategies.

## Block Signal Detection

### HTTP Status Codes

| Status | Meaning | Response Strategy |
|--------|---------|-------------------|
| 200 + Abnormal Content | Soft block, returns empty or warning | Reduce frequency |
| 403 Forbidden | Access denied | Change IP/Cookie |
| 429 Too Many Requests | Request too frequent | Significantly increase delay |
| 503 Service Unavailable | Service temporarily unavailable | Retry after waiting |
| 5xx | Server error | Retry after waiting |

### Content Anomalies

```python
def detect_soft_block(html_content):
    """Detect soft block signals"""
    block_indicators = [
        # Captcha
        'captcha', 'recaptcha', 'hcaptcha',
        '验证码', '人机验证', '安全验证',

        # Block notices
        'access denied', 'blocked', 'forbidden',
        '访问被拒绝', '您的访问已被限制', '请稍后再试',

        # Login required
        'please login', 'sign in required',
        '请登录', '需要登录',

        # Rate limit
        'rate limit', 'too many requests',
        '请求过于频繁', '操作太快'
    ]

    content_lower = html_content.lower()
    for indicator in block_indicators:
        if indicator.lower() in content_lower:
            return True, indicator

    return False, None
```

### Page Changes

```python
def detect_content_anomaly(current_result, previous_result):
    """Detect content anomalies"""
    # Content suddenly shrinks significantly
    if len(current_result.html) < len(previous_result.html) * 0.3:
        return True, "content_shrunk"

    # Page structure completely different
    if not similar_structure(current_result.html, previous_result.html):
        return True, "structure_changed"

    return False, None
```

---

## Defense Strategies

### 1. Request Frequency Control

**Basic Delay Configuration**:
```python
import random
import asyncio

class RateLimiter:
    def __init__(self, min_delay=2, max_delay=5):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.current_level = 0  # Escalation level

    async def wait(self):
        """Wait based on current level"""
        multiplier = 2 ** self.current_level  # Exponential backoff
        delay = random.uniform(
            self.min_delay * multiplier,
            self.max_delay * multiplier
        )
        await asyncio.sleep(delay)

    def escalate(self):
        """Escalate delay (when block signal detected)"""
        self.current_level = min(self.current_level + 1, 3)

    def reset(self):
        """Reset delay (on sustained success)"""
        self.current_level = max(self.current_level - 1, 0)
```

**Delay Levels**:
| Level | Delay Range | Trigger |
|-------|-------------|---------|
| 0 | 2-5s | Default |
| 1 | 4-10s | Single 429 or 503 |
| 2 | 8-20s | Consecutive block signals |
| 3 | 16-40s | Persistent blocking |

### 2. User-Agent Rotation

```python
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",

    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",

    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)
```

### 3. Complete Request Headers

```python
def get_browser_headers(url):
    """Get headers simulating real browser"""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc

    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Referer": f"https://{domain}/",
    }
```

### 4. Proxy Rotation

```python
class ProxyRotator:
    def __init__(self, proxies):
        self.proxies = proxies
        self.current_index = 0
        self.failed_proxies = set()

    def get_next(self):
        """Get next available proxy"""
        available = [p for p in self.proxies if p not in self.failed_proxies]
        if not available:
            self.failed_proxies.clear()
            available = self.proxies

        proxy = available[self.current_index % len(available)]
        self.current_index += 1
        return proxy

    def mark_failed(self, proxy):
        """Mark proxy as failed"""
        self.failed_proxies.add(proxy)

# Usage example
proxies = [
    "http://proxy1:port",
    "http://proxy2:port",
    "http://user:pass@proxy3:port",
]
rotator = ProxyRotator(proxies)
```

### 5. Cookie Management

```python
class CookieManager:
    def __init__(self):
        self.cookies = {}

    def save_cookies(self, response):
        """Save cookies from response"""
        for cookie in response.cookies:
            self.cookies[cookie.name] = cookie.value

    def get_cookies_header(self):
        """Generate Cookie header"""
        return "; ".join([f"{k}={v}" for k, v in self.cookies.items()])

    def clear(self):
        """Clear cookies"""
        self.cookies.clear()
```

---

## Adaptive Strategy Engine

### Complete Implementation

```python
import asyncio
import random
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class BlockLevel(Enum):
    NONE = 0
    LIGHT = 1
    MODERATE = 2
    SEVERE = 3
    BLOCKED = 4

@dataclass
class CrawlConfig:
    min_delay: float = 2.0
    max_delay: float = 5.0
    use_proxy: bool = False
    proxy: Optional[str] = None
    user_agent: Optional[str] = None
    max_retries: int = 3

class AdaptiveCrawler:
    """Adaptive crawler that auto-adjusts strategy based on block signals"""

    def __init__(self, proxy_rotator=None):
        self.block_level = BlockLevel.NONE
        self.consecutive_successes = 0
        self.consecutive_failures = 0
        self.proxy_rotator = proxy_rotator

    def get_config(self) -> CrawlConfig:
        """Get config based on current block level"""
        configs = {
            BlockLevel.NONE: CrawlConfig(
                min_delay=2, max_delay=5,
                use_proxy=False
            ),
            BlockLevel.LIGHT: CrawlConfig(
                min_delay=5, max_delay=10,
                use_proxy=False
            ),
            BlockLevel.MODERATE: CrawlConfig(
                min_delay=10, max_delay=20,
                use_proxy=True
            ),
            BlockLevel.SEVERE: CrawlConfig(
                min_delay=30, max_delay=60,
                use_proxy=True
            ),
            BlockLevel.BLOCKED: CrawlConfig(
                min_delay=120, max_delay=300,
                use_proxy=True
            ),
        }

        config = configs[self.block_level]

        if config.use_proxy and self.proxy_rotator:
            config.proxy = self.proxy_rotator.get_next()

        config.user_agent = get_random_user_agent()

        return config

    def report_success(self):
        """Report successful request"""
        self.consecutive_successes += 1
        self.consecutive_failures = 0

        if self.consecutive_successes >= 5:
            if self.block_level.value > 0:
                self.block_level = BlockLevel(self.block_level.value - 1)
            self.consecutive_successes = 0

    def report_failure(self, status_code=None, content=None):
        """Report failed request"""
        self.consecutive_failures += 1
        self.consecutive_successes = 0

        if status_code == 429:
            self._escalate(2)
        elif status_code == 403:
            self._escalate(2)
        elif content and detect_soft_block(content)[0]:
            self._escalate(1)
        else:
            self._escalate(1)

    def _escalate(self, levels=1):
        """Escalate block level"""
        new_level = min(self.block_level.value + levels, BlockLevel.BLOCKED.value)
        self.block_level = BlockLevel(new_level)

    async def wait(self):
        """Wait based on current config"""
        config = self.get_config()
        delay = random.uniform(config.min_delay, config.max_delay)
        await asyncio.sleep(delay)

    def should_pause(self) -> bool:
        """Whether to pause crawling"""
        return self.block_level == BlockLevel.BLOCKED
```

### Usage Example

```python
async def adaptive_crawl(urls):
    crawler = AdaptiveCrawler()
    results = []

    for url in urls:
        if crawler.should_pause():
            print("Severe blocking detected, pausing")
            print("Suggestion: Wait or change IP before continuing")
            break

        try:
            config = crawler.get_config()
            result = await fetch_page(url, config)

            if result.success:
                crawler.report_success()
                results.append(result)
            else:
                crawler.report_failure(
                    status_code=result.status_code,
                    content=result.html
                )

        except Exception as e:
            crawler.report_failure()

        await crawler.wait()

    return results
```

---

## robots.txt Compliance

```python
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

class RobotsChecker:
    def __init__(self):
        self.parsers = {}

    async def can_fetch(self, url, user_agent="*"):
        """Check if crawling is allowed"""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain not in self.parsers:
            robots_url = f"{domain}/robots.txt"
            try:
                parser = RobotFileParser()
                parser.set_url(robots_url)
                parser.read()
                self.parsers[domain] = parser
            except:
                return True

        return self.parsers[domain].can_fetch(user_agent, url)

    def get_crawl_delay(self, url, user_agent="*"):
        """Get recommended crawl delay"""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        if domain in self.parsers:
            delay = self.parsers[domain].crawl_delay(user_agent)
            if delay:
                return delay

        return None
```

---

## Best Practices Checklist

### DO

- ✅ Set reasonable request intervals (at least 2 seconds)
- ✅ Randomize request delays
- ✅ Use real browser User-Agents
- ✅ Respect robots.txt
- ✅ Handle HTTP error status codes
- ✅ Detect captcha and block pages
- ✅ Implement exponential backoff retry
- ✅ Pause and notify user when blocked

### DON'T

- ❌ Request rapidly without delays
- ❌ Use obvious crawler User-Agents
- ❌ Ignore 429/403 errors and continue requesting
- ❌ High concurrent requests in short time
- ❌ Access same IP at high frequency
- ❌ Attempt to bypass captcha (legal risk)
- ❌ Scrape login-required private content

---

## Captcha Handling

### Detect Captcha

```python
CAPTCHA_INDICATORS = [
    # Common captcha services
    'recaptcha', 'hcaptcha', 'funcaptcha', 'geetest',

    # Chinese prompts
    '验证码', '人机验证', '滑动验证', '点击验证',
    '请完成安全验证', '请进行验证',

    # English prompts
    'captcha', 'verify you are human', 'security check',
    'prove you are not a robot',

    # Common DOM elements
    'captcha-container', 'challenge-form',
]

def detect_captcha(html_content, snapshot=None):
    """Detect if page contains captcha"""
    content_lower = html_content.lower()

    for indicator in CAPTCHA_INDICATORS:
        if indicator.lower() in content_lower:
            return True

    return False
```

### Captcha Response Strategy

When captcha detected:

1. **Pause automatic crawling**
2. **Notify user**
3. **Provide manual handling options**:
   - Complete verification manually in Playwright browser
   - Wait for captcha to expire and retry
   - Retry after changing IP/proxy

```python
async def handle_captcha(url):
    """Handle captcha"""
    print(f"⚠️ Captcha detected: {url}")
    print("Options:")
    print("1. Complete verification manually in browser")
    print("2. Wait and retry")
    print("3. Skip this page")

    return "skip"  # or "retry" or "continue"
```

---

## FAQ

### Q: How long before blocking lifts?

Typically wait 15-30 minutes, or change IP for immediate retry.

### Q: How to tell if IP or account is blocked?

- IP blocked: Can access after changing IP
- Account blocked: Still blocked after IP change
- Session blocked: Can access after clearing cookies

### Q: Does using proxy completely avoid blocking?

No. Proxy only changes IP, websites may identify crawlers through other fingerprints.

### Q: Will Playwright browser be detected as crawler?

Playwright has some detectable features by default, but is closer to real browser than direct HTTP requests.
