# Browser Use Cloud — Feature Reference

Complete reference for all free-tier features.

## Anti-Detection & Stealth

All cloud browsers include by default (zero config):
- Canvas, WebGL, fonts, navigator fingerprint randomization per session
- Ad/cookie banner blocking
- Cloudflare / PerimeterX bypass
- Residential proxies (195+ countries)
- Passes CreepJS, BrowserLeaks, and other fingerprint detectors

## Proxies (195+ Countries)

```python
# Set proxy country on browser creation
browser = await client.browsers.create(proxy_country_code="jp")

# Available via WebSocket too
WSS = "wss://connect.browser-use.com?apiKey=KEY&proxyCountryCode=de"

# Disable proxy (e.g. for localhost testing)
browser = await client.browsers.create(proxy_country_code=None)

# Custom proxy (enterprise)
browser = await client.browsers.create(custom_proxy={
    "host": "proxy.example.com",
    "port": 8080,
    "username": "user",
    "password": "pass",
})
```

Common codes: `us` (USA), `gb` (UK), `de` (Germany), `jp` (Japan), `kr` (Korea), `cn` (China), `sg` (Singapore), `au` (Australia).

## Video Recording (MP4)

```python
# Enable on creation
browser = await client.browsers.create(enable_recording=True)

# ... do your work ...

# Stop and get download URL (valid 1 hour)
stopped = await client.browsers.stop(browser.id)
recording_url = stopped.recording_url

# Download the MP4
import urllib.request
urllib.request.urlretrieve(recording_url, "recording.mp4")
```

Agent mode:
```python
result = await client.run("task", enable_recording=True)
urls = await client.sessions.wait_for_recording(result.session.id)
```

## Live Preview

Watch the browser in real-time:
```python
browser = await client.browsers.create()
print(browser.live_url)  # Open in any browser to watch

# Embed in HTML
# <iframe src="{live_url}" style="width:100%;aspect-ratio:16/9;border:none;"></iframe>

# Customize: ?theme=light&ui=false (hide URL bar)
```

## AgentMail (Built-in Email)

Each agent session gets a free disposable email address:
```python
result = await client.run("Sign up on example.com", agentmail=True)
print(result.session.agentmail_email)  # e.g. finehand661@mail.bu.app
```

The agent can automatically read verification emails and 2FA codes sent to this address.

## Browser Profiles (Persistent Login)

Save and reuse browser state (cookies, localStorage, sessions):

```python
# Create a named profile
profile = await client.profiles.create(name="my-twitter")

# First time: login manually via live URL
session = await client.sessions.create(profile_id=profile.id)
print(f"Login here: {session.live_url}")
# ... complete login + 2FA manually ...
await client.sessions.stop(session.id)  # IMPORTANT: saves cookies

# Future sessions: auto-logged-in, no 2FA
browser = await client.browsers.create(profile_id=profile.id)

# Manage profiles
profiles = await client.profiles.list()
await client.profiles.update(profile_id, name="renamed")
await client.profiles.delete(profile_id)
```

## Workspaces (Persistent File Storage)

Store and retrieve files across sessions:

```python
# Create workspace
ws = await client.workspaces.create(name="my-scraper")

# Upload files
await client.workspaces.upload(ws.id, "input.csv")

# Use in agent task
result = await client.run("Process input.csv", workspace_id=str(ws.id))

# Download results
await client.workspaces.download(ws.id, "output.json", to="./output.json")
await client.workspaces.download_all(ws.id, to="./output/")

# List files
files = await client.workspaces.files(ws.id)
for f in files.files:
    print(f"{f.path} ({f.size} bytes)")
```

## Structured Output (Pydantic / Zod)

Get typed, validated results from agent tasks:

```python
from pydantic import BaseModel

class Article(BaseModel):
    title: str
    url: str
    points: int

class HNFeed(BaseModel):
    articles: list[Article]

result = await client.run(
    "Get top 10 Hacker News articles",
    output_schema=HNFeed
)
for a in result.output.articles:
    print(f"{a.title} ({a.points} pts) — {a.url}")
```

TypeScript (Zod v4):
```typescript
import { z } from "zod";
const HNFeed = z.object({
    articles: z.array(z.object({
        title: z.string(),
        url: z.string(),
        points: z.number(),
    }))
});
const result = await client.run("Get top 10 HN articles", { schema: HNFeed });
```

## Cached Scripts (Pay Once, Rerun Free)

Mark parameters with `@{{}}` to enable caching:

```python
# First call: agent explores, creates script (~$0.10, ~60s)
result = await client.run(
    "Get top @{{5}} stories from https://news.ycombinator.com as JSON",
    workspace_id=str(ws.id)
)

# Second call: cached script, different param ($0 LLM, ~5s)
result2 = await client.run(
    "Get top @{{10}} stories from https://news.ycombinator.com as JSON",
    workspace_id=str(ws.id)
)
```

Auto-healing: if the cached script breaks (site layout change), the system detects it and re-runs the full agent automatically.

## Follow-Up Tasks (Multi-Step Sessions)

Keep a session alive for sequential tasks:

```python
session = await client.sessions.create()

# Step 1
result1 = await client.run("Go to amazon.com, search laptops", session_id=session.id)

# Step 2 (browser state carries over)
result2 = await client.run("Open the first result", session_id=session.id)

# Step 3
result3 = await client.run("Extract reviews", session_id=session.id)

await client.sessions.stop(session.id)
```

## 2FA Handling

### Option 1: Profiles (recommended)
Login once, save cookies, reuse forever. See Profiles section above.

### Option 2: Human in the Loop
```python
session = await client.sessions.create()
result = await client.run("Login with user/pass, stop before 2FA", session_id=session.id)
# Human completes 2FA via session.live_url
result2 = await client.run("Continue to dashboard", session_id=session.id)
```

### Option 3: AgentMail (email 2FA)
Agent reads verification codes from its auto-assigned email.

### Option 4: TOTP Secret
```python
result = await client.run(f"""
    Login and when prompted for 2FA:
    import pyotp
    code = pyotp.TOTP("{totp_secret}").now()
    Enter the code.
""")
```

## Webhooks

Configure at `cloud.browser-use.com/settings?tab=webhooks`:

Events:
- `agent.task.status_update` — task status changes

Payload:
```json
{
    "type": "agent.task.status_update",
    "timestamp": "2025-01-15T10:30:00Z",
    "payload": {
        "task_id": "task_abc123",
        "session_id": "session_xyz",
        "status": "idle"
    }
}
```

## Session Limits

- Default inactivity timeout: 15 minutes
- Maximum session duration: 4 hours (240 minutes)
- Free tier: 3 concurrent browsers
- To extend: send a lightweight task to reset the timer

## Models (Agent Mode)

| Model | Input | Output | Best For |
|-------|-------|--------|----------|
| gemini-3-flash | $0.60/1M | $3.60/1M | Simple tasks, speed |
| claude-sonnet-4.6 | $3.60/1M | $18.00/1M | Complex workflows |
| claude-opus-4.6 | $6.00/1M | $30.00/1M | Hardest tasks |

## API Reference

Base URL: `https://api.browser-use.com`

### Browsers (Raw CDP)
- `POST /v3/browsers` — create browser session
- `GET /v3/browsers/{id}` — get session details
- `POST /v3/browsers/{id}/stop` — stop session
- `GET /v3/browsers` — list sessions

### Agent Sessions
- `POST /v3/sessions` — create agent session
- `GET /v3/sessions/{id}` — get status
- `POST /v3/sessions/{id}/task` — send follow-up task
- `POST /v3/sessions/{id}/stop` — stop (strategy: "task" or "session")
- `GET /v3/sessions/{id}/messages` — get agent messages

### Profiles
- `POST /v3/profiles` — create
- `GET /v3/profiles` — list
- `PATCH /v3/profiles/{id}` — update
- `DELETE /v3/profiles/{id}` — delete

### Workspaces
- `POST /v3/workspaces` — create
- `POST /v3/workspaces/{id}/upload` — upload files
- `GET /v3/workspaces/{id}/download/{path}` — download file
- `GET /v3/workspaces/{id}/files` — list files

All requests require header: `X-Browser-Use-API-Key: bu_xxx`
