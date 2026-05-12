# agentlog · Setup

Multi-device install. Everything below assumes you have Python 3.11+ and `git`.

## 1. Install agentlog

```bash
git clone https://github.com/YOUR_USER/yrzhe_skill.git ~/code/yrzhe_skill
cd ~/code/yrzhe_skill/plugins/agentlog
pip install -e .
```

Or, if you prefer running it without packaging:

```bash
export PATH="$HOME/code/yrzhe_skill/plugins/agentlog/scripts:$PATH"
```

The `scripts/agentlog` wrapper sets `PYTHONPATH` and dispatches to `src/agentlog/cli.py`.

Verify:

```bash
agentlog --help
```

## 2. Create the pool repo (one time, on any one device)

This is the private GitHub repo that holds your normalized event pool. **Make it private** — it contains the contents of every agent session.

```bash
gh repo create agent-seeds --private --confirm
```

## 3. Initialize on the first device

```bash
agentlog init --repo git@github.com:YOUR_USER/agent-seeds.git
```

This:
- Clones the repo to `~/.agent-seeds/` (override with `AGENTLOG_POOL` env var)
- Generates a stable `device_id` for this machine and writes it to `state/this-device.json`
- Creates `pool/`, `artifacts/`, `state/`, `indexes/` skeleton
- Sets a `.gitattributes` with `pool/**/*.jsonl merge=union` (resolves cross-device append conflicts cleanly)

Smoke test:

```bash
agentlog poll --once --source claude_code
agentlog pool --last 1h
```

You should see your most recent Claude Code session events.

## 4. Initialize on each additional device

Same command — the device_id is generated fresh per machine:

```bash
agentlog init --repo git@github.com:YOUR_USER/agent-seeds.git
agentlog poll --once --source codex
agentlog sync
```

## 5. (Optional) Migrate historical seed data

If you already use the `seed` skill, run:

```bash
agentlog migrate-from-seed --dry-run
agentlog migrate-from-seed
```

This imports `~/.claude/skills/seed/state/sessions/*.md` into the pool as `source_type="claude_code_seed"` events (distinct from live `claude_code` to avoid duplicate-counting).

## 6. (Optional) Install the Claude Code Stop hook

For near-real-time capture (so your most recent turn shows up in `agentlog pool` immediately instead of waiting for the next daemon poll), install the bundled Stop hook:

```bash
cp <agentlog-dir>/hooks/capture-claude-code.sh ~/.claude/hooks/agentlog-stop.sh
chmod +x ~/.claude/hooks/agentlog-stop.sh
```

Then add it to `~/.claude/settings.json` under the `Stop` hook list:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "command": "bash ~/.claude/hooks/agentlog-stop.sh", "type": "command" }
        ],
        "matcher": ""
      }
    ]
  }
}
```

Cost: ~150ms per turn (warm cursor) — the hook only reads new lines from the current session's transcript, not the whole `~/.claude/projects/` tree.

The hook coexists with the `seed` skill's hook — both can run side-by-side without conflict.

## 7. (Optional) Run the daemon

Foreground (good for sanity check):

```bash
agentlog daemon --once
agentlog daemon  # actual loop, Ctrl-C to stop
```

macOS LaunchAgent:

```bash
agentlog daemon install --type launchd --bin "$(which agentlog)" > ~/Library/LaunchAgents/ai.agentlog.daemon.plist
launchctl load ~/Library/LaunchAgents/ai.agentlog.daemon.plist
```

Linux systemd (user):

```bash
mkdir -p ~/.config/systemd/user
agentlog daemon install --type systemd --bin "$(which agentlog)" > ~/.config/systemd/user/agentlog.service
systemctl --user daemon-reload && systemctl --user enable --now agentlog
```

## Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `AGENTLOG_POOL` | Where to store the local pool clone | `~/.agent-seeds/` |
| `CLAUDE_PROJECTS_ROOT` | Where ClaudeCodeAdapter scans for `.jsonl` files | `~/.claude/projects/` |
| `CODEX_SESSIONS_ROOT` | Where CodexAdapter scans for `rollout-*.jsonl` | `~/.codex/sessions/` |

## SSH vs HTTPS for the pool repo

Use SSH if you push frequently. With HTTPS you'll either need to cache a PAT in the macOS keychain (`gh auth setup-git`) or accept periodic prompts.

## Multi-machine merge story

JSONL shards under `pool/dt=YYYY-MM-DD/device=<id>/source=<source>/shard-NNN.jsonl` are *device-scoped* paths — no two devices ever write the same file. The only place merges happen is when a device pulls others' shards, which `merge=union` handles by concatenating both sides.

If you ever see a non-fast-forward push rejection:

```bash
agentlog pull
agentlog push
```
