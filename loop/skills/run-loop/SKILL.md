---
name: run-loop
description: Create, run, resume, or inspect a bounded autonomous coding loop with an explicit verifier and hard resource limits. Use when the user asks to design or operate agent loops, overnight coding runs, iterative build-test-revise cycles, or verifier-driven automation.
---

# Run Loop

Use the bundled `agent-loop` engine; do not simulate iterations in chat.

1. Locate the plugin root from this skill's directory and invoke `python3 -m agent_loop.cli` with that root on `PYTHONPATH`, or use an installed `agent-loop` executable.
2. For a new loop, translate the user's request into a measurable `loop.goal` in `loop.toml`. Include concrete acceptance checks. Run `init` only if no config exists, then edit the generated file.
3. Always keep finite `max_iterations`, `max_minutes`, and `step_timeout_seconds`. Never weaken repository permissions or bypass approvals just to keep a loop moving.
4. Prefer different executor and verifier providers when both are installed. A command verifier is also valid, but wrap it so successful output includes `LOOP_VERDICT: PASS` only after all checks pass.
5. Run `run --dry-run` and show the resolved plan before the first material run unless the user explicitly asked to start immediately.
6. Start with `run`; use `run --resume` only for a prior `STOPPED` or incomplete run. Report the final status and the state path. `PASSED` means the verifier passed; `EXHAUSTED` and `FAILED` are not success.

From the plugin root:

```bash
PYTHONPATH=. python3 -m agent_loop.cli --config /path/to/repo/loop.toml init
PYTHONPATH=. python3 -m agent_loop.cli --config /path/to/repo/loop.toml run --dry-run
PYTHONPATH=. python3 -m agent_loop.cli --config /path/to/repo/loop.toml run
PYTHONPATH=. python3 -m agent_loop.cli --config /path/to/repo/loop.toml status
```

Do not run an unattended loop when the goal is vague, the verifier cannot observe success, or consequential external side effects are required without a separate approval boundary.
