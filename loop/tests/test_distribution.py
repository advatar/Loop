import json
from pathlib import Path
import tomllib
import unittest

import agent_loop


ROOT = Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def test_release_versions_match(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(project["version"], agent_loop.__version__)
        self.assertEqual(project["version"], codex["version"])
        self.assertEqual(project["version"], claude["version"])

    def test_plugin_names_and_skill_paths_match(self):
        for manifest_path in (
            ROOT / ".codex-plugin/plugin.json",
            ROOT / ".claude-plugin/plugin.json",
        ):
            with self.subTest(manifest=manifest_path):
                manifest = json.loads(manifest_path.read_text())
                self.assertEqual(manifest["name"], ROOT.name)
                self.assertTrue((ROOT / manifest["skills"]).is_dir())

    def test_release_documents_exist(self):
        for name in ("README.md", "LICENSE", "CHANGELOG.md", "SECURITY.md"):
            with self.subTest(name=name):
                self.assertGreater((ROOT / name).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
