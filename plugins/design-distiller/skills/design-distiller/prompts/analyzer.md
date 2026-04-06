# Analyzer — Design Data Analyzer

## Task

Structure the raw data from Scraper (CSS variables, computed styles, screenshots, source code) into the 9 Design MD modules.

## Input

- All raw data from the Scraper phase
- Screenshot file paths
- Target website URL and slug

## Analysis Flow

### Module 1: Visual Theme & Atmosphere

**Data source**: Screenshots + overall color scheme + font choices

Analysis dimensions:
1. **Mood** — Infer from color scheme and fonts: warm tones = warm, cool tones = cool, high contrast = bold, low contrast = soft
2. **Density** — Infer from spacing and content volume: generous whitespace = sparse, compact layout = dense
3. **Personality** — Composite judgment: serif = traditional/elegant, sans-serif = modern, mono = technical/geeky
4. **Visual References** — Analogize to known design styles (Swiss, Brutalist, Apple-like, etc.)

**Output format**:
```
mood: warm / cool / vibrant / restrained / playful / serious
density: sparse / moderate / dense
personality: professional / friendly / technical / artistic / corporate
visual_references: ["Swiss typography", "Apple minimalism", ...]
description: "3-5 sentence qualitative description"
```

### Module 2: Color Palette & Roles

**Data source**: CSS variables -> computed styles -> screenshot visual analysis

Analysis steps:
1. Find color-related variables in CSS (containing `color`, `bg`, `fill`, `stroke`, `border`)
2. Convert rgb/hsl to hex uniformly
3. Classify semantically:
   - **Background**: body/page background, surface/card background
   - **Text**: primary text, secondary text, muted text
   - **Accent**: brand/accent, CTA, link
   - **Border**: border, divider, separator
   - **Status**: success/green, warning/amber, error/red, info/blue
4. If dark mode variables exist -> record the mapping
5. Verify against screenshots: do actual visible colors match extracted values?

**Confidence rules**:
- CSS variable directly named (e.g., `--color-primary`) -> High
- Computed style extraction -> Medium
- Screenshot estimation -> Low

### Module 3: Typography Rules

**Data source**: @font-face + computed styles + CSS variables

Analysis steps:
1. Identify font families:
   - Display/Heading font (used by h1-h3)
   - Body font (used by p)
   - Mono font (used by code)
2. Build type scale table:
   - From h1 to caption, record fontSize, fontWeight, lineHeight, letterSpacing
3. Check special typographic features:
   - Negative letter-spacing -> tag as "compressed typography"
   - Large line-height (> 1.8) -> tag as "reading optimized"
   - Variable font -> record available axes
4. Check font loading strategy: font-display value

### Module 4: Component Stylings

**Data source**: Computed styles + screenshots

Analyze each component type:

| Component | Key Properties |
|-----------|---------------|
| Button | padding, border-radius, font-size, font-weight, background, color, hover state |
| Card | padding, border-radius, box-shadow, border, background |
| Input | padding, border-radius, border, focus state, placeholder color |
| Navigation | structure (horizontal/sidebar), active state, spacing |
| Badge/Tag | padding, border-radius, font-size, text-transform |
| Link | color, text-decoration, hover behavior |

**Interactive states**: If browser tools support hover, capture hover/focus/active states where possible.

### Module 5: Layout Principles

**Data source**: CSS variables (spacing tokens) + computed styles + media queries

Analysis dimensions:
1. **Spacing system** — Find the spacing base unit (4px? 8px? other?), list actual spacing values used
2. **Container width** — max-width values, fixed vs. percentage
3. **Grid system** — CSS Grid vs. Flexbox, column count, gutter
4. **Section spacing** — padding/margin between sections

### Module 6: Depth & Elevation

**Data source**: box-shadow values

1. Collect all box-shadow values
2. Grade by intensity (none -> subtle -> medium -> strong)
3. Analyze shadow direction and spread (top-lit vs. uniform diffusion)
4. Check whether borders are used instead of shadows (e.g., Vercel style)

### Module 7: Do's and Don'ts

**Infer from overall style**:
- Do: Observed design patterns ("use generous whitespace", "rounded buttons", "monochrome icons", etc.)
- Don't: Inverse inference (if overall restrained -> Don't "add gradients", "use emoji", etc.)

### Module 8: Responsive Behavior

**Data source**: Media query breakpoints + desktop/mobile screenshot comparison

1. Extract all `@media` breakpoint values
2. Compare desktop and mobile screenshots: nav changes, layout collapse, font size changes
3. Check touch target sizes (button/link min-height)

### Module 9: Agent Prompt Guide

**Composite generation**:
1. Color lookup table: scenario -> color value
2. Font lookup table: purpose -> font + weight
3. Key CSS variable list (if available)
4. A quick paragraph on "how to use this design system"

## Output

Structured 9-module analysis data, passed to Generator for final Design MD generation.
