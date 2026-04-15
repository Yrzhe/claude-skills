# Chinese Persona Pipeline (Scaffold)

No ready-made Chinese persona dataset exists today (as of 2026-04). The workable path:

## Three-source recipe

1. **Demographic skeleton** — 第七次人口普查 (2020) aggregate tables (by province × age × gender × education × occupation)
   - Source: http://www.stats.gov.cn/sj/pcsj/rkpc/7rp/indexch.htm
   - License: Public (government open data), safe to redistribute
   - Use for: IPF marginals + synthetic sampling of demographic profiles

2. **Value/attitude anchor** — WVS Wave 7 China slice (~3036 respondents)
   - Source: https://www.worldvaluessurvey.org/WVSDocumentationWV7.jsp
   - License: Registration required, NO redistribution
   - Use for: LLM seeds for attitude/value fields on synthesized personas

3. **Narrative synthesis** — LLM-generated life biographies
   - Input: (demo profile from #1) + (value profile from #2) + region-specific context
   - Output: 300-800 word first-person narrative like Nemotron's `professional_persona`
   - Cost: ~$0.01-0.05/persona at Haiku rates

## Pipeline stages (not yet implemented)

```
stage_01_sample_demographics.py  # draw age×gender×region×edu×occ from 七普 joint dist
stage_02_attach_values.py        # nearest-neighbor match to WVS respondent, copy value scores
stage_03_generate_narrative.py   # LLM → life story in 中文
stage_04_validate.py             # check narrative contains expected demo markers + no hallucinations
stage_05_export_parquet.py       # write to ~/.claude/data/personas/chinese_synthetic/vNNN.parquet
```

## Eval baseline for Chinese personas

- **CGSS** (中国综合社会调查) — 10K+ households/year, academic-only, no redistribute
  - Use ONLY as eval baseline (JS-divergence vs synthetic panel attitudes)
  - Do not feed into persona generation

## Known gaps before this is usable

- [ ] 七普的 5-way joint distribution (age × gender × region × edu × occ) is not published; need IPF from marginals or assume independence
- [ ] WVS China's 290+ variables need schema mapping to canonical persona fields
- [ ] LLM narrative generation prompts need validation — Chinese names, place names, occupation titles are harder to generate realistically than US equivalents (see Eric Xu's "两千万中国有机人口" first post for naming)
- [ ] No equivalent of Nemotron's `professional_persona` + `sports_persona` etc. multi-domain narratives — needs separate prompt library
- [ ] Values survey validation: ensure LLM doesn't leak US-centric assumptions into Chinese persona responses

## Build order when ready

1. **Write `data/chinese_synthetic/manifest_seed.json`** — 10K demo profiles sampled from 七普, no narratives yet
2. **Attach WVS values** via matching — stage_02
3. **Generate narratives for 1K** — test before scaling to 20K+
4. **Eval vs CGSS 20 attitude questions** — JS divergence baseline
5. **If eval passes, scale to 20K** — enough for Chinese `sample_personas(source="chinese_synthetic")`

This is ~2-4 weeks of work. Low priority unless user has a concrete Chinese simulation project.
