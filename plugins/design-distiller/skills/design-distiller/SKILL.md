---
name: design-distiller
description: "Scrape any website's design system into a structured Design MD + decomposed design tokens. Supports Browser Use Cloud, Playwright, Chrome headless, source code analysis. Maintains a Reference Pool of full Design MDs and a Digest Pool of cross-site design tokens for mix-and-match composition."
argument-hint: "[url]"
version: "1.1.0"
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, BrowserUse, Playwright
---

# Design Distiller

> Give any website URL, extract the complete design system into a Design MD + composable design tokens.

## Triggers

- `/design-distiller`
- "scrape this website's design" / "extract design system"
- "design scrape" / "make a Design MD"
- "analyze this site's design"

## Core Concepts

### Design MD
A pure Markdown design system document that AI agents can read directly to generate matching UI. Format follows [awesome-design-md](https://github.com/VoltAgent/awesome-design-md).

### Reference Pool
`references/{slug}/` — One folder per website, containing the full Design MD + screenshot assets. This is the raw material library.

### Digest Pool
`digests/` — Cross-site design tokens decomposed by dimension (typography, colors, spacing, components, etc.). Each entry is tagged with its source website. Used for mix-and-match composition when building new sites.

## Output Structure

```
design-distiller/
├── references/                # Reference Pool
│   └── {slug}/
│       ├── DESIGN.md          # Full Design MD (9 modules)
│       ├── meta.json          # Metadata
│       └── screenshots/       # Key page screenshots
│           ├── homepage.png
│           ├── homepage-mobile.png
│           └── components.png
└── digests/                   # Digest Pool
    ├── typography.md          # All font systems
    ├── colors.md              # All color systems
    ├── spacing.md             # All spacing systems
    ├── components.md          # All component patterns
    ├── depth.md               # All shadow & elevation systems
    ├── motion.md              # All motion specs
    ├── layouts.md             # All layout systems
    └── philosophy.md          # All design philosophies
```

### Pre-loaded References

The Reference Pool ships with **55 pre-loaded brands** imported from [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) and the nothing-design skill. These text-only imports differ from freshly scraped references:

- **No `screenshots/`** — visual data was not captured during batch import. Screenshots are generated only when running the full 4-phase pipeline on a new URL.
- **No `meta.json`** — metadata is generated only by the pipeline's Generate phase. Pre-loaded references have their metadata embedded in the Digest Pool cross-references instead.
- **Nothing uses an extended format** — `references/nothing/` contains multi-file documentation (DESIGN.md + tokens.md + components.md + platform-mapping.md) from a standalone design system skill. It does not follow the standard 9-module format because its craft rules and composition philosophy cannot be reduced to that template.

All other references follow the standard 9-module Design MD format.

---

## Workflow — 4 Phase Pipeline

### Phase 1: Scrape
-> `prompts/scraper.md`

**Goal**: Extract design information from the target website using all available tools.

#### Tool Priority

| Priority | Method | Use Case | Tool Pattern |
|----------|--------|----------|--------------|
| 1 | **Browser Use Cloud** | Full browsing + screenshots + DOM extraction | `browser-use_run_session`, `browser-use_get_session`, `browser-use_send_task` |
| 2 | **Playwright** | Screenshots + DOM extraction | `playwright_browser_navigate`, `playwright_browser_take_screenshot`, `playwright_browser_evaluate` |
| 3 | **Chrome Headless CLI** | Screenshots | Local Chrome command line via `Bash` |
| 4 | **WebFetch + Source Analysis** | HTML/CSS source code | `webfetch`, `websearch_web_search_exa` |

**Capability Detection**: Before starting a scrape, check which browser tools are available in the current environment. Try the highest-priority tool first; if unavailable or erroring, fall back to the next tier. Do not assume any specific tool is present.

#### Extraction Checklist

For each website, collect:

**A. Visual Screenshots** (via browser tools)
- [ ] Homepage full-page screenshot (desktop 1440px + mobile 390px)
- [ ] Dark/light mode toggle (if available)
- [ ] 2-3 key subpages (about, product, pricing)
- [ ] Interactive states (button hover, input focus)

**B. CSS Source Extraction** (via browser JS execution or source analysis)
- [ ] CSS custom properties (`--*` variables)
- [ ] `@font-face` declarations
- [ ] Computed styles for key selectors (h1-h6, body, button, input, card)
- [ ] Media query breakpoints
- [ ] Animation/transition definitions

**C. Asset Files**
- [ ] External CSS file URL list
- [ ] Font file URLs
- [ ] Design token files (e.g., `design-tokens.json`, `theme.ts`)

**D. Page Structure**
- [ ] DOM hierarchy (main landmark elements)
- [ ] Component pattern identification (nav, card, list, form, etc.)

#### Browser JS Extraction Scripts

Execute via browser tools to extract design data:

```javascript
// 1. Extract all CSS custom properties
(() => {
  const styles = getComputedStyle(document.documentElement);
  const vars = {};
  for (const sheet of document.styleSheets) {
    try {
      for (const rule of sheet.cssRules) {
        if (rule.style) {
          for (let i = 0; i < rule.style.length; i++) {
            const prop = rule.style[i];
            if (prop.startsWith('--')) {
              vars[prop] = rule.style.getPropertyValue(prop).trim();
            }
          }
        }
      }
    } catch(e) {} // cross-origin sheets
  }
  return JSON.stringify(vars, null, 2);
})()

// 2. Extract computed styles for key elements
(() => {
  const selectors = ['h1','h2','h3','h4','h5','h6','p','a','button',
    'input','nav','footer','[class*=card]','[class*=hero]'];
  const result = {};
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const s = getComputedStyle(el);
    result[sel] = {
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
      boxShadow: s.boxShadow,
      transition: s.transition
    };
  }
  return JSON.stringify(result, null, 2);
})()

// 3. Extract fonts
(() => {
  const fonts = new Set();
  for (const sheet of document.styleSheets) {
    try {
      for (const rule of sheet.cssRules) {
        if (rule instanceof CSSFontFaceRule) {
          fonts.add({
            family: rule.style.getPropertyValue('font-family'),
            src: rule.style.getPropertyValue('src'),
            weight: rule.style.getPropertyValue('font-weight'),
            style: rule.style.getPropertyValue('font-style')
          });
        }
      }
    } catch(e) {}
  }
  return JSON.stringify([...fonts], null, 2);
})()
```

### Phase 2: Analyze
-> `prompts/analyzer.md`

**Goal**: Structure the raw scraped data into the 9 Design MD modules.

#### Design MD — 9 Modules

| # | Module | Content | Key Output |
|---|--------|---------|------------|
| 1 | **Visual Theme & Atmosphere** | Design philosophy, mood, visual personality | 3-5 sentence qualitative description |
| 2 | **Color Palette & Roles** | Semantic color names + hex values + usage | Color palette table |
| 3 | **Typography Rules** | Font families, weight hierarchy, line-height, letter-spacing | Type scale table |
| 4 | **Component Stylings** | Buttons, cards, inputs, nav — all interactive states | Component specs |
| 5 | **Layout Principles** | Spacing system, grid, container widths, whitespace philosophy | Spacing token table |
| 6 | **Depth & Elevation** | Shadow system, surface hierarchy | Shadow level table |
| 7 | **Do's and Don'ts** | Design guardrails, anti-patterns | Rules list |
| 8 | **Responsive Behavior** | Breakpoints, touch targets, collapsing strategies | Breakpoint table |
| 9 | **Agent Prompt Guide** | Quick AI reference, color/font lookup tables | Cheat sheet |

#### Analysis Principles

1. **Observation over guessing** — Only document what screenshots and code show. Never fabricate.
2. **Precise values** — Colors must be hex, font sizes must be px, spacing must be concrete numbers.
3. **Semantic naming** — Don't write `#171717`, write `Near Black (#171717) — primary text color`.
4. **Source attribution** — Tag each value as extracted from CSS variables vs. visually estimated.
5. **Uncertainty marking** — If visually estimated from screenshots, mark as `(visual estimate)`.

### Phase 3: Generate
-> `prompts/generator.md`

**Goal**: Generate the final Design MD file + meta.json.

#### meta.json Schema

```json
{
  "name": "Site Name",
  "slug": "site-name",
  "url": "https://example.com",
  "scraped_at": "YYYY-MM-DD",
  "version": "v1",
  "theme_modes": ["light", "dark"],
  "primary_font": "Font Name",
  "primary_color": "#hexval",
  "style_keywords": ["minimalist", "warm", "industrial"],
  "confidence": {
    "colors": "high",
    "typography": "high",
    "spacing": "medium",
    "components": "medium",
    "motion": "low"
  },
  "pages_analyzed": [
    "https://example.com/",
    "https://example.com/about"
  ]
}
```

#### Design MD Template

See the 9-module template in `prompts/generator.md`. Each module follows the structure:
- Section heading with number
- Key data in Markdown tables
- Contextual notes and usage guidelines

### Phase 4: Digest
-> `prompts/digester.md`

**Goal**: Decompose the newly generated Design MD and merge into the Digest Pool.

#### Digest File Format

Each digest file is organized by source website for easy mix-and-match:

```markdown
# Typography Digest

## Cross References
- Vercel and Linear both use Geist Sans
- Claude and Notion both use warm-toned backgrounds

## Vercel
- **Display Font**: Geist Sans, -2.4px letter-spacing
- **Body Font**: Geist Sans, 400 weight, 16px/1.6
- **Mono**: Geist Mono
- **Style**: Extreme compression, modern geometric

## Stripe
- **Display Font**: sohne-var, variable weight
- **Body Font**: sohne-var, 16px/1.5
- **Style**: Sophisticated, OpenType features
```

#### Digest Rules

1. **Auto-update after each new reference** — No manual trigger needed.
2. **Tag confidence** — `(CSS var)` vs `(visual estimate)`.
3. **Tag uniqueness** — Mark distinctive choices with `[unique]`.
4. **Cross-reference** — If two sites share the same font/color, note the connection.

---

## Command Interface

### Basic Usage

```
/design-distiller https://vercel.com
```
-> Full pipeline: Scrape -> Analyze -> Generate -> Digest

### Extended Commands

| Command | Description |
|---------|-------------|
| `/design-distiller [url]` | Full distillation |
| `/design-distiller digest` | Run digest only (when references exist) |
| `/design-distiller compare [slug1] [slug2]` | Compare two design systems |
| `/design-distiller compose [description]` | Mix-and-match from Digest Pool to generate a new Design MD |
| `/design-distiller list` | List all references |
| `/design-distiller update [slug]` | Re-scrape and update an existing reference |

### Compose Example

```
/design-distiller compose "Developer tool landing page with Vercel typography + Stripe colors + Linear component style"
```

-> Extracts matching dimensions from Digest Pool, composes a new Design MD.

---

## Scraping Strategies

### Browser Use Cloud (Priority)

```
1. Create session -> mcp__browser-use__run_session
2. Navigate to target URL
3. Screenshot homepage (desktop + mobile)
4. Execute JS to extract CSS variables and computed styles
5. Navigate to 2-3 subpages for screenshots
6. Try toggling dark mode for screenshots
7. Close session
```

### Playwright MCP (Fallback)

```
1. browser_navigate -> target URL
2. browser_take_screenshot -> homepage screenshot
3. browser_evaluate -> execute JS extraction scripts
4. browser_resize -> mobile viewport, screenshot again
5. browser_navigate -> subpages
```

### Source Code Analysis (Last Resort)

```
1. WebFetch -> get HTML
2. Extract <link rel="stylesheet"> URLs from HTML
3. WebFetch -> fetch each CSS file
4. Regex extract CSS variables, @font-face, key selectors
5. Analyze <meta> tags for theme colors
```

---

## Parallel Scraping Strategy

When multiple scraping tools are available, launch parallel Agent tasks:

| Agent | Task | Output |
|-------|------|--------|
| **visual** | Browser screenshots + interaction state recording | `screenshots/` |
| **tokens** | JS extract CSS variables + computed styles | `raw/tokens.json` |
| **source** | Source CSS file download + parsing | `raw/stylesheets/` |
| **fonts** | Font file identification + Google Fonts matching | `raw/fonts.json` |

---

## Quality Standards

### Design MD Completeness Check

| Dimension | Minimum Requirement |
|-----------|-------------------|
| Color | At least 6 semantic colors (bg, text, accent, border, success, error) |
| Typography | At least heading + body font families, 5-level type scale |
| Spacing | At least 4 spacing tokens |
| Components | At least button + card + input |
| Layout | At least container width + basic breakpoints |
| Depth | At least 2 shadow levels |

### Confidence Levels

| Level | Description | Tag |
|-------|-------------|-----|
| High | Directly extracted from CSS variables/source | `(CSS)` |
| Medium | Extracted from computed styles | `(computed)` |
| Low | Visually estimated from screenshots | `(visual estimate)` |

---

## Agent Behavior Rules

### Before Starting

1. **Capability detection** — `ToolSearch` to check browser-use / playwright / chrome availability
2. **Check Reference Pool** — Whether the target site already has a reference
3. **Inform user** — Which scraping strategy will be used

### During Scraping

- Save screenshots to `references/{slug}/screenshots/`
- Raw extraction data does not need persistence (use and discard)
- If anti-bot/CAPTCHA encountered -> inform user, degrade to source analysis
- If the site has public design system docs -> prioritize scraping those

### After Generation

- **User must review** Design MD before it's committed to the pool
- Digest Pool updates should show diff to user
- meta.json confidence field must be honestly tagged

### Prohibited Actions

- Never fabricate design values that cannot be observed
- Never screenshot login-gated or paid content
- Never store authentication credentials
- Never overwrite existing references without versioning (see Version Management below)

### Version Management

When re-scraping an existing reference:

1. **Check existing version** — Read `meta.json` `version` field (e.g., `"v1"`)
2. **Increment** — Bump to next version (`"v2"`, `"v3"`, etc.)
3. **Archive previous** — Rename existing folder to `{slug}-v{N}` before writing new version
4. **Update Digest Pool** — Replace the slug's entries in all digest files with the new data
5. **Log in meta.json** — Record `"previous_version": "v1"` and `"updated_at": "YYYY-MM-DD"`

For pre-loaded references (no meta.json), the first re-scrape creates `"version": "v2"` with `"previous_version": "imported"`.
