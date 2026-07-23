# Changelog

All notable changes to Loop will be documented here. This project follows
[Semantic Versioning](https://semver.org/).

## 0.1.0 - 2026-07-22

- Add the vendor-neutral `agent-loop` CLI and Python runner.
- Add Codex and Claude Code plugin manifests backed by one shared skill.
- Add atomic state, append-only events, concurrent-run locking, and stale-lock recovery.
- Require bounded iterations, elapsed time, and per-step timeouts.
- Require an independent verifier to exit successfully and emit an exact pass line.
- Add clean-package, CLI, manifest, and runner validation in CI.
