# Components Digest

## Cross References
- `[technique:shadow-as-border]` **Shadow-as-border**: Claude, Vercel, Linear all use `0px 0px 0px 1px` ring shadows instead of CSS borders
- `[shape:pill-button]` **Pill buttons (9999px/999px/500px)**: Spotify, Uber, Supabase, Linear, Framer, Nothing use full-pill CTAs
- `[radius:8px-card]` **8px standard card radius**: Vercel, Cursor, Uber, Supabase, Spotify share 8px as workhorse card radius
- `[technique:multi-layer-shadow]` **Multi-layer shadow stacks**: Vercel, Stripe, Notion, Airbnb, Raycast layer 3-5 shadow values per element
- `[technique:frosted-glass]` **Frosted glass buttons**: Framer and Raycast use `rgba(255,255,255,0.1)` translucent buttons on dark
- `[palette:warm-near-black]` **Warm near-black text (not #000)**: Claude (#141413), Cursor (#26251e), Airbnb (#222222), Notion (rgba(0,0,0,0.95)), Superhuman (#292827), Stripe (#061b31)
- `[approach:mono-uppercase-label]` **Monospace uppercase labels**: Supabase (Source Code Pro), Nothing (Space Mono), Linear (Berkeley Mono), Framer (Azeret Mono) all use uppercase mono for technical markers

---

## Claude
> Warm, editorial components with ring shadows and terracotta accent on parchment
### Button
- Radius: 8px (standard), 12px (primary)
- Padding: 0px 12px 0px 8px (asymmetric) or 8px 16px
- Variants: Warm Sand (#e8e6dc), White Surface, Dark Charcoal (#30302e), Brand Terracotta (#c96442), Dark Primary
- Shadow: ring-based `0px 0px 0px 1px` warm gray halos
### Card
- Radius: 8px (standard), 16px (featured), 32px (hero)
- Border: `1px solid #f0eee6` (light), `1px solid #30302e` (dark)
- Shadow: whisper `rgba(0,0,0,0.05) 0px 4px 24px`
### Input
- Radius: 12px
- Border: warm standard borders
- Focus: ring with Focus Blue (#3898ec) -- the only cool color
### Other Notable
- Model Comparison Cards (Opus/Sonnet/Haiku grid)
- Organic hand-drawn illustrations in terracotta, black, muted green
- Dark/Light section alternation for chapter-like page rhythm
*Source*: awesome-design-md | 2026-04-06

---

## Vercel
> Achromatic precision with shadow-as-border technique and Geist typography
### Button
- Radius: 6px (standard), 9999px (pill badges), 64-100px (nav pills)
- Padding: 0px 6px (minimal) to 8px 16px (primary dark)
- Variants: Primary White (shadow-bordered), Primary Dark (#171717), Pill Badge (#ebf5ff), Large Pill Nav
- Shadow: `rgb(235,235,235) 0px 0px 0px 1px` ring-border
### Card
- Radius: 8px (standard), 12px (featured/image)
- Border: via shadow `rgba(0,0,0,0.08) 0px 0px 0px 1px` -- never CSS border
- Shadow stack: ring + `0px 2px 2px` + `0px 8px 8px -8px` + inner `#fafafa` ring
### Input
- Border: via shadow technique, not traditional border
- Focus: `2px solid hsla(212, 100%, 48%, 1)` outline
### Other Notable
- Workflow Pipeline (Develop Blue / Preview Pink / Ship Red)
- Trust Bar / Logo Grid in grayscale
- Metric Cards with 48px Geist weight 600
*Source*: awesome-design-md | 2026-04-06

---

## Stripe
> Premium fintech with blue-tinted shadows, conservative radius, and weight-300 headlines
### Button
- Radius: 4px (all variants)
- Padding: 8px 16px
- Variants: Primary Purple (#533afd), Ghost/Outlined (1px solid #b9b9f9), Transparent Info, Neutral Ghost
- Hover: #4434d4 on primary
### Card
- Radius: 4px (tight), 5px (standard), 6px (comfortable), 8px (featured)
- Border: `1px solid #e5edf5`
- Shadow: blue-tinted `rgba(50,50,93,0.25) 0px 30px 45px -30px, rgba(0,0,0,0.1) 0px 18px 36px -18px`
### Input
- Radius: 4px
- Border: `1px solid #e5edf5`
- Focus: `1px solid #533afd` purple ring
### Other Notable
- Success Badge (green tinted, 4px radius, 10px text)
- Dashed Borders in purple (#362baa) for drop zones
- Dark brand sections (#1c1e54) for immersive breaks
*Source*: awesome-design-md | 2026-04-06

---

## Linear
> Dark-mode-native with translucent surfaces, indigo accent, and luminance-stepped depth
### Button
- Radius: 6px (standard), 2px (toolbar), 9999px (pill), 50% (icon)
- Variants: Ghost (`rgba(255,255,255,0.02)`), Subtle (0.04), Primary Brand (#5e6ad2), Icon Circle, Pill, Small Toolbar
- Border: `1px solid rgba(255,255,255,0.08)` or `rgb(36,40,44)`
### Card
- Radius: 8px (standard), 12px (featured), 22px (large panels)
- Background: `rgba(255,255,255,0.02)` to `0.05` -- always translucent, never solid
- Border: `1px solid rgba(255,255,255,0.08)`
### Input
- Background: `rgba(255,255,255,0.02)`
- Border: `1px solid rgba(255,255,255,0.08)`
- Radius: 6px
- Focus: multi-layer shadow stack
### Other Notable
- Command palette trigger (Cmd+K)
- Success Pill (#10b981, 50% circular, 10px weight 510)
- Neutral Pill (9999px with dark border)
*Source*: awesome-design-md | 2026-04-06

---

## Notion
> Warm, whisper-bordered components on white with blue CTA and editorial illustrations
### Button
- Radius: 4px (standard), 9999px (pill badges)
- Padding: 8px 16px
- Variants: Primary Blue (#0075de), Secondary (rgba(0,0,0,0.05)), Ghost/Link, Pill Badge (#f2f9ff)
- Active: scale(0.9) transform
### Card
- Radius: 12px (standard), 16px (featured/hero)
- Border: `1px solid rgba(0,0,0,0.1)` -- whisper weight
- Shadow: 4-layer stack, max opacity 0.04
### Input
- Radius: 4px
- Border: `1px solid #dddddd`
- Focus: blue outline ring
- Placeholder: warm gray #a39e98
### Other Notable
- Feature Cards with large illustrative headers
- Trust Bar with company logos in brand colors
- Metric Cards (40px+ weight 700)
*Source*: awesome-design-md | 2026-04-06

---

## Figma
> Black-and-white interface chrome with pill geometry and vibrant product gradients
### Button
- Radius: 50px (pill), 50% (circle for icon buttons)
- Padding: 8px 18px 10px (asymmetric vertical)
- Variants: Black Solid, White Pill, Glass Dark (rgba(0,0,0,0.08)), Glass Light (rgba(255,255,255,0.16))
- Focus: dashed 2px outline (echoes editor selection handles)
### Card
- Radius: 6px (small), 8px (standard)
- Border: none or minimal
- Shadow: subtle to medium
### Input
- Not prominently featured on marketing site
### Other Notable
- Product Tab Bar (pill-shaped, 50px radius)
- Hero Gradient Section (multi-color: green, yellow, purple, pink)
- Dashed Focus Indicators connecting website UI to product UI
*Source*: awesome-design-md | 2026-04-06

---

## Airbnb
> Photography-forward with warm pill navigation, three-layer shadows, and generous rounding
### Button
- Radius: 8px (primary dark), 50% (circular nav controls)
- Padding: 0px 24px (primary), 14px 16px (chips)
- Variants: Primary Dark (#222222), Circular Nav (#f2f2f2), Chip/Filter
- Focus: `0 0 0 2px` ring + scale(0.92)
### Card
- Radius: 14px (badges), 20px (standard cards), 32px (large)
- Shadow: three-layer `rgba(0,0,0,0.02) 0px 0px 0px 1px, rgba(0,0,0,0.04) 0px 2px 6px, rgba(0,0,0,0.1) 0px 4px 8px`
- Listing cards: full-width photography on top
### Input
- Search bar: pill-like rounding
- Focus: primary-error background tint + ring
### Other Notable
- Category Pill Bar (horizontal scrolling filters)
- Heart/Wishlist icon overlay on images
- Image carousel with dot indicators
*Source*: awesome-design-md | 2026-04-06

---

## Spotify
> Dark immersive pill-and-circle geometry with uppercase button labels and heavy shadows
### Button
- Radius: 9999px (pill), 500px (large pill), 50% (circular play)
- Padding: 8px 16px (dark pill), 0px 43px (large), 12px (circular)
- Variants: Dark Pill (#1f1f1f), Light Pill (#eeeeee), Outlined Pill (1px solid #7c7c7c), Circular Play
- Labels: uppercase + letter-spacing 1.4px-2px
### Card
- Radius: 6px-8px
- Background: #181818 or #1f1f1f
- No visible borders on most cards
- Shadow: `rgba(0,0,0,0.3) 0px 8px 8px` on elevated
### Input
- Radius: 500px (pill)
- Background: #1f1f1f
- Border: inset `rgb(124,124,124) 0px 0px 0px 1px inset`
### Other Notable
- Sidebar navigation with active/inactive weight toggle (700/400)
- Full-width now-playing bar
- Album art as primary color source
*Source*: awesome-design-md | 2026-04-06

---

## Cursor
> Warm craft with gothic/serif/mono trio, oklab borders, and cream surfaces
### Button
- Radius: 8px (primary), full pill 9999px (secondary/tags)
- Padding: 10px 12px 10px 14px (primary), 3px 8px (pill)
- Variants: Primary Warm Surface (#ebeae5), Secondary Pill (#e6e5e0), Tertiary Pill (#e1e0db), Ghost, Light Surface
- Hover: text shifts to warm crimson #cf2d56
### Card
- Radius: 4px (compact), 8px (standard), 10px (featured)
- Border: `1px solid oklab(0.263/0.1)` -- perceptually uniform warm brown
- Shadow: `rgba(0,0,0,0.14) 0px 28px 70px` + `rgba(0,0,0,0.1) 0px 14px 32px` for elevated
### Input
- Border: `1px solid oklab(0.263/0.1)`
- Focus: border to oklab(0.263/0.2) or accent orange
### Other Notable
- AI Timeline (thinking peach / grep sage / read blue / edit lavender)
- Code Editor Previews with warm cream border frame
- Three-font system: CursorGothic, jjannon serif, berkeleyMono
*Source*: awesome-design-md | 2026-04-06

---

## Supabase
> Dark-mode developer aesthetic with emerald green identity, borderless depth, and pill CTAs
### Button
- Radius: 9999px (primary pill), 6px (ghost/secondary)
- Padding: 8px 32px (pill), 8px (ghost)
- Variants: Primary Pill Dark (#0f0f0f, white border), Secondary Pill (dark border), Ghost (transparent, 6px)
- Border: `1px solid #fafafa` (primary) or `1px solid #2e2e2e` (secondary)
### Card
- Radius: 8px-16px
- Background: #171717 or slightly lighter
- Border: `1px solid #2e2e2e` or `#363636`
- No visible shadows -- borders define edges
### Input
- Not prominently featured
### Other Notable
- Pill Tab indicators (9999px)
- Green accent borders `rgba(62,207,142,0.3)` as brand highlight
- Technical labels: Source Code Pro uppercase, 1.2px letter-spacing
*Source*: awesome-design-md | 2026-04-06

---

## Raycast
> macOS-native dark UI with multi-layer inset shadows, keyboard key caps, and red punctuation
### Button
- Radius: 86px (pill primary), 6px (secondary rectangular)
- Variants: Primary Pill (transparent, inset shadow), Secondary (6px, subtle border), Ghost (86px, gray text), CTA Download (semi-transparent white, dark text)
- Shadow: multi-layer inset `rgba(255,255,255,0.1) 0px 1px 0px 0px inset` + `rgba(255,255,255,0.25) 0px 0px 0px 1px`
- Hover: opacity transition to 0.6 (not color change)
### Card
- Radius: 12px-16px (standard), 20px (hero)
- Background: #101111
- Border: `1px solid rgba(255,255,255,0.06)`
- Shadow: double-ring `rgb(27,28,30) 0px 0px 0px 1px` outer + `rgb(7,8,10) 0px 0px 0px 1px inset`
### Input
- Radius: 8px
- Background: #07080a
- Border: `1px solid rgba(255,255,255,0.08)`
- Focus: blue glow ring `hsla(202,100%,67%,0.15)`
### Other Notable
- Keyboard Shortcut Keys with gradient caps and 5-layer physical shadow
- Warm glow aura `rgba(215,201,175,0.05)` behind featured elements
- Diagonal stripe hero pattern in Raycast Red
*Source*: awesome-design-md | 2026-04-06

---

## Nothing
> Industrial monochrome with dot-matrix motif, flat surfaces, zero shadows
### Button
- Radius: 999px (pill primary/secondary/destructive), 0 (ghost)
- Padding: 12px 24px, min height 44px
- Variants: Primary (white bg, black text), Secondary (transparent, border-visible), Ghost (no border), Destructive (accent red border)
- Text: Space Mono, 13px, ALL CAPS, 0.06em spacing
### Card
- Radius: 12-16px (cards), 8px (compact), 4px (technical)
- Background: --surface (#111111) or --surface-raised (#1A1A1A)
- Border: `1px solid --border` (#222222), no shadows ever
### Input
- Style: underline preferred (`1px solid --border-visible` bottom) or full border 8px radius
- Focus: border brightens to --text-primary
- Label: Space Mono, ALL CAPS, --text-secondary
### Other Notable
- Segmented Progress Bars (discrete blocks, no radius, 2px gaps)
- Dot-matrix backgrounds via radial-gradient
- Bracket navigation `[ HOME ] GALLERY INFO`
- Toggle/Switch with inverted thumb
*Source*: awesome-design-md | 2026-04-06

---

## Uber
> Stark black-and-white with pill-shaped everything, billboard typography, and whisper shadows
### Button
- Radius: 999px (all buttons -- non-negotiable)
- Padding: 10px 12px (primary), 14px 16px (chips)
- Variants: Primary Black (#000000), Secondary White, Chip/Filter (#efefef), Floating Action (white + shadow)
- Active: inset shadow `rgba(0,0,0,0.08)` on chips
- Focus: `rgb(255,255,255) 0px 0px 0px 2px inset`
### Card
- Radius: 8px (standard), 12px (featured)
- Shadow: `rgba(0,0,0,0.12) 0px 4px 16px` -- featherweight lift
- Border: none by default, defined by shadow
### Input
- Radius: 8px
- Border: `1px solid #000000` -- the only place visible borders appear
### Other Notable
- Category Pill Navigation (horizontal pills for Ride/Drive/Business/Uber Eats)
- Hero with Dual Action (text + map/illustration split)
- Warm human illustrations contrasting monochrome interface
*Source*: awesome-design-md | 2026-04-06

---

## Superhuman
> Luxury minimalism with purple hero gradient, warm cream buttons, and two-radius system
### Button
- Radius: 8px (all buttons -- only radius used)
- Variants: Warm Cream Primary (#e9e5dd), Dark Primary (#292827), Ghost/Text Link, Hero CTA (cream on purple)
- Hover: subtle opacity or brightness shift
### Card
- Radius: 16px (all cards -- only radius used)
- Border: `1px solid #dcd7d3` (Parchment Border)
- Shadow: minimal, depth via borders and color contrast
### Input
- Minimal form presence; dark-bordered with warm tones
- Focus: border emphasis increase
### Other Notable
- Only two border-radius values in entire system: 8px and 16px
- Deep purple hero gradient (#1b1938) as singular dramatic gesture
- Product screenshots as primary visual content
- Lavender Glow (#cbb7fb) as sole accent color
*Source*: awesome-design-md | 2026-04-06

---

## Framer
> Cinematic void-black with extreme GT Walsheim compression, blue glow rings, and frosted glass
### Button
- Radius: 40px (frosted pill), 100px (solid white pill)
- Variants: Frosted Pill (rgba(255,255,255,0.1), black text), Solid White Pill, Ghost (text only)
- Animation: scale-based matrix transforms, opacity transitions
### Card
- Radius: 10px-15px
- Background: black or near-black (#090909)
- Border: blue ring shadow `rgba(0,153,255,0.15) 0px 0px 0px 1px`
- Shadow: white top highlight `rgba(255,255,255,0.1) 0px 0.5px` + deep ambient `rgba(0,0,0,0.25) 0px 10px 30px`
### Input
- Dark background, subtle border
- Focus: Framer Blue (#0099ff) ring border
### Other Notable
- Product screenshots as hero art (tool IS the marketing)
- Blue glow auras behind interactive areas
- Dark floating nav bar with frosted glass effect
*Source*: awesome-design-md | 2026-04-06
