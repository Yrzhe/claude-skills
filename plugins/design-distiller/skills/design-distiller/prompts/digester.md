# Digester — Design Token Decomposer

## Task

Decompose a Design MD (`references/{slug}/DESIGN.md`) into independent design dimensions and merge into the Digest Pool (`digests/`).

## Input

- Newly generated `references/{slug}/DESIGN.md`
- Corresponding `meta.json`

## Digestion Flow

### Step 1: Read Existing Digest Files

Read all existing files in `digests/` to understand current entries.

### Step 2: Decompose Design MD by Dimension

Extract corresponding dimension info from the Design MD's 9 modules:

| Digest File | Extracted From |
|-------------|---------------|
| `typography.md` | Module 3: Typography Rules |
| `colors.md` | Module 2: Color Palette & Roles |
| `spacing.md` | Module 5: Layout Principles (spacing portion) |
| `components.md` | Module 4: Component Stylings |
| `depth.md` | Module 6: Depth & Elevation |
| `motion.md` | Module 4 transition values + other motion data |
| `layouts.md` | Module 5: Layout Principles (grid/container) + Module 8: Responsive |
| `philosophy.md` | Module 1: Visual Theme + Module 7: Do's and Don'ts |

### Step 3: Format New Entries

Entry format for each dimension:

```markdown
## {Site Name}

> {One-line style characterization}

- **{Property 1}**: {value} {(confidence tag)}
- **{Property 2}**: {value}
- ...
{If distinctive}: `[unique]` tag

*Source*: {url} | scraped {date}
```

### Step 4: Merge into Digest

For each digest file:

1. If slug already exists -> replace that section (update)
2. If slug doesn't exist -> append to end of file (new)
3. Maintain alphabetical order or chronological order

### Step 5: Cross References

Scan merged digests and tag interesting connections:

- **Same font**: "Vercel and Linear both use Geist Sans"
- **Similar colors**: "Stripe and Coinbase blues are close"
- **Similar patterns**: "Claude and Notion both use warm-toned backgrounds"

Maintain a `## Cross References` section at the top of each file.

## Digest File Entry Structures

### typography.md

```markdown
## {Site Name}

> {One-line font style summary}

- **Display**: {font-family}, {weight}, {size range}
- **Body**: {font-family}, {weight}, {size}, line-height {lh}
- **Mono**: {font-family}
- **Notable features**: {negative letter-spacing / large line-height / variable font / OpenType features / ...}
- **Type scale**: Display {n}px -> H1 {n}px -> Body {n}px -> Caption {n}px

*Source*: {url} | {date}
```

### colors.md

```markdown
## {Site Name}

> {One-line color style summary}

- **Background**: {name} `{hex}`
- **Text**: {name} `{hex}` / {name} `{hex}`
- **Accent**: {name} `{hex}`
- **Border**: `{hex}` / `{rgba}`
- **Status**: Success `{hex}` / Warning `{hex}` / Error `{hex}`
- **Dark mode**: {yes/no}, {inversion strategy summary}
- **Color strategy**: {monochrome / dual-tone / multicolor / gradient}

*Source*: {url} | {date}
```

### spacing.md

```markdown
## {Site Name}

> {One-line spacing style summary}

- **Base unit**: {n}px
- **Tokens**: {xs}px / {sm}px / {md}px / {lg}px / {xl}px
- **Section spacing**: {n}px
- **Component internal padding**: {n}px
- **Whitespace strategy**: {generous / moderate / compact}

*Source*: {url} | {date}
```

### components.md

```markdown
## {Site Name}

> {One-line component style summary}

### Button
- border-radius: {n}px
- padding: {v}px {h}px
- Variants: {primary/secondary/ghost/...}

### Card
- border-radius: {n}px
- shadow: {description}
- border: {description}

### Input
- border-radius: {n}px
- border: {description}
- Focus state: {description}

### Other Notable Components
- {description}

*Source*: {url} | {date}
```

### motion.md

```markdown
## {Site Name}

> {One-line motion style summary}

- **Duration**: micro {n}ms, transition {n}ms
- **Easing**: {cubic-bezier(...)} / {ease-out/...}
- **Style**: {restrained / fluid / bouncy / no animation}
- **Common effects**: {fade / slide / scale / ...}

*Source*: {url} | {date}
```

### depth.md

```markdown
## {Site Name}

> {One-line depth/elevation style summary}

- **Primary technique**: {shadow-as-border / multi-layer stack / luminance stepping / border-only / ...}
- **Card shadow**: {full shadow value or "none"}
- **Elevation levels**: {N} ({description of levels})
- **Border role**: {sole depth cue / coexists with shadows / replaced by shadows}
- **Direction**: {top-lit / diffuse / none}
- **Distinctive**: {what makes this depth system unique}

*Source*: {url} | {date}
```

### layouts.md

```markdown
## {Site Name}

> {One-line layout style summary}

- **Container**: max-width {n}px
- **Grid**: {CSS Grid / Flexbox}, {n} columns, gutter {n}px
- **Breakpoints**: Mobile <{n}px / Tablet {n}px / Desktop {n}px
- **Navigation**: {top-fixed / sidebar / bottom-tab}
- **Layout strategy**: {centered single-column / multi-column / masonry / ...}

*Source*: {url} | {date}
```

### philosophy.md

```markdown
## {Site Name}

> {One-line design philosophy}

- **Mood**: {description}
- **Keywords**: [{keyword1}, {keyword2}, ...]
- **Do**: {3-5 items}
- **Don't**: {3-5 items}
- **Design references**: {Swiss / Brutalist / Apple-like / ...}

*Source*: {url} | {date}
```

## Compose Feature

When user runs the `compose` command:

1. Read user's requirement description
2. Select matching entries from each digest file
3. Compose into a new Design MD at `references/composed-{name}/DESIGN.md`
4. Tag each module with its source website

Conflict resolution during composition:
- **User specification wins** — If the user named a specific source for a dimension ("Vercel typography"), use that source's values exactly
- **First-mentioned source wins** — For unspecified dimensions, use the first source mentioned in the user's description
- **Present conflicts, don't guess** — If two sources conflict on a critical value (e.g., 4px vs 8px base unit, serif vs sans-serif heading), present both options to the user with a brief rationale for each, and ask them to choose
- **Unspecified dimensions** — Select the source whose overall philosophy best matches the user's description. If still ambiguous, pick the source with higher confidence tags in the digest entry
- **Never average values** — Do not interpolate between sources (e.g., "6px" as middle ground between 4px and 8px). Design tokens must come from a single source per dimension
