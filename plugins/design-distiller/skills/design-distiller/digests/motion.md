# Motion Digest

> **⚠ Data Coverage: Low** — Most pre-loaded references were imported from static Design MDs that lack explicit animation/transition specifications. Duration and easing values are frequently marked "not explicitly specified." When running the full scrape pipeline on new sites, prioritize extracting `transition` and `animation` CSS properties via computed styles to improve coverage.

## Cross References
- `[pattern:motion-light]` **Motion-light approach**: Most brands in this set are marketing/product pages with minimal explicit animation specs in their design MDs
- `[technique:opacity-hover]` **Opacity-based hover**: Raycast and Framer both use opacity transitions for hover rather than color changes
- `[technique:scale-press]` **Scale press feedback**: Notion uses scale(0.9) on active/pressed and scale(1.05) on hover; Airbnb uses scale(0.92) on focus
- `[approach:no-spring]` **No spring/bounce consensus**: Nothing explicitly bans spring/bounce easing; most brands favor restrained, functional transitions
- `[technique:shadow-hover]` **Shadow transitions for elevation**: Cursor, Raycast, Linear all use shadow intensification on hover as a motion cue
- `[technique:color-hover]` **Gradient/color transitions on hover**: Stripe uses background darkening; Claude uses text color shifts; Uber uses background-color shifts

## Cursor
> Warm, restrained transitions focused on color shifts and shadow depth
- **Duration**: micro ~150ms (color), transition ~200ms (shadow/elevation)
- **Easing**: ease (both color and shadow transitions)
- **Style**: restrained, functional
- **Common effects**: text color shift to warm crimson (#cf2d56) on hover; shadow intensification (ambient to elevated) on card hover; subtle scale/translate for interactive feedback
*Source*: awesome-design-md | 2026-04-06

## Raycast
> Opacity-driven hover with macOS-native tactile feel
- **Duration**: not explicitly specified (CSS transition-based)
- **Easing**: standard CSS transitions
- **Style**: restrained, mechanical, macOS-native
- **Common effects**: opacity transition to 0.6 on all button hovers (signature pattern -- no color changes); border opacity increase on card hover; subtle shadow enhancement; text brightening (gray to white) on ghost button hover
*Source*: awesome-design-md | 2026-04-06

## Nothing
> Percussive and mechanical -- click not swoosh, tick not chime
- **Duration**: not explicitly specified
- **Easing**: subtle ease-out only (spring/bounce explicitly banned)
- **Style**: percussive, mechanical, precise
- **Common effects**: no parallax, no scroll-jacking, no gratuitous animation; inline status text ([SAVED], [ERROR]) instead of toast popups; segmented spinner or [LOADING...] text instead of skeleton screens; all transitions should feel mechanical and precise
*Source*: awesome-design-md | 2026-04-06

## Notion
> Micro-scale transforms for interactive feedback
- **Duration**: not explicitly specified
- **Easing**: standard CSS transitions
- **Style**: subtle, tactile
- **Common effects**: scale(1.05) on button hover; scale(0.9) on active/pressed state; color shift on text hover; underline-on-hover for links; shadow intensification on card hover
*Source*: awesome-design-md | 2026-04-06

## Airbnb
> Touch-optimized feedback with subtle scale and shadow shifts
- **Duration**: not explicitly specified
- **Easing**: standard CSS transitions
- **Style**: warm, tactile, touch-friendly
- **Common effects**: scale(0.92) focus shrink on circular nav buttons; translateX(50%) on circular button hover; shadow elevation on hover (rgba(0,0,0,0.08) 0px 4px 12px); 4px white border ring on active state; image carousel transitions
*Source*: awesome-design-md | 2026-04-06

## Framer
> Scale-based animations with matrix transforms
- **Duration**: not explicitly specified
- **Easing**: matrix transform-based (scale factor 0.85)
- **Style**: kinetic, product-forward
- **Common effects**: scale-based matrix transforms (0.85 scale factor); opacity transitions for reveal effects; glow increase on Framer Blue ring shadow on hover; brightness shift on frosted surfaces; lazy-load reveal on scroll
*Source*: awesome-design-md | 2026-04-06

## Superhuman
> Ultra-restrained -- depth through color contrast, not movement
- **Duration**: not explicitly specified
- **Easing**: not explicitly specified
- **Style**: restrained, luxury-minimal
- **Common effects**: subtle opacity/brightness shift on button hover (no dramatic color transformations); sticky nav with background transition on scroll (transparent on hero to white on content); minimal state changes overall -- consistency and calm over flashy interactions
*Source*: awesome-design-md | 2026-04-06

## Spotify
> Dark-immersive app with subtle surface lightening
- **Duration**: not explicitly specified
- **Easing**: not explicitly specified
- **Style**: functional, app-like
- **Common effects**: slight background lightening on card hover; album art carousel with swipe on mobile; sidebar collapse/expand transitions; dot indicator transitions on image carousels
*Source*: awesome-design-md | 2026-04-06

## Linear
> Luminance stepping instead of traditional motion depth cues
- **Duration**: not explicitly specified
- **Easing**: not explicitly specified
- **Style**: restrained, precision-engineered
- **Common effects**: background opacity increase on hover (rgba white stepping 0.02 to 0.04 to 0.05); text lightening from #d0d6e0 to #f7f8f8 on hover; subtle shadow enhancement on interactive elements; hero visual simplification on mobile (fewer floating UI elements)
*Source*: awesome-design-md | 2026-04-06

---

**Note**: Claude, Vercel, Stripe, Figma, Supabase, and Uber DESIGN.md files do not contain explicit motion/animation specifications beyond static hover state descriptions. Their motion systems are either minimal by design or documented elsewhere.
