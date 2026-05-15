from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fcntl


BACKOFF_SECONDS = (60, 300, 900, 1800)
DEBOUNCE_SECONDS = 30


@dataclass(frozen=True)
class PullResult:
    ok: bool
    fetched: bool
    ahead_local: int
    ahead_remote: int
    conflicts: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class PushResult:
    ok: bool
    pushed: bool
    committed: bool
    skipped: bool
    ahead_local: int
    ahead_remote: int
    commit: str | None = None
    error: str | None = None


class Sync:
    def __init__(self, root_dir: Path, device_id: str) -> None:
        self.root_dir = Path(root_dir)
        self.device_id = device_id
        self.state_dir = self.root_dir / "state"
        self.lock_path = self.state_dir / "sync.lock"
        self.state_path = self.state_dir / "sync-state.json"

    def pull(self) -> PullResult:
        with self._locked():
            blocked = self._backoff_error()
            if blocked:
                return PullResult(False, False, 0, 0, error=blocked)
            return self._pull_locked()

    def push(
        self,
        *,
        force: bool = False,
        batch_threshold_events: int = 50,
        batch_threshold_bytes: int = 1 << 20,
    ) -> PushResult:
        with self._locked():
            blocked = self._backoff_error()
            if blocked and not force:
                return PushResult(False, False, False, True, 0, 0, error=blocked)

            committed = False
            commit_sha: str | None = None
            try:
                self._ensure_repo()
                event_count, dirty_bytes = self._dirty_pool_stats()
                if self._is_dirty():
                    message = (
                        f"append pool events: {self.device_id} "
                        f"{datetime.now(timezone.utc).date().isoformat()} {event_count}"
                    )
                    self._git(["add", "-A"])
                    self._git(
                        [
                            "-c",
                            "user.name=agentlog",
                            "-c",
                            "user.email=agentlog@example.invalid",
                            "commit",
                            "-m",
                            message,
                        ]
                    )
                    committed = True
                    commit_sha = self._git(["rev-parse", "--short", "HEAD"]).stdout.strip()

                if (
                    not force
                    and event_count < batch_threshold_events
                    and dirty_bytes < batch_threshold_bytes
                    and self._seconds_since_last_push() < DEBOUNCE_SECONDS
                ):
                    ahead_local, ahead_remote = self._ahead_counts()
                    self._write_state(success=True, pushed=False)
                    return PushResult(
                        True,
                        False,
                        committed,
                        True,
                        ahead_local,
                        ahead_remote,
                        commit=commit_sha,
                    )

                pull_result = self._pull_locked(ignore_backoff=True)
                if not pull_result.ok:
                    return PushResult(
                        False,
                        False,
                        committed,
                        False,
                        pull_result.ahead_local,
                        pull_result.ahead_remote,
                        commit=commit_sha,
                        error=pull_result.error,
                    )

                ahead_local, ahead_remote = self._ahead_counts()
                if ahead_local <= 0:
                    self._write_state(success=True, pushed=False)
                    return PushResult(
                        True,
                        False,
                        committed,
                        True,
                        ahead_local,
                        ahead_remote,
                        commit=commit_sha,
                    )

                self._git(["push", "-u", "origin", self._branch()])
                ahead_local, ahead_remote = self._ahead_counts()
                self._write_state(success=True, pushed=True)
                return PushResult(
                    True,
                    True,
                    committed,
                    False,
                    ahead_local,
                    ahead_remote,
                    commit=commit_sha,
                )
            except subprocess.CalledProcessError as exc:
                error = _command_error(exc)
            except Exception as exc:
                error = str(exc)

            self._write_state(success=False, error=error)
            ahead_local, ahead_remote = self._safe_ahead_counts()
            return PushResult(
                False,
                False,
                committed,
                False,
                ahead_local,
                ahead_remote,
                commit=commit_sha,
                error=error,
            )

    def sync(self) -> tuple[PullResult, PushResult]:
        pull_result = self.pull()
        push_result = self.push()
        return pull_result, push_result

    def set_remote(self, url: str, *, name: str = "origin") -> None:
        with self._locked():
            self._ensure_repo()
            remotes = self._git(["remote"]).stdout.splitlines()
            if name in remotes:
                self._git(["remote", "set-url", name, url])
            else:
                self._git(["remote", "add", name, url])

    def _pull_locked(self, *, ignore_backoff: bool = False) -> PullResult:
        if not ignore_backoff:
            blocked = self._backoff_error()
            if blocked:
                return PullResult(False, False, 0, 0, error=blocked)

        try:
            self._ensure_repo()
            if not self._has_remote():
                return PullResult(False, False, 0, 0, error="git remote `origin` is not configured")

            fetch = self._git(["fetch", "origin"])
            remote_ref = self._remote_ref()
            if not self._ref_exists(remote_ref):
                self._validate_pool_jsonl()
                ahead_local, ahead_remote = self._ahead_counts()
                self._write_state(success=True, fetched=bool(fetch.stderr or fetch.stdout))
                return PullResult(True, bool(fetch.stderr or fetch.stdout), ahead_local, ahead_remote)

            rebase = self._git(["rebase", remote_ref], check=False)
            conflicts: list[str] = []
            if rebase.returncode != 0:
                conflicts = self._unmerged_paths()
                if conflicts and self._resolve_jsonl_conflicts(conflicts):
                    self._validate_pool_jsonl()
                    self._git(["add", *conflicts])
                    self._git(["rebase", "--continue"], env={"GIT_EDITOR": "true"})
                else:
                    error = rebase.stderr.strip() or rebase.stdout.strip() or "git rebase failed"
                    self._write_state(success=False, error=error)
                    ahead_local, ahead_remote = self._safe_ahead_counts()
                    return PullResult(False, True, ahead_local, ahead_remote, conflicts, error)

            self._validate_pool_jsonl()
            ahead_local, ahead_remote = self._ahead_counts()
            self._write_state(success=True, fetched=bool(fetch.stderr or fetch.stdout), conflicts=conflicts)
            return PullResult(True, bool(fetch.stderr or fetch.stdout), ahead_local, ahead_remote, conflicts)
        except subprocess.CalledProcessError as exc:
            error = _command_error(exc)
        except Exception as exc:
            error = str(exc)

        self._write_state(success=False, error=error)
        ahead_local, ahead_remote = self._safe_ahead_counts()
        return PullResult(False, True, ahead_local, ahead_remote, error=error)

    def _ensure_repo(self) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        if not (self.root_dir / ".git").exists():
            self._run(["git", "init", "-q", str(self.root_dir)])
        self._ensure_line(self.root_dir / ".gitattributes", "pool/**/*.jsonl merge=union\n")
        self._ensure_line(self.root_dir / ".gitattributes", "*.jsonl text eol=lf\n")
        for line in (
            "state/cursors/\n",
            "state/quarantine/\n",
            "state/sync.lock\n",
            "state/sync-state.json\n",
            "state/this-device.json\n",
            "state/daemon.log\n",
            "state/*.log\n",
        ):
            self._ensure_line(self.root_dir / ".gitignore", line)

    def _ensure_line(self, path: Path, line: str) -> None:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if line not in existing.splitlines(keepends=True):
            with path.open("a", encoding="utf-8") as file:
                file.write(line)

    def _validate_pool_jsonl(self) -> None:
        for path in sorted((self.root_dir / "pool").glob("**/*.jsonl")):
            with path.open("r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, 1):
                    if not line.strip():
                        continue
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as exc:
                        rel = path.relative_to(self.root_dir)
                        raise ValueError(f"invalid JSONL in {rel}:{line_number}: {exc}") from exc

    def _resolve_jsonl_conflicts(self, conflicts: list[str]) -> bool:
        for rel in conflicts:
            if not rel.startswith("pool/") or not rel.endswith(".jsonl"):
                return False
            path = self.root_dir / rel
            resolved: list[str] = []
            for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
                if line.startswith("<<<<<<< ") or line.startswith("=======") or line.startswith(">>>>>>> "):
                    continue
                resolved.append(line)
            path.write_text("".join(resolved), encoding="utf-8")
        return True

    def _dirty_pool_stats(self) -> tuple[int, int]:
        event_count = 0
        byte_count = 0
        for rel in self._dirty_paths():
            if not rel.startswith("pool/") or not rel.endswith(".jsonl"):
                continue
            path = self.root_dir / rel
            if not path.exists():
                continue
            byte_count += path.stat().st_size
            with path.open("r", encoding="utf-8") as file:
                event_count += sum(1 for line in file if line.strip())
        return event_count, byte_count

    def _dirty_paths(self) -> list[str]:
        status = self._git(["status", "--porcelain"]).stdout.splitlines()
        paths: list[str] = []
        for line in status:
            if not line:
                continue
            paths.append(line[3:] if line.startswith("R ") else line[3:].strip())
        return paths

    def _is_dirty(self) -> bool:
        return bool(self._git(["status", "--porcelain"]).stdout.strip())

    def _ahead_counts(self) -> tuple[int, int]:
        remote_ref = self._remote_ref()
        if not self._has_remote() or not self._ref_exists(remote_ref):
            result = self._git(["rev-list", "--count", "HEAD"], check=False)
            ahead = int(result.stdout.strip() or "0") if result.returncode == 0 else 0
            return ahead, 0
        result = self._git(["rev-list", "--left-right", "--count", f"HEAD...{remote_ref}"])
        left, right = result.stdout.strip().split()
        return int(left), int(right)

    def _safe_ahead_counts(self) -> tuple[int, int]:
        try:
            return self._ahead_counts()
        except Exception:
            return 0, 0

    def _unmerged_paths(self) -> list[str]:
        result = self._git(["diff", "--name-only", "--diff-filter=U"], check=False)
        return [line for line in result.stdout.splitlines() if line]

    def _has_remote(self) -> bool:
        return "origin" in self._git(["remote"], check=False).stdout.splitlines()

    def _branch(self) -> str:
        result = self._git(["branch", "--show-current"], check=False)
        return result.stdout.strip() or "main"

    def _remote_ref(self) -> str:
        return f"origin/{self._branch()}"

    def _ref_exists(self, ref: str) -> bool:
        return self._git(["show-ref", "--verify", "--quiet", f"refs/remotes/{ref}"], check=False).returncode == 0

    def _seconds_since_last_push(self) -> float:
        state = self._read_state()
        value = state.get("last_push_at")
        if not value:
            return float("inf")
        try:
            last = datetime.fromisoformat(value)
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - last).total_seconds()
        except ValueError:
            return float("inf")

    def _backoff_error(self) -> str | None:
        state = self._read_state()
        failures = int(state.get("failure_count") or 0)
        last_failure = state.get("last_failure_at")
        if failures <= 0 or not last_failure:
            return None
        try:
            failed_at = datetime.fromisoformat(last_failure)
            if failed_at.tzinfo is None:
                failed_at = failed_at.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
        delay = BACKOFF_SECONDS[min(failures - 1, len(BACKOFF_SECONDS) - 1)]
        elapsed = (datetime.now(timezone.utc) - failed_at).total_seconds()
        if elapsed < delay:
            return f"sync backoff active; retry in {int(delay - elapsed)}s"
        return None

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _write_state(
        self,
        *,
        success: bool,
        pushed: bool | None = None,
        fetched: bool | None = None,
        conflicts: list[str] | None = None,
        error: str | None = None,
    ) -> None:
        state = self._read_state()
        now = datetime.now(timezone.utc).isoformat()
        state["updated_at"] = now
        if pushed:
            state["last_push_at"] = now
        if fetched:
            state["last_pull_at"] = now
        if conflicts is not None:
            state["last_conflicts"] = conflicts
        if success:
            state["failure_count"] = 0
            state.pop("last_error", None)
            state.pop("last_failure_at", None)
        else:
            state["failure_count"] = int(state.get("failure_count") or 0) + 1
            state["last_failure_at"] = now
            state["last_error"] = error
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.state_path)

    def _locked(self) -> _FileLock:
        return _FileLock(self.lock_path)

    def _git(
        self,
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return self._run(["git", "-C", str(self.root_dir), *args], check=check, env=env)

    def _run(
        self,
        args: list[str],
        *,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(args, capture_output=True, text=True, check=check, env=merged_env)


class _FileLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._file: Any = None

    def __enter__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a+", encoding="utf-8")
        fcntl.flock(self._file.fileno(), fcntl.LOCK_EX)
        return None

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._file is None:
            return
        fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        self._file.close()


def _command_error(exc: subprocess.CalledProcessError) -> str:
    return (exc.stderr or exc.stdout or str(exc)).strip()
