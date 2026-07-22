from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

from dewey.cli import app


class DeweyCliStandardsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def invoke(self, args: list[str]):
        previous = Path.cwd()
        os.chdir(self.root)
        try:
            return self.runner.invoke(app, args, catch_exceptions=False, env={})
        finally:
            os.chdir(previous)

    def test_packaged_doc_commands_emit_markdown(self) -> None:
        meta_result = self.invoke(["meta"])
        agent_result = self.invoke(["agent"])
        readme_result = self.invoke(["readme"])

        self.assertEqual(meta_result.exit_code, 0)
        self.assertEqual(agent_result.exit_code, 0)
        self.assertEqual(readme_result.exit_code, 0)
        self.assertIn("# Dewey", meta_result.stdout)
        self.assertIn("# Dewey Agent Guide", agent_result.stdout)
        self.assertIn("# Dewey", readme_result.stdout)

    def test_agent_start_reports_no_project_then_repo_state(self) -> None:
        result = self.invoke(["agent-start", "--json"])
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "no-project")
        self.assertEqual(payload["counts"]["sources"], 0)
        self.assertIn("dewey init", payload["useful_commands"])

        init_result = self.invoke(["init", "--json"])
        self.assertEqual(init_result.exit_code, 0)

        result = self.invoke(["agent-start", "--json"])
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "setup")
        self.assertEqual(payload["counts"]["sources"], 0)
        self.assertEqual(payload["primary_doc"], "AGENT.md")
