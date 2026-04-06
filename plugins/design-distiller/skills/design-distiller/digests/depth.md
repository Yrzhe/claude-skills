# Depth & Elevation Digest

## Cross References

### Shared Techniques
- `[technique:shadow-as-border]` **Shadow-as-border (0px 0px 0px 1px)**: Claude, Vercel, Linear, Resend use zero-offset ring shadows instead of CSS borders — cleaner transitions, no box model implications
- `[technique:multi-layer-shadow]` **Multi-layer shadow stacks (3-5 values)**: Vercel, Stripe, Notion, Airbnb, Raycast layer multiple shadow declarations per element, each serving a distinct role (border + elevation + ambient)
- `[technique:border-only-depth]` **Border-only depth (no shadows)**: Nothing (zero shadows), Supabase (border-defined edges), Figma (minimal shadow) avoid traditional drop shadows entirely
- `[technique:luminance-stepping]` **Luminance stepping**: Linear, Spotify use background opacity increments (rgba white 0.02 → 0.04 → 0.05) instead of shadows to convey elevation on dark surfaces
- `[technique:blue-tinted-shadow]` **Blue-tinted shadows**: Stripe (`rgba(50,50,93,0.25)`) and Resend (`rgba(214,235,253,0.19)`) both carry brand-adjacent blue into their depth system
- `[technique:inset-shadow]` **Inset shadows for physicality**: Raycast and Spotify use inset shadows to create pressed/recessed physical button feel
- `[technique:frosted-glass]` **Frosted glass / translucent surfaces**: Framer and Raycast use `rgba(255,255,255,0.1)` translucent buttons and panels on dark backgrounds

### Depth Philosophy Spectrum
- **Zero depth**: Nothing — flat surfaces, border separation only, shadows explicitly banned
- **Whisper depth**: Notion — 4-layer stacks but max opacity 0.04 per layer; Claude — single `rgba(0,0,0,0.05)` whisper
- **Moderate depth**: Vercel — multi-layer stacks with signature inner `#fafafa` ring; Cursor — warm `rgba(0,0,0,0.14)` ambient
- **Deep depth**: Stripe — parallax blue-tinted stacks; Airbnb — three-layer with visible lift; Raycast — physical 5-layer keyboard key caps

---

## Claude
> Whisper-weight ring shadows on warm parchment — depth as subtle halo, not lift

- **Primary technique**: Shadow-as-border ring `0px 0px 0px 1px` warm gray halos
- **Card shadow**: `rgba(0,0,0,0.05) 0px 4px 24px` — single-layer whisper
- **Elevation levels**: 2 (flat surface + subtle lift)
- **Border role**: `1px solid #f0eee6` (light) / `1px solid #30302e` (dark) — borders coexist with ring shadows
- **Direction**: Diffuse (no directional bias)
- **Dark mode depth**: Same ring technique with warm dark borders
- **Distinctive**: Warm-toned ring shadows that feel like paper halos, not digital elevation

*Source*: awesome-design-md | 2026-04-06

---

## Vercel
> Multi-layer shadow stacks where each layer has a job — the shadow IS the border

- **Primary technique**: Shadow-as-border `rgba(0,0,0,0.08) 0px 0px 0px 1px` — replaces all CSS borders
- **Card shadow stack**: `rgba(0,0,0,0.08) 0px 0px 0px 1px` (border) + `rgba(0,0,0,0.04) 0px 2px 2px` (lift) + `rgba(0,0,0,0.04) 0px 8px 8px -8px` (ambient) + `#fafafa 0px 0px 0px 1px` (inner ring)
- **Elevation levels**: 3 (flat + subtle + elevated)
- **Border role**: None — ALL borders are shadows. No CSS `border` property used.
- **Direction**: Top-lit (2px and 8px offsets downward)
- **Ring border**: `rgb(235,235,235) 0px 0px 0px 1px` for tabs and images
- **Distinctive**: Inner `#fafafa` ring highlight creates micro-bevel effect `[unique]`

*Source*: awesome-design-md | 2026-04-06

---

## Stripe
> Blue-tinted parallax shadows — financial depth with chromatic temperature

- **Primary technique**: Multi-layer blue-tinted shadows
- **Card shadow**: `rgba(50,50,93,0.25) 0px 30px 45px -30px, rgba(0,0,0,0.1) 0px 18px 36px -18px`
- **Elevation levels**: 3+ (flat + subtle border + deep parallax)
- **Border role**: `1px solid #e5edf5` — traditional borders coexist with shadows
- **Direction**: Strongly top-lit with large offsets (30px, 18px) — creates parallax depth
- **Shadow tint**: Blue-gray (`rgba(50,50,93)`) — brand-adjacent, not neutral
- **Distinctive**: Shadows carry brand color temperature — depth feels on-brand, not generic `[unique]`

*Source*: awesome-design-md | 2026-04-06

---

## Linear
> Luminance stepping — elevation is brightness, not shadow

- **Primary technique**: Translucent white background stepping (rgba white 0.02 → 0.04 → 0.05)
- **Card surface**: `rgba(255,255,255,0.02)` to `0.05` — always translucent, never solid
- **Elevation levels**: 4+ (background luminance steps: 0.02, 0.04, 0.05, 0.08)
- **Border role**: `1px solid rgba(255,255,255,0.08)` or solid `#23252a` — semi-transparent white borders
- **Direction**: None — luminance is omnidirectional
- **Focus shadow**: Multi-layer shadow stack for input focus
- **Distinctive**: Zero drop shadows for surface elevation — brightness IS depth `[unique]`

*Source*: awesome-design-md | 2026-04-06

---

## Notion
> Whisper-weight 4-layer stacks where no single layer exceeds 0.04 opacity

- **Primary technique**: Multi-layer whisper shadows (4+ layers, all sub-0.05 opacity)
- **Card shadow**: 4-layer stack, max opacity 0.04 per layer
- **Elevation levels**: 2-3 (flat + whisper + hover-enhanced)
- **Border role**: `1px solid rgba(0,0,0,0.1)` — whisper-weight borders
- **Direction**: Subtle top-lit
- **Hover effect**: Shadow intensification on card hover
- **Distinctive**: The accumulated effect of many near-invisible layers creates analog paper feel

*Source*: awesome-design-md | 2026-04-06

---

## Figma
> Monochrome gallery chrome — minimal shadows, geometry defines depth

- **Primary technique**: Minimal shadows; depth through geometry (pill shapes, circles) and background contrast
- **Card shadow**: Subtle to medium
- **Elevation levels**: 2 (flat + subtle)
- **Border role**: Minimal — monochrome interface relies on shape contrast
- **Focus**: Dashed 2px outline (echoing editor selection handles) `[unique]`
- **Distinctive**: Depth comes from geometric contrast (round vs rectangular) more than shadow elevation

*Source*: awesome-design-md | 2026-04-06

---

## Airbnb
> Three-layer warm shadows with generous rounding and photography-forward cards

- **Primary technique**: Three-layer shadow stacks
- **Card shadow**: `rgba(0,0,0,0.02) 0px 0px 0px 1px, rgba(0,0,0,0.04) 0px 2px 6px, rgba(0,0,0,0.1) 0px 4px 8px`
- **Elevation levels**: 3 (ring + soft lift + visible elevation)
- **Border role**: Defined by shadow ring, not CSS border
- **Direction**: Top-lit (2px and 4px offsets)
- **Hover**: `rgba(0,0,0,0.08) 0px 4px 12px` shadow elevation on hover
- **Focus**: `0 0 0 2px` ring + `scale(0.92)` — shadow + scale combined

*Source*: awesome-design-md | 2026-04-06

---

## Spotify
> Dark immersive depth — surface lightening replaces shadow elevation

- **Primary technique**: Background color stepping on dark surfaces
- **Card shadow**: `rgba(0,0,0,0.3) 0px 8px 8px` on elevated elements
- **Elevation levels**: 2-3 (base dark + lighter surface + heavy shadow)
- **Border role**: Inset `rgb(124,124,124) 0px 0px 0px 1px inset` for inputs
- **Direction**: Top-lit where shadows are used
- **Distinctive**: Dark surfaces (#121212 → #181818 → #1f1f1f) create depth through lightening, not shadow

*Source*: awesome-design-md | 2026-04-06

---

## Cursor
> Warm perceptual-uniform borders with ambient shadow clouds

- **Primary technique**: `oklab()` perceptually uniform warm brown borders + ambient shadow clouds
- **Card shadow**: `rgba(0,0,0,0.14) 0px 28px 70px` + `rgba(0,0,0,0.1) 0px 14px 32px` — large diffuse clouds
- **Elevation levels**: 3 (flat border + ambient cloud + elevated)
- **Border role**: `1px solid oklab(0.263/0.1)` — perceptually uniform warm brown `[unique]`
- **Direction**: Large diffuse downward (28px, 14px offsets)
- **Focus**: Border opacity increase to `oklab(0.263/0.2)` or accent orange

*Source*: awesome-design-md | 2026-04-06

---

## Supabase
> Border-defined depth — no shadows, edges define everything

- **Primary technique**: Border-only containment, zero shadows
- **Card border**: `1px solid #2e2e2e` or `#363636`
- **Elevation levels**: 2 (flat + bordered)
- **Border role**: `1px solid #2e2e2e` (standard) / `1px solid #fafafa` (primary button) — borders are the ONLY depth cue
- **Green accent**: `rgba(62,207,142,0.3)` border as brand highlight
- **Distinctive**: Zero shadows in entire system — deliberate anti-shadow philosophy `[unique]`

*Source*: awesome-design-md | 2026-04-06

---

## Raycast
> macOS-native physicality — inset shadows, double-ring borders, and keyboard key caps

- **Primary technique**: Multi-layer inset shadows + double-ring borders
- **Button shadow**: `rgba(255,255,255,0.1) 0px 1px 0px 0px inset` + `rgba(255,255,255,0.25) 0px 0px 0px 1px`
- **Card shadow**: Double-ring `rgb(27,28,30) 0px 0px 0px 1px` outer + `rgb(7,8,10) 0px 0px 0px 1px inset` inner
- **Elevation levels**: 4+ (flat + inset + ring + physical key caps)
- **Border role**: `1px solid rgba(255,255,255,0.06)` — very subtle
- **Focus**: Blue glow ring `hsla(202,100%,67%,0.15)`
- **Warm glow**: `rgba(215,201,175,0.05)` aura behind featured elements
- **Distinctive**: 5-layer physical keyboard key cap shadows — most complex depth in set `[unique]`

*Source*: awesome-design-md | 2026-04-06

---

## Nothing
> Flat is the philosophy — zero shadows, zero blur, border separation only

- **Primary technique**: Zero shadows. Flat surfaces with border separation.
- **Card border**: `1px solid --border` (#222222), no shadows ever
- **Elevation levels**: 2 (flat + bordered — that's it)
- **Border role**: Sole depth mechanism — `--border` (#222222) decorative, `--border-visible` (#333333) intentional
- **Explicitly banned**: Shadows, blur, gradients in UI chrome
- **Distinctive**: Anti-shadow philosophy — "no shadows, no blur, flat surfaces, border separation" is a design rule, not a limitation `[unique]`

*Source*: awesome-design-md | 2026-04-06

---

## Uber
> Whisper shadows — featherweight lift defined by absence

- **Primary technique**: Single-layer featherweight shadows
- **Card shadow**: `rgba(0,0,0,0.12) 0px 4px 16px` — light lift
- **Elevation levels**: 2 (flat + whisper lift)
- **Border role**: Only on inputs (`1px solid #000000` — the sole visible border usage)
- **Active state**: Inset `rgba(0,0,0,0.08)` on chip/filter buttons
- **Focus**: `rgb(255,255,255) 0px 0px 0px 2px inset` ring
- **Distinctive**: All buttons are pill (999px) — border-radius creates depth sensation even without shadow

*Source*: awesome-design-md | 2026-04-06

---

## Superhuman
> Two-radius minimalism — depth through border and color contrast, not shadow

- **Primary technique**: Border-defined depth with minimal shadows
- **Card border**: `1px solid #dcd7d3` (Parchment Border)
- **Elevation levels**: 2 (flat + bordered)
- **Border-radius system**: Only two values exist — 8px (buttons) and 16px (cards) `[unique]`
- **Shadow role**: Minimal; depth achieved via borders and color contrast
- **Hero depth**: Deep purple gradient (#1b1938) as singular dramatic gesture — depth through COLOR, not shadow

*Source*: awesome-design-md | 2026-04-06

---

## Framer
> Cinematic void with blue glow rings and frosted glass on black

- **Primary technique**: Colored ring shadows + frosted glass surfaces
- **Card shadow**: Blue ring `rgba(0,153,255,0.15) 0px 0px 0px 1px` + white top highlight `rgba(255,255,255,0.1) 0px 0.5px` + deep ambient `rgba(0,0,0,0.25) 0px 10px 30px`
- **Elevation levels**: 3 (flat void + ring glow + deep ambient)
- **Button surface**: Frosted pill `rgba(255,255,255,0.1)` — translucent glass on black
- **Direction**: Top-lit (0.5px white highlight at top edge)
- **Hover**: Glow increase on Framer Blue ring shadow
- **Distinctive**: Blue-tinted ring glow creates branded depth on void-black canvas `[unique]`

*Source*: awesome-design-md | 2026-04-06
