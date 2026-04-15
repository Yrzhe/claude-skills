# yrzhe Claude Code Skills

A collection of powerful Claude Code skills and plugins by [@yrzhe](https://x.com/yrzhe_top).

## Installation

### Option 1: Via Plugin Marketplace

Add this marketplace to your Claude Code:

```bash
/plugin marketplace add yrzhe/claude-skills
```

Then install any plugin you want:

```bash
/plugin install intelligent-web-scraper@yrzhe-skills
```

### Option 2: Manual Installation

If the plugin command doesn't work, you can manually copy the skill files:

1. Clone or download this repository
2. Copy the skill folder to your Claude skills directory:

**macOS / Linux:**
```bash
cp -r plugins/intelligent-web-scraper/skills/intelligent-web-scraper ~/.claude/skills/
```

**Windows (PowerShell):**
```powershell
Copy-Item -Recurse plugins\intelligent-web-scraper\skills\intelligent-web-scraper $env:USERPROFILE\.claude\skills\
```

3. Restart Claude Code to load the new skill

## Available Plugins

### intelligent-web-scraper

Self-learning intelligent web scraper agent that automatically analyzes page structure, handles pagination, anti-blocking, and discovers article series. No user configuration needed - AI decides everything.

**Features:**
- Intelligent page analysis and data extraction
- Smart pagination handling (page numbers, infinite scroll, load more)
- Detail link following for complete data
- Anti-blocking with adaptive delays
- Series/chapter discovery
- Self-learning system that remembers successful patterns
- Resume capability for interrupted scrapes
- Concurrent scraping with rate limiting
- Local browser support (preserve login sessions)

**Usage:**
```
/intelligent-web-scraper
```

Then provide a URL to scrape and let the AI handle everything.

### lenny-advisor

Product and business diagnostic advisor powered by distilled wisdom from **289 Lenny's Podcast guests** and **348 newsletter articles**. Not a knowledge dump — an active advisor that diagnoses your real problem before delivering expert frameworks.

**Features:**
- Diagnose → Probe → Deliver methodology (asks before answering)
- 18 topic areas: growth, pricing, PMF, positioning, hiring, leadership, metrics, fundraising, marketplace, AI strategy, and more
- 40 deep expert profiles (Shreyas Doshi, Elena Verna, April Dunford, Rahul Vohra, etc.)
- 3-layer progressive loading (minimal token usage)
- Companion workflow with [dbskill](https://github.com/dontbesilent2025/dbskill) and [gstack](https://github.com/garrytan/gstack)

**Install:**
```bash
/plugin install lenny-advisor@yrzhe-skills
```

**Manual install:**
```bash
cp -r plugins/lenny-advisor/skills/lenny-advisor ~/.claude/skills/
```

The skill activates automatically when you discuss product decisions, business strategy, growth, pricing, or any product/business topic.

### persona-sim

Simulate feedback from **census-grounded virtual populations**. Panel-score your product / copy / pricing, predict votes with IPF post-stratification, or run what-if social-sandbox experiments — before paying for real user research. Backed by [NVIDIA Nemotron-Personas](https://huggingface.co/datasets/nvidia/Nemotron-Personas) (1M US Census-aligned synthetic people) and methodology from [Park et al. 2024](https://arxiv.org/abs/2411.10109).

**Features:**
- 4 skills in one plugin: `persona-sim` (core engine) + `product-feedback-sim` (SGO A/B ranking) + `vote-predict` (policy/voting with IPF) + `social-sandbox` (what-if experiments)
- SGO (Semantic Gradient Optimization) with **anchored counterfactuals** — causal attribution, not independent re-scoring
- Persuadable-middle identification (score 4-7 only) to avoid wasting LLM calls on extremes
- IPF post-stratification to reweight panels to real-population marginals (PUMS-ready)
- **Bias audit** with 4 probe types (framing, acquiescence, order, authority) — flags when the simulation under-represents human biases
- 6-suite eval score card (GSS attitudes, Big Five norms, test-retest, diversity, demo-correlation, bias-audit)
- HuggingFace streaming — no local dataset download required for MVP
- Multi-provider LLM routing: native Anthropic, Anthropic-compatible gateways, OpenAI-compatible gateways

**Install:**
```bash
/plugin install persona-sim@yrzhe-skills
```

**Manual install:**
```bash
cp -r plugins/persona-sim/skills/persona-sim ~/.claude/skills/
cp -r plugins/persona-sim/skills/product-feedback-sim ~/.claude/skills/
cp -r plugins/persona-sim/skills/vote-predict ~/.claude/skills/
cp -r plugins/persona-sim/skills/social-sandbox ~/.claude/skills/
```

**First-time setup:** see `plugins/persona-sim/skills/persona-sim/SETUP.md` — you need to create `~/.claude/data/personas/config.json` (from the provided `config.example.json`) with your LLM API key, and a venv for Python dependencies.

**Usage examples:**
- "Score this landing page copy with 30 software developers" → auto-triggers `product-feedback-sim`
- "Predict US support for a $22 minimum wage, by age and education" → auto-triggers `vote-predict`
- "If AI copilots got regulated tomorrow, what would developers do?" → auto-triggers `social-sandbox`
- Direct Python use: `from persona_sim import sampler, sim_engine`

### design-distiller

Scrape any website's design system into a structured **Design MD** + decomposed **design tokens**. Ships with **55 pre-analyzed brand references** (Vercel, Stripe, Linear, Notion, Claude, Figma, Airbnb, Spotify, and more) and an **8-dimension Digest Pool** for mix-and-match composition.

**Features:**
- 4-phase pipeline: Scrape → Analyze → Generate → Digest
- Multi-tier browser support: Browser Use Cloud / Playwright / Chrome Headless / WebFetch fallback
- 9-module Design MD format following [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) standard
- 55 pre-loaded brand references with full design system documentation
- 8-dimension Digest Pool (typography, colors, spacing, components, depth, motion, layouts, philosophy)
- Compose command: mix-and-match from Digest Pool to generate new design systems
- Machine-friendly cross-reference tags for programmatic matching
- Confidence tagging: High (CSS var) / Medium (computed) / Low (visual estimate)

**Install:**
```bash
/plugin install design-distiller@yrzhe-skills
```

**Manual install:**
```bash
cp -r plugins/design-distiller/skills/design-distiller ~/.claude/skills/
```

**Usage:**
```
/design-distiller https://vercel.com              # Full pipeline
/design-distiller compose "Vercel typography + Stripe colors + Linear components"
/design-distiller compare vercel stripe            # Side-by-side comparison
/design-distiller list                             # List all 55 references
```

## Contributing

Feel free to open issues or submit pull requests to improve these skills.

## License

MIT License - see individual plugins for details.

## Author

**yrzhe** - [@yrzhe_top](https://x.com/yrzhe_top)
