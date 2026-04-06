# Spacing Digest

## Cross References
- `[base:8px]` **8px base unit**: All 15 brands use 8px as their foundational spacing unit
- `[pattern:gallery-section-spacing]` **Gallery-level section spacing (80-120px+)**: Claude, Vercel, Linear, Raycast, Framer share dramatic vertical section gaps
- `[pattern:compressed-text-expanded-space]` **Compressed text + expanded space**: Vercel, Linear, Cursor, Framer all combine aggressive negative letter-spacing with generous surrounding whitespace
- `[pattern:dark-section-isolation]` **Dark-mode section isolation**: Linear, Supabase, Spotify, Raycast, Framer use the dark void itself as whitespace
- `[pattern:light-dark-alternation]` **Light/Dark alternation**: Claude (parchment/black), Notion (white/warm white), Stripe (white/navy) alternate section backgrounds for rhythm
- `[pattern:dense-within-sparse-between]` **Dense-within, sparse-between**: Uber, Spotify, Supabase pack content tight inside sections but space sections generously apart
- `[container:1200px]` **Max container ~1200px**: Claude, Vercel, Linear, Cursor, Supabase, Raycast, Framer, Superhuman all center around 1200px max-width

---

## Claude
> Editorial magazine pacing with warm parchment canvas and chapter-like rhythm
- **Base unit**: 8px
- **Tokens**: 3/4/6/8/10/12/16/20/24/30px
- **Section spacing**: 80-120px between major sections
- **Card padding**: 24-32px
- **Button padding**: asymmetric (0px 12px 0px 8px) or balanced (8px 16px)
- **Max container**: ~1200px centered
- **Whitespace strategy**: generous -- editorial serif-driven rhythm demands breathing room; light/dark section alternation creates distinct "rooms"
*Source*: awesome-design-md | 2026-04-06

---

## Vercel
> Gallery emptiness where compressed text floats in vast achromatic space
- **Base unit**: 8px
- **Tokens**: 1/2/3/4/5/6/8/10/12/14/16/32/36/40px (notable gap: 16px jumps to 32px)
- **Section spacing**: 80-120px+ vertical between major sections
- **Whitespace strategy**: generous -- the white space IS the design; separation through shadow-borders and spacing alone, no color variation between sections
- **Max container**: ~1200px centered
- **Grid**: 2-3 column card grids, full-width dividers with `1px solid #171717`
*Source*: awesome-design-md | 2026-04-06

---

## Stripe
> Precision spacing with dense data in generous chrome frames
- **Base unit**: 8px
- **Tokens**: 1/2/4/6/8/10/11/12/14/16/18/20px (dense at small end, every 2px from 4-12)
- **Section spacing**: 64px+ between major sections (40px on mobile)
- **Whitespace strategy**: moderate/precise -- financial data is tightly packed but surrounding UI chrome is generous; white/dark brand sections alternate
- **Max container**: ~1080px centered
- **Grid**: 2-3 column feature card grids
*Source*: awesome-design-md | 2026-04-06

---

## Linear
> Darkness as space with compressed headlines floating in vast dark padding
- **Base unit**: 8px
- **Tokens**: 1/4/7/8/11/12/16/19/20/22/24/28/32/35px (7px and 11px for optical adjustments)
- **Primary rhythm**: 8/16/24/32px (standard 8px grid)
- **Section spacing**: 80px+ between major sections (no visible dividers)
- **Whitespace strategy**: generous -- empty dark space IS the whitespace; content emerges from darkness; section isolation through vast vertical padding alone
- **Max container**: ~1200px centered
*Source*: awesome-design-md | 2026-04-06

---

## Notion
> Content-first generous rhythm with warm alternating section backgrounds
- **Base unit**: 8px
- **Tokens**: 2/3/4/5/6/7/8/11/12/14/16/24/32px (non-rigid organic scale with fractional micro-adjustments)
- **Section spacing**: 64-120px between major sections
- **Hero padding**: 80-120px top
- **Whitespace strategy**: generous -- vast vertical rhythm between sections; white alternates with warm white (#f6f5f4) for gentle visual rhythm; compact body text (1.50 line-height) surrounded by ample margin
- **Max container**: ~1200px centered
*Source*: awesome-design-md | 2026-04-06

---

## Figma
> Gallery-like pacing with color sections providing chromatic breathing room
- **Base unit**: 8px
- **Tokens**: 1/2/4/4.5/8/10/12/16/18/24/32/40/46/48/50px
- **Section spacing**: generous (gallery-exhibit pacing)
- **Whitespace strategy**: generous -- each product section breathes as its own exhibit; gradient hero and product showcases provide chromatic relief between monochrome sections
- **Max container**: up to 1920px
- **Grid**: responsive from 559px to 1920px
*Source*: awesome-design-md | 2026-04-06

---

## Airbnb
> Travel-magazine spacing with photography density and search-bar prominence
- **Base unit**: 8px
- **Tokens**: 2/3/4/6/8/10/11/12/15/16/22/24/32px
- **Section spacing**: generous vertical padding (travel-magazine pacing)
- **Button padding**: 0px 24px (primary), 14px 16px (chips)
- **Whitespace strategy**: moderate -- generous between sections for leisurely browsing; listing cards packed relatively tight but each image large enough to feel immersive; search bar gets maximum prominence
- **Max container**: full-width with responsive multi-column (3-5 columns)
*Source*: awesome-design-md | 2026-04-06

---

## Spotify
> Dark compression with dense content and minimal breathing room
- **Base unit**: 8px
- **Tokens**: 1/2/3/4/5/6/8/10/12/14/15/16/20px
- **Section spacing**: minimal -- app-like density
- **Whitespace strategy**: compact -- content packed densely (playlists, track lists, nav); dark background provides visual rest between elements without needing large gaps; every pixel serves the listening experience
- **Layout**: sidebar (fixed) + main content area + now-playing bar
*Source*: awesome-design-md | 2026-04-06

---

## Cursor
> Warm negative space with fine-grained sub-8px micro-adjustments
- **Base unit**: 8px
- **Fine scale**: 1.5/2/2.5/3/4/5/6px (sub-8px for icon/text micro-alignment)
- **Standard scale**: 8/10/12/14px
- **Extended (inferred)**: 16/24/32/48/64/96px
- **Section spacing**: 80-120px+ between sections (reduces to 32px on mobile)
- **Whitespace strategy**: generous -- cream background gives warmth to negative space; compressed CursorGothic headlines balanced by generous surrounding margins; alternating surface tones for subtle section differentiation
- **Max container**: ~1200px centered
*Source*: awesome-design-md | 2026-04-06

---

## Supabase
> Cinematic dark-mode pacing with dramatic jumps between sections
- **Base unit**: 8px
- **Tokens**: 1/4/6/8/12/16/20/24/32/40/48/90/96/128px (notable large jumps: 48 to 90 to 128)
- **Section spacing**: 90-128px between major sections (cinematic pacing)
- **Card padding**: 16-24px
- **Whitespace strategy**: dramatic between sections (90-128px), dense within sections (16-24px); border-defined separation instead of whitespace + shadows
- **Max container**: centered with generous max-width
*Source*: awesome-design-md | 2026-04-06

---

## Raycast
> macOS-native precision with dramatic section voids
- **Base unit**: 8px
- **Tokens**: 1/2/3/4/8/10/12/16/20/24/32/40px
- **Section spacing**: 80-120px vertical between major sections
- **Card padding**: 16-32px
- **Component gaps**: 8-16px between related elements
- **Whitespace strategy**: generous -- sections float in vast dark void creating cinematic pacing; product UI screenshots are dense but marketing copy uses minimal text with generous spacing; consistent 24-32px vertical rhythm within sections
- **Max container**: ~1200px (breakpoint at 1204px)
*Source*: awesome-design-md | 2026-04-06

---

## Nothing
> Instrument-panel precision with 8px base and spacing-as-meaning philosophy
- **Base unit**: 8px
- **Tokens**: 2px (2xs) / 4px (xs) / 8px (sm) / 16px (md) / 24px (lg) / 32px (xl) / 48px (2xl) / 64px (3xl) / 96px (4xl)
- **Section spacing**: 48-64px (2xl-3xl), 96px for hero breathing room
- **Whitespace strategy**: deliberate -- spacing IS the primary tool for communicating relationships; tight (4-8px) = belongs together, medium (16px) = same group, wide (32-48px) = new group, vast (64-96px) = new context; "if a divider is needed, the spacing is probably wrong"
*Source*: awesome-design-md | 2026-04-06

---

## Uber
> Transit-system spacing that is efficient without being airy
- **Base unit**: 8px
- **Tokens**: 4/6/8/10/12/14/16/18/20/24/32px
- **Section spacing**: 64-96px between major sections
- **Button padding**: 10px 12px (compact) or 14px 16px (comfortable)
- **Card padding**: 24-32px
- **Whitespace strategy**: moderate/compact -- functional spacing, enough to separate but never empty; content-dense cards with tight internal spacing; major sections get generous vertical spacing but within sections elements are closely grouped
- **Max container**: ~1136px centered
*Source*: awesome-design-md | 2026-04-06

---

## Superhuman
> Confident emptiness with progressive density from spacious hero to dense grids
- **Base unit**: 8px
- **Tokens**: 2/4/6/8/12/16/18/20/24/28/32/36/40/48/56px
- **Section spacing**: 48-80px between major sections
- **Card padding**: 16-32px
- **Component gaps**: 8-16px
- **Whitespace strategy**: generous -- confident emptiness signals premium positioning; large product screenshots fill space instead of marketing copy; progressive density (spacious hero -> dense feature grids -> open CTAs)
- **Max container**: ~1200px centered
*Source*: awesome-design-md | 2026-04-06

---

## Framer
> Void-black breathing with dense components floating in generous darkness
- **Base unit**: 8px
- **Tokens**: 1/2/3/4/5/6/8/10/12/15/20/30/35px
- **Section spacing**: 80-120px between sections (60px on mobile)
- **Card padding**: 15-30px
- **Component gaps**: 8-20px
- **Whitespace strategy**: generous -- black background manifests whitespace as void, creating dramatic pauses; individual components are tightly composed (compressed text, tight line-heights) but float in generous surrounding space; product-first density allowed in screenshot areas
- **Max container**: ~1200px centered
*Source*: awesome-design-md | 2026-04-06
