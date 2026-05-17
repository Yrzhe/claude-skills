"""Command line interface for grok-cli."""

from __future__ import annotations

import argparse
import getpass
import json
import shlex
import sys
import time
from pathlib import Path
from typing import Any

from .auth import AuthError, AuthManager, PROVIDER_API_KEY, PROVIDER_OAUTH
from .client import XaiClient, XaiClientError, compact_response, download_url
from .config import Config, load_config, save_config, set_config_value
from .sessions import SessionStore


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def print_answer(answer: str, citations: list[dict[str, Any]] | None = None) -> None:
    print(answer.strip() or "[empty response]")
    cites = citations or []
    if cites:
        print("\nReferences:")
        seen: set[str] = set()
        for i, c in enumerate(cites, start=1):
            url = str(c.get("url") or "").strip()
            title = str(c.get("title") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            label = title or url
            print(f"  {i}. {label} — {url}")


def cmd_login(args: argparse.Namespace) -> int:
    auth = AuthManager()
    state = auth.login(no_browser=args.no_browser, port=args.port, timeout_seconds=args.timeout)
    print("Login complete.")
    if args.json:
        sanitized = {k: v for k, v in state.items() if k not in {"access_token", "refresh_token", "id_token"}}
        print_json(sanitized)
    return 0


def cmd_logout(args: argparse.Namespace) -> int:
    AuthManager().logout(args.provider)
    print("Logged out." if args.provider is None else f"Removed provider: {args.provider}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    data = AuthManager().status()
    data["config"] = load_config().__dict__
    print_json(data)
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    state = AuthManager().refresh_now()
    sanitized = {k: v for k, v in state.items() if k not in {"access_token", "refresh_token", "id_token"}}
    print_json(sanitized)
    return 0


def cmd_key_set(args: argparse.Namespace) -> int:
    key = args.key or getpass.getpass("xAI API key: ")
    AuthManager().set_api_key(key)
    print("Saved API key fallback in local auth store.")
    return 0


def cmd_config_get(args: argparse.Namespace) -> int:
    cfg = load_config().__dict__
    if args.key:
        if args.key not in cfg:
            raise KeyError(f"Unknown config key: {args.key}")
        print(cfg[args.key])
    else:
        print_json(cfg)
    return 0


def cmd_config_set(args: argparse.Namespace) -> int:
    cfg = set_config_value(args.key, args.value)
    print_json(cfg.__dict__)
    return 0


def _resolve_session(name: str | None) -> tuple[SessionStore, Any, Config]:
    cfg = load_config()
    store = SessionStore()
    session = store.ensure_session(name or cfg.current_session, model=cfg.default_model)
    return store, session, cfg


def cmd_ask(args: argparse.Namespace) -> int:
    store, session, cfg = _resolve_session(args.session)
    client = XaiClient(config=cfg)
    prompt = args.prompt
    input_items = store.build_input(session, prompt, max_messages=args.max_context_messages or cfg.max_context_messages)
    store.add_message(session.id, "user", prompt)
    response = client.create_response(
        input_items=input_items,
        model=args.model or session.model or cfg.default_model,
        store=args.server_store,
    )
    compact = compact_response(response)
    answer = compact["answer"]
    citations = compact.get("inline_citations") or compact.get("citations") or []
    store.add_message(
        session.id,
        "assistant",
        answer,
        provider_response_id=str(compact.get("id") or ""),
        raw_response=response,
        citations=citations,
    )
    if args.json:
        print_json(compact)
    else:
        print_answer(answer, citations)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    store, session, cfg = _resolve_session(args.session)
    client = XaiClient(config=cfg)
    result = client.x_search(
        args.query,
        allowed_x_handles=args.allowed or None,
        excluded_x_handles=args.excluded or None,
        from_date=args.from_date,
        to_date=args.to_date,
        enable_image_understanding=args.images,
        enable_video_understanding=args.videos,
        model=args.model or cfg.search_model,
        store=False,
    )
    if args.save:
        store.add_message(session.id, "user", f"[x_search] {args.query}")
        store.add_message(
            session.id,
            "assistant",
            result.get("answer", ""),
            provider_response_id=result.get("response_id"),
            raw_response=result.get("raw"),
            citations=result.get("inline_citations") or result.get("citations") or [],
        )
    if args.json:
        if args.raw:
            print_json(result)
        else:
            compact = dict(result)
            compact.pop("raw", None)
            print_json(compact)
    else:
        print_answer(result.get("answer", ""), result.get("inline_citations") or result.get("citations") or [])
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    data = XaiClient().list_models()
    print_json(data)
    return 0


_MIME_EXT = {"image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png", "image/webp": "webp"}


def _ext_from_mime(mime: str, default: str) -> str:
    return _MIME_EXT.get((mime or "").strip().lower(), default)


def _confirm_paid(kind: str, approx_note: str, *, assume_yes: bool) -> bool:
    """Paid generation guard. --yes or an interactive 'y' required; agents must pass --yes."""
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        print(
            f"Error: {kind} generation costs real money ({approx_note}). "
            f"Refusing in non-interactive mode without --yes.",
            file=sys.stderr,
        )
        return False
    ans = input(f"{kind} generation costs real money ({approx_note}). Proceed? [y/N] ").strip().lower()
    return ans in {"y", "yes"}


def cmd_image(args: argparse.Namespace) -> int:
    if not _confirm_paid("Image", "~$0.02 per image", assume_yes=args.yes or args.json):
        return 2
    cfg = load_config()
    client = XaiClient(config=cfg)
    result = client.generate_image(args.prompt, model=args.model, n=args.count)
    if not result.get("images"):
        print("Error: no image returned", file=sys.stderr)
        return 2
    saved: list[str] = []
    if not args.no_download:
        ts = time.strftime("%Y%m%d-%H%M%S")
        multi = len(result["images"]) > 1
        for i, img in enumerate(result["images"], start=1):
            ext = _ext_from_mime(img.get("mime_type", ""), "jpg")
            if args.output:
                base = Path(args.output).expanduser()
                dest = base if not multi else base.with_name(f"{base.stem}-{i}{base.suffix or '.' + ext}")
            else:
                dest = Path.cwd() / (f"grok-image-{ts}-{i}.{ext}" if multi else f"grok-image-{ts}.{ext}")
            saved.append(download_url(img["url"], str(dest)))
    payload = {
        "model": result["model"],
        "prompt": result["prompt"],
        "images": result["images"],
        "saved": saved,
        "usage": result["usage"],
    }
    if args.json:
        print_json(payload)
    else:
        for u in result["images"]:
            print(u["url"])
        for s in saved:
            print(f"saved: {s}")
        cost = result["usage"].get("cost_usd_approx")
        if cost is not None:
            print(f"cost ≈ ${cost}")
    return 0


def cmd_video(args: argparse.Namespace) -> int:
    if getattr(args, "fetch", None):
        return cmd_video_fetch(args)
    if not args.prompt:
        print("Error: prompt is required (or use --fetch <request_id>)", file=sys.stderr)
        return 2
    if not _confirm_paid("Video", "~$0.40 per 8s clip, ~20x an image", assume_yes=args.yes or args.json):
        return 2
    cfg = load_config()
    client = XaiClient(config=cfg)
    job = client.generate_video(args.prompt, model=args.model)
    rid = job["request_id"]
    if args.no_wait:
        out = {"request_id": rid, "model": job["model"], "prompt": job["prompt"]}
        print_json(out) if args.json else print(f"request_id: {rid}\nFetch later: grok-cli video --fetch {rid}")
        return 0
    if not args.json:
        print(f"video job {rid} running...", file=sys.stderr)
    result = client.wait_video(
        rid,
        interval=args.poll_interval,
        timeout=args.poll_timeout,
        on_progress=(None if args.json else (lambda s, p: print(f"  {s} {p}%", file=sys.stderr))),
    )
    if not result.get("success"):
        print(f"Error: video job ended with status {result.get('status')}", file=sys.stderr)
        if args.json:
            print_json(result)
        return 2
    saved = ""
    if not args.no_download:
        ts = time.strftime("%Y%m%d-%H%M%S")
        dest = Path(args.output).expanduser() if args.output else Path.cwd() / f"grok-video-{ts}.mp4"
        saved = download_url(result["video"].get("url", ""), str(dest))
    payload = {
        "request_id": rid,
        "model": result.get("model"),
        "prompt": job["prompt"],
        "video": result.get("video"),
        "saved": saved,
        "usage": result.get("usage"),
    }
    if args.json:
        print_json(payload)
    else:
        print(result["video"].get("url", ""))
        if saved:
            print(f"saved: {saved}")
        cost = (result.get("usage") or {}).get("cost_usd_approx")
        if cost is not None:
            print(f"cost ≈ ${cost}")
    return 0


def cmd_video_fetch(args: argparse.Namespace) -> int:
    data = XaiClient().get_video(args.fetch)
    print_json(data)
    return 0


def cmd_session_new(args: argparse.Namespace) -> int:
    store = SessionStore()
    cfg = load_config()
    session = store.ensure_session(args.name, model=args.model or cfg.default_model, system_prompt=args.system)
    if args.use:
        store.use_session(session.name)
    print_json(session.__dict__)
    return 0


def cmd_session_use(args: argparse.Namespace) -> int:
    session = SessionStore().use_session(args.name)
    print(f"Current session: {session.name}")
    return 0


def cmd_session_list(args: argparse.Namespace) -> int:
    print_json(SessionStore().list_sessions())
    return 0


def cmd_session_delete(args: argparse.Namespace) -> int:
    ok = SessionStore().delete_session(args.name)
    print("Deleted." if ok else "Session not found.")
    return 0 if ok else 1


def cmd_session_export(args: argparse.Namespace) -> int:
    text = SessionStore().export_session_markdown(args.name)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(text)
    return 0


def cmd_session_show(args: argparse.Namespace) -> int:
    store = SessionStore()
    session = store.get_session(args.name)
    if not session:
        print("Session not found.")
        return 1
    print_json({"session": session.__dict__, "messages": store.all_messages(session.id)})
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    store, session, cfg = _resolve_session(args.session)
    messages = store.all_messages(session.id)
    if not messages:
        print("No messages to summarize.")
        return 0
    transcript = "\n\n".join(f"{m['role']}: {m['content']}" for m in messages[-args.last:])
    prompt = (
        "Summarize this grok-cli session for future context. Preserve durable facts, user preferences, "
        "open tasks, claims that need citations, and unresolved questions. Keep it concise but useful.\n\n"
        + transcript
    )
    client = XaiClient(config=cfg)
    response = client.create_response(input_items=prompt, model=args.model or cfg.default_model, store=False)
    summary = client.extract_text(response)
    covered = messages[-1]["id"] if messages else None
    store.add_summary(session.id, summary, covered_until_message_id=covered)
    print(summary)
    return 0


def cmd_chat(args: argparse.Namespace) -> int:
    store, session, cfg = _resolve_session(args.session)
    if args.session:
        store.use_session(session.name)
    client = XaiClient(config=cfg)
    print(f"grok-cli chat — session={session.name}, model={args.model or session.model or cfg.default_model}")
    print("Commands: /exit, /search <query>, /session <name>, /summarize, /status")
    while True:
        try:
            line = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in {"/exit", "/quit"}:
            break
        if line.startswith("/session "):
            new_name = line.split(maxsplit=1)[1]
            session = store.use_session(new_name)
            print(f"Current session: {session.name}")
            continue
        if line == "/status":
            print_json({"session": session.__dict__, "config": load_config().__dict__})
            continue
        if line == "/summarize":
            ns = argparse.Namespace(session=session.name, last=50, model=args.model)
            cmd_summarize(ns)
            continue
        if line.startswith("/search "):
            query = line.split(maxsplit=1)[1]
            result = client.x_search(query, model=args.search_model or cfg.search_model)
            store.add_message(session.id, "user", f"[x_search] {query}")
            store.add_message(
                session.id,
                "assistant",
                result.get("answer", ""),
                provider_response_id=result.get("response_id"),
                raw_response=result.get("raw"),
                citations=result.get("inline_citations") or result.get("citations") or [],
            )
            print_answer(result.get("answer", ""), result.get("inline_citations") or result.get("citations") or [])
            continue

        input_items = store.build_input(session, line, max_messages=cfg.max_context_messages)
        store.add_message(session.id, "user", line)
        try:
            response = client.create_response(input_items=input_items, model=args.model or session.model or cfg.default_model, store=args.server_store)
            compact = compact_response(response)
            answer = compact["answer"]
            citations = compact.get("inline_citations") or compact.get("citations") or []
            store.add_message(session.id, "assistant", answer, provider_response_id=compact.get("id"), raw_response=response, citations=citations)
            print("\nGrok> ", end="")
            print_answer(answer, citations)
        except Exception as exc:
            print(f"Error: {exc}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="grok-cli", description="SuperGrok OAuth + xAI Responses + X Search CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("login", help="Log in with xAI / SuperGrok OAuth")
    p.add_argument("--no-browser", action="store_true", help="Print the authorize URL instead of opening a browser")
    p.add_argument("--port", type=int, default=56121, help="Local loopback callback port")
    p.add_argument("--timeout", type=int, default=180, help="Login timeout in seconds")
    p.add_argument("--json", action="store_true", help="Print sanitized token metadata as JSON")
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("logout", help="Remove stored credentials")
    p.add_argument("provider", nargs="?", choices=[PROVIDER_OAUTH, PROVIDER_API_KEY], help="Provider to remove; omit to remove all")
    p.set_defaults(func=cmd_logout)

    p = sub.add_parser("status", help="Show sanitized auth and config status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("refresh", help="Refresh OAuth token now")
    p.set_defaults(func=cmd_refresh)

    p = sub.add_parser("key", help="Manage xAI API key fallback")
    key_sub = p.add_subparsers(dest="key_cmd", required=True)
    kp = key_sub.add_parser("set", help="Store an xAI API key fallback")
    kp.add_argument("key", nargs="?", help="API key; omitted means prompt securely")
    kp.set_defaults(func=cmd_key_set)

    p = sub.add_parser("config", help="Get or set local config")
    cfg_sub = p.add_subparsers(dest="config_cmd", required=True)
    gp = cfg_sub.add_parser("get")
    gp.add_argument("key", nargs="?")
    gp.set_defaults(func=cmd_config_get)
    sp = cfg_sub.add_parser("set")
    sp.add_argument("key")
    sp.add_argument("value")
    sp.set_defaults(func=cmd_config_set)

    p = sub.add_parser("ask", help="Ask Grok once and save to a session")
    p.add_argument("prompt")
    p.add_argument("-s", "--session")
    p.add_argument("--model")
    p.add_argument("--max-context-messages", type=int)
    p.add_argument("--server-store", action="store_true", help="Allow xAI server-side response storage")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("search", help="Search X posts/profiles/threads with Grok x_search")
    p.add_argument("query")
    p.add_argument("-s", "--session")
    p.add_argument("--model")
    p.add_argument("--allowed", nargs="*", help="Only include these X handles, max 10")
    p.add_argument("--excluded", nargs="*", help="Exclude these X handles, max 10")
    p.add_argument("--from", dest="from_date", help="YYYY-MM-DD start date")
    p.add_argument("--to", dest="to_date", help="YYYY-MM-DD end date")
    p.add_argument("--images", action="store_true", help="Enable image understanding for matched posts")
    p.add_argument("--videos", action="store_true", help="Enable video understanding for matched posts")
    p.add_argument("--save", action="store_true", help="Save result into session history")
    p.add_argument("--json", action="store_true")
    p.add_argument("--raw", action="store_true", help="Include raw xAI response when --json is used")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("chat", help="Interactive chat REPL")
    p.add_argument("-s", "--session")
    p.add_argument("--model")
    p.add_argument("--search-model")
    p.add_argument("--server-store", action="store_true")
    p.set_defaults(func=cmd_chat)

    p = sub.add_parser("models", help="List models from xAI")
    p.set_defaults(func=cmd_models)

    p = sub.add_parser("image", help="Generate image(s) with Grok Imagine")
    p.add_argument("prompt")
    p.add_argument("--model", help="Override image model (default: config image_model)")
    p.add_argument("-n", "--count", type=int, default=1, help="How many images (1-10)")
    p.add_argument("-o", "--output", help="Output file path (auto-suffixed when n>1)")
    p.add_argument("--no-download", action="store_true", help="Print URLs only, do not save")
    p.add_argument("--yes", action="store_true", help="Skip the paid-action confirmation")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_image)

    p = sub.add_parser("video", help="Generate a video with Grok Imagine (async, paid ~20x an image)")
    p.add_argument("prompt", nargs="?", help="Prompt (omit when using --fetch)")
    p.add_argument("--fetch", metavar="REQUEST_ID", help="Fetch status/result of an existing video job")
    p.add_argument("--model", help="Override video model (default: config video_model)")
    p.add_argument("-o", "--output", help="Output mp4 path")
    p.add_argument("--no-wait", action="store_true", help="Return request_id immediately, do not poll")
    p.add_argument("--no-download", action="store_true", help="Do not save the mp4 after completion")
    p.add_argument("--poll-interval", type=float, default=6.0, help="Seconds between status polls")
    p.add_argument("--poll-timeout", type=float, default=600.0, help="Max seconds to wait for completion")
    p.add_argument("--yes", action="store_true", help="Skip the paid-action confirmation")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_video)

    p = sub.add_parser("summarize", help="Summarize current or selected session for compact context")
    p.add_argument("-s", "--session")
    p.add_argument("--last", type=int, default=50, help="Number of latest messages to summarize")
    p.add_argument("--model")
    p.set_defaults(func=cmd_summarize)

    p = sub.add_parser("session", help="Manage sessions")
    sess_sub = p.add_subparsers(dest="session_cmd", required=True)
    np = sess_sub.add_parser("new")
    np.add_argument("name")
    np.add_argument("--model")
    np.add_argument("--system")
    np.add_argument("--use", action="store_true")
    np.set_defaults(func=cmd_session_new)
    up = sess_sub.add_parser("use")
    up.add_argument("name")
    up.set_defaults(func=cmd_session_use)
    lp = sess_sub.add_parser("list")
    lp.set_defaults(func=cmd_session_list)
    dp = sess_sub.add_parser("delete")
    dp.add_argument("name")
    dp.set_defaults(func=cmd_session_delete)
    ep = sess_sub.add_parser("export")
    ep.add_argument("name")
    ep.add_argument("-o", "--output")
    ep.set_defaults(func=cmd_session_export)
    shp = sess_sub.add_parser("show")
    shp.add_argument("name")
    shp.set_defaults(func=cmd_session_show)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (AuthError, XaiClientError, KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
