# Lessons Learned

This document accumulates wisdom from web scraping experiences - both successes and failures.

> **IMPORTANT**: Add new entries at the TOP of each section so recent lessons are seen first.

---

## Table of Contents

- [General Best Practices](#general-best-practices)
- [Domain-Specific Lessons](#domain-specific-lessons)
- [Anti-Bot Patterns Encountered](#anti-bot-patterns-encountered)
- [Failure Log](#failure-log)

---

## General Best Practices

### Rate Limiting
- **Default safe delay**: 3-5 seconds between requests
- **Aggressive sites**: 5-10 seconds minimum
- **After any 429**: Double the delay immediately

### User-Agent Strategy
- Always use real browser User-Agents
- Rotate between Chrome, Firefox, Safari
- Mobile UAs sometimes bypass restrictions

### Session Management
- Keep cookies between requests on same domain
- Some sites track session duration - restart after 100 requests
- Clear cookies if getting soft blocks

### Pagination Gotchas
- Always check if "next page" link equals current page (infinite loop trap)
- Some sites hide pagination after page 50
- API pagination may have different limits than UI

---

## Domain-Specific Lessons

> Add domain-specific knowledge here as you learn it.

### Template Entry
```markdown
### domain.com
**Last Updated**: YYYY-MM-DD
**Difficulty**: Easy | Medium | Hard | Very Hard

**Key Learnings**:
- [Learning 1]
- [Learning 2]

**Recommended Settings**:
- Delay: X-Y seconds
- Needs Login: Yes/No
- Special Headers: [if any]

**Gotchas**:
- [Gotcha 1]
- [Gotcha 2]
```

---

## Anti-Bot Patterns Encountered

> Document anti-bot measures you've encountered and how to handle them.

### Cloudflare
- **Detection**: "Checking your browser" interstitial
- **Solution**: Use real browser (Playwright), wait for challenge completion
- **Notes**: May require JavaScript execution

### reCAPTCHA
- **Detection**: Google reCAPTCHA widget appears
- **Solution**: Cannot bypass automatically - pause and notify user
- **Notes**: Often triggered after N requests or suspicious patterns

### Rate Limiting (429)
- **Detection**: HTTP 429 status code
- **Solution**: Exponential backoff, start with 30s wait
- **Notes**: Some sites don't return 429, just empty content

### IP Blocking (403)
- **Detection**: HTTP 403 or "Access Denied" page
- **Solution**: Wait 15-30 minutes, or use different IP
- **Notes**: May be temporary or permanent

### Fingerprinting
- **Detection**: Blocked despite normal behavior
- **Solution**: Randomize viewport, timezone, WebGL
- **Notes**: Advanced sites check browser fingerprints

---

## Failure Log

> Record failures chronologically. Add new entries at the TOP.

### Template Entry
```markdown
## [YYYY-MM-DD] domain.com - /url/pattern

**Task**: What you were trying to do

**Error**:
- Type: [HTTP Error | Selector Not Found | Rate Limited | Captcha | Other]
- Details: [Specific error message or behavior]
- At Request #: [If applicable]

**Root Cause**: [Your analysis]

**Resolution**: [How you fixed it or worked around it]

**Prevention**: [How to avoid this in future]

**Tags**: #tag1 #tag2
```

---

<!-- New entries go below this line -->

