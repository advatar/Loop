from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

from .core import Config, LoopError, Runner


EXAMPLE = '''[loop]
goal = """Replace this with a measurable goal and acceptance conditions."""
max_iterations = 8
max_minutes = 60
step_timeout_seconds = 900
state_dir = ".loop"

[executor]
provider = "codex" # or "claude"; command = ["my-agent", "{prompt}"] also works

[verifier]
provider = "claude" # use a different agent when available
pass_marker = "LOOP_VERDICT: PASS"
'''


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="agent-loop", description="Run bounded, verified agent loops")
    result.add_argument("--config", default="loop.toml")
    sub = result.add_subparsers(dest="action", required=True)
    sub.add_parser("init", help="write an example loop.toml")
    run = sub.add_parser("run", help="start a loop")
    run.add_argument("--resume", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    sub.add_parser("status", help="show the most recent state")
    return result


def load(path: Path) -> Config:
    with path.open("rb") as stream:
        return Config.from_dict(tomllib.load(stream))


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    path = Path(args.config).resolve()
    try:
        if args.action == "init":
            if path.exists():
                raise LoopError(f"refusing to overwrite {path}")
            path.write_text(EXAMPLE)
            print(path)
            return 0
        config = load(path)
        runner = Runner(config, path.parent)
        if args.action == "status":
            state = runner.load()
            print(json.dumps(state.__dict__ if state else {"status": "NOT_STARTED"}, indent=2))
            return 0
        state = runner.run(resume=args.resume, dry_run=args.dry_run)
        print(json.dumps(state.__dict__, indent=2))
        return 0 if state.status in {"PASSED", "DRY_RUN"} else 2
    except (LoopError, FileNotFoundError, tomllib.TOMLDecodeError) as exc:
        print(f"agent-loop: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
