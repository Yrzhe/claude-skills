# Troubleshooting

## No xAI credentials available

Run:

```bash
grok-cli login
```

or set:

```bash
export XAI_API_KEY=...
```

or store fallback key:

```bash
grok-cli key set
```

## Authorization timed out

Run login again. The default timeout is 180 seconds:

```bash
grok-cli login --timeout 300
```

## Login from remote server fails

Forward the callback port first:

```bash
ssh -N -L 56121:127.0.0.1:56121 user@remote-host
```

Then run on the remote host:

```bash
grok-cli login --no-browser
```

## State mismatch

Do not reuse an old login URL. Run login again.

## Token refresh failed

Refresh token may have been revoked or rotated. Run:

```bash
grok-cli login
```

## x_search not enabled

Try:

```bash
grok-cli config set search_model grok-4.20-reasoning
```

Then retry search. If it still fails, your account/subscription/model may not have the server-side `x_search` entitlement.

## Isolate state for tests

```bash
export GROK_CLI_HOME=/tmp/grok-cli-test
grok-cli status
```
