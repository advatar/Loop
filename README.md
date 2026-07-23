# Loop

**A bounded build → verify → revise runner for coding agents.**

Loop is for developers who want an agent to keep working toward a measurable
repository goal without manually sending the next prompt after every attempt.
You provide the goal, an executor, an independent verifier, and hard resource
limits. Loop repeats until the verifier passes or a limit stops the run.

Loop is packaged as a Codex plugin, a Claude Code plugin, and a standalone
Python CLI. It has no Python runtime dependencies and does not require an
Advatar or Acme service.

## Should you install Loop?

You probably want Loop if all of these are true:

- You already use Codex, Claude Code, or another command-line coding agent.
- Your task has an observable finish line: tests pass, a migration is complete,
  a static check is clean, or a reviewer can evaluate explicit acceptance criteria.
- You want the agent to make several focused attempts without requiring you to
  prompt each attempt manually.
- You are comfortable letting the executor modify the selected working tree.
- You want every run bounded by iteration, elapsed-time, and per-step limits.

Good uses include fixing a failing test suite, completing a bounded refactor,
removing a deprecated API, satisfying a deterministic validation script, and
iterating on a feature with concrete acceptance criteria.

Loop is probably **not** the right tool if:

- The goal is subjective or open-ended, such as “make the product amazing.”
- Success cannot be checked independently.
- The work requires unapproved deployments, purchases, merges, production
  changes, or other consequential external effects.
- You expect a scheduler, hosted service, web dashboard, pull-request bot, or
  multi-repository control plane. Loop is a local runner, not those products.
- You are not prepared to review agent-authored changes before shipping them.

## What installing the plugin gives you

The plugin teaches the host agent how to create, preview, run, resume, and
inspect a Loop configuration. The execution engine is the bundled `agent-loop`
CLI; the skill does not pretend to perform iterations inside one chat response.

A run has five explicit parts:

1. **Trigger** — you, `agent-loop run`, or your own scheduler starts it.
2. **State** — atomic state and append-only events are stored under `.loop/`.
3. **Executor** — a coding agent receives the goal and previous verifier feedback.
4. **Verifier** — another agent or deterministic command inspects the result.
5. **Stop condition** — pass, iteration limit, time limit, step timeout, failure,
   or operator interruption.

Loop does not choose work on its own. It repeatedly works on the goal you put in
`loop.toml`, in the repository containing that file.

## What a run looks like

```text
executor changes repository
          ↓
verifier checks the actual repository
          ↓
PASS ───────────────→ stop with PASSED
FAIL + feedback ────→ next executor attempt
limit reached ──────→ stop with EXHAUSTED
```

`PASSED` requires both a zero verifier exit code and the configured pass marker
as an exact output line. `EXHAUSTED`, `STOPPED`, and `FAILED` are never reported
as success.

## Requirements

- Python 3.11 or newer.
- At least one prompt-taking command-line agent or executor command.
- A verifier command. Using a different agent from the executor is recommended,
  but a deterministic test script is often stronger.
- A working tree you are willing to let the executor modify.

Built-in provider adapters support `codex` and `claude`. They must already be
installed and authenticated. Loop does not provide model access or credentials.

## Codex and Claude support

Loop supports both products in two independent roles:

| Role | Codex | Claude Code |
|---|---|---|
| Plugin host | `.codex-plugin/plugin.json` | `.claude-plugin/plugin.json` |
| Executor | `codex exec` with workspace-write sandbox | `claude -p` with `acceptEdits` permission mode |
| Verifier | `codex exec` with read-only sandbox | `claude -p` with `plan` permission mode |

The host does not lock you to the matching provider. You can load the plugin in
Codex and use Claude as the executor or verifier. You can load it in Claude Code
and use Codex in either role. Both CLIs can also be used together from the
standalone `agent-loop` command.

For stronger verification, use different providers when both are available:

```toml
[executor]
provider = "codex"

[verifier]
provider = "claude"
pass_marker = "LOOP_VERDICT: PASS"
```

To reverse the roles, swap the two provider values. To use only one installed
agent, set both provider values to `codex` or both to `claude`. A deterministic
command can replace either provider.

The release checks keep the two manifest names and versions aligned and assert
the exact built-in command lines for executor and read-only verifier modes. The
Codex manifest is checked with the Codex plugin validator, and the Claude
manifest passes `claude plugin validate loop`.

## Quick start with the CLI

From the distributable [`loop/`](loop/README.md) directory:

```bash
python3 -m pip install -e .
agent-loop init
```

Edit the generated `loop.toml`. Replace the example goal with a measurable goal
and keep every limit finite:

```toml
[loop]
goal = """
Make all tests under tests/ pass without deleting or weakening tests.
Acceptance: python3 -m unittest discover -s tests exits successfully.
"""
max_iterations = 6
max_minutes = 45
step_timeout_seconds = 600

[executor]
provider = "codex"

[verifier]
provider = "claude"
pass_marker = "LOOP_VERDICT: PASS"
```

Preview the resolved commands before allowing changes, then run and inspect:

```bash
agent-loop run --dry-run
agent-loop run
agent-loop status
```

The executor above receives workspace-write access. The built-in verifier runs
read-only. Custom commands run with the permissions of the parent process.

## Use it as a plugin

The distributable [`loop/`](loop/README.md) directory contains both manifests
and the shared [`run-loop` skill](loop/skills/run-loop/SKILL.md).

For Claude Code development:

```bash
claude --plugin-dir /absolute/path/to/Loop/loop
```

Then invoke `/loop:run-loop` or ask Claude to create or operate a bounded,
verifier-driven loop.

Loading Loop in Claude Code does not require Codex unless `provider = "codex"`
appears in `loop.toml`. Likewise, running Loop from Codex does not require Claude
unless `provider = "claude"` appears in the configuration.

Codex plugins are installed from configured plugin marketplaces. Add the
marketplace that distributes Loop, then install `loop` from that marketplace.
If you are developing Loop locally, follow the local-marketplace workflow in
the Codex plugin documentation; Codex loads the installed cached copy rather
than this source directory directly.

**Current alpha distribution status:** this repository contains a validated
Codex manifest but does not yet publish a marketplace catalog. In other words,
the plugin source is ready, but there is not yet a one-command public Codex
installation path. Until a marketplace is published, use the CLI, load the
Claude plugin directly, or package this directory in your own Codex marketplace.

## Safety and trust boundaries

Loop provides bounds and evidence, not a sandbox or deployment approval:

- It never grants permissions or bypasses the host agent's approval policy.
- It does not merge, deploy, purchase, or approve consequential effects.
- Child commands inherit the operating-system permissions of the Loop process.
- A malicious `loop.toml` can name a malicious command; review configuration
  from third parties before running it.
- A verifier pass is evidence that its checks passed, not proof that the change
  is correct or authorization to ship it.
- The built-in runner has no telemetry or hosted service. Configured child
  agents may use their own network services and data policies.

Review the working-tree diff and verifier evidence before accepting any result.
See [`SECURITY.md`](loop/SECURITY.md) for vulnerability reporting.

## Repository layout

- [`loop/`](loop/README.md) — the distributable plugin and Python package.
- [`loop/agent_loop/`](loop/agent_loop/) — vendor-neutral execution engine.
- [`loop/skills/run-loop/`](loop/skills/run-loop/SKILL.md) — shared Agent Skill.
- [`loop/tests/`](loop/tests/) — runner and distribution contract tests.
- [`X.md`](X.md) — the essay that motivated this experiment.

## Relationship to Acme

Loop is a bounded iteration mechanism. Acme/Company Command is a governed
control plane for durable work, capabilities, approvals, and effects. Loop stays
standalone so it works in any repository. Acme can invoke it through the narrow
adapter described in [`loop/docs/ACME.md`](loop/docs/ACME.md); Loop does not need
to import or modify Acme.

## Release status

Loop `0.1.0` is an alpha release. Its configuration and state formats may evolve.
See [`CHANGELOG.md`](loop/CHANGELOG.md) for release notes. The project is licensed
under Apache-2.0.
