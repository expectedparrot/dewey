from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dewey.cli import app


class DeweyCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_file(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def invoke(self, args: list[str]):
        previous = Path.cwd()
        os.chdir(self.root)
        try:
            return self.runner.invoke(app, args, catch_exceptions=False, env={})
        finally:
            os.chdir(previous)

    def init_repo(self) -> None:
        result = self.invoke(["init", "--json"])
        self.assertEqual(result.exit_code, 0)

    def add_bib_source(self, filename: str, bibtex: str) -> str:
        bib = self.write_file(filename, bibtex)
        result = self.invoke(["add", "source", str(bib), "--json"])
        self.assertEqual(result.exit_code, 0)
        return json.loads(result.stdout)["source_id"]

    def test_init_add_search_and_doctor(self) -> None:
        bib = self.write_file(
            "sample.bib",
            """@article{smith2024example,
  title={Example Paper},
  author={Smith, Jane},
  year={2024},
  journal={Journal of Tests}
}
""",
        )

        result = self.invoke(["init", "--json"])
        self.assertEqual(result.exit_code, 0)

        result = self.invoke(["add", "source", str(bib), "--json"])
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.stdout)
        source_id = payload["source_id"]

        result = self.invoke(["state", "set", source_id, "reading", "--json"])
        self.assertEqual(result.exit_code, 0)

        result = self.invoke(["notes", "edit", source_id, "--append", "Foundational paper.", "--json"])
        self.assertEqual(result.exit_code, 0)

        result = self.invoke(["search", "Foundational", "--json"])
        self.assertEqual(result.exit_code, 0)
        search_payload = json.loads(result.stdout)
        self.assertEqual(len(search_payload["results"]), 1)
        self.assertEqual(search_payload["results"][0]["source_id"], source_id)

        result = self.invoke(["doctor", "--json"])
        self.assertEqual(result.exit_code, 0)
        doctor_payload = json.loads(result.stdout)
        self.assertEqual(doctor_payload["issues"], [])

    def test_duplicate_bibtex_key_is_rejected(self) -> None:
        bib = self.write_file(
            "duplicate.bib",
            """@article{samekey,
  title={First},
  author={Smith, Jane},
  year={2024}
}
""",
        )

        self.assertEqual(self.invoke(["init"]).exit_code, 0)
        self.assertEqual(self.invoke(["add", "source", str(bib)]).exit_code, 0)

        result = self.invoke(["add", "source", str(bib), "--json"])
        self.assertEqual(result.exit_code, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["error"]["code"], "duplicate_bibtex_key")

    def test_render_md_uses_paper2md_output(self) -> None:
        pdf = self.write_file("paper.pdf", "%PDF-1.4\nfake pdf\n")

        self.init_repo()

        with patch("dewey.repo.convert_pdf_with_paper2md", return_value=("# Title\n\nBody\n", "test-version")):
            result = self.invoke(["add", "source", str(pdf), "--no-md", "--json"])
            self.assertEqual(result.exit_code, 0)
            payload = json.loads(result.stdout)
            source_id = payload["source_id"]

            result = self.invoke(["render", "md", source_id, "--json"])
            self.assertEqual(result.exit_code, 0)

        source_dir = self.root / ".dewey" / "sources" / source_id
        metadata = json.loads((source_dir / "metadata.json").read_text(encoding="utf-8"))
        markdown = (source_dir / "source.md").read_text(encoding="utf-8")

        self.assertEqual(markdown, "# Title\n\nBody\n")
        self.assertEqual(metadata["markdown_status"], "ready")
        self.assertEqual(metadata["markdown_generator"]["name"], "paper2md")
        self.assertEqual(metadata["markdown_generator"]["version"], "test-version")

    def test_bib_commands_update_metadata_and_output(self) -> None:
        self.init_repo()
        source_id = self.add_bib_source(
            "sample.bib",
            """@article{smith2024example,
  title={Example Paper},
  author={Smith, Jane},
  year={2024}
}
""",
        )
        replacement = self.write_file(
            "replacement.bib",
            """@book{smith2025book,
  title={Example Book},
  author={Smith, Jane},
  year={2025},
  publisher={Test Press}
}
""",
        )

        result = self.invoke(["bib", "show", source_id, "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.stdout)["parsed"]["key"], "smith2024example")

        result = self.invoke(["bib", "set", source_id, "--file", str(replacement), "--json"])
        self.assertEqual(result.exit_code, 0)

        result = self.invoke(
            ["bib", "edit", source_id, "--field", "title", "--value", "Revised Book", "--field", "year", "--value", "2026", "--json"]
        )
        self.assertEqual(result.exit_code, 0)

        result = self.invoke(["cite", source_id, "--format", "key", "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.stdout)["citation"], "smith2025book")

        source_dir = self.root / ".dewey" / "sources" / source_id
        metadata = json.loads((source_dir / "metadata.json").read_text(encoding="utf-8"))
        entry = (source_dir / "entry.bib").read_text(encoding="utf-8")
        self.assertEqual(metadata["bibtex_key"], "smith2025book")
        self.assertEqual(metadata["entry_type"], "book")
        self.assertIn("title={Revised Book}", entry)
        self.assertIn("year={2026}", entry)

    def test_state_commands_cover_priority_and_mark_read(self) -> None:
        self.init_repo()
        source_id = self.add_bib_source(
            "state.bib",
            """@article{statepaper,
  title={State Paper},
  author={Reader, Robin},
  year={2024}
}
""",
        )

        self.assertEqual(self.invoke(["state", "set", source_id, "included", "--json"]).exit_code, 0)
        self.assertEqual(self.invoke(["state", "set-priority", source_id, "3", "--json"]).exit_code, 0)
        self.assertEqual(self.invoke(["state", "mark-read", source_id, "--json"]).exit_code, 0)

        result = self.invoke(["state", "show", source_id, "--json"])
        payload = json.loads(result.stdout)
        state = payload["state"]
        self.assertEqual(state["status"], "read")
        self.assertTrue(state["included"])
        self.assertEqual(state["priority"], 3)
        self.assertIsNotNone(state["last_read_at"])

    def test_notes_instructions_and_paths(self) -> None:
        self.init_repo()
        source_id = self.add_bib_source(
            "notes.bib",
            """@misc{notespaper,
  title={Notes Paper},
  year={2024}
}
""",
        )
        notes_file = self.write_file("new_notes.md", "Alpha\nBeta\n")
        instructions_file = self.write_file("instructions.md", "Review carefully.\n")

        self.assertEqual(self.invoke(["notes", "set", source_id, "--file", str(notes_file), "--json"]).exit_code, 0)
        self.assertEqual(self.invoke(["notes", "edit", source_id, "--append", "Gamma", "--json"]).exit_code, 0)
        self.assertEqual(self.invoke(["instructions", "set", "--file", str(instructions_file), "--json"]).exit_code, 0)
        self.assertEqual(self.invoke(["instructions", "append", "Then summarize.", "--json"]).exit_code, 0)

        notes_payload = json.loads(self.invoke(["notes", "show", source_id, "--json"]).stdout)
        instructions_payload = json.loads(self.invoke(["instructions", "show", "--json"]).stdout)
        path_payload = json.loads(self.invoke(["path", source_id, "--notes", "--json"]).stdout)

        self.assertIn("Gamma", notes_payload["notes"])
        self.assertIn("Then summarize.", instructions_payload["instructions"])
        self.assertTrue(path_payload["path"].endswith("notes.md"))

    def test_link_order_and_remove_update_repository_state(self) -> None:
        self.init_repo()
        first = self.add_bib_source(
            "first.bib",
            """@article{firstpaper,
  title={First Paper},
  year={2024}
}
""",
        )
        second = self.add_bib_source(
            "second.bib",
            """@article{secondpaper,
  title={Second Paper},
  year={2025}
}
""",
        )

        self.assertEqual(self.invoke(["link", "add", second, first, "--type", "builds_on", "--json"]).exit_code, 0)
        self.assertEqual(self.invoke(["order", "set", first, second, "--json"]).exit_code, 0)
        self.assertEqual(self.invoke(["order", "add", second, "--before", first, "--json"]).exit_code, 0)

        link_payload = json.loads(self.invoke(["link", "list", first, "--json"]).stdout)
        order_payload = json.loads(self.invoke(["order", "show", "--json"]).stdout)
        self.assertEqual(len(link_payload["incoming"]), 1)
        self.assertEqual(order_payload["order"]["order"][0], second)

        self.assertEqual(self.invoke(["remove", "source", second, "--yes", "--json"]).exit_code, 0)

        status_payload = json.loads(self.invoke(["status", "--json"]).stdout)
        order_payload = json.loads(self.invoke(["order", "show", "--json"]).stdout)
        self.assertEqual(status_payload["counts"]["sources"], 1)
        self.assertEqual(status_payload["counts"]["total_links"], 0)
        self.assertEqual(order_payload["order"]["order"], [first])

    def test_search_filters_and_index_commands(self) -> None:
        self.init_repo()
        first = self.add_bib_source(
            "alpha.bib",
            """@article{alpha2024,
  title={Alpha Scaling},
  author={Alpha, Ada},
  year={2024}
}
""",
        )
        second = self.add_bib_source(
            "beta.bib",
            """@article{beta2025,
  title={Beta Methods},
  author={Beta, Ben},
  year={2025}
}
""",
        )

        self.assertEqual(self.invoke(["state", "set", first, "reading", "--json"]).exit_code, 0)
        self.assertEqual(self.invoke(["notes", "edit", second, "--append", "Contains scaling discussion.", "--json"]).exit_code, 0)
        self.assertEqual(self.invoke(["link", "add", second, first, "--type", "builds_on", "--json"]).exit_code, 0)

        query_payload = json.loads(self.invoke(["search", "--status", "reading", "--json"]).stdout)
        author_payload = json.loads(self.invoke(["search", "--author", "Beta", "--json"]).stdout)
        linked_payload = json.loads(self.invoke(["search", "--linked-to", first, "--json"]).stdout)
        self.assertEqual([item["source_id"] for item in query_payload["results"]], [first])
        self.assertEqual([item["source_id"] for item in author_payload["results"]], [second])
        self.assertEqual([item["source_id"] for item in linked_payload["results"]], [second])

        rebuild = self.invoke(["index", "rebuild", "--json"])
        self.assertEqual(rebuild.exit_code, 0)
        stats_payload = json.loads(self.invoke(["index", "stats", "--json"]).stdout)
        self.assertEqual(stats_payload["stats"]["sources"], 2)
        self.assertEqual(stats_payload["stats"]["links"], 1)

    def test_error_json_for_missing_repo_and_missing_source(self) -> None:
        result = self.invoke(["status", "--json"])
        self.assertEqual(result.exit_code, 3)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "repo_not_found")

        self.init_repo()
        result = self.invoke(["show", "src_missing", "--json"])
        self.assertEqual(result.exit_code, 4)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "source_not_found")


if __name__ == "__main__":
    unittest.main()
