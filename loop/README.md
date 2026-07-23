# Loop plugin

A bounded build → verify → revise runner that works as:

- a Codex plugin (`.codex-plugin/plugin.json`),
- a Claude Code plugin (`.claude-plugin/plugin.json`), and
- an independent CLI (`agent-loop`).

Both plugins discover the same `skills/run-loop/SKILL.md`; the actual execution
logic lives in the vendor-neutral `agent_loop` package.

Codex and Claude Code are both first-class hosts and providers. Installing the
plugin in one does not require the other: use `provider = "codex"` for a
Codex-only setup, `provider = "claude"` for a Claude-only setup, or use one as
executor and the other as an independent verifier.

## Is this for you?

Install Loop when you already use a command-line coding agent, can state a
measurable repository goal, and want several autonomous attempts with hard
iteration and time limits. Typical tasks are fixing a failing suite, completing
a bounded refactor, or satisfying a deterministic validation script.

Do not install it expecting a hosted agent service, scheduler, dashboard,
deployment system, merge bot, or a replacement for code review. Do not use it
for vague goals or work whose success cannot be independently observed.

The executor can modify the working tree. Loop stops only when the verifier
passes or a configured limit/failure stops it; it never treats exhaustion as
success. Review the safety model below before your first unattended run.

## Install the CLI

```bash
python3 -m pip install -e .
agent-loop init
```

Run the test suite from this directory with:

```bash
python3 -m unittest discover -s tests -v
```

Edit `loop.toml` so the goal is observable and finite, then preview and run:

```bash
agent-loop run --dry-run
agent-loop run
agent-loop status
```

State is written atomically to `.loop/state.json`; lifecycle events are appended
to `.loop/events.jsonl`. A concurrent-run lock prevents two processes from
operating the same loop.

## Configure providers

Built-in adapters:

```toml
[executor]
provider = "codex"

[verifier]
provider = "claude"
```

The inverse configuration is equally supported:

```toml
[executor]
provider = "claude"

[verifier]
provider = "codex"
```

Built-in verifier adapters run read-only (`codex --sandbox read-only` or Claude
`--permission-mode plan`). Executor adapters receive workspace-write access but
do not bypass the parent CLI's approval or sandbox model.

Swap them, use the same provider twice, or provide arbitrary argv. `{prompt}`
and `{root}` are substituted without a shell:

```toml
[executor]
command = ["my-agent", "--prompt", "{prompt}"]

[verifier]
command = ["sh", "scripts/verify-loop.sh"]
pass_marker = "LOOP_VERDICT: PASS"
```

A verifier passes only when its exit code is zero **and** its output contains
the configured pass marker as an exact line. Deterministic verifier scripts should print that
marker only after every acceptance check succeeds.

## Load as a plugin

For Claude Code development:

```bash
claude --plugin-dir /absolute/path/to/Loop/loop
```

Then invoke `/loop:run-loop` or describe a verifier-driven loop task. For Codex,
install the directory from a local marketplace or use the bundled skill
directly. The Codex manifest is validated by this repository's test workflow.

## Safety model

Loop does not grant permissions, approve side effects, merge code, or hide
failures. The child CLI runs with the permissions of its parent process. Hard
iteration, elapsed-time, and per-step timeout limits are mandatory. A passing
verifier is evidence, not authorization for deployment or other consequential
effects.

## Release status

Loop is currently an alpha release. See [CHANGELOG.md](CHANGELOG.md) for release
notes and [SECURITY.md](SECURITY.md) for the vulnerability-reporting and
execution-safety policy.
