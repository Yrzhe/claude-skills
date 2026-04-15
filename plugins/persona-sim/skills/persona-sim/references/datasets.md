# Datasets (see manifest.json for machine-readable version)

| id | source | license | size | default_mode | redistribute |
|---|---|---|---|---|---|
| nemotron_usa | hf://nvidia/Nemotron-Personas | CC-BY-4.0 | 230MB | local | false |
| nemotron_japan | hf://nvidia/Nemotron-Personas-Japan | CC-BY-4.0 | 240MB | local | false |
| nemotron_india | hf://nvidia/Nemotron-Personas-India | CC-BY-4.0 | 230MB | local | false |
| personahub | hf://proj-persona/PersonaHub | research-only | 80MB | local | false |
| nature2025_synpop | zenodo (180+ countries) | CC-BY-4.0 | 20GB | stream | false |
| gss | gss.norc.org | public | varies | ask | false |
| wvs_wave7 | worldvaluessurvey.org | WVS terms | varies | ask | false |
| pums_us_1yr | census.gov ACS | public domain | 500MB | local | true |
| cgss | cgss.ruc.edu.cn | academic, gated | varies | ask | false |

## Field-map design principle

Different datasets have different field names. The sampler projects all rows into a canonical schema (see manifest.json `canonical_schema`). Fields under `narrative:*` are concatenated into the unified `narrative` field — this is the prompt backbone, not the demographic fields.

## Adding a new dataset

1. Add entry to `manifest.json` with source, license, size, default_mode, field_map, redistribute flag.
2. If HF-hosted and standard parquet/jsonl, `fetch.py` handles download automatically.
3. If custom source (gov/academic), set `default_mode: "ask"` — user fetches manually, then sampler picks up the local file.

## Never redistribute

`redistribute: false` datasets must NEVER be committed to the skill repo. When packaging with `/skill-creator package`, the `~/.claude/data/personas/` directory is outside the skill folder, so this is automatic — but verify no data file leaks into `persona-sim/` itself.
