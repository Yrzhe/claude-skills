# Prompt for Codex or another coding agent

You have access to a local skill named `grok-cli`. Use it when you need Grok chat, SuperGrok OAuth, or X Search.

Install if needed:

```bash
cd grok-cli
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Use these commands:

```bash
grok-cli status
# If not logged in, ask the user to run:
grok-cli login

# Chat:
grok-cli ask "<prompt>" --session "<session-name>" --json

# X Search:
grok-cli search "<query>" --allowed xai --from 2026-05-01 --json --save
```

Rules:

- Never ask the user for their xAI password.
- Never print tokens or API keys.
- Prefer OAuth if available.
- Use `--json` for machine-readable output.
- Use `--save` on searches when the result should become part of the working session.
