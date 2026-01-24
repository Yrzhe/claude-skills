# Series Discovery Algorithm Guide

## Overview

Automatically discovering and scraping entire series from a single article is a core capability of the intelligent scraper. This guide covers link discovery and series recognition algorithms.

## Series Marker Recognition

### 1. Navigation Elements

**Prev/Next Links**:
```html
<!-- Common structures -->
<a class="prev" href="/post/1">← Previous</a>
<a class="next" href="/post/3">Next →</a>

<nav class="post-navigation">
    <a rel="prev" href="...">Previous Post</a>
    <a rel="next" href="...">Next Post</a>
</nav>

<div class="article-nav">
    <span class="nav-previous"><a href="...">« Previous Chapter</a></span>
    <span class="nav-next"><a href="...">Next Chapter »</a></span>
</div>
```

**Recognition Keywords**:
| Language | Previous | Next |
|----------|----------|------|
| English | Previous, Prev, Prior, Earlier, « | Next, Following, Continue, » |
| Chinese | 上一篇, 上一章, 前一篇, 上一节, « | 下一篇, 下一章, 后一篇, 下一节, » |

**CSS Selectors**:
```python
PREV_NEXT_SELECTORS = [
    '.prev', '.next',
    '.previous', '.following',
    '[rel="prev"]', '[rel="next"]',
    '.nav-previous', '.nav-next',
    '.post-prev', '.post-next',
    '.article-prev', '.article-next',
]
```

### 2. Table of Contents / Index Links

**Common Structures**:
```html
<!-- Sidebar TOC -->
<aside class="sidebar">
    <h3>Series Contents</h3>
    <ul class="series-toc">
        <li><a href="/post/1">Chapter 1: Introduction</a></li>
        <li><a href="/post/2">Chapter 2: Basics</a></li>
        <li class="active"><a href="/post/3">Chapter 3: Advanced</a></li>
        ...
    </ul>
</aside>

<!-- In-article TOC -->
<div class="table-of-contents">
    <h2>Contents</h2>
    <ol>
        <li><a href="#section1">Part One</a></li>
        <li><a href="#section2">Part Two</a></li>
    </ol>
</div>

<!-- Series label -->
<div class="series-info">
    <span>This article belongs to series: </span>
    <a href="/series/python-tutorial">Python Tutorial</a>
    <span>(10 articles total)</span>
</div>
```

**Recognition Keywords**:
- English: Contents, Index, Series, Chapters, All Posts, Table of Contents, TOC
- Chinese: 目录, 索引, 系列, 章节, 全部文章, 文章列表

### 3. Series Labels / Numbers

**URL Patterns**:
```
# Number sequences
/tutorial/part-1, /tutorial/part-2
/post/001, /post/002
/chapter-1, /chapter-2

# Query parameters
?id=1, ?id=2
?page=1, ?page=2
?episode=1, ?episode=2
```

**Title Patterns**:
```
# English
Part 1: xxx
Chapter 1 - xxx
Episode 1: xxx
[Series] xxx #1

# Chinese
第1章: xxx
第一部分 - xxx
(1/10) xxx
【系列】xxx (一)
```

### 4. Related Recommendations

```html
<div class="related-posts">
    <h3>Related Articles</h3>
    <ul>
        <li><a href="...">Related Article 1</a></li>
        <li><a href="...">Related Article 2</a></li>
    </ul>
</div>

<section class="more-from-series">
    <h3>More from This Series</h3>
    ...
</section>
```

---

## Link Scoring Algorithm

### Scoring Dimensions

```python
def calculate_link_score(link, current_page):
    """
    Calculate link relevance score to current page
    Score range: 0-100
    """
    score = 0

    # 1. URL pattern similarity (0-30 points)
    url_similarity = calculate_url_pattern_similarity(link.url, current_page.url)
    score += url_similarity * 30

    # 2. Title similarity (0-25 points)
    title_similarity = calculate_title_similarity(link.text, current_page.title)
    score += title_similarity * 25

    # 3. DOM position weight (0-20 points)
    position_score = get_position_score(link.position)
    score += position_score * 20

    # 4. Series indicator bonus (0-15 points)
    series_indicators = count_series_indicators(link)
    score += min(series_indicators * 5, 15)

    # 5. Same domain bonus (0-10 points)
    if same_domain(link.url, current_page.url):
        score += 10

    return score
```

### URL Pattern Analysis

```python
import re
from urllib.parse import urlparse, parse_qs

def analyze_url_pattern(url):
    """Analyze URL pattern features"""
    parsed = urlparse(url)
    path = parsed.path
    query = parse_qs(parsed.query)

    patterns = {
        'has_number': bool(re.search(r'\d+', path)),
        'number_at_end': bool(re.search(r'/\d+/?$', path)),
        'part_pattern': bool(re.search(r'part[-_]?\d+', path, re.I)),
        'chapter_pattern': bool(re.search(r'(chapter|chap|ch)[-_]?\d+', path, re.I)),
        'page_param': 'page' in query or 'p' in query,
        'id_param': 'id' in query,
    }

    return patterns

def calculate_url_pattern_similarity(url1, url2):
    """Calculate similarity between two URLs"""
    parsed1 = urlparse(url1)
    parsed2 = urlparse(url2)

    if parsed1.netloc != parsed2.netloc:
        return 0

    path1 = parsed1.path
    path2 = parsed2.path

    segments1 = [s for s in path1.split('/') if s]
    segments2 = [s for s in path2.split('/') if s]

    if len(segments1) != len(segments2):
        return 0.3

    same_segments = 0
    diff_is_number = False

    for s1, s2 in zip(segments1, segments2):
        if s1 == s2:
            same_segments += 1
        elif re.match(r'^\d+$', s1) and re.match(r'^\d+$', s2):
            diff_is_number = True

    similarity = same_segments / len(segments1)

    if diff_is_number:
        similarity = min(similarity + 0.3, 1.0)

    return similarity
```

### Title Similarity

```python
from difflib import SequenceMatcher
import re

def calculate_title_similarity(title1, title2):
    """Calculate title similarity"""
    if not title1 or not title2:
        return 0

    def remove_numbers(text):
        text = re.sub(r'^(第\s*)?\d+\s*(章|节|部分|篇)?[:\-\s]*', '', text)
        text = re.sub(r'^(Part|Chapter|Episode)\s*\d+[:\-\s]*', '', text, flags=re.I)
        text = re.sub(r'\(\d+/\d+\)', '', text)
        return text.strip()

    clean1 = remove_numbers(title1)
    clean2 = remove_numbers(title2)

    return SequenceMatcher(None, clean1.lower(), clean2.lower()).ratio()
```

### DOM Position Weight

```python
def get_position_score(link_element):
    """Calculate weight based on link's DOM position"""
    position_weights = {
        # Navigation area
        'nav': 0.9,
        'navigation': 0.9,
        'post-navigation': 0.95,
        'article-navigation': 0.95,

        # Sidebar TOC
        'sidebar': 0.7,
        'toc': 0.85,
        'table-of-contents': 0.85,
        'series-toc': 0.95,

        # Related articles
        'related': 0.6,
        'related-posts': 0.65,

        # Footer
        'footer': 0.4,

        # Main content
        'content': 0.5,
        'article': 0.5,
        'main': 0.5,
    }

    for ancestor_class in link_element.get('ancestor_classes', []):
        for key, weight in position_weights.items():
            if key in ancestor_class.lower():
                return weight

    return 0.5
```

---

## Series Discovery Algorithm

### BFS Breadth-First Search

```python
from collections import deque
from urllib.parse import urljoin

async def discover_series_bfs(start_url, max_pages=50):
    """
    Discover series articles using BFS
    """
    visited = set()
    queue = deque([start_url])
    series = []
    base_domain = urlparse(start_url).netloc

    while queue and len(series) < max_pages:
        current_url = queue.popleft()

        if current_url in visited:
            continue

        visited.add(current_url)

        page = await fetch_page(current_url)
        if not page:
            continue

        series.append({
            'url': current_url,
            'title': page.title,
            'content': page.content
        })

        links = extract_links(page)
        scored_links = []

        for link in links:
            if urlparse(link.url).netloc != base_domain:
                continue

            if link.url in visited:
                continue

            score = calculate_link_score(link, page)
            if score >= 50:
                scored_links.append((link.url, score))

        scored_links.sort(key=lambda x: x[1], reverse=True)
        for url, _ in scored_links[:10]:
            if url not in visited:
                queue.append(url)

    return series
```

### Intelligent Series Recognition

```python
async def discover_series_intelligent(start_url):
    """
    Intelligently recognize series articles
    Using multiple strategies combined
    """
    page = await fetch_page(start_url)
    if not page:
        return []

    series_urls = set([start_url])

    # Strategy 1: Find prev/next links
    prev_next = find_prev_next_links(page)
    if prev_next:
        series_urls.update(await follow_prev_next_chain(start_url, prev_next))

    # Strategy 2: Find TOC/index
    toc_links = find_toc_links(page)
    if toc_links:
        series_urls.update(toc_links)

    # Strategy 3: Analyze URL patterns
    url_pattern = analyze_url_pattern(start_url)
    if url_pattern['has_number']:
        adjacent_urls = generate_adjacent_urls(start_url)
        for url in adjacent_urls:
            if await url_exists(url):
                series_urls.add(url)

    # Strategy 4: Title similarity based
    all_links = extract_links(page)
    similar_title_links = [
        link.url for link in all_links
        if calculate_title_similarity(link.text, page.title) > 0.5
    ]
    series_urls.update(similar_title_links)

    series = await fetch_series_metadata(series_urls)
    series = sort_series(series)

    return series

def find_prev_next_links(page):
    """Find prev/next links"""
    result = {'prev': None, 'next': None}

    prev_link = page.find_element('[rel="prev"]')
    next_link = page.find_element('[rel="next"]')

    if prev_link:
        result['prev'] = prev_link.get('href')
    if next_link:
        result['next'] = next_link.get('href')

    if not result['prev']:
        for text in ['Previous', 'Prev', '上一篇', '上一章', '«']:
            link = page.find_link_by_text(text)
            if link:
                result['prev'] = link.get('href')
                break

    if not result['next']:
        for text in ['Next', '下一篇', '下一章', '»']:
            link = page.find_link_by_text(text)
            if link:
                result['next'] = link.get('href')
                break

    return result

async def follow_prev_next_chain(start_url, initial_links):
    """Traverse entire series along prev/next chain"""
    urls = set([start_url])

    # Traverse backwards
    current = initial_links.get('prev')
    while current and current not in urls:
        urls.add(current)
        page = await fetch_page(current)
        if not page:
            break
        links = find_prev_next_links(page)
        current = links.get('prev')

    # Traverse forwards
    current = initial_links.get('next')
    while current and current not in urls:
        urls.add(current)
        page = await fetch_page(current)
        if not page:
            break
        links = find_prev_next_links(page)
        current = links.get('next')

    return urls
```

### URL Pattern Generation

```python
import re

def generate_adjacent_urls(url):
    """Generate adjacent URLs based on URL pattern"""
    adjacent = []

    numbers = re.findall(r'\d+', url)

    for num in numbers:
        num_int = int(num)

        for delta in [-2, -1, 1, 2]:
            new_num = num_int + delta
            if new_num > 0:
                if num.startswith('0'):
                    new_num_str = str(new_num).zfill(len(num))
                else:
                    new_num_str = str(new_num)

                new_url = url.replace(num, new_num_str, 1)
                if new_url != url:
                    adjacent.append(new_url)

    return list(set(adjacent))
```

---

## Series Sorting

```python
def sort_series(series):
    """Sort series articles"""

    def extract_order(article):
        """Extract sort key from article"""
        url = article['url']
        title = article['title']

        # 1. Extract number from URL
        url_numbers = re.findall(r'(\d+)', url)
        if url_numbers:
            return int(url_numbers[-1])

        # 2. Extract number from title
        # Chinese numbers
        cn_num_map = {'一':1, '二':2, '三':3, '四':4, '五':5,
                      '六':6, '七':7, '八':8, '九':9, '十':10}
        cn_match = re.search(r'第([一二三四五六七八九十]+)[章节篇部]', title)
        if cn_match:
            cn_num = cn_match.group(1)
            if cn_num in cn_num_map:
                return cn_num_map[cn_num]

        # Arabic numbers
        title_numbers = re.findall(r'第?\s*(\d+)\s*[章节篇部]?', title)
        if title_numbers:
            return int(title_numbers[0])

        # Part/Chapter pattern
        part_match = re.search(r'(part|chapter|episode)\s*(\d+)', title, re.I)
        if part_match:
            return int(part_match.group(2))

        return 999

    return sorted(series, key=extract_order)
```

---

## Series Completeness Verification

```python
def verify_series_completeness(series):
    """Verify if series is complete"""
    issues = []

    if len(series) < 2:
        return {'complete': False, 'issues': ['Series has too few articles']}

    numbers = []
    for article in series:
        order = extract_order_number(article)
        if order:
            numbers.append(order)

    if not numbers:
        return {'complete': True, 'issues': ['Cannot determine order, assuming complete']}

    numbers.sort()

    if numbers[0] != 1:
        issues.append(f'Series may be missing beginning, min number is {numbers[0]}')

    for i in range(1, len(numbers)):
        if numbers[i] - numbers[i-1] > 1:
            missing = list(range(numbers[i-1]+1, numbers[i]))
            issues.append(f'May be missing parts {missing}')

    return {
        'complete': len(issues) == 0,
        'issues': issues,
        'found_range': f'{min(numbers)} - {max(numbers)}' if numbers else 'N/A'
    }
```

---

## Usage Examples

### Basic Usage

```python
# Discover series from single article
start_url = "https://blog.example.com/python-tutorial/part-3"
series = await discover_series_intelligent(start_url)

print(f"Discovered {len(series)} series articles:")
for i, article in enumerate(series, 1):
    print(f"{i}. {article['title']} - {article['url']}")

# Verify completeness
verification = verify_series_completeness(series)
if not verification['complete']:
    print("⚠️ Series may be incomplete:")
    for issue in verification['issues']:
        print(f"  - {issue}")
```

### Combined with Crawler

```python
async def crawl_series(start_url, output_dir):
    """Crawl entire series"""

    # 1. Discover series
    print("🔍 Discovering series articles...")
    series = await discover_series_intelligent(start_url)

    # 2. Confirm with user
    print(f"\nDiscovered {len(series)} articles:")
    for i, article in enumerate(series, 1):
        print(f"  {i}. {article['title']}")

    # 3. Verify completeness
    verification = verify_series_completeness(series)
    if not verification['complete']:
        print("\n⚠️ Notes:")
        for issue in verification['issues']:
            print(f"  - {issue}")

    # 4. Start scraping after user confirms
    # ...
```

---

## FAQ

### Q: How to handle TOC requiring login?

Login in browser first, maintain session then run discovery algorithm.

### Q: Too many discovered links?

Raise score threshold (e.g., from 50 to 70), or limit links added per page.

### Q: URL has no numbers, how to recognize series?

Rely mainly on title similarity and DOM position (prev/next links).

### Q: Series has paid articles in middle?

Will be marked as "access failed", continue scraping accessible articles, report missing at end.
