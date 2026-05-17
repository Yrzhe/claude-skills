# Agent usage examples

## Verify login status

```bash
grok-cli status
```

## Ask Grok and parse JSON

```bash
grok-cli ask "Summarize the current state of AI coding agents." --session agent-research --json
```

## Search X and save into session

```bash
grok-cli search "What are people on X saying about Hermes Agent x_search?" --from 2026-05-01 --save --json
```

## Restrict search to accounts

```bash
grok-cli search "latest Grok updates" --allowed xai elonmusk --json
```

## Export research session

```bash
grok-cli session export agent-research -o agent-research.md
```
