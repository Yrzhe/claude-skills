# Scraper — Design System Extractor

## Task

Given a website URL, extract design system information using all available tools.

## Input

- `url`: Target website URL
- `slug`: Website identifier (lowercase, hyphenated)
- `tool_capability`: Available tool list (detected by main workflow before this phase)

## Extraction Steps

### Step 1: Page Screenshots

**Use browser tools (by priority)**:

#### Browser Use Cloud
```
1. mcp__browser-use__run_session -> create session
2. Navigate to URL
3. Wait for page load complete
4. Screenshot desktop (1440x900 viewport)
5. Screenshot mobile (390x844 viewport)
6. Navigate to /about, /pricing, /product subpages, screenshot each
7. If page has dark mode toggle -> switch and screenshot
```

#### Playwright MCP
```
1. mcp__playwright__browser_navigate -> URL
2. mcp__playwright__browser_resize -> 1440, 900
3. mcp__playwright__browser_take_screenshot -> homepage.png
4. mcp__playwright__browser_resize -> 390, 844
5. mcp__playwright__browser_take_screenshot -> homepage-mobile.png
6. mcp__playwright__browser_navigate -> subpages
7. Repeat screenshots
```

#### Chrome Headless CLI (Fallback)
```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1440,900 \
  --screenshot="references/{slug}/screenshots/homepage.png" \
  "{url}"
```

### Step 2: CSS Variable Extraction

Execute via browser JS (`browser_evaluate` / `browser_run_code`):

```javascript
// Extract all CSS custom properties
(() => {
  const vars = {};
  for (const sheet of document.styleSheets) {
    try {
      for (const rule of sheet.cssRules) {
        if (rule.selectorText === ':root' || rule.selectorText === ':root, :host') {
          for (let i = 0; i < rule.style.length; i++) {
            const prop = rule.style[i];
            if (prop.startsWith('--')) {
              vars[prop] = rule.style.getPropertyValue(prop).trim();
            }
          }
        }
      }
    } catch(e) {}
  }
  // Also get from computedStyle
  const computed = getComputedStyle(document.documentElement);
  for (let i = 0; i < computed.length; i++) {
    const prop = computed[i];
    if (prop.startsWith('--') && !vars[prop]) {
      vars[prop] = computed.getPropertyValue(prop).trim();
    }
  }
  return JSON.stringify(vars, null, 2);
})()
```

### Step 3: Computed Style Extraction

```javascript
(() => {
  const targets = {
    'h1': 'h1',
    'h2': 'h2',
    'h3': 'h3',
    'h4': 'h4',
    'p': 'p',
    'a': 'a',
    'button': 'button',
    'input': 'input, [type="text"], [type="email"]',
    'nav': 'nav, [role="navigation"]',
    'card': '[class*="card"], [class*="Card"]',
    'hero': '[class*="hero"], [class*="Hero"]',
    'footer': 'footer',
    'code': 'code, pre',
    'badge': '[class*="badge"], [class*="Badge"], [class*="tag"], [class*="Tag"]'
  };
  
  const result = {};
  for (const [name, selector] of Object.entries(targets)) {
    const el = document.querySelector(selector);
    if (!el) continue;
    const s = getComputedStyle(el);
    result[name] = {
      fontFamily: s.fontFamily,
      fontSize: s.fontSize,
      fontWeight: s.fontWeight,
      lineHeight: s.lineHeight,
      letterSpacing: s.letterSpacing,
      color: s.color,
      backgroundColor: s.backgroundColor,
      padding: s.padding,
      margin: s.margin,
      borderRadius: s.borderRadius,
      border: s.border,
      boxShadow: s.boxShadow,
      transition: s.transition,
      opacity: s.opacity,
      textTransform: s.textTransform,
      textDecoration: s.textDecoration
    };
  }
  return JSON.stringify(result, null, 2);
})()
```

### Step 4: Font Extraction

```javascript
(() => {
  const fonts = [];
  for (const sheet of document.styleSheets) {
    try {
      for (const rule of sheet.cssRules) {
        if (rule instanceof CSSFontFaceRule) {
          fonts.push({
            family: rule.style.getPropertyValue('font-family').replace(/['"]/g, ''),
            src: rule.style.getPropertyValue('src').substring(0, 200),
            weight: rule.style.getPropertyValue('font-weight') || 'normal',
            style: rule.style.getPropertyValue('font-style') || 'normal',
            display: rule.style.getPropertyValue('font-display') || 'auto'
          });
        }
      }
    } catch(e) {}
  }
  
  // Also collect actually used font families
  const usedFonts = new Set();
  document.querySelectorAll('*').forEach(el => {
    const ff = getComputedStyle(el).fontFamily;
    if (ff) usedFonts.add(ff.split(',')[0].trim().replace(/['"]/g, ''));
  });
  
  return JSON.stringify({ declared: fonts, used: [...usedFonts] }, null, 2);
})()
```

### Step 5: Source CSS Analysis (Fallback / Supplementary)

If browser tools are unavailable, or as a supplement:

1. `WebFetch` to get HTML
2. Extract all `<link rel="stylesheet" href="...">` URLs from HTML
3. Extract all `<style>` tag contents
4. Extract `<meta name="theme-color">` value
5. `WebFetch` to fetch each CSS file
6. Regex extract:
   - CSS variables in `:root` blocks
   - `@font-face` declarations
   - `@media` breakpoints
   - `@keyframes` animations

### Step 6: Design System Documentation Probe

Some websites have public design system documentation. Prioritize scraping those:

```
Search these paths:
- /design-system
- /design
- /brand
- /styleguide
- /style-guide
- /tokens
Search these external links:
- design.{domain}
- {brand}.design
- github.com/{org}/*design*
- github.com/{org}/*tokens*
```

If found -> additionally scrape those pages.

## Output

All raw data is kept in memory (no persistence needed), passed to Analyzer.

Screenshots are saved to `references/{slug}/screenshots/`.

## Notes

- CAPTCHA/anti-bot encountered -> degrade strategy + inform user
- Login wall encountered -> only scrape public portion
- SPA pages -> wait for JS rendering complete before screenshotting
- Dark mode -> try `prefers-color-scheme: dark` media query or page toggle
