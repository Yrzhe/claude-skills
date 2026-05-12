from __future__ import annotations

import hashlib
import secrets
import time
import uuid
from datetime import datetime
from typing import Any, NotRequired, TypedDict


SCHEMA_VERSION = "agentlog.event.v0"
MAX_SUMMARY_CHARS = 240
MAX_TEXT_EXCERPT_CHARS = 2_000

SOURCE_TYPES = {"claude_code", "claude_code_seed", "codex", "maestri", "browser_use", "manual"}
ACTOR_KINDS = {"human", "agent", "system"}
ACTION_TYPES = {
    "session_started",
    "session_completed",
    "user_request",
    "agent_response",
    "tool_call",
    "tool_result",
    "file_changed",
    "command_run",
    "note_created",
    "note_updated",
    "message_sent",
    "browser_step",
    "error",
    "checkpoint",
}
ACTION_STATUSES = {"completed", "blocked", "error", "in_progress"}
ARTIFACT_KINDS = {
    "file",
    "url",
    "note",
    "screenshot",
    "terminal",
    "repo",
    "diff",
    "unknown",
}
ARTIFACT_STORAGE = {"git", "external", "local_only"}

REQUIRED_FIELDS = {
    "schema_version",
    "id",
    "source_event_id",
    "timestamp",
    "ingested_at",
    "actor",
    "source_type",
    "source",
    "project",
    "action",
    "summary",
    "payload",
    "artifact_refs",
}


class EventValidationError(ValueError):
    """Raised when an event does not satisfy the v0 schema."""


class ActorV0(TypedDict):
    id: str
    name: str
    kind: str


class SourceV0(TypedDict, total=False):
    device_id: str
    host: str | None
    process_id: str | None
    session_id: str | None


class ProjectV0(TypedDict, total=False):
    name: str
    path: str | None
    id: str | None
    git_remote: str | None
    git_commit: str | None


class ActionV0(TypedDict, total=False):
    type: str
    status: str
    label: str | None


class ArtifactRefV0(TypedDict, total=False):
    kind: str
    uri: str
    storage: str
    sha256: str | None
    bytes: int | None
    mime_type: str | None
    title: str | None
    metadata: dict[str, Any]


class EventV0(TypedDict):
    schema_version: str
    id: str
    source_event_id: str
    timestamp: str
    ingested_at: str
    actor: ActorV0
    source_type: str
    source: SourceV0
    project: ProjectV0
    action: ActionV0
    summary: str
    payload: dict[str, Any]
    artifact_refs: list[ArtifactRefV0]
    session: NotRequired[dict[str, Any]]
    parent_id: NotRequired[str]
    thread_id: NotRequired[str]
    tags: NotRequired[list[str]]
    links: NotRequired[list[dict[str, Any]]]
    metrics: NotRequired[dict[str, Any]]
    privacy: NotRequired[dict[str, Any]]
    dedupe_key: NotRequired[str]
    raw_ref: NotRequired[dict[str, Any]]


def make_event_id() -> str:
    """Return a UUIDv7 string without depending on a third-party package."""
    unix_ms = int(time.time() * 1000)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)

    value = (unix_ms & ((1 << 48) - 1)) << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b
    return str(uuid.UUID(int=value))


def validate(event_dict: dict[str, Any]) -> EventV0:
    missing = sorted(REQUIRED_FIELDS - event_dict.keys())
    if missing:
        raise EventValidationError(f"missing required field(s): {', '.join(missing)}")

    _expect_equal(event_dict["schema_version"], SCHEMA_VERSION, "schema_version")
    _expect_non_empty_string(event_dict["id"], "id")
    _expect_non_empty_string(event_dict["source_event_id"], "source_event_id")
    _expect_rfc3339(event_dict["timestamp"], "timestamp")
    _expect_rfc3339(event_dict["ingested_at"], "ingested_at")

    source_type = event_dict["source_type"]
    if source_type not in SOURCE_TYPES:
        raise EventValidationError(f"bad source_type: {source_type!r}")

    actor = _expect_object(event_dict["actor"], "actor")
    _expect_non_empty_string(actor.get("id"), "actor.id")
    _expect_non_empty_string(actor.get("name"), "actor.name")
    if actor.get("kind") not in ACTOR_KINDS:
        raise EventValidationError(f"bad actor.kind: {actor.get('kind')!r}")

    source = _expect_object(event_dict["source"], "source")
    _expect_non_empty_string(source.get("device_id"), "source.device_id")

    project = _expect_object(event_dict["project"], "project")
    _expect_non_empty_string(project.get("name"), "project.name")

    action = _expect_object(event_dict["action"], "action")
    if action.get("type") not in ACTION_TYPES:
        raise EventValidationError(f"bad action.type: {action.get('type')!r}")
    if action.get("status") not in ACTION_STATUSES:
        raise EventValidationError(f"bad action.status: {action.get('status')!r}")

    summary = event_dict["summary"]
    _expect_non_empty_string(summary, "summary")
    if "\n" in summary or "\r" in summary:
        raise EventValidationError("summary must be a single line")
    if len(summary) > MAX_SUMMARY_CHARS:
        raise EventValidationError("summary exceeds 240 characters")

    payload = _expect_object(event_dict["payload"], "payload")
    text_excerpt = payload.get("text_excerpt")
    if isinstance(text_excerpt, str) and len(text_excerpt) > MAX_TEXT_EXCERPT_CHARS:
        raise EventValidationError("payload.text_excerpt exceeds 2000 characters")

    artifact_refs = event_dict["artifact_refs"]
    if not isinstance(artifact_refs, list):
        raise EventValidationError("artifact_refs must be an array")
    for index, artifact in enumerate(artifact_refs):
        _validate_artifact_ref(artifact, index)

    if "tags" in event_dict and (
        not isinstance(event_dict["tags"], list)
        or not all(isinstance(tag, str) for tag in event_dict["tags"])
    ):
        raise EventValidationError("tags must be a string array")

    return event_dict  # type: ignore[return-value]


def normalize_dedupe_key(event: dict[str, Any]) -> str:
    validate(event)
    source = event["source"]
    action = event["action"]
    summary = " ".join(event["summary"].split())
    raw = "\n".join(
        [
            event["source_type"],
            source["device_id"],
            source.get("session_id") or "",
            action["type"],
            event["timestamp"],
            summary,
        ]
    )
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate_artifact_ref(artifact: Any, index: int) -> None:
    obj = _expect_object(artifact, f"artifact_refs[{index}]")
    if obj.get("kind") not in ARTIFACT_KINDS:
        raise EventValidationError(
            f"bad artifact_refs[{index}].kind: {obj.get('kind')!r}"
        )
    _expect_non_empty_string(obj.get("uri"), f"artifact_refs[{index}].uri")
    if obj.get("storage") not in ARTIFACT_STORAGE:
        raise EventValidationError(
            f"bad artifact_refs[{index}].storage: {obj.get('storage')!r}"
        )
    if "bytes" in obj and obj["bytes"] is not None:
        if not isinstance(obj["bytes"], int) or obj["bytes"] < 0:
            raise EventValidationError(f"artifact_refs[{index}].bytes must be >= 0")


def _expect_equal(value: Any, expected: str, field: str) -> None:
    if value != expected:
        raise EventValidationError(f"{field} must be {expected!r}")


def _expect_non_empty_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise EventValidationError(f"{field} must be a non-empty string")


def _expect_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EventValidationError(f"{field} must be an object")
    return value


def _expect_rfc3339(value: Any, field: str) -> None:
    _expect_non_empty_string(value, field)
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EventValidationError(f"{field} must be RFC3339") from exc
