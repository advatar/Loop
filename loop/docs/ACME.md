# Acme integration

Keep Loop as an optional worker adapter, not part of Acme's governance kernel.
Acme implements this boundary in `comcmd.workers.loop.LoopWorker`: it maps a
`TaskEnvelope` to a policy-owned Loop configuration, runs a bounded `Runner` in
a persistent task/step-specific repository clone, and translates the terminal
state into a `WorkerResult`:

| Loop status | Acme worker status | Meaning |
|---|---|---|
| `PASSED` | `ok` | Return state and verifier evidence as the artifact |
| `EXHAUSTED`, `STOPPED` | `deferred` | No false success; operator can inspect/resume |
| `FAILED` | `error` | Return the reason in usage metadata |

Acme treats `deferred` as `FAILED_RETRYABLE`; it does not emit
`step_succeeded`. The deferred artifact and Loop run ID are recorded in the
event stream, and a `STOPPED`/incomplete run resumes from the same workspace.
Terminal `PASSED`, `EXHAUSTED`, and `FAILED` states are reused rather than
silently spending another iteration budget.

The adapter must not bypass Acme's capability gateway. Loop may modify its
isolated working tree as an agent worker, but consequential effects still need
to become separate `ActionIntent`s and flow through Acme approvals and its
idempotent executor. Acme owns provider selection, hard limits, state paths, and
the child-process environment allowlist; task input cannot supply commands.

Install Acme with its `loop` optional extra and inject `LoopWorker` through
`build_runner(..., worker=...)`, or use `comcmd run --worker loop`. The worker
runtime still needs OS/container-level filesystem, credential, and network
isolation. Environment filtering and model permission modes are not themselves
a complete security boundary.
