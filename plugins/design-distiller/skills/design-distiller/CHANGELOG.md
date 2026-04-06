# Changelog

## [1.1.0] - 2026-04-06

### Fixed
- **Nothing reference format** — Removed stale YAML frontmatter (`name: nothing-design`, `version: 3.0.0`, `allowed-tools`) from `references/nothing/DESIGN.md`. Added HTML comment explaining why Nothing uses an extended multi-file format instead of the standard 9-module template.

### Added
- **depth.md digest** — New Digest Pool dimension covering shadow systems, elevation techniques, and border-vs-shadow philosophies across all 15 brands. Includes cross-references for shadow-as-border, luminance stepping, frosted glass, blue-tinted shadows, and zero-shadow approaches.
- **Pre-loaded reference documentation** — SKILL.md now explains that the 55 pre-loaded brands lack `screenshots/` and `meta.json` because they were batch-imported from awesome-design-md, not scraped via the full pipeline.
- **Version management rules** — SKILL.md now documents the versioning workflow: check existing version → increment → archive previous → update Digest Pool → log in meta.json.
- **Machine-friendly cross-reference tags** — All 8 digest files now include `[tag:value]` prefixes on cross-reference entries (e.g., `[font:inter]`, `[technique:shadow-as-border]`, `[palette:warm-parchment]`) for programmatic matching during `compose` operations.
- **depth.md entry template** — Added to `prompts/digester.md` so new scrapes decompose Module 6 into the Digest Pool.
- **Motion data coverage warning** — `digests/motion.md` now includes a header note about low data coverage from batch-imported references.

### Changed
- **Tool names updated** — SKILL.md and scraper references now use actual tool patterns (`browser-use_run_session`, `playwright_browser_*`, `websearch_web_search_exa`) instead of abstract names (`ToolSearch`, `mcp__browser-use__*`, `Agent`). `allowed-tools` frontmatter updated accordingly.
- **Compose conflict resolution** — `prompts/digester.md` now uses explicit rules: user specification wins → first-mentioned source wins → present conflicts to user → never average values. Replaced the vague "take middle ground" strategy.
- **Digest Pool structure** — Updated from 7 to 8 dimensions (added `depth.md`), reflected in SKILL.md output structure, `prompts/digester.md` decomposition table, and file listing.

## [1.0.0] - 2026-04-06

### Added
- **4-Phase Pipeline**: Scrape -> Analyze -> Generate -> Digest
- **Browser Use Cloud priority** — Supports Browser Use Cloud / Playwright MCP / Chrome Headless CLI / WebFetch with 4-tier fallback
- **Design MD 9-module format** — Following awesome-design-md standard (Visual Theme, Colors, Typography, Components, Layout, Depth, Do's/Don'ts, Responsive, Agent Guide)
- **Reference Pool** — `references/{slug}/` stores full Design MD + screenshots. Pre-loaded with 55 brands from awesome-design-md + nothing-design-skill
- **Digest Pool** — `digests/` decomposes into 7 dimensions (typography, colors, spacing, components, motion, layouts, philosophy)
- **Compose command** — Mix-and-match from Digest Pool to generate new Design MD
- **JS extraction scripts** — Auto-extract CSS variables, computed styles, font declarations
- **Confidence levels** — High (CSS var) / Medium (computed) / Low (visual estimate)
- **Cross references** — Digest Pool auto-tags cross-site design similarities
- 4 prompt files: scraper.md, analyzer.md, generator.md, digester.md
