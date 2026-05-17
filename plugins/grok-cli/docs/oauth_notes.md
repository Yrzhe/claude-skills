# OAuth implementation notes

`grok-cli login` implements OAuth 2.0 Authorization Code + PKCE:

1. Fetch discovery metadata from xAI's OIDC discovery URL.
2. Generate `state`, `code_verifier`, and `code_challenge`.
3. Bind a loopback listener on `127.0.0.1:56121/callback` by default.
4. Build an authorization URL using the public Hermes/xAI OAuth client id and SuperGrok-related scopes.
5. Open the browser or print the URL with `--no-browser`.
6. Validate callback `state`.
7. Exchange `code` + `code_verifier` for token data.
8. Store token state locally.
9. Refresh before expiration and reactively on 401.

## Remote host login

The callback server binds the host where the CLI is running. For SSH usage, forward the remote callback port to your local machine:

```bash
ssh -N -L 56121:127.0.0.1:56121 user@remote-host
```

Then run on the remote host:

```bash
grok-cli login --no-browser
```

Open the printed URL in your local browser.

## Credential precedence

By default:

1. OAuth bearer from `grok-cli login`
2. `XAI_API_KEY` environment variable
3. stored API key from `grok-cli key set`

Set `prefer_oauth` false to prefer API keys:

```bash
grok-cli config set prefer_oauth false
```

## Security caveat

This package stores tokens in a local file with owner-only permissions where possible. For higher-security environments, replace `AuthManager._save()` / `_load()` with OS keychain integration.
