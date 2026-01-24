# Self-Learning Experience System

This directory contains the accumulated knowledge and patterns learned from web scraping tasks.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXPERIENCE SYSTEM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────┐         ┌──────────────────┐             │
│   │ site_patterns.json│◄───────│  Successful      │             │
│   │                  │         │  Scraping        │             │
│   │ - Domain patterns│         │  Sessions        │             │
│   │ - Selectors      │         └──────────────────┘             │
│   │ - Pagination     │                                          │
│   │ - Rate limits    │         ┌──────────────────┐             │
│   │ - Success counts │         │  Failed          │             │
│   └──────────────────┘         │  Attempts        │             │
│                                └────────┬─────────┘             │
│   ┌──────────────────┐                  │                       │
│   │lessons_learned.md│◄─────────────────┘                       │
│   │                  │                                          │
│   │ - What went wrong│                                          │
│   │ - Root causes    │                                          │
│   │ - Solutions      │                                          │
│   └──────────────────┘                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Files

### `site_patterns.json`

Stores learned patterns for each domain/URL pattern combination.

**Structure**:
```json
{
  "domain.com": {
    "url_patterns": {
      "/path/pattern/*": {
        "selectors": { ... },
        "pagination": { ... },
        "anti_block": { ... },
        "success_count": 0,
        "last_success": null,
        "notes": ""
      }
    }
  }
}
```

**When to Update**:
- After every successful scraping task
- When discovering new patterns
- When refining existing selectors

### `lessons_learned.md`

Chronological log of failures and their solutions.

**When to Update**:
- After scraping fails
- When encountering new anti-bot measures
- When finding workarounds for blocked sites

## Usage Instructions

### Before Scraping (ALWAYS DO THIS)

```python
# 1. Load existing patterns
patterns = load_json("experiences/site_patterns.json")

# 2. Extract domain from target URL
domain = urlparse(target_url).netloc

# 3. Check for matching pattern
if domain in patterns:
    # Check for URL pattern match
    for pattern, config in patterns[domain]["url_patterns"].items():
        if url_matches_pattern(target_url, pattern):
            # USE THE LEARNED CONFIG
            print(f"Using learned pattern (success_count: {config['success_count']})")
            return config
```

### After Successful Scraping (ALWAYS DO THIS)

```python
# 1. Load current patterns
patterns = load_json("experiences/site_patterns.json")

# 2. Update or create pattern
if domain not in patterns:
    patterns[domain] = {"url_patterns": {}}

url_pattern = generalize_url(target_url)  # e.g., /movie/*/comments

patterns[domain]["url_patterns"][url_pattern] = {
    "selectors": discovered_selectors,
    "pagination": detected_pagination,
    "anti_block": {
        "min_delay": used_min_delay,
        "max_delay": used_max_delay,
        "blocked_at": request_count_when_blocked
    },
    "success_count": previous_count + 1,
    "last_success": datetime.now().isoformat(),
    "notes": observations
}

# 3. Save updated patterns
save_json("experiences/site_patterns.json", patterns)
```

### After Failed Scraping (ALWAYS DO THIS)

```markdown
# Append to lessons_learned.md:

## [YYYY-MM-DD] - domain.com - /url/pattern

**Issue**: [Description of what went wrong]

**Error Details**:
- Status Code: [if applicable]
- Error Message: [if applicable]
- At Request #: [if applicable]

**Root Cause**: [Analysis of why it happened]

**Solution**: [How to avoid or fix this in the future]

**Tags**: #rate-limit #captcha #selector-change #login-required
```

## Pattern Matching

URL patterns use wildcards for flexible matching:

| Pattern | Matches |
|---------|---------|
| `/movie/*/comments` | `/movie/123/comments`, `/movie/abc/comments` |
| `/page/*` | `/page/1`, `/page/2`, `/page/anything` |
| `/api/v*/users` | `/api/v1/users`, `/api/v2/users` |

## Best Practices

1. **Be Specific with Patterns**
   - Use the most specific pattern that still generalizes
   - `/movie/*/comments` is better than `/*`

2. **Update Success Counts**
   - Increment after each successful run
   - Helps identify reliable patterns

3. **Note Rate Limits**
   - Record the request count where blocking occurred
   - Helps calibrate delays for future runs

4. **Document Gotchas**
   - Use the `notes` field for special observations
   - "Requires login after 10 pages"
   - "Changes layout on mobile UA"

5. **Review Lessons Regularly**
   - Check `lessons_learned.md` before tackling new domains
   - Similar sites often have similar protections

## Maintenance

### Cleaning Old Patterns

Patterns with `last_success` older than 6 months may be stale:
```python
# Mark as potentially stale
if days_since_last_success > 180:
    pattern["status"] = "stale"
```

### Validating Patterns

Before using a learned pattern, optionally verify:
```python
# Quick check if selectors still work
test_result = await quick_validate(url, pattern["selectors"])
if not test_result.valid:
    pattern["status"] = "needs_update"
```
