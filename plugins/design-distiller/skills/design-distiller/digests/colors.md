# Colors Digest

## Cross References

### Shared Palettes & Patterns
- `[palette:warm-parchment]` **Warm parchment/cream backgrounds**: Claude (`#f5f4ed`), Cursor (`#f2f1ed`), Notion (`#f6f5f4`), PostHog (`#fdfdf8`) all use warm off-white instead of pure white -- these brands share a "paper not screen" philosophy
- `[palette:pure-black-void]` **Pure black void canvas**: Framer (`#000000`), Resend (`#000000`), Spotify (`#121212`), Linear (`#08090a`) share a dark-first approach where UI disappears behind content
- `[palette:near-black-text]` **Near-black text (not pure black)**: Apple (`#1d1d1f`), Airbnb (`#222222`), Stripe (`#061b31`), Vercel (`#171717`), Superhuman (`#292827`), Coinbase (`#0a0b0d`) -- universally, top brands soften their darkest text
- `[pattern:single-accent]` **Single-accent-color systems**: Apple (blue `#0071e3`), Notion (blue `#0075de`), Figma (black+white only), Uber (black only), Airbnb (red `#ff385c`), Supabase (green `#3ecf8e`), Mintlify (green `#18E299`) -- each uses one chromatic color for all interactive elements
- `[pattern:pill-9999]` **Pill button geometry (9999px)**: Vercel, Spotify, Supabase, Resend, Mintlify, Uber, Linear, PostHog -- pill-shaped CTAs are the dominant pattern in modern design
- `[pattern:shadow-as-border]` **Shadow-as-border technique (0px 0px 0px 1px)**: Vercel, Claude, Linear, Resend share the ring-shadow approach replacing CSS borders
- `[pattern:blue-tinted-shadow]` **Blue-tinted shadows**: Stripe (`rgba(50,50,93,0.25)`) and Resend (`rgba(214,235,253,0.19)`) both tint their depth system with brand-adjacent blue
- `[palette:warm-gray]` **Warm gray families**: Claude, Cursor, Notion, PostHog all carry yellow-brown or olive undertones in their neutral scales; Linear, Raycast, Vercel stay cool-neutral
- `[pattern:dark-section-alternation]` **Dark section alternation**: Apple (black/`#f5f5f7`), Claude (parchment/near-black), Stripe (white/`#1c1e54`), Coinbase (white/`#0a0b0d`) use light-dark rhythm for cinematic pacing

---

## Claude (Anthropic)
> Warm parchment canvas with terracotta accent -- literary salon meets product page

- **Background**: Parchment `#f5f4ed` / Ivory `#faf9f5` / Dark `#141413`
- **Text**: Anthropic Near Black `#141413` / Olive Gray `#5e5d59` / Stone Gray `#87867f`
- **Accent**: Terracotta Brand `#c96442` / Coral `#d97757`
- **Border**: `#f0eee6` / `#e8e6dc` (light) / `#30302e` (dark)
- **Status**: Error `#b53333` / Focus Blue `#3898ec` (accessibility only)
- **Dark mode**: Yes, first-class -- alternating light/dark sections; dark surfaces use `#141413` and `#30302e` with warm silver text `#b0aea5`
- **Strategy**: Dual-tone (warm cream + warm charcoal), exclusively warm-toned neutrals

*Source*: awesome-design-md | 2026-04-06

---

## Vercel
> Monochrome engineering precision -- white gallery with black text and shadow-borders

- **Background**: Pure White `#ffffff`
- **Text**: Vercel Black `#171717` / Gray 600 `#4d4d4d` / Gray 500 `#666666`
- **Accent**: Workflow-specific -- Ship Red `#ff5b4f` / Preview Pink `#de1d8d` / Develop Blue `#0a72ef` / Link Blue `#0072f5`
- **Border**: Shadow-as-border `rgba(0,0,0,0.08) 0px 0px 0px 1px` / Gray 100 `#ebebeb`
- **Status**: Console Blue `#0070f3` / Console Purple `#7928ca` / Console Pink `#eb367f`
- **Dark mode**: No prominent dark mode on marketing; system is achromatic white
- **Strategy**: Monochrome (pure grayscale), functional-only color in workflow pipeline

*Source*: awesome-design-md | 2026-04-06

---

## Stripe
> Deep navy + saturated purple -- fintech luxury with blue-tinted shadows

- **Background**: Pure White `#ffffff` / Brand Dark `#1c1e54`
- **Text**: Deep Navy `#061b31` / Slate `#64748d` / Label `#273951`
- **Accent**: Stripe Purple `#533afd` / Ruby `#ea2261` / Magenta `#f96bee`
- **Border**: `#e5edf5` / Purple `#b9b9f9` / Dashed `#362baa`
- **Status**: Success Green `#15be53` / Success Text `#108c3d` / Lemon Warning `#9b6829`
- **Dark mode**: Yes, via dark brand sections `#1c1e54` with white text; not a full system toggle
- **Strategy**: Dual-tone (white + indigo dark), purple-anchored with blue-tinted depth

*Source*: awesome-design-md | 2026-04-06

---

## Linear
> Dark-mode-native precision -- near-black canvas with indigo-violet accent

- **Background**: Marketing Black `#08090a` / Panel `#0f1011` / Surface `#191a1b`
- **Text**: Primary `#f7f8f8` / Secondary `#d0d6e0` / Tertiary `#8a8f98` / Quaternary `#62666d`
- **Accent**: Brand Indigo `#5e6ad2` / Violet `#7170ff` / Hover `#828fff`
- **Border**: `rgba(255,255,255,0.05)` / `rgba(255,255,255,0.08)` / Solid `#23252a`
- **Status**: Success Green `#27a644` / Emerald `#10b981`
- **Dark mode**: Dark-native (primary), light mode available with `#f7f8f8` bg and `#d0d6e0` borders
- **Strategy**: Monochrome dark with single indigo-violet accent

*Source*: awesome-design-md | 2026-04-06

---

## Notion
> Warm neutral canvas with blue accent -- approachable minimalism on quality paper

- **Background**: Pure White `#ffffff` / Warm White `#f6f5f4`
- **Text**: Near Black `rgba(0,0,0,0.95)` / Warm Gray 500 `#615d59` / Warm Gray 300 `#a39e98`
- **Accent**: Notion Blue `#0075de` / Active Blue `#005bab` / Focus Blue `#097fe8`
- **Border**: `rgba(0,0,0,0.1)` / Input `#dddddd`
- **Status**: Teal `#2a9d99` / Green `#1aae39` / Orange `#dd5b00`
- **Dark mode**: Not prominent on marketing; warm white alternation serves as tonal variation
- **Strategy**: Monochrome warm with single blue accent; multi-color semantic tokens for features

*Source*: awesome-design-md | 2026-04-06

---

## Figma
> Strictly black-and-white chrome -- color exists only in product content

- **Background**: Pure White `#ffffff`
- **Text**: Pure Black `#000000`
- **Accent**: None in UI chrome; vibrant multicolor gradients (green, yellow, purple, pink) only in hero/product showcases
- **Border**: Minimal; Glass Black `rgba(0,0,0,0.08)` / Glass White `rgba(255,255,255,0.16)`
- **Status**: Not defined in interface layer -- binary black/white only
- **Dark mode**: No; the interface is strictly B&W; color is content, not chrome
- **Strategy**: Pure monochrome (absolute black + white binary); color is product output only

*Source*: awesome-design-md | 2026-04-06

---

## Airbnb
> White canvas with singular Rausch Red -- photography-forward travel warmth

- **Background**: Pure White `#ffffff`
- **Text**: Near Black `#222222` / Secondary `#6a6a6a` / Disabled `rgba(0,0,0,0.24)`
- **Accent**: Rausch Red `#ff385c` / Deep Rausch `#e00b41` / Luxe Purple `#460479` / Plus Magenta `#92174d`
- **Border**: `#c1c1c1` / Card shadow ring `rgba(0,0,0,0.02) 0px 0px 0px 1px`
- **Status**: Error Red `#c13515` / Legal Blue `#428bff`
- **Dark mode**: No; white-first design with photography providing all color
- **Strategy**: Monochrome warm with singular red accent; photography is the color source

*Source*: awesome-design-md | 2026-04-06

---

## Spotify
> Near-black immersive dark -- album art provides all color

- **Background**: Near Black `#121212` / Dark Surface `#181818` / Mid Dark `#1f1f1f`
- **Text**: White `#ffffff` / Silver `#b3b3b3` / Near White `#cbcbcb`
- **Accent**: Spotify Green `#1ed760`
- **Border**: `#4d4d4d` / Light `#7c7c7c` / Green variant `#1db954`
- **Status**: Negative Red `#f3727f` / Warning Orange `#ffa42b` / Announcement Blue `#539df5`
- **Dark mode**: Dark-native; light mode is not the primary experience
- **Strategy**: Monochrome dark with single green accent; content (album art) provides color

*Source*: awesome-design-md | 2026-04-06

---

## Apple
> Cinematic black/gray binary -- single blue accent for all interactivity

- **Background**: Pure Black `#000000` / Light Gray `#f5f5f7`
- **Text**: Near Black `#1d1d1f` / White `#ffffff` / Black 80% `rgba(0,0,0,0.8)` / Black 48% `rgba(0,0,0,0.48)`
- **Accent**: Apple Blue `#0071e3` / Link Blue `#0066cc` / Bright Blue `#2997ff` (dark bg)
- **Border**: Almost none; borderless cards; navigation glass `rgba(0,0,0,0.8)` + blur
- **Status**: Not prominently displayed on marketing; blue handles all interactive states
- **Dark mode**: Yes, via alternating black and `#f5f5f7` sections; dark surfaces `#272729` to `#2a2a2d`
- **Strategy**: Dual-tone (black + light gray alternation), single blue accent for everything interactive

*Source*: awesome-design-md | 2026-04-06

---

## Cursor
> Warm cream canvas with orange accent -- print-publication warmth meets code editor

- **Background**: Cream `#f2f1ed` / Light `#e6e5e0` / Surface `#ebeae5`
- **Text**: Warm Near-Black `#26251e` / Secondary `rgba(38,37,30,0.55)` / Muted `rgba(38,37,30,0.6)`
- **Accent**: Orange `#f54e00` / Gold `#c08532`
- **Border**: `oklab(0.263 -0.002 0.012 / 0.1)` -- perceptually uniform warm brown; fallback `rgba(38,37,30,0.1)`
- **Status**: Error `#cf2d56` / Success `#1f8a65` / Timeline colors: Thinking `#dfa88f`, Grep `#9fc9a2`, Read `#9fbbe0`, Edit `#c0a8dd`
- **Dark mode**: Not primary; warm cream is the native mode
- **Strategy**: Dual-tone (warm cream surfaces), orange accent with warm palette throughout

*Source*: awesome-design-md | 2026-04-06

---

## Supabase
> Dark-mode-native developer platform -- emerald green on near-black

- **Background**: Dark `#171717` / Deep `#0f0f0f`
- **Text**: Off White `#fafafa` / Light Gray `#b4b4b4` / Mid Gray `#898989`
- **Accent**: Supabase Green `#3ecf8e` / Green Link `#00c573`
- **Border**: `#242424` (subtle) / `#2e2e2e` (standard) / `#363636` (prominent) / Green `rgba(62,207,142,0.3)`
- **Status**: Via Radix tokens -- Crimson (alert), Yellow (warning), Tomato (error), Violet (accent)
- **Dark mode**: Dark-native; depth through border hierarchy not shadows
- **Strategy**: Monochrome dark with single emerald-green accent; HSL-based token system

*Source*: awesome-design-md | 2026-04-06

---

## Raycast
> Near-black blue-tinted void -- macOS-native shadow system with red punctuation

- **Background**: Near-Black Blue `#07080a` / Surface `#101111`
- **Text**: Near White `#f9f9f9` / Light Gray `#cecece` / Medium Gray `#9c9c9d` / Dim `#6a6b6c`
- **Accent**: Raycast Red `#FF6363` / Blue `hsl(202,100%,67%)` (~`#55b3ff`)
- **Border**: `hsl(195,5%,15%)` (~`#252829`) / `rgba(255,255,255,0.06)` / Dark `#2f3031`
- **Status**: Success Green `hsl(151,59%,59%)` (~`#5fc992`) / Warning Yellow `hsl(43,100%,60%)` (~`#ffbc33`) / Error Red `#FF6363`
- **Dark mode**: Dark-native; blue-cold tinted void canvas; macOS-inspired inset shadow system
- **Strategy**: Monochrome dark (cool-tinted), red brand punctuation + blue interactive accent

*Source*: awesome-design-md | 2026-04-06

---

## Framer
> Pure black void -- electric blue accent, compressed typography

- **Background**: Void Black `#000000` / Near Black `#090909`
- **Text**: Pure White `#ffffff` / Muted Silver `#a6a6a6` / Ghost White `rgba(255,255,255,0.6)`
- **Accent**: Framer Blue `#0099ff`
- **Border**: Blue glow ring `rgba(0,153,255,0.15) 0px 0px 0px 1px` / Near-black ring `rgb(9,9,9) 0px 0px 0px 2px`
- **Status**: Not formally defined; blue handles all interactive states
- **Dark mode**: Dark-only; pure black is the only canvas
- **Strategy**: Monochrome dark (absolute black), single electric-blue accent

*Source*: awesome-design-md | 2026-04-06

---

## Nothing
> Industrial monochrome -- OLED black with signal-red accent as interruption

- **Background**: OLED Black `#000000` (dark) / Off-White `#F5F5F5` (light) / Surface `#111111` / `#1A1A1A`
- **Text**: Display `#FFFFFF` / Primary `#E8E8E8` / Secondary `#999999` / Disabled `#666666`
- **Accent**: Nothing Red `#D71921` -- one per screen, never decorative
- **Border**: `#222222` (subtle) / `#333333` (visible)
- **Status**: Success `#4A9E5C` / Warning `#D4A843` / Error `#D71921` (shares accent red) / Interactive `#5B9BF6`
- **Dark mode**: Yes, both modes are first-class; dark = instrument panel, light = printed manual (`#F5F5F5` bg, `#FFFFFF` cards)
- **Strategy**: Pure monochrome with red-as-signal; both modes fully designed, not derived

*Source*: awesome-design-md | 2026-04-06

---

## Uber
> Black-and-white binary -- no mid-tones, no accent color, no gradients

- **Background**: Pure White `#ffffff` / Uber Black `#000000` (footer, CTAs)
- **Text**: Uber Black `#000000` / Body Gray `#4b4b4b` / Muted Gray `#afafaf`
- **Accent**: None -- true black is the sole brand color; warm illustrations provide all hue
- **Border**: `#000000` (1px solid, inputs only) / Chip Gray `#efefef`
- **Status**: Default Link Blue `#0000ee` (browser standard, minimal use)
- **Dark mode**: No; binary black/white sections only (black footer); no system-wide dark mode
- **Strategy**: Pure monochrome (absolute binary black/white), entirely gradient-free

*Source*: awesome-design-md | 2026-04-06

---

## Coinbase
> Blue-and-white financial clarity -- single saturated blue accent

- **Background**: Pure White `#ffffff` / Near Black `#0a0b0d` (dark sections)
- **Text**: Near Black `#0a0b0d` / White `#ffffff`
- **Accent**: Coinbase Blue `#0052ff` / Hover Blue `#578bfa` / Link Blue `#0667d0`
- **Border**: `rgba(91,97,110,0.2)` / Cool Gray Surface `#eef0f3`
- **Status**: Not prominently defined on marketing; blue handles interactive states
- **Dark mode**: Yes, via alternating white and `#0a0b0d` dark sections
- **Strategy**: Dual-tone (white + dark sections), single saturated blue accent

*Source*: awesome-design-md | 2026-04-06

---

## Superhuman
> Deep purple hero dissolving into white -- luxury email with muted cream buttons

- **Background**: Pure White `#ffffff` / Hero gradient `#1b1938`
- **Text**: Charcoal Ink `#292827` / Translucent White `rgba(255,255,255,0.95)` (on dark)
- **Accent**: Lavender Glow `#cbb7fb` / Amethyst Link `#714cb6`
- **Border**: Parchment Border `#dcd7d3` / Semi-transparent `rgba(255,255,255,0.2)` on hero
- **Status**: Not displayed on marketing; extreme color restraint
- **Dark mode**: Hero gradient only; content body is white-only; no system dark mode
- **Strategy**: Dual-tone (purple gradient hero + white body); singular lavender accent; luxury restraint

*Source*: awesome-design-md | 2026-04-06

---

## PostHog
> Warm sage/olive on parchment -- anti-corporate with hidden orange hover surprise

- **Background**: Warm Parchment `#fdfdf8` / Sage Cream `#eeefe9` / Light Sage `#e5e7e0`
- **Text**: Olive Ink `#4d4f46` / Deep Olive `#23251d` / Muted Olive `#65675e`
- **Accent**: PostHog Orange `#F54E00` (hover-only) / Amber Gold `#F7A501` (dark button hover)
- **Border**: Sage Border `#bfc1b7` / Light Border `#b6b7af`
- **Status**: Focus Blue `#3b82f6` (accessibility only)
- **Dark mode**: No; warm parchment is the native and only mode
- **Strategy**: Monochrome warm (olive/sage family); orange appears only on interaction -- anti-corporate

*Source*: awesome-design-md | 2026-04-06

---

## Resend
> Pure black void with icy blue-tinted frost borders -- three-font editorial hierarchy

- **Background**: Void Black `#000000`
- **Text**: Near White `#f0f0f0` / Silver `#a1a4a5` / Dark Gray `#464a4d`
- **Accent**: Orange `#ff801f` / Green `#11ff99` / Blue `#3b9eff` / Yellow `#ffc53d` / Red `#ff2047` -- multi-color system
- **Border**: Frost `rgba(214,235,253,0.19)` / Ring shadow `rgba(176,199,217,0.145) 0px 0px 0px 1px`
- **Status**: Red `#ff2047` (at 34% opacity) / Green `#11ff99` (at 18% opacity) / Yellow `#ffc53d` / Blue `#0075ff`
- **Dark mode**: Dark-only; pure black void is the sole canvas
- **Strategy**: Monochrome dark with multi-color accent scale (each feature gets its own color at low opacity)

*Source*: awesome-design-md | 2026-04-06

---

## Mintlify
> White, airy documentation clarity -- green accent with atmospheric gradient hero

- **Background**: Pure White `#ffffff` / Dark mode `#0d0d0d`
- **Text**: Near Black `#0d0d0d` / Gray 700 `#333333` / Gray 500 `#666666` / Gray 400 `#888888`
- **Accent**: Brand Green `#18E299` / Green Light `#d4fae8` / Green Deep `#0fa76e`
- **Border**: `rgba(0,0,0,0.05)` (5% opacity) / `rgba(0,0,0,0.08)` (interactive) / `#e5e5e5`
- **Status**: Warning Amber `#c37d0d` / Error Red `#d45656` / Info Blue `#3772cf`
- **Dark mode**: Yes, full inversion -- bg `#0d0d0d`, text `#ededed`, border `rgba(255,255,255,0.08)`, card `#141414`; green accent unchanged
- **Strategy**: Monochrome light with single green accent; dark mode as full inversion; atmospheric gradient hero

*Source*: awesome-design-md | 2026-04-06
