# Acme integration

Keep Loop as an optional worker adapter, not part of Acme's governance kernel.
The boundary should map an Acme `TaskEnvelope` to a temporary `loop.toml`, run a
bounded `Runner`, and translate the terminal state into a `WorkerResult`:

| Loop status | Acme worker status | Meaning |
|---|---|---|
| `PASSED` | `ok` | Return state and verifier evidence as the artifact |
| `EXHAUSTED`, `STOPPED` | `deferred` | No false success; operator can inspect/resume |
| `FAILED` | `error` | Return the reason in usage metadata |

The adapter must not bypass Acme's capability gateway. Loop may modify its
isolated working tree as an agent worker, but consequential effects still need
to become `ActionIntent`s and flow through Acme approvals and its idempotent
executor. Persist the Loop run ID in the Acme artifact/event stream so retries
can resume rather than start duplicate loops.

No Acme source change is required for the standalone release. A future
`LoopWorker` can implement the existing `comcmd.workers.api.Worker` protocol and
depend on `agent-loop` as an optional package extra.
