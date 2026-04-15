# persona-sim setup (first-time only)

Dependencies live in a dedicated venv next to the data dir (NOT inside the skill, so sharing the skill doesn't ship secrets or packages):

```bash
python3 -m venv ~/.claude/data/personas/.venv
~/.claude/data/personas/.venv/bin/pip install -r ~/.claude/skills/persona-sim/requirements.txt
```

## Config

Copy `~/.claude/data/personas/config.json` template and fill in your own key. `provider` field selects the active gateway. Supported `api_style`: `anthropic` (native or Colorist-routed) or `openai` (OpenRouter, vLLM, etc.).

## Running

```bash
~/.claude/data/personas/.venv/bin/python ~/.claude/skills/persona-sim/scripts/smoke_test.py
```

Scripts do NOT use global Python — always call the venv's interpreter.

## For Claude Code / agent use

Set an env var so `llm_router` finds the config even from subagent cwd:

```bash
export PERSONA_SIM_CONFIG=~/.claude/data/personas/config.json
```

## Data fetch (when you actually need it)

```bash
~/.claude/data/personas/.venv/bin/python -m persona_sim.fetch nemotron_usa
```

Datasets are NOT bundled with the skill — each user fetches per manifest.
