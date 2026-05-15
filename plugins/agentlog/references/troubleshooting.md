# agentlog · Troubleshooting

Four failure modes seen in real second-device installs (Mac → Ubuntu VPS, fresh laptop, etc.) and how to fix each.

---

## §1. `pip install` "succeeds" but the package is `UNKNOWN-0.0.0` and `agentlog` is not on PATH

### Symptom
```
$ pip install -e .
... Successfully installed UNKNOWN-0.0.0

$ which agentlog
(nothing)

$ python3 -m agentlog --help
ModuleNotFoundError: No module named 'agentlog'
```

### Root cause
System `setuptools` is older than **61.0** (the PEP 621 cutoff). When setuptools doesn't recognize `[project]` in `pyproject.toml`, it silently falls back to legacy mode, can't find a `setup.py`, and registers the package as `UNKNOWN-0.0.0`. No `[project.scripts]` entry point gets installed → no `agentlog` command.

Common on Debian / Ubuntu LTS images and any system pip that hasn't been refreshed in a year.

### Fix
```bash
pip install --upgrade pip setuptools wheel
pip uninstall -y UNKNOWN                          # clear the bogus install
pip install -e ~/code/claude-skills/plugins/agentlog
which agentlog                                    # should now resolve
```

If you can't (or don't want to) upgrade system tooling, use the `pipx` install path from `setup.md` Option A — pipx ships its own modern setuptools inside its venv and is immune.

---

## §2. `agentlog: command not found` despite a clean install

### Symptom
```
$ pip show agentlog
Name: agentlog
Version: 0.11.0
... (looks fine)

$ which agentlog
(nothing)
```

### Root cause
The entry point script was installed to a directory that's not on your `PATH`. Common culprits:

- **`pip install --user`** puts scripts in `~/.local/bin/` on Linux or `~/Library/Python/X.Y/bin/` on macOS. Neither is on `PATH` by default.
- **System pip on macOS with brew Python** puts scripts in `/opt/homebrew/bin/` or `/usr/local/bin/` depending on architecture.

### Fix
Find where it landed, then add to `PATH`:

```bash
# Locate the entry point
python3 -c "import sysconfig; print(sysconfig.get_path('scripts'))"

# Add the printed dir to PATH (example for ~/.local/bin)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc   # or ~/.zshrc
source ~/.bashrc
```

Alternatively, skip the entry point and always invoke via `python3 -m agentlog ...` — it works as long as the package is importable.

---

## §3. `agentlog init` fails with `Permission denied (publickey)` or `Repository not found`

### Symptom
```
$ agentlog init --repo git@github.com:YOUR_USER/agent-seeds.git
Cloning git@github.com:YOUR_USER/agent-seeds.git ...
ERROR: git@github.com: Permission denied (publickey).
```

### Root cause
The device has no SSH key registered with GitHub, or the agent-seeds repo doesn't exist on the GitHub account whose key is being offered.

### Fix
Verify SSH first:
```bash
ssh -T git@github.com
```

If that fails, generate a key and register it:
```bash
ssh-keygen -t ed25519 -C "<descriptive label>" -N "" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
# Paste at https://github.com/settings/keys → "New SSH key"
```

If the SSH test passes but the repo "isn't found", make sure you actually ran `gh repo create agent-seeds --private --confirm` from the same GitHub account whose key you registered.

Alternative — use HTTPS with a PAT cached in the credential helper:
```bash
gh auth login   # interactive, sets up credential helper
agentlog init --repo https://github.com/YOUR_USER/agent-seeds.git
```

---

## §4. Two devices with the same hostname overwrite each other's shards

### Symptom
Events you captured on device A are missing after a `pull` from device B, or `agentlog pool` shows duplicate-looking shards under `pool/dt=*/device=<same-id>/`.

### Root cause
Without `AGENTLOG_DEVICE_ID` set, agentlog derives `device_id` from `socket.gethostname()`. Two devices with the same hostname (multiple Macs all named `MacBook-Air`, multiple VPSes from the same image, multiple devs all on `localhost`) produce identical shard paths → `merge=union` concatenates everything into the same file, but two devices appending the same timestamps creates duplicates and confused recap output.

### Fix
Set a unique `AGENTLOG_DEVICE_ID` on each device, persisted in shell rc:

```bash
echo 'export AGENTLOG_DEVICE_ID="mbp-yrzhe-2024"' >> ~/.zshrc   # tailor per device
source ~/.zshrc
```

To recover existing data captured under the colliding ID, manually rename the shard directories in `~/.agent-seeds/pool/dt=*/device=<old>/` to use the new device_id, commit, and push.

---

## §5. `agentlog brief` errors with `ANTHROPIC_API_KEY not set`

### Symptom
```
$ agentlog brief --project agentlog
agentlog: ANTHROPIC_API_KEY not set — `agentlog brief` requires an Anthropic API key.
```

### Root cause
`brief` calls Anthropic's API to distill events with Haiku 4.5; the key is mandatory and read from env.

### Fix
```bash
export ANTHROPIC_API_KEY=sk-ant-...     # get one from https://console.anthropic.com/
# Persist in shell rc so daemon + new shells inherit it
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.zshrc
```

Cost is ~$0.001 per `brief` call with Haiku 4.5 (typical 7-day window, ~50 events).

---

## §6. Cursor adapter emits 0 events on a machine where Cursor is clearly installed

### Symptom
```
$ agentlog poll --once --source cursor
Emitted: 0, skipped: 0
```

### Root cause options
1. Cursor stores its workspace data under a path the adapter doesn't know about. The default is `~/Library/Application Support/Cursor/User/workspaceStorage/` (macOS). On Linux it's `~/.config/Cursor/User/workspaceStorage/`. The default constant in `src/agentlog/adapters/cursor.py` is the macOS path.
2. Cursor's chat key has changed in a newer version (the adapter expects `workbench.panel.aichat.view.aichat.chatdata`).
3. You have only opened Cursor on this machine but never used the AI chat panel.

### Fix
Override the storage root:
```bash
export CURSOR_STORAGE_ROOT="$HOME/.config/Cursor/User/workspaceStorage"   # Linux
agentlog poll --once --source cursor
```

If the schema has drifted, the adapter logs a warning rather than crashing; check stderr for `cursor workspace <hash>: chatdata not valid JSON` style messages and file a fix to `CHATDATA_KEY` in the source.

---

## When to bail out and ask for help

If you've worked through the relevant section above and the failure persists, capture:

```bash
agentlog status
agentlog --help | head -5
python3 -c "import agentlog, sys; print(agentlog.__file__, sys.version)"
which agentlog
pip show agentlog
```

…and open an issue on [github.com/Yrzhe/claude-skills](https://github.com/Yrzhe/claude-skills/issues) with that output. Almost every install-time failure I've seen so far is one of §1–§4.
