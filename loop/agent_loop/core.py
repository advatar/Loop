from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


class LoopError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    goal: str
    executor: tuple[str, ...]
    verifier: tuple[str, ...]
    max_iterations: int = 8
    max_minutes: float = 60
    step_timeout_seconds: int = 900
    pass_marker: str = "LOOP_VERDICT: PASS"
    state_dir: str = ".loop"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Config":
        loop = raw.get("loop", {})
        executor = raw.get("executor", {})
        verifier = raw.get("verifier", {})
        if not all(isinstance(section, dict) for section in (loop, executor, verifier)):
            raise LoopError("loop, executor, and verifier must be TOML tables")
        goal = str(loop.get("goal", "")).strip()
        if not goal:
            raise LoopError("loop.goal must not be empty")
        exec_command = command_for(executor)
        verify_command = command_for(verifier, verifier=True)
        try:
            max_iterations = int(loop.get("max_iterations", 8))
            max_minutes = float(loop.get("max_minutes", 60))
            timeout = int(loop.get("step_timeout_seconds", 900))
        except (TypeError, ValueError) as exc:
            raise LoopError("limits must be numbers") from exc
        if max_iterations < 1 or max_minutes <= 0 or timeout < 1:
            raise LoopError("limits must be positive")
        pass_marker = str(verifier.get("pass_marker", "LOOP_VERDICT: PASS")).strip()
        if not pass_marker or "\n" in pass_marker or "\r" in pass_marker:
            raise LoopError("verifier.pass_marker must be one non-empty line")
        state_dir = str(loop.get("state_dir", ".loop")).strip()
        if not state_dir:
            raise LoopError("loop.state_dir must not be empty")
        return cls(
            goal=goal,
            executor=exec_command,
            verifier=verify_command,
            max_iterations=max_iterations,
            max_minutes=max_minutes,
            step_timeout_seconds=timeout,
            pass_marker=pass_marker,
            state_dir=state_dir,
        )


def command_for(section: dict[str, Any], *, verifier: bool = False) -> tuple[str, ...]:
    if "command" in section:
        value = section["command"]
        if isinstance(value, str):
            result = tuple(shlex.split(value))
            if result:
                return result
        if isinstance(value, list) and all(isinstance(x, str) for x in value):
            result = tuple(value)
            if result and all(result):
                return result
        raise LoopError("command must be a non-empty string or array of non-empty strings")
    provider = section.get("provider")
    if verifier and not provider:
        raise LoopError("verifier requires command or provider")
    if provider == "codex":
        sandbox = "read-only" if verifier else "workspace-write"
        return ("codex", "exec", "--sandbox", sandbox, "--ephemeral", "{prompt}")
    if provider == "claude":
        mode = "plan" if verifier else "acceptEdits"
        return ("claude", "-p", "--permission-mode", mode, "--no-session-persistence", "{prompt}")
    raise LoopError("provider must be 'codex' or 'claude', or supply command")


@dataclass
class State:
    run_id: str
    status: str
    iteration: int
    started_at: str
    updated_at: str
    feedback: str = ""
    reason: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Runner:
    def __init__(
        self, config: Config, root: Path, *, env: Mapping[str, str] | None = None
    ):
        self.config = config
        self.root = root.resolve()
        self.env = dict(env) if env is not None else None
        state_dir = Path(config.state_dir)
        self.state_dir = state_dir if state_dir.is_absolute() else self.root / state_dir
        self.state_path = self.state_dir / "state.json"
        self.events_path = self.state_dir / "events.jsonl"
        self.lock_path = self.state_dir / "run.lock"

    def run(self, *, resume: bool = False, dry_run: bool = False) -> State:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        if dry_run:
            return State("dry-run", "DRY_RUN", 0, now(), now(), reason=self.describe())
        self._acquire_lock()
        try:
            state = self.load() if resume else None
            if state is None or state.status in {"PASSED", "EXHAUSTED", "FAILED"}:
                stamp = now()
                state = State(uuid.uuid4().hex, "RUNNING", 0, stamp, stamp)
                self._save(state, "run_started")
            started = datetime.fromisoformat(state.started_at).timestamp()
            deadline = started + self.config.max_minutes * 60
            while state.iteration < self.config.max_iterations:
                if time.time() >= deadline:
                    return self._stop(state, "EXHAUSTED", "time limit reached")
                state.iteration += 1
                state.updated_at = now()
                self._save(state, "iteration_started")
                execution = self._invoke(
                    self.config.executor, self._execution_prompt(state), deadline=deadline
                )
                if execution.returncode != 0:
                    state.feedback = clip(execution.stderr or execution.stdout)
                    state.history.append({"iteration": state.iteration, "executor_exit": execution.returncode})
                    self._save(state, "executor_failed")
                    continue
                if time.time() >= deadline:
                    return self._stop(state, "EXHAUSTED", "time limit reached")
                verification = self._invoke(
                    self.config.verifier, self._verification_prompt(state), deadline=deadline
                )
                output = (verification.stdout + "\n" + verification.stderr).strip()
                passed = verification.returncode == 0 and self.config.pass_marker in output.splitlines()
                state.feedback = clip(output)
                state.history.append({
                    "iteration": state.iteration,
                    "executor_exit": execution.returncode,
                    "verifier_exit": verification.returncode,
                    "passed": passed,
                })
                self._save(state, "verification_completed")
                if passed:
                    return self._stop(state, "PASSED", "verifier passed")
            return self._stop(state, "EXHAUSTED", "iteration limit reached")
        except KeyboardInterrupt:
            if "state" in locals():
                return self._stop(state, "STOPPED", "interrupted")
            raise
        except Exception as exc:
            if "state" in locals():
                self._stop(state, "FAILED", str(exc))
            raise
        finally:
            self.lock_path.unlink(missing_ok=True)

    def _invoke(
        self, command: tuple[str, ...], prompt: str, *, deadline: float
    ) -> subprocess.CompletedProcess[str]:
        argv = [part.replace("{prompt}", prompt).replace("{root}", str(self.root)) for part in command]
        timeout = min(self.config.step_timeout_seconds, max(0.001, deadline - time.time()))
        try:
            return subprocess.run(
                argv, cwd=self.root, text=True, capture_output=True,
                timeout=timeout, check=False, env=self.env,
            )
        except FileNotFoundError as exc:
            raise LoopError(f"executable not found: {argv[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(argv, 124, exc.stdout or "", "step timed out")

    def _execution_prompt(self, state: State) -> str:
        return (
            "Work autonomously on the goal below. Inspect the repository, make a focused improvement, "
            "and run relevant checks. Do not claim success merely because work was attempted.\n\n"
            f"GOAL:\n{self.config.goal}\n\nITERATION: {state.iteration}/{self.config.max_iterations}\n"
            f"PREVIOUS VERIFIER FEEDBACK:\n{state.feedback or '(first iteration)'}"
        )

    def _verification_prompt(self, state: State) -> str:
        return (
            "Independently verify the repository against the goal below. Inspect the actual files and run "
            "relevant tests. If and only if every acceptance condition is satisfied, include the exact line "
            f"'{self.config.pass_marker}'. Otherwise explain concrete failures and next actions.\n\n"
            f"GOAL:\n{self.config.goal}\n\nITERATION: {state.iteration}"
        )

    def load(self) -> State | None:
        if not self.state_path.exists():
            return None
        return State(**json.loads(self.state_path.read_text()))

    def _save(self, state: State, event: str) -> None:
        state.updated_at = now()
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(asdict(state), indent=2) + "\n")
        os.replace(temporary, self.state_path)
        with self.events_path.open("a") as stream:
            stream.write(json.dumps({"at": state.updated_at, "event": event, "run_id": state.run_id,
                                     "iteration": state.iteration, "status": state.status}) + "\n")

    def _stop(self, state: State, status: str, reason: str) -> State:
        state.status, state.reason = status, reason
        self._save(state, "run_stopped")
        return state

    def _acquire_lock(self) -> None:
        for attempt in range(2):
            try:
                fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError as exc:
                if attempt or self._lock_owner_is_alive():
                    raise LoopError(f"another loop is running ({self.lock_path})") from exc
                self.lock_path.unlink(missing_ok=True)
        with os.fdopen(fd, "w") as stream:
            stream.write(str(os.getpid()))

    def _lock_owner_is_alive(self) -> bool:
        try:
            pid = int(self.lock_path.read_text().strip())
            if pid < 1:
                return False
            os.kill(pid, 0)
        except (FileNotFoundError, ValueError, ProcessLookupError):
            return False
        except PermissionError:
            return True
        return True

    def describe(self) -> str:
        return (f"root={self.root}; executor={shlex.join(self.config.executor)}; "
                f"verifier={shlex.join(self.config.verifier)}; iterations={self.config.max_iterations}; "
                f"minutes={self.config.max_minutes}")


def clip(value: str, limit: int = 12000) -> str:
    return value.strip()[-limit:]
