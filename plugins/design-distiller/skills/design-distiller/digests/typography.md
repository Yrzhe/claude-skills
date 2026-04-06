# Typography Digest

## Cross References

### Shared Fonts
- `[font:inter]` **Inter**: Used by Linear, Raycast, Mintlify, Framer (body), Resend (body). The most popular choice for body/UI text across modern design systems. Linear and Raycast both enable `ss03`; Framer layers on 6+ OpenType features (`cv01`, `cv05`, `cv09`, `cv11`, `ss03`, `ss07`).
- `[font:geist]` **Geist / Geist Mono**: Vercel's proprietary family. Also used by Raycast (GeistMono for code) and Mintlify (Geist Mono for code labels).
- `[font:berkeley-mono]` **Berkeley Mono**: Shared by Linear (code) and Cursor (code) as the premium monospace choice.
- `[font:source-code-pro]` **Source Code Pro**: Used by Stripe (code) and Supabase (code labels). Also referenced by PostHog for code display.
- `[font:circular]` **Circular**: Used by Supabase (primary) and Spotify (CircularSp / SpotifyMixUI is a Circular derivative).
- `[font:sf-pro]` **SF Pro**: Apple's system font. Referenced by Raycast as fallback for system UI elements.

### Shared Approaches
- `[approach:negative-tracking]` **Negative letter-spacing at display sizes**: Nearly universal. Vercel (-2.88px), Framer (-5.5px), Linear (-1.58px), Stripe (-1.4px), Notion (-2.13px), Cursor (-2.16px), Apple (-0.28px), Superhuman (-1.32px), Resend (-2.8px on ABC Favorit), Mintlify (-1.28px), Figma (-1.72px). Only Spotify and Uber use neutral/zero tracking.
- `[approach:variable-fonts]` **Variable fonts**: Figma (figmaSans), Stripe (sohne-var), Airbnb (Cereal VF), Superhuman (Super Sans VF), Linear (Inter Variable), PostHog (IBM Plex Sans Variable), Notion (NotionInter).
- `[approach:opentype-identity]` **OpenType features as brand identity**: Stripe (`ss01`), Linear (`cv01`, `ss03`), Figma (`kern`), Framer (6+ features on Inter), Resend (`ss01`, `ss03`, `ss04`, `ss11`), Raycast (`calt`, `kern`, `liga`, `ss03`).
- `[approach:light-weight-headlines]` **Weight 300 as signature**: Stripe uses light 300 for all headlines -- the most distinctive lightweight approach. Apple also uses 300 for large decorative text.
- `[approach:single-font]` **Single-font systems**: Vercel (Geist only), Uber (UberMove + UberMoveText), Supabase (Circular only), Mintlify (Inter only), Coinbase (CoinbaseDisplay/Sans/Text family).
- `[approach:three-font]` **Three-font systems**: Cursor (CursorGothic + jjannon + berkeleyMono), Resend (Domaine + ABC Favorit + Inter), Nothing (Doto + Space Grotesk + Space Mono).
- `[approach:pill-uppercase]` **Pill buttons with uppercase + wide tracking**: Spotify (1.4-2px), Nothing (Space Mono labels at 0.08em), Resend (ABC Favorit nav at +0.35px), Mintlify (Geist Mono labels at 0.6px).
- `[approach:warm-near-black]` **Warm near-black text instead of pure black**: Claude (#141413), Cursor (#26251e), Airbnb (#222222), Superhuman (#292827), Notion (rgba 0.95), Mintlify (#0d0d0d), Vercel (#171717), PostHog (#4d4f46 olive).

---

## Claude (Anthropic)
> Warm literary serif for headlines, sans for utility -- parchment-paper editorial elegance
- **Display**: Anthropic Serif, 500, 64px, line-height 1.10
- **Body**: Anthropic Sans, 400, 16-17px, line-height 1.60
- **Mono**: Anthropic Mono, 15px, letter-spacing -0.32px
- **Notable**: Custom three-font family (Serif/Sans/Mono). Single weight 500 for all serifs -- no bold, no light. Relaxed 1.60 body line-height. Micro letter-spacing on labels (0.12-0.5px at 12px and below). Serif for authority, sans for utility -- the split IS the identity.
- **Scale**: Display 64px -> Section 52px -> Sub 36px -> Body 17px -> Caption 14px -> Label 12px -> Overline 10px

*Source*: awesome-design-md | 2026-04-06

## Vercel
> Geist with extreme negative tracking -- text compressed like minified code
- **Display**: Geist, 600, 48px, line-height 1.00, letter-spacing -2.4px to -2.88px
- **Body**: Geist, 400, 16-18px, line-height 1.50-1.56
- **Mono**: Geist Mono, 12-16px, with `"liga"` and `"tnum"`
- **Notable**: Most aggressive negative tracking of any major system (-2.88px at 48px). OpenType `"liga"` enabled globally. Three strict weights: 400/500/600. Progressive tracking relaxation: -2.4px at 48px -> -1.28px at 32px -> -0.96px at 24px -> normal at 14px. Shadow-as-border technique throughout.
- **Scale**: Display 48px -> Section 40px -> Sub 32px -> Card 24px -> Body 18px -> Button 14px -> Caption 12px -> Micro 7px

*Source*: awesome-design-md | 2026-04-06

## Stripe
> sohne-var at whisper-light weight 300 with ss01 -- luxurious confidence through lightness
- **Display**: sohne-var, 300, 56px, line-height 1.03, letter-spacing -1.4px, `"ss01"`
- **Body**: sohne-var, 300-400, 16px, line-height 1.40, `"ss01"`
- **Mono**: SourceCodePro, 500-700, 12px, line-height 2.00
- **Notable**: Weight 300 as headline signature -- the lightest display weight of any major brand. `"ss01"` stylistic set on ALL text, non-negotiable. `"tnum"` for tabular/financial data. Progressive tracking: -1.4px at 56px -> -0.96px at 48px -> normal at 16px. Deep navy (#061b31) headings instead of black. Blue-tinted shadows.
- **Scale**: Display 56px -> Large 48px -> Section 32px -> Sub 26px -> Body 16px -> Caption 13px -> Micro 10px -> Nano 8px

*Source*: awesome-design-md | 2026-04-06

## Linear
> Inter Variable with cv01+ss03 and signature weight 510 -- dark-mode precision engineering
- **Display**: Inter Variable, 510, 72px, line-height 1.00, letter-spacing -1.584px, `"cv01","ss03"`
- **Body**: Inter Variable, 400, 16px, line-height 1.50, `"cv01","ss03"`
- **Mono**: Berkeley Mono, 400, 14px, line-height 1.50
- **Notable**: Signature weight 510 (between regular and medium). OpenType `cv01` (single-story 'a') and `ss03` globally. Three-tier system: 400/510/590. Aggressive display tracking: -1.584px at 72px. Dark-mode-native design with near-white text (#f7f8f8). Luminance stepping for elevation.
- **Scale**: Display 72px -> Large 64px -> Section 48px -> H1 32px -> H2 24px -> H3 20px -> Body 16px -> Small 15px -> Caption 13px -> Label 12px -> Tiny 10px

*Source*: awesome-design-md | 2026-04-06

## Notion
> NotionInter (modified Inter) with 700 bold headlines and warm neutral palette
- **Display**: NotionInter, 700, 64px, line-height 1.00, letter-spacing -2.125px, `"lnum","locl"`
- **Body**: NotionInter, 400, 16px, line-height 1.50
- **Mono**: None specified (product uses monospace internally)
- **Notable**: Four-weight system: 400/500/600/700 -- broader than most. Heavy display compression (-2.125px at 64px). Warm neutral grays with yellow-brown undertones. Badge micro-tracking with positive +0.125px at 12px. Ultra-thin whisper borders (rgba 0.1). Warm white (#f6f5f4) section alternation.
- **Scale**: Display 64px -> Secondary 54px -> Section 48px -> Sub 40px -> Card 22px -> Body Large 20px -> Body 16px -> Caption 14px -> Badge 12px

*Source*: awesome-design-md | 2026-04-06

## Figma
> figmaSans variable with ultra-light weights (320-340) and kerning everywhere
- **Display**: figmaSans, 400, 86px, line-height 1.00, letter-spacing -1.72px, `"kern"`
- **Body**: figmaSans, 320-340, 16-18px, line-height 1.40-1.45, letter-spacing -0.14px
- **Mono**: figmaMono, 400, 12-18px, uppercase, letter-spacing 0.54-0.6px
- **Notable**: Custom variable font with exotic weight stops: 320, 330, 340, 450, 480, 540, 700. Body text lighter than typical 400 (uses 320-340). Negative letter-spacing on everything, even body text (-0.1px to -0.26px). Strictly black-and-white interface chrome. figmaMono in uppercase with positive tracking for structural labels. Dashed 2px focus outlines echoing editor UI.
- **Scale**: Display 86px -> Section 64px -> Sub 26px -> Feature 24px -> Body Large 20px -> Body 16px -> Mono Label 18px -> Mono Small 12px

*Source*: awesome-design-md | 2026-04-06

## Airbnb
> Cereal VF with warm rounded terminals -- cozy marketplace typography
- **Display**: Airbnb Cereal VF, 700, 28px, line-height 1.43
- **Body**: Airbnb Cereal VF, 400, 14px, line-height 1.43
- **Mono**: None specified
- **Notable**: Custom variable font with warm, rounded terminals. Weight range 500-700 for headings (no thin weights). Negative tracking on headings (-0.18px to -0.44px) for intimacy. `"salt"` (stylistic alternates) on specific caption/badge elements. Near-black (#222222) text. Compact type scale (max heading 28px on marketing page). Photography-first with type supporting, not leading.
- **Scale**: Section 28px -> Card 22px -> Sub 21px -> Feature 20px -> UI 16px -> Body 14px -> Small 13px -> Tag 12px -> Badge 11px -> Micro 8px

*Source*: awesome-design-md | 2026-04-06

## Spotify
> SpotifyMixUI (CircularSp derivative) -- compact, bold, designed for scanning playlists
- **Display**: SpotifyMixUITitle, 700, 24px, line-height normal
- **Body**: SpotifyMixUI, 400, 16px, line-height normal
- **Mono**: None specified
- **Notable**: Bold/regular binary (700 or 400, 600 sparingly). Uppercase buttons with wide positive letter-spacing (1.4-2px). Compact sizing range (10-24px). Global script support (Arabic, Hebrew, Cyrillic, Greek, Devanagari, CJK). Separate title font (SpotifyMixUITitle) for section titles. No negative letter-spacing. Dark immersive theme (#121212).
- **Scale**: Title 24px -> Feature 18px -> Body 16px -> Button/Nav 14px -> Small 12px -> Badge 10.5px -> Micro 10px

*Source*: awesome-design-md | 2026-04-06

## Apple
> SF Pro with optical sizing -- letterforms adapt to size context automatically
- **Display**: SF Pro Display, 600, 56px, line-height 1.07, letter-spacing -0.28px
- **Body**: SF Pro Text, 400, 17px, line-height 1.47, letter-spacing -0.374px
- **Mono**: None specified on marketing site
- **Notable**: Optical sizing boundary at 20px (Display above, Text below). Negative letter-spacing at ALL sizes, even body (-0.374px at 17px, -0.224px at 14px, -0.12px at 12px). Extreme line-height range: 1.07 headlines to 2.41 button contexts. Weight restraint: mostly 400 and 600. Binary light/dark section alternation. 980px pill radius for CTA links. Translucent dark glass navigation.
- **Scale**: Display 56px -> Section 40px -> Tile 28px -> Card 21px -> Nav 34px -> Body 17px -> Link 14px -> Micro 12px -> Nano 10px

*Source*: awesome-design-md | 2026-04-06

## Cursor
> Three typographic voices: CursorGothic (display), jjannon serif (editorial), berkeleyMono (code)
- **Display**: CursorGothic, 400, 72px, line-height 1.10, letter-spacing -2.16px
- **Body**: jjannon (serif), 400-500, 17-19px, line-height 1.35-1.50, OpenType `"cswh"` (contextual swashes)
- **Mono**: berkeleyMono, 400, 11-12px, line-height 1.33-1.67
- **Notable**: One of the richest typographic palettes in developer tooling. Gothic compressed display + literary serif body + refined mono code. Warm off-white canvas (#f2f1ed). oklab-space borders for perceptually uniform warm brown edges. CursorGothic uses weight 400 exclusively, relying on size + tracking for hierarchy. jjannon `"cswh"` adds calligraphic quality. Accent orange (#f54e00).
- **Scale**: Display 72px -> Section 36px -> Sub 26px -> Title 22px -> Body Serif 19px -> Body Sans 16px -> Button 14px -> Caption 11px

*Source*: awesome-design-md | 2026-04-06

## Supabase
> Circular with zero-leading hero and developer-console mono labels
- **Display**: Circular, 400, 72px, line-height 1.00
- **Body**: Circular, 400, 16px, line-height 1.50
- **Mono**: Source Code Pro, 400, 12px, uppercase, letter-spacing 1.2px
- **Notable**: Hero text at 1.00 line-height (absolute zero leading) is the signature. Weight restraint: nearly all 400, only 500 for nav/buttons. No bold (700) detected. Negative tracking on cards (-0.16px at 24px). Circular's rounded terminals create warmth in a technical dark interface. Emerald green accent (#3ecf8e). HSL-based translucent color token system.
- **Scale**: Display 72px -> Section 36px -> Card 24px -> Sub 18px -> Body 16px -> Nav/Button 14px -> Small/Code 12px

*Source*: awesome-design-md | 2026-04-06

## Raycast
> Inter with positive letter-spacing on dark -- airy readability against the void
- **Display**: Inter, 600, 64px, line-height 1.10, letter-spacing 0px, OpenType `ss02`, `ss08`, `liga 0`
- **Body**: Inter, 500, 16px, line-height 1.60, letter-spacing +0.2px, OpenType `calt`, `kern`, `liga`, `ss03`
- **Mono**: GeistMono, 400-500, 12-14px, letter-spacing 0.2-0.3px
- **Notable**: Positive letter-spacing (+0.2-0.4px) on body text -- unusual for dark UI, creates airy readability. Weight 500 as body baseline (not 400). macOS-native multi-layer inset shadow system. Extensive OpenType: `ss03` globally, `ss02`+`ss08` on display, `liga 0` on hero headings. Opacity-based hover transitions. Blue-tinted background (#07080a).
- **Scale**: Display 64px -> Section 56px -> Heading 24px -> Card 22px -> Sub 20px -> Body 16px -> Caption 14px -> Small 12px

*Source*: awesome-design-md | 2026-04-06

## Framer
> GT Walsheim with extreme -5.5px tracking at 110px -- spring-loaded compressed headlines
- **Display**: GT Walsheim Framer Medium, 500, 110px, line-height 0.85, letter-spacing -5.5px
- **Body**: Inter Variable, 400, 15px, line-height 1.30, letter-spacing -0.01px, 6+ OpenType features
- **Mono**: Azeret Mono, 400, 10.4px, line-height 1.60
- **Notable**: Most extreme negative tracking of any brand (-5.5px at 110px). Ultra-tight display line-height (0.85). GT Walsheim at weight 500 only -- never bold. Mona Sans (GitHub font) at ultra-light 100 for ethereal accent text. Pure black (#000000) void canvas. Inter with maximalist OpenType (`cv01`, `cv05`, `cv09`, `cv11`, `ss03`, `ss07`). Open Runde for micro badges (9px).
- **Scale**: Display 110px -> Section 85px -> Heading 62px -> Feature 32px -> Card 24px -> Feature Title 22px -> Body 15px -> Caption 14px -> Label 13px -> Small 12px -> Micro Code 10.4px -> Badge 9px -> Micro 7px

*Source*: awesome-design-md | 2026-04-06

## Nothing
> Industrial dot-matrix + Swiss typography -- monochrome instrument panel aesthetic
- **Display**: Doto (variable dot-matrix), 400-700, 36px+, line-height 1.0-1.1, letter-spacing -0.02 to -0.03em
- **Body**: Space Grotesk, 300-500, 16px, line-height 1.5
- **Mono**: Space Mono, 400-700, 11-12px, ALL CAPS, letter-spacing 0.06-0.1em
- **Notable**: Three-font system inspired by Braun/Teenage Engineering. Doto = variable dot-matrix mimicking Nothing's NDot 57 typeface. Space Grotesk + Space Mono by same foundry (Colophon) as Nothing's actual fonts. Labels always Space Mono ALL CAPS with wide tracking. Max 2 font families + 3 sizes + 2 weights per screen. OLED black (#000000) dark mode, warm off-white (#F5F5F5) light mode. No shadows, no gradients. Data as beauty.
- **Scale**: Display XL 72px -> Display LG 48px -> Display MD 36px -> Heading 24px -> Sub 18px -> Body 16px -> Body SM 14px -> Caption 12px -> Label 11px

*Source*: awesome-design-md | 2026-04-06

## Uber
> UberMove Bold headlines + UberMoveText utility -- billboard-force transit typography
- **Display**: UberMove, 700, 52px, line-height 1.23
- **Body**: UberMoveText, 400-500, 16px, line-height 1.25-1.50
- **Mono**: None specified
- **Notable**: Exclusively bold (700) for all headlines -- every heading hits like a billboard. Two fonts with strict roles: UberMove for headings only, UberMoveText for everything else. No letter-spacing, no text-transform, no ornamental treatment anywhere. Tight heading line-heights (1.22-1.40). Pure black (#000000) and pure white only. 999px pill radius on all buttons. Compact, information-dense layouts.
- **Scale**: Display 52px -> Section 36px -> Card 32px -> Sub 24px -> Small Heading 20px -> Nav 18px -> Body 16px -> Caption 14px -> Micro 12px

*Source*: awesome-design-md | 2026-04-06

## Coinbase
> Four-font proprietary family with ultra-tight 1.00 display line-height
- **Display**: CoinbaseDisplay, 400, 80px, line-height 1.00
- **Body**: CoinbaseText, 400, 18px, line-height 1.56
- **Mono**: None specified
- **Notable**: Four-font family (Display, Sans, Text, Icons) -- most comprehensive proprietary set. Display headings at 1.00 line-height for zero-waste density. Weight 400 for display, 600 for UI emphasis. Button labels with +0.16px tracking. `text-transform: lowercase` on some buttons (unusual). 56px pill radius for CTAs. Cool gray secondary surface (#eef0f3) with blue tint.
- **Scale**: Display 80px -> Secondary 64px -> Third 52px -> Section 36px -> Card 32px -> Feature 18px -> Body 16-18px -> Button 16px -> Caption 14px -> Small 13px

*Source*: awesome-design-md | 2026-04-06

## Superhuman
> Super Sans VF with non-standard 460/540 weights -- luxury email typography
- **Display**: Super Sans VF, 540, 64px, line-height 0.96, letter-spacing 0px
- **Body**: Super Sans VF, 460, 16px, line-height 1.50
- **Mono**: None specified (product uses Messina Mono)
- **Notable**: Non-standard variable font weight stops: 460 and 540 sit deliberately between conventional categories. Display line-height 0.96 (below 1.0!) -- lines nearly overlap. Extreme compression/generosity tension: 0.96 display vs 1.50 body. Selective negative tracking: -1.32px at 48px, 0px on body. Only two border-radius values (8px, 16px) in entire system. Warm cream (#e9e5dd) buttons. Single accent: Lavender Glow (#cbb7fb).
- **Scale**: Display 64px -> Section 48px -> Feature 28px -> Sub 26px -> Card 22px -> Heading 20px -> Emphasis 18px -> Body 16px -> Caption 14px -> Micro 12px

*Source*: awesome-design-md | 2026-04-06

## PostHog
> IBM Plex Sans Variable at bold 700-800 -- scrappy startup energy meets technical credibility
- **Display**: IBM Plex Sans Variable, 800, 30px, line-height 1.20, letter-spacing -0.75px
- **Body**: IBM Plex Sans Variable, 400, 16px, line-height 1.50
- **Mono**: Source Code Pro, 500, 14px (code), system monospace stack
- **Notable**: Extra-bold headings (700-800) -- most assertive heading weight of any brand. Generous body line-heights (1.50-1.71) for content-heavy editorial layout. Fractional computed sizes (21.4px, 19.3px) from fluid type system. Uppercase bold labels (18-20px/700) for magazine-editorial category headers. Olive/sage color palette instead of conventional blues. Hidden brand orange (#F54E00) appears only on hover. Warm parchment (#fdfdf8) background.
- **Scale**: Display 30px -> Section 36px -> Feature 24px -> Card 21.4px -> Sub 20px -> Body Emphasis 19.3px -> Label 18px -> Body 16px -> Nav 15px -> Caption 14px -> Small 13px -> Micro 12px

*Source*: awesome-design-md | 2026-04-06

## Resend
> Three-font editorial hierarchy: Domaine serif hero + ABC Favorit geometric sections + Inter body
- **Display**: Domaine Display (Klim), 400, 96px, line-height 1.00, letter-spacing -0.96px, `"ss01","ss04","ss11"`
- **Body**: Inter, 400, 16px, line-height 1.50
- **Mono**: Commit Mono, 400, 14-16px, line-height 1.43-1.50
- **Notable**: Three fonts with strict lane discipline: serif hero, geometric sans sections, readable body. ABC Favorit at -2.8px tracking for section headings. Positive +0.35px tracking on ABC Favorit nav links -- only positive tracking in system. Pure black (#000000) void canvas. Icy blue-tinted frost borders (rgba(214,235,253,0.19)). Multi-color accent scale with numbered CSS variables. OpenType stylistic sets on all display fonts.
- **Scale**: Display 96px -> Section 56px -> Feature 24px -> Sub 20px -> Body 16px -> Nav/Button 14px -> Small 12px -> Micro Code 12px

*Source*: awesome-design-md | 2026-04-06

## Mintlify
> Inter with documentation-grade clarity and Geist Mono technical labels
- **Display**: Inter, 600, 64px, line-height 1.15, letter-spacing -1.28px
- **Body**: Inter, 400, 16px, line-height 1.50
- **Mono**: Geist Mono, 500-600, 10-12px, uppercase, letter-spacing 0.6px
- **Notable**: Clean two-font system optimized for documentation readability. Three weights only: 400/500/600 (no bold). Uppercase Geist Mono labels with positive tracking (0.6px) as hierarchy signal. Brand green (#18E299) used sparingly. Ultra-round corners (16px cards, 24px featured, 9999px pills). 5% opacity borders as primary separation. Atmospheric green-white gradient hero. White-on-white throughout with no gray sections.
- **Scale**: Display 64px -> Section 40px -> Sub 24px -> Card Title 20px -> Body Large 18px -> Body 16px -> Button 15px -> Link/Caption 14px -> Label 13px -> Mono 12px -> Mono Micro 10px

*Source*: awesome-design-md | 2026-04-06
