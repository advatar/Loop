# Resume handoff

Last updated: 2026-07-27.

## Current state

Loop is a release-ready alpha plugin and standalone Python CLI for bounded,
externally verified coding-agent work. It supports Codex and Claude Code as
plugin hosts and as independently selectable executor/verifier providers.

The implementation includes:

- finite iteration, elapsed-time, and per-step limits;
- exact-line verifier verdicts;
- atomic state, append-only events, locking, and stale-lock recovery;
- constrained child-process environments for trusted embedding runtimes;
- Codex and Claude plugin manifests backed by one shared skill;
- Acme integration documentation for `comcmd.workers.loop.LoopWorker`.

The important product-positioning decision is now explicit: Codex `/goal` is
the preferred interactive long-running workflow. Loop is differentiated by
provider neutrality, independent/deterministic verification, hard external
bounds, machine-readable state, headless operation, and Acme embedding.

## Validation baseline

```bash
cd /Users/johansellstrom/dev/advatar/Loop
PYTHONPATH=loop python3 -m unittest discover -s loop/tests -v
python3 /Users/johansellstrom/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py loop
claude plugin validate loop
python3 /Users/johansellstrom/.codex/skills/.system/skill-creator/scripts/quick_validate.py loop/skills/run-loop
```

Expected: 18 tests pass; both manifests and the shared skill validate.

## Remaining release work

1. Publish a Codex marketplace catalog so installation becomes one command.
2. Decide whether to retain the current `0.1.0` alpha version or cut the
   constrained-environment/Acme work as `0.1.1`.
3. Run one explicitly authorized live smoke test for each provider pairing;
   automated tests currently avoid paid Codex/Claude execution.
4. Keep README positioning centered on an externally verifiable execution
   harness, not a replacement for Codex `/goal`.

No background Loop process or disposable test workspace is required to resume.
