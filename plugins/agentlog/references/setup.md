# agentlog · Setup

Multi-device install. Everything below assumes you have Python 3.11+ and `git`.

> **If anything below errors, jump to [`troubleshooting.md`](troubleshooting.md)** — it has root-cause + fix for the four most common install failures (`UNKNOWN-0.0.0`, `agentlog: command not found`, `Permission denied (publickey)`, cross-device shard collision).

## 1. Install agentlog

### Option A: pipx (recommended — isolates the package in its own venv)

```bash
# Install pipx itself if you don't have it
python3 -m pip install --user pipx && python3 -m pipx ensurepath

# Then:
git clone https://github.com/YOUR_USER/claude-skills.git ~/code/claude-skills
pipx install ~/code/claude-skills/plugins/agentlog
```

### Option B: editable pip (for hacking the skill source)

```bash
# CRITICAL on Ubuntu/Debian: upgrade build tooling first. The system setuptools
# is often <61 and silently ignores [project] in pyproject.toml, which makes
# `pip install` register the package as UNKNOWN-0.0.0 with no CLI entry point.
pip install --upgrade pip setuptools wheel

git clone https://github.com/YOUR_USER/claude-skills.git ~/code/claude-skills
pip install -e ~/code/claude-skills/plugins/agentlog
```

### Option C: no-install dev mode (skip packaging entirely)

```bash
export PATH="$HOME/code/claude-skills/plugins/agentlog/scripts:$PATH"
```

The `scripts/agentlog` wrapper sets `PYTHONPATH` and dispatches to `src/agentlog/cli.py`. Good for quick edits without re-installing.

### Verify install

```bash
agentlog --help | head -5
```

You should see the subcommand list (`init,status,poll,event,pool,recap,...`). If `agentlog: command not found` appears, also try:

```bash
python3 -m agentlog --help    # works as long as the package is importable
```

If that also fails, see [`troubleshooting.md`](troubleshooting.md) §1.

## 2. Create the pool repo (one time, on any one device)

This is the private GitHub repo that holds your normalized event pool. **Make it private** — it contains the contents of every agent session.

```bash
gh repo create agent-seeds --private --confirm
```

## 2.5 Verify GitHub SSH access on this device

`agentlog init` will `git clone` the pool repo over SSH. On a fresh machine (new VPS, new laptop, freshly reimaged box), check first:

```bash
ssh -T git@github.com
# Expect: "Hi <user>! You've successfully authenticated, but GitHub does not provide shell access."
```

If you see `Permission denied (publickey)`, set up an SSH key on this device:

```bash
ssh-keygen -t ed25519 -C "<descriptive label e.g. yrzhe-vps>" -N "" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
# Paste the public key at https://github.com/settings/keys → "New SSH key"
```

HTTPS is also supported (`agentlog init --repo https://github.com/.../agent-seeds.git`) but requires a Personal Access Token cached in the local credential helper, which is fiddlier than SSH on Linux. SSH is the recommended path.

## 3. Initialize on the first device

> **Cross-device hostname collision warning**: agentlog derives `device_id` from `hostname` by default. If two devices share a hostname (multiple Macs all named `MacBook-Air`, multiple VPSes from the same image), their pool shards will collide and one device will overwrite the other's data. **Set `AGENTLOG_DEVICE_ID` explicitly per device** the first time you set up — see Step 3.5 below.

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

## 3.5 Set an explicit `AGENTLOG_DEVICE_ID` (recommended)

Add to your shell rc (`~/.zshrc` / `~/.bashrc`) so every shell session picks it up:

```bash
export AGENTLOG_DEVICE_ID="<unique-string-per-device>"
# e.g.:
#   export AGENTLOG_DEVICE_ID="mbp-yrzhe-2024"
#   export AGENTLOG_DEVICE_ID="vps-do-sfo"
#   export AGENTLOG_DEVICE_ID="studio-m2"
```

Without this, agentlog falls back to `hostname`, and a hostname collision silently mangles your pool. The variable is read at adapter construction time, so re-running `agentlog init` after setting it is *not* required — but if you've already polled with the wrong device_id, you'll want to `agentlog status` and inspect the device-id of shards under `pool/dt=*/device=*/`.

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
