# Layouts Digest

## Cross References
- `[container:1200px]` **~1200px max-width consensus**: Claude, Vercel, Linear, Notion, Cursor, Raycast, Superhuman, Framer all converge on ~1200px max container width
- `[base:8px]` **8px base spacing grid**: All 15 brands use 8px as the foundational spacing unit
- `[pattern:hero-then-grid]` **Centered single-column hero + multi-column features**: Nearly universal pattern -- full-width centered hero followed by 2-3 column card grids
- `[pattern:sticky-top-nav]` **Sticky top navigation**: Claude, Vercel, Stripe, Notion, Airbnb, Supabase, Raycast, Uber, Superhuman, Framer all use fixed/sticky top nav
- `[pattern:section-alternation]` **Light/dark section alternation**: Claude (parchment/near-black), Stripe (white/brand-dark), Notion (white/warm-white), Supabase (dark throughout), Linear (dark throughout)
- `[pattern:responsive-collapse]` **Collapsing pattern**: Universal 3-col -> 2-col -> 1-col card grid collapse across all brands
- `[pattern:section-spacing-responsive]` **Section spacing 80-120px desktop -> 48px mobile**: Shared by Claude, Vercel, Linear, Cursor, Raycast, Framer

## Claude
> Warm editorial layout with magazine-like pacing and serif-driven rhythm
- **Container**: max-width ~1200px
- **Grid**: 2-3 column card grids; 3-column model comparison grid
- **Breakpoints**: Mobile <479px / Tablet 768px / Desktop 992px+
- **Navigation**: top-fixed horizontal, hamburger on mobile
- **Strategy**: centered single-column hero; light/dark section alternation creates chapter-like page rhythm; editorial pacing with generous 80-120px section spacing
*Source*: awesome-design-md | 2026-04-06

## Vercel
> Gallery-like emptiness where white space IS the design
- **Container**: max-width ~1200px
- **Grid**: 2-3 column feature card grids; full-width dividers using 1px solid borders
- **Breakpoints**: Mobile <600px / Tablet 768px / Desktop 1200px+
- **Navigation**: top-fixed sticky on white; horizontal links collapse to hamburger
- **Strategy**: centered single-column hero; compressed text counterbalanced by vast surrounding whitespace; no color variation between sections -- separation via shadow-borders and spacing alone
*Source*: awesome-design-md | 2026-04-06

## Stripe
> Precision spacing with dense data in generous chrome
- **Container**: max-width ~1080px
- **Grid**: 2-3 column feature card grids; code/dashboard previews as contained cards
- **Breakpoints**: Mobile <640px / Tablet 640-1024px / Desktop 1024px+
- **Navigation**: top-fixed sticky with blur backdrop; horizontal collapse to hamburger
- **Strategy**: centered single-column hero with lightweight headlines; white sections alternate with dark brand (#1c1e54) sections; dense financial data displays in generously spaced frames
*Source*: awesome-design-md | 2026-04-06

## Linear
> Dark-mode-native -- content emerges from darkness like starlight
- **Container**: max-width ~1200px
- **Grid**: 2-3 column feature card grids; single-column changelog timeline
- **Breakpoints**: Mobile <600px / Tablet 640-768px / Desktop 1024px+
- **Navigation**: top-fixed dark sticky header; hamburger at 768px
- **Strategy**: centered single-column hero; darkness as space with no visible dividers -- background provides natural separation; 80px+ section spacing with generous vertical padding
*Source*: awesome-design-md | 2026-04-06

## Notion
> Generous vertical rhythm with warm alternating sections
- **Container**: max-width ~1200px
- **Grid**: 2-3 column card grids; full-width warm-white section backgrounds
- **Breakpoints**: Mobile <400px / Tablet 768px / Desktop 1200px+
- **Navigation**: top horizontal (not sticky); hamburger on mobile; product dropdowns
- **Strategy**: centered single-column hero with 80-120px top padding; white sections alternate with warm-white (#f6f5f4) sections for gentle visual rhythm; content-first density with compact text blocks in ample margin
*Source*: awesome-design-md | 2026-04-06

## Figma
> Gallery-like pacing with each product section as its own exhibit
- **Container**: max-width up to 1920px
- **Grid**: alternating product showcases; full-width gradient hero
- **Breakpoints**: Mobile <560px / Tablet 768px / Desktop 960-1280px / Ultra-wide 1440-1920px
- **Navigation**: top horizontal on white; pill-shaped tab navigation (50px radius)
- **Strategy**: full-width gradient hero with centered content; gallery-like pacing lets each product section breathe; chromatic gradient hero provides visual breathing between monochrome interface sections
*Source*: awesome-design-md | 2026-04-06

## Airbnb
> Photography-forward marketplace with travel-magazine spacing
- **Container**: full-width responsive grid (3-5 columns on desktop)
- **Grid**: responsive multi-column listing grid; category pill bar as horizontal scrollable row
- **Breakpoints**: Mobile <375px / Tablet 744px / Desktop 1128px / Large 1440px / Ultra-wide 1920px+ (61 detected breakpoints -- extremely granular)
- **Navigation**: top-fixed sticky with centered search bar; category filter pills below
- **Strategy**: full-width header with search prominence; listing grid fills viewport; photography density with large immersive images; search bar gets maximum vertical space
*Source*: awesome-design-md | 2026-04-06

## Spotify
> Dark immersive app layout -- sidebar + content area + bottom bar
- **Container**: sidebar (fixed) + flexible main content area
- **Grid**: grid-based album/playlist cards; full-width now-playing bar at bottom
- **Breakpoints**: Mobile <425px / Tablet 576-768px / Desktop 1024px+
- **Navigation**: sidebar (collapses on mobile to bottom-tab); full-width now-playing bar persists
- **Strategy**: app-shell layout with fixed sidebar + bottom bar; dense content packing -- dark background provides visual rest without large gaps; content density over breathing room
*Source*: awesome-design-md | 2026-04-06

## Cursor
> Warm compressed editorial with three-font typographic richness
- **Container**: max-width ~1200px
- **Grid**: 2-3 column feature grids; sidebar layouts for documentation
- **Breakpoints**: Mobile <600px / Tablet 768px / Desktop 1279px+
- **Navigation**: top-fixed sticky on warm cream; tab navigation with bottom borders
- **Strategy**: centered single-column hero with 80-120px padding; warm negative space (cream background gives whitespace warmth); alternating surface tones (cream variations) for subtle section differentiation
*Source*: awesome-design-md | 2026-04-06

## Supabase
> Dark-mode-native with dramatic section spacing and border-defined containment
- **Container**: centered content with generous max-width; full-width dark sections
- **Grid**: icon-based feature grids with consistent card sizes; logo grids
- **Breakpoints**: Mobile <600px / Desktop 600px+ (notably minimal -- single primary breakpoint)
- **Navigation**: top-fixed dark sticky header; product dropdown
- **Strategy**: dramatic 90-128px section spacing creates cinematic pacing; dense content blocks (16-24px) within sections; border-defined space instead of whitespace + shadows
*Source*: awesome-design-md | 2026-04-06

## Raycast
> macOS-native dark instrument case with cinematic section isolation
- **Container**: max-width ~1200px (breakpoint at 1204px), centered
- **Grid**: single-column hero; 2-3 column feature grids; full-width showcase sections
- **Breakpoints**: Mobile <600px / Tablet 768px / Desktop 1024px+
- **Navigation**: top-fixed dark sticky nav; semi-transparent white pill CTA; hamburger on mobile
- **Strategy**: dramatic negative space with sections floating in dark void; dense product UI contrasts with sparse marketing copy; 80-120px section padding; consistent 24-32px element gaps within sections
*Source*: awesome-design-md | 2026-04-06

## Nothing
> Spacing-as-meaning system with industrial grid discipline
- **Container**: not specified (design system rather than marketing page)
- **Grid**: spacing-based grouping; no explicit grid spec -- hierarchy through proximity
- **Breakpoints**: not specified
- **Navigation**: not specified
- **Strategy**: spacing communicates relationships (4-8px tight = "belong together", 16px medium = "same group", 32-48px wide = "new group", 64-96px vast = "new context"); dividers are a symptom of insufficient spacing contrast; asymmetric composition preferred over centered symmetry
*Source*: awesome-design-md | 2026-04-06

## Uber
> Transit-system efficiency -- compact, clear, purpose-driven
- **Container**: max-width ~1136px, centered
- **Grid**: 2-column card grids; split hero (text left, visual right); full-width footer
- **Breakpoints**: Mobile 320-600px / Tablet 768px / Desktop 1120-1136px
- **Navigation**: top-fixed sticky white; horizontal pill nav chips; hamburger on mobile
- **Strategy**: split hero layout with text+CTA left, map/illustration right; efficient spacing -- enough to separate, never enough to feel empty; content-dense cards with minimal internal padding; black footer anchors the page
*Source*: awesome-design-md | 2026-04-06

## Superhuman
> Cinematic hero-to-white transition with luxury spacing
- **Container**: max-width ~1200px, centered
- **Grid**: full-width hero; 2-3 column feature grid; single-column key messaging
- **Breakpoints**: Mobile <768px / Tablet 768-1024px / Desktop 1024-1440px
- **Navigation**: top-fixed sticky; transparent on hero gradient, white on content sections
- **Strategy**: dramatic purple gradient hero dissolves into white content body; progressive density -- spacious cinematic hero, denser feature grids, opens up again for CTAs; product screenshots as primary visual fill; binary border-radius system (8px small, 16px large only)
*Source*: awesome-design-md | 2026-04-06

## Framer
> Cinematic dark void with product screenshots as hero art
- **Container**: max-width ~1200px, centered
- **Grid**: full-width hero; 2-column asymmetric features (40% text / 60% screenshot); single-column showcases
- **Breakpoints**: Mobile <809px / Tablet 809-1199px / Desktop 1199px+
- **Navigation**: top-fixed dark floating nav with frosted glass effect; hamburger on mobile
- **Strategy**: full-width hero with extreme negative tracking headlines; dense components float in generous surrounding void; asymmetric feature sections (text + screenshot); 80-120px section spacing
*Source*: awesome-design-md | 2026-04-06
