# Generator — Design MD Generator

## Task

Generate the final Design MD file + meta.json from the Analyzer's structured analysis data.

## Input

- 9-module structured data from Analyzer output
- slug, url, screenshot paths

## Generation Rules

### 1. Language

- All content in English
- Technical values (hex colors, px sizes, etc.) in standard notation
- Proper nouns preserved as-is

### 2. Precision

| Data Type | Precision Requirement | Format |
|-----------|---------------------|--------|
| Colors | 6-digit hex | `#1A1A1A` |
| Font size | Integer px | `16px` |
| Spacing | Integer px | `24px` |
| Border radius | Integer px | `8px` |
| Font weight | Standard values | `400`, `500`, `600`, `700` |
| Line height | Decimal or ratio | `1.5` or `24px` |
| Letter spacing | Decimal | `-0.02em` or `-0.5px` |
| Shadows | Full value | `0 2px 8px rgba(0,0,0,0.08)` |
| Opacity | Percentage | `72%` |

### 3. Confidence Tagging

Optionally tag each value with its source:

- `(CSS var)` — Directly extracted from CSS custom properties
- `(computed)` — Extracted from computed styles
- `(visual estimate)` — Estimated from screenshot visual analysis
- `(docs)` — Extracted from the website's design system documentation

Only tag when the value is uncertain. High-confidence values need no tag.

### 4. Module Completeness

**Required modules** (mark `(insufficient data)` if missing):
1. Visual Theme & Atmosphere
2. Color Palette & Roles
3. Typography Rules
4. Component Stylings
5. Layout Principles

**Best-effort modules** (can be omitted if no data):
6. Depth & Elevation
7. Do's and Don'ts
8. Responsive Behavior
9. Agent Prompt Guide

### 5. Table Format

Use Markdown tables for systematic data (color palettes, type scales, spacing tokens, etc.). Keep columns aligned.

### 6. Code Examples

Key CSS values use inline code format: `value`

Compound styles use code blocks:
```css
.example {
  property: value;
}
```

## meta.json Generation Rules

```json
{
  "name": "Site display name",
  "slug": "url-slug",
  "url": "https://example.com",
  "scraped_at": "YYYY-MM-DD",
  "version": "v1",
  "theme_modes": ["light"] or ["light", "dark"],
  "primary_font": "Primary font name",
  "primary_color": "#hex-accent",
  "style_keywords": ["up to 5 style keywords"],
  "confidence": {
    "colors": "high/medium/low",
    "typography": "high/medium/low",
    "spacing": "high/medium/low",
    "components": "high/medium/low",
    "motion": "high/medium/low"
  },
  "pages_analyzed": [
    "List of actually analyzed page URLs"
  ]
}
```

### Confidence Criteria

| Level | Condition |
|-------|-----------|
| high | Directly extracted from CSS variables/design token files, 80%+ coverage |
| medium | Primarily from computed styles, 50%+ coverage |
| low | Mainly relying on screenshot visual analysis |

## Output

1. `references/{slug}/DESIGN.md` — Full Design MD
2. `references/{slug}/meta.json` — Metadata
3. Trigger Digester for decomposition
