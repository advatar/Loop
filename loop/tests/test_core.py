from pathlib import Path
import os
import tempfile
import time
import unittest

from agent_loop.core import Config, LoopError, Runner, command_for


def config(**loop):
    return Config.from_dict({
        "loop": {"goal": "make it pass", "max_iterations": 2, **loop},
        "executor": {"command": ["true"]},
        "verifier": {"command": ["printf", "LOOP_VERDICT: PASS"]},
    })


class CoreTests(unittest.TestCase):
    def test_config_requires_goal(self):
        with self.assertRaises(LoopError):
            Config.from_dict({"loop": {}, "executor": {"provider": "codex"},
                              "verifier": {"provider": "claude"}})

    def test_config_rejects_empty_or_multiline_marker(self):
        for marker in ("", "PASS\nFAIL"):
            with self.subTest(marker=marker), self.assertRaises(LoopError):
                Config.from_dict({
                    "loop": {"goal": "make it pass"},
                    "executor": {"command": ["true"]},
                    "verifier": {"command": ["true"], "pass_marker": marker},
                })

    def test_config_rejects_invalid_sections_and_limits(self):
        with self.assertRaises(LoopError):
            Config.from_dict({"loop": [], "executor": {}, "verifier": {}})
        with self.assertRaises(LoopError):
            Config.from_dict({
                "loop": {"goal": "make it pass", "max_iterations": "many"},
                "executor": {"command": ["true"]},
                "verifier": {"command": ["true"]},
            })

    def test_command_must_not_be_empty(self):
        for value in ("", [], [""]):
            with self.subTest(value=value), self.assertRaises(LoopError):
                command_for({"command": value})

    def test_codex_provider_commands(self):
        self.assertEqual(
            command_for({"provider": "codex"}),
            ("codex", "exec", "--sandbox", "workspace-write", "--ephemeral", "{prompt}"),
        )
        self.assertEqual(
            command_for({"provider": "codex"}, verifier=True),
            ("codex", "exec", "--sandbox", "read-only", "--ephemeral", "{prompt}"),
        )

    def test_claude_provider_commands(self):
        self.assertEqual(
            command_for({"provider": "claude"}),
            ("claude", "-p", "--permission-mode", "acceptEdits",
             "--no-session-persistence", "{prompt}"),
        )
        self.assertEqual(
            command_for({"provider": "claude"}, verifier=True),
            ("claude", "-p", "--permission-mode", "plan",
             "--no-session-persistence", "{prompt}"),
        )

    def test_command_verifier_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = Runner(config(), root).run()
            self.assertEqual(state.status, "PASSED")
            self.assertEqual(state.iteration, 1)
            self.assertTrue((root / ".loop/state.json").exists())

    def test_missing_marker_exhausts(self):
        value = Config.from_dict({
            "loop": {"goal": "make it pass", "max_iterations": 2},
            "executor": {"command": ["true"]},
            "verifier": {"command": ["true"]},
        })
        with tempfile.TemporaryDirectory() as directory:
            state = Runner(value, Path(directory)).run()
        self.assertEqual(state.status, "EXHAUSTED")
        self.assertEqual(state.iteration, 2)

    def test_marker_must_be_an_exact_line(self):
        value = Config.from_dict({
            "loop": {"goal": "make it pass", "max_iterations": 1},
            "executor": {"command": ["true"]},
            "verifier": {"command": ["printf", "NOT LOOP_VERDICT: PASS"]},
        })
        with tempfile.TemporaryDirectory() as directory:
            state = Runner(value, Path(directory)).run()
        self.assertEqual(state.status, "EXHAUSTED")

    def test_executor_failure_is_recorded(self):
        value = Config.from_dict({
            "loop": {"goal": "make it pass", "max_iterations": 1},
            "executor": {"command": ["sh", "-c", "echo broken >&2; exit 7"]},
            "verifier": {"command": ["true"]},
        })
        with tempfile.TemporaryDirectory() as directory:
            state = Runner(value, Path(directory)).run()
        self.assertEqual(state.status, "EXHAUSTED")
        self.assertEqual(state.feedback, "broken")
        self.assertEqual(state.history[0]["executor_exit"], 7)

    def test_dry_run_does_not_create_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = Runner(config(), root).run(dry_run=True)
            self.assertEqual(state.status, "DRY_RUN")
            self.assertFalse((root / ".loop/state.json").exists())

    def test_stale_lock_is_recovered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_dir = root / ".loop"
            state_dir.mkdir()
            (state_dir / "run.lock").write_text("999999999")
            state = Runner(config(), root).run()
        self.assertEqual(state.status, "PASSED")

    def test_live_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_dir = root / ".loop"
            state_dir.mkdir()
            (state_dir / "run.lock").write_text(str(os.getpid()))
            with self.assertRaises(LoopError):
                Runner(config(), root).run()

    def test_run_time_limit_bounds_a_step(self):
        value = Config.from_dict({
            "loop": {
                "goal": "make it pass",
                "max_iterations": 2,
                "max_minutes": 0.001,
                "step_timeout_seconds": 10,
            },
            "executor": {"command": ["sleep", "1"]},
            "verifier": {"command": ["printf", "LOOP_VERDICT: PASS"]},
        })
        started = time.monotonic()
        with tempfile.TemporaryDirectory() as directory:
            state = Runner(value, Path(directory)).run()
        self.assertEqual(state.status, "EXHAUSTED")
        self.assertEqual(state.reason, "time limit reached")
        self.assertLess(time.monotonic() - started, 0.8)

    def test_runner_can_constrain_child_environment(self):
        marker = "LOOP_TEST_ENV"
        value = Config(
            goal="make it pass",
            executor=("true",),
            verifier=("python3", "-c",
                      f'import os; assert os.getenv("{marker}") == "allowed"; '
                      'print("LOOP_VERDICT: PASS")'),
        )
        with tempfile.TemporaryDirectory() as directory:
            state = Runner(
                value, Path(directory),
                env={"PATH": os.environ["PATH"], marker: "allowed"},
            ).run()
        self.assertEqual(state.status, "PASSED")


if __name__ == "__main__":
    unittest.main()
