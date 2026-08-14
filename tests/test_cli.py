from __future__ import annotations

import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from dewey.cli import app
from dewey.reporting import embed_explorer
from dewey.repo import convert_pdf_with_paper2md


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

    def test_attach_document_to_metadata_only_source(self) -> None:
        self.init_repo()
        source_id = self.add_bib_source(
            "metadata-only.bib",
            """@article{smith2024metadata,
  title={Metadata Only Paper},
  author={Smith, Jane},
  year={2024}
}
""",
        )
        pdf = self.write_file("retrieved.pdf", "%PDF-1.4\nretrieved\n")

        result = self.invoke(["add", "document", source_id, str(pdf), "--json"])
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["source_id"], source_id)

        source_dir = self.root / ".dewey" / "sources" / source_id
        metadata = json.loads((source_dir / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["managed_pdf_path"], f".dewey/sources/{source_id}/source.pdf")
        self.assertEqual((source_dir / "source.pdf").read_text(encoding="utf-8"), "%PDF-1.4\nretrieved\n")

        duplicate = self.invoke(["add", "document", source_id, str(pdf), "--json"])
        self.assertEqual(duplicate.exit_code, 2)
        self.assertEqual(json.loads(duplicate.stdout)["error"]["code"], "document_exists")

    def test_next_requests_document_before_summary(self) -> None:
        self.init_repo()
        self.invoke(["topic", "set", "--topic", "Interviews", "--question", "What works?"])
        source_id = self.add_bib_source(
            "lead.bib",
            """@article{smith2024lead,
  title={A Relevant Lead},
  author={Smith, Jane},
  year={2024}
}
""",
        )

        result = self.invoke(["next", "--json"])
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["phase"], "retrieve")
        self.assertIn(f"dewey add document {source_id}", payload["next_steps"][0])

    def test_render_md_can_use_firecrawl_backend(self) -> None:
        pdf = self.write_file("cloud-paper.pdf", "%PDF-1.4\nfake pdf\n")
        self.init_repo()

        with patch("dewey.repo.convert_pdf_with_firecrawl", return_value=("# Cloud result\n", "v2")):
            result = self.invoke(["add", "source", str(pdf), "--backend", "firecrawl", "--json"])
        self.assertEqual(result.exit_code, 0)
        source_id = json.loads(result.stdout)["source_id"]
        metadata = json.loads((self.root / ".dewey" / "sources" / source_id / "metadata.json").read_text())
        self.assertEqual(metadata["markdown_generator"], {"name": "firecrawl", "version": "v2"})

    @patch("paper2md.converter.convert")
    @patch("dewey.repo._paper2md_version", return_value="0.1.0")
    def test_paper2md_retries_with_pymupdf(self, _version, convert) -> None:
        class Result:
            markdown = "# Recovered\n"
            backend_used = "pymupdf"

        convert.side_effect = [KeyError("encoder"), Result()]
        pdf = self.write_file("fallback.pdf", "%PDF-1.4\n")
        markdown, version = convert_pdf_with_paper2md(pdf, self.root / "output")
        self.assertEqual(markdown, "# Recovered\n")
        self.assertEqual(version, "0.1.0 (pymupdf)")
        self.assertEqual(convert.call_args_list[1].kwargs["backend"], "pymupdf")

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
            [
                "bib",
                "edit",
                source_id,
                "--field",
                "title",
                "--value",
                "Revised Book",
                "--field",
                "year",
                "--value",
                "2026",
                "--json",
            ]
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
        self.assertEqual(
            self.invoke(["notes", "edit", second, "--append", "Contains scaling discussion.", "--json"]).exit_code, 0
        )
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

    def test_topic_summary_and_next_workflow(self) -> None:
        self.init_repo()
        initial = json.loads(self.invoke(["next", "--json"]).stdout)
        self.assertEqual(initial["phase"], "frame")

        result = self.invoke(
            ["topic", "set", "--topic", "Synthetic surveys", "--question", "When do LLM agents match people?", "--json"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(self.invoke(["next", "--json"]).stdout)["phase"], "seed")

        source_id = self.add_bib_source(
            "anchor.bib",
            """@article{anchor2025,
  title={Synthetic Survey Validation},
  author={Researcher, Riley},
  year={2025},
  doi={10.1234/example}
}
""",
        )
        result = self.invoke(
            [
                "summary",
                "set",
                source_id,
                "--text",
                "Tests synthetic answers against held-out human responses.",
                "--json",
            ]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            json.loads(self.invoke(["summary", "show", source_id, "--json"]).stdout)["summary"].strip(),
            "Tests synthetic answers against held-out human responses.",
        )
        self.assertEqual(json.loads(self.invoke(["status", "--json"]).stdout)["counts"]["summarized"], 1)

    def test_discovery_queue_acceptance_and_citation_provenance(self) -> None:
        self.init_repo()
        parent = self.add_bib_source(
            "parent.bib",
            """@article{parent2025,
  title={Parent Paper},
  author={Parent, Pat},
  year={2025}
}
""",
        )
        result = self.invoke(
            [
                "discover",
                "add",
                "--title",
                "A Relevant Cited Paper",
                "--author",
                "Scholar One",
                "--year",
                "2020",
                "--doi",
                "10.1/cited",
                "--json",
            ]
        )
        candidate_id = json.loads(result.stdout)["candidate"]["candidate_id"]

        self.assertEqual(json.loads(self.invoke(["next", "--json"]).stdout)["phase"], "frame")

        discovery_path = self.root / ".dewey" / "discovery.json"
        discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
        discovery["candidates"][0]["cited_by_source_id"] = parent
        discovery_path.write_text(json.dumps(discovery), encoding="utf-8")

        accepted = self.invoke(["discover", "accept", candidate_id, "--json"])
        self.assertEqual(accepted.exit_code, 0)
        child = json.loads(accepted.stdout)["source_id"]
        links = json.loads(self.invoke(["link", "list", parent, "--json"]).stdout)
        self.assertEqual(links["outgoing"][0]["target"], child)
        self.assertEqual(links["outgoing"][0]["type"], "cites")

    def test_discovery_candidate_can_resolve_to_existing_source(self) -> None:
        self.init_repo()
        parent = self.add_bib_source("parent.bib", "@article{parent, title={Parent}, year={2025}}\n")
        child = self.add_bib_source("child.bib", "@article{child, title={Child}, year={2024}}\n")
        added = self.invoke(["discover", "add", "--title", "Child", "--json"])
        candidate_id = json.loads(added.stdout)["candidate"]["candidate_id"]
        path = self.root / ".dewey" / "discovery.json"
        data = json.loads(path.read_text())
        data["candidates"][0]["cited_by_source_id"] = parent
        path.write_text(json.dumps(data))

        resolved = self.invoke(["discover", "resolve", candidate_id, child, "--json"])
        self.assertEqual(resolved.exit_code, 0)
        candidate = json.loads(path.read_text())["candidates"][0]
        self.assertEqual(candidate["status"], "added")
        self.assertEqual(candidate["added_source_id"], child)
        links = json.loads(self.invoke(["link", "list", parent, "--json"]).stdout)
        self.assertEqual(links["outgoing"][0]["target"], child)

    def test_duplicate_discovery_sightings_preserve_all_citation_provenance(self) -> None:
        self.init_repo()
        first_parent = self.add_bib_source("first.bib", "@article{first, title={First}, year={2025}}\n")
        second_parent = self.add_bib_source("second.bib", "@article{second, title={Second}, year={2025}}\n")
        child = self.add_bib_source("child.bib", "@article{child, title={Shared Work}, year={2024}}\n")
        discovery_path = self.root / ".dewey" / "discovery.json"
        discovery_path.write_text(
            json.dumps(
                {
                    "candidates": [
                        {
                            "candidate_id": "cand_first",
                            "title": "Shared Work",
                            "authors": [],
                            "year": 2024,
                            "doi": "https://doi.org/10.1234/SHARED",
                            "cited_by_source_id": first_parent,
                            "discovery_method": "document_references",
                            "status": "candidate",
                            "created_at": "2026-01-01T00:00:00Z",
                        },
                        {
                            "candidate_id": "cand_second",
                            "title": "Shared work.",
                            "authors": [],
                            "year": 2024,
                            "doi": "10.1234/shared",
                            "cited_by_source_id": second_parent,
                            "discovery_method": "document_references",
                            "status": "candidate",
                            "created_at": "2026-01-02T00:00:00Z",
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )

        audit = json.loads(self.invoke(["discover", "dedupe", "--json"]).stdout)
        self.assertEqual(audit["duplicates"], 1)
        applied = json.loads(self.invoke(["discover", "dedupe", "--apply", "--json"]).stdout)
        self.assertEqual(applied["merged"], 1)
        candidate = json.loads(discovery_path.read_text())["candidates"][0]
        self.assertEqual(len(candidate["provenance"]), 2)

        resolved = self.invoke(["discover", "resolve", candidate["candidate_id"], child, "--json"])
        self.assertEqual(resolved.exit_code, 0)
        for parent in (first_parent, second_parent):
            links = json.loads(self.invoke(["link", "list", parent, "--json"]).stdout)
            self.assertEqual(links["outgoing"][0]["target"], child)

    def test_dedupe_joins_transitive_identity_matches(self) -> None:
        self.init_repo()
        discovery_path = self.root / ".dewey" / "discovery.json"
        records = [
            {
                "candidate_id": "by_doi",
                "title": "Abbreviated title",
                "doi": "10.1234/shared",
                "raw_citation": "First sighting",
                "created_at": "2026-01-01T00:00:00Z",
            },
            {
                "candidate_id": "by_title",
                "title": "The full study title",
                "raw_citation": "Second sighting",
                "created_at": "2026-01-02T00:00:00Z",
            },
            {
                "candidate_id": "bridge",
                "title": "The full study title",
                "doi": "10.1234/shared",
                "raw_citation": "Third sighting",
                "created_at": "2026-01-03T00:00:00Z",
            },
        ]
        discovery_path.write_text(json.dumps({"candidates": records}), encoding="utf-8")

        audit = json.loads(self.invoke(["discover", "dedupe", "--json"]).stdout)
        self.assertEqual(audit["duplicates"], 2)
        applied = json.loads(self.invoke(["discover", "dedupe", "--apply", "--json"]).stdout)
        self.assertEqual(applied["after"], 1)
        status = json.loads(self.invoke(["status", "--json"]).stdout)
        self.assertEqual(status["counts"]["discovery_sightings"], 3)

    def test_screening_decisions_are_append_only_and_structured(self) -> None:
        self.init_repo()
        added = json.loads(self.invoke(["discover", "add", "--title", "Candidate study", "--json"]).stdout)
        candidate_id = added["candidate"]["candidate_id"]

        first = self.invoke(
            [
                "screen",
                "decide",
                candidate_id,
                "--decision",
                "include",
                "--stage",
                "title-abstract",
                "--reviewer",
                "agent-a",
                "--criterion",
                "population=yes",
                "--criterion",
                "comparison=unclear",
                "--rationale",
                "Needs full-text review",
                "--protocol-version",
                "v1",
                "--json",
            ]
        )
        self.assertEqual(first.exit_code, 0)
        second = self.invoke(
            [
                "screen",
                "decide",
                candidate_id,
                "--decision",
                "exclude",
                "--stage",
                "full-text",
                "--reviewer",
                "agent-b",
                "--criterion",
                "comparison=no",
                "--reason",
                "no-comparator",
                "--rationale",
                "No eligible comparator",
                "--json",
            ]
        )
        self.assertEqual(second.exit_code, 0)
        history = json.loads(self.invoke(["screen", "history", candidate_id, "--json"]).stdout)
        self.assertEqual(len(history["decisions"]), 2)
        self.assertEqual(history["decisions"][0]["criteria"]["population"], "yes")
        self.assertEqual(history["decisions"][1]["stage"], "full-text")
        self.assertEqual(history["decisions"][1]["reason_code"], "no-comparator")
        self.assertEqual(history["decisions"][0]["protocol_version"], "v1")
        audit = json.loads(self.invoke(["screen", "audit", "--json"]).stdout)
        self.assertTrue(audit["ok"])

    def test_reference_traversal_queues_candidates(self) -> None:
        self.init_repo()
        self.invoke(["topic", "set", "--topic", "survey validation", "--question", "What predicts validity?"])
        parent = self.add_bib_source(
            "parent.bib",
            """@article{parent2025,
  title={Parent Paper},
  year={2025},
  doi={10.1234/parent}
}
""",
        )
        source_dir = self.root / ".dewey" / "sources" / parent
        markdown_path = source_dir / "source.md"
        markdown_path.write_text(
            """# Parent Paper

Body.

# References

1. Smith, A. (2020). Survey validation evidence. Journal of Tests. https://doi.org/10.1234/example

2. Jones, B. (2019). Measurement and synthetic samples. Methods Quarterly.
""",
            encoding="utf-8",
        )
        metadata_path = source_dir / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["markdown_path"] = str(markdown_path.relative_to(self.root))
        metadata["markdown_status"] = "ready"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        result = self.invoke(["traverse", "references", parent, "--limit", "10", "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.stdout)["added"], 2)
        candidates = json.loads(self.invoke(["discover", "list", "--json"]).stdout)["candidates"]
        self.assertEqual(candidates[0]["discovery_method"], "document_references")
        self.assertTrue(any(item["doi"] == "10.1234/example" for item in candidates))

    def test_reference_traversal_accepts_formatted_heading(self) -> None:
        from dewey.discovery import extract_reference_entries

        entries = extract_reference_entries(
            "# Paper\n\n## **References**\n\n- Smith, A. (2024). A sufficiently long citation title. Journal.\n"
        )
        self.assertEqual(len(entries), 1)

    def test_export_html_builds_self_contained_literature_explorer(self) -> None:
        self.init_repo()
        self.invoke(["topic", "set", "--topic", "AI interviewers", "--question", "Do they collect rich data?"])
        source_id = self.add_bib_source(
            "paper.bib", "@article{paper2025, title={Interview Evidence}, author={Smith, A.}, year={2025}}\n"
        )
        self.invoke(["summary", "set", source_id, "--text", "A concise source summary."])
        self.invoke(["discover", "add", "--title", "Candidate Study", "--json"])
        result = self.invoke(
            ["export", "html", "--output", "report/explorer.html", "--title", "AI Interview Explorer", "--json"]
        )
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["sources"], 1)
        explorer = (self.root / "report" / "explorer.html").read_text(encoding="utf-8")
        self.assertIn("new URLSearchParams(location.hash.slice(1))", explorer)
        self.assertIn("sourceLink", explorer)
        self.assertIn("AI Interview Explorer", explorer)
        self.assertIn("Interview Evidence", explorer)
        self.assertIn("Candidate Study", explorer)
        self.assertIn('data-tab="sources"', explorer)
        self.assertIn('data-tab="candidates"', explorer)
        self.assertIn('data-tab="graph"', explorer)
        self.assertIn("Download BibTeX", explorer)
        self.assertIn("Chronological citation network", explorer)
        self.assertIn("Smith (2025)", explorer)
        self.assertIn("possible sources found through searches", explorer)
        self.assertNotIn("source.pdf", explorer)

    def test_export_zip_is_portable_and_excludes_secrets(self) -> None:
        self.init_repo()
        source_id = self.add_bib_source(
            "paper.bib", "@article{paper2025, title={Portable Evidence}, author={Smith, A.}, year={2025}}\n"
        )
        self.write_file(".env", "SECRET=do-not-share\n")
        self.write_file(".git/private", "git internals\n")
        self.write_file("analysis/results.csv", "estimate,se\n0.2,0.1\n")
        result = self.invoke(["export", "zip", "--output", "review.dewey.zip", "--json"])
        self.assertEqual(result.exit_code, 0)
        payload = json.loads(result.stdout)
        archive_path = Path(payload["path"])
        self.assertTrue(archive_path.exists())
        with zipfile.ZipFile(archive_path) as archive:
            names = archive.namelist()
            root = names[0].split("/", 1)[0]
            self.assertIn(f"{root}/.dewey/config.json", names)
            self.assertIn(f"{root}/.dewey/sources/{source_id}/entry.bib", names)
            self.assertIn(f"{root}/analysis/results.csv", names)
            self.assertIn(f"{root}/dewey-export-manifest.json", names)
            self.assertFalse(any(name.endswith("/.env") for name in names))
            self.assertFalse(any("/.git/" in name for name in names))
            manifest = json.loads(archive.read(f"{root}/dewey-export-manifest.json"))
            self.assertTrue(all(len(item["sha256"]) == 64 for item in manifest["files"]))
            self.assertTrue(any(item["path"] == ".env" for item in manifest["excluded"]))

        extracted = self.root / "unpacked"
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extracted)
        previous_root = self.root
        self.root = extracted / root
        try:
            doctor = json.loads(self.invoke(["doctor", "--json"]).stdout)
            self.assertTrue(doctor["ok"])
        finally:
            self.root = previous_root

    def test_explorer_citation_labels_follow_author_year_conventions(self) -> None:
        from dewey.html_export import citation_label

        self.assertEqual(citation_label("Horton, John", "2026"), "Horton (2026)")
        self.assertEqual(citation_label("", "", "A Useful Unresolved Citation"), "A Useful Unresolved Citation")
        self.assertEqual(citation_label("Horton, John and Smith, Ada", "2026"), "Horton & Smith (2026)")
        self.assertEqual(
            citation_label("Horton, John and Smith, Ada and Jones, Lin", "2026"),
            "Horton et al. (2026)",
        )

    def test_study_finding_appraisal_matrix_and_next_workflow(self) -> None:
        self.init_repo()
        self.invoke(["topic", "set", "--topic", "AI interviews", "--question", "What improves disclosure?"])
        source_id = self.add_bib_source(
            "study.bib", "@article{study2026, title={Interview Study}, author={Smith, A.}, year={2026}}\n"
        )
        self.invoke(["summary", "set", source_id, "--text", "A randomized interview experiment."])
        self.invoke(["state", "set", source_id, "included"])
        self.assertEqual(json.loads(self.invoke(["next", "--json"]).stdout)["phase"], "extract")

        study_file = self.write_file(
            "study.json",
            json.dumps(
                {
                    "label": "Disclosure experiment",
                    "design": "randomized experiment",
                    "population": "online adults",
                    "sample_size": 120,
                    "intervention": "AI interviewer",
                    "comparator": "human interviewer framing",
                    "methods": ["between-subject randomization"],
                    "measures": ["disclosure score"],
                }
            ),
        )
        result = self.invoke(["study", "create", source_id, "--file", str(study_file), "--json"])
        self.assertEqual(result.exit_code, 0)
        study_id = json.loads(result.stdout)["study"]["study_id"]
        self.assertEqual(json.loads(self.invoke(["next", "--json"]).stdout)["phase"], "extract")

        invalid_finding = self.write_file(
            "invalid-finding.json",
            json.dumps(
                {
                    "author_claim": "Disclosure increased.",
                    "evidence_statement": "The treatment mean was higher.",
                    "reviewer_interpretation": "Suggestive experimental evidence.",
                    "outcome": "disclosure",
                    "locators": [],
                }
            ),
        )
        self.assertEqual(
            self.invoke(["finding", "add", study_id, "--file", str(invalid_finding)]).exit_code,
            2,
        )
        finding_file = self.write_file(
            "finding.json",
            json.dumps(
                {
                    "author_claim": "Disclosure increased.",
                    "evidence_statement": "The treatment mean was higher.",
                    "reviewer_interpretation": "Suggestive experimental evidence.",
                    "outcome": "disclosure",
                    "direction": "positive",
                    "certainty": "moderate",
                    "locators": [{"page": "7", "table": "2"}],
                }
            ),
        )
        result = self.invoke(["finding", "add", study_id, "--file", str(finding_file), "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(self.invoke(["next", "--json"]).stdout)["phase"], "appraise")

        appraisal_file = self.write_file(
            "appraisal.json",
            json.dumps(
                {
                    "framework": "review-specific risk of bias",
                    "dimensions": [
                        {
                            "name": "internal validity",
                            "judgment": "low concern",
                            "rationale": "Random assignment was reported.",
                            "locators": [{"page": "4"}],
                        }
                    ],
                    "overall_judgment": "moderate confidence",
                    "applicability": "Directly applicable to AI-mediated interviews.",
                    "reviewer": "test reviewer",
                }
            ),
        )
        result = self.invoke(["appraisal", "set", study_id, "--file", str(appraisal_file), "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(self.invoke(["next", "--json"]).stdout)["phase"], "synthesize")

        result = self.invoke(["matrix", "evidence", "--format", "csv", "--output", "matrix.csv", "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(len(json.loads(result.stdout)["rows"]), 1)
        matrix = (self.root / "matrix.csv").read_text(encoding="utf-8")
        self.assertIn("author_claim,evidence_statement,reviewer_interpretation", matrix)
        self.assertIn("Disclosure increased.", matrix)
        self.assertEqual(self.invoke(["doctor", "--json"]).exit_code, 0)

        coverage = json.loads(self.invoke(["synthesis", "coverage", "--json"]).stdout)
        self.assertTrue(coverage["ok"])
        self.assertEqual(coverage["coverage"]["represented_included_sources"], 1)

        update = self.write_file("study-update.json", json.dumps({"sample_size": 125, "setting": "updated setting"}))
        result = self.invoke(["study", "update", study_id, "--file", str(update), "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.stdout)["study"]["sample_size"], 125)

        finding_id = json.loads(
            self.invoke(["finding", "list", "--study", study_id, "--json"]).stdout
        )["findings"][0]["finding_id"]
        finding_update = self.write_file(
            "finding-update.json", json.dumps({"reviewer_interpretation": "Updated interpretation."})
        )
        result = self.invoke(["finding", "update", finding_id, "--file", str(finding_update), "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.stdout)["finding"]["reviewer_interpretation"], "Updated interpretation.")

        result = self.invoke(["matrix", "evidence", "--outcome", "disclosure", "--format", "markdown"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("| study | outcome | direction |", result.stdout)
        self.assertEqual(len(json.loads(self.invoke(["appraisal", "list", "--json"]).stdout)["appraisals"]), 1)

        theme_file = self.write_file(
            "theme.json", json.dumps({"label": "Disclosure", "description": "Evidence about disclosure outcomes."})
        )
        theme = json.loads(self.invoke(["theme", "create", "--file", str(theme_file), "--json"]).stdout)["theme"]
        claim_file = self.write_file(
            "claim.json",
            json.dumps(
                {
                    "theme_ids": [theme["theme_id"]],
                    "statement": "AI framing may increase disclosure.",
                    "scope": "Short online interviews.",
                    "evidence": [
                        {"finding_id": finding_id, "relationship": "supports", "rationale": "Direct experiment."}
                    ],
                    "confidence": "moderate",
                    "confidence_rationale": "One randomized study.",
                }
            ),
        )
        claim = json.loads(self.invoke(["claim", "create", "--file", str(claim_file), "--json"]).stdout)["claim"]
        self.assertEqual(len(json.loads(self.invoke(["claim", "list", "--theme", theme["theme_id"], "--json"]).stdout)["claims"]), 1)
        audit = json.loads(self.invoke(["claim", "audit", "--json"]).stdout)
        self.assertEqual(audit["issues"], [{"code": "unqualified_claim", "claim_id": claim["claim_id"]}])
        report = json.loads(self.invoke(["report", "context", "--json"]).stdout)
        self.assertEqual(report["bundle"]["review"]["topic"], "AI interviews")
        self.assertEqual(report["bundle"]["themes"][0]["claim_ids"], [claim["claim_id"]])
        self.assertEqual(report["bundle"]["claims"][0]["evidence"][0]["finding"]["finding_id"], finding_id)
        self.assertFalse(report["bundle"]["readiness"]["ready"])
        result = self.invoke(
            ["report", "context", "--format", "markdown", "--output", "report-context.md", "--json"]
        )
        self.assertEqual(result.exit_code, 0)
        scaffold = (self.root / "report-context.md").read_text(encoding="utf-8")
        self.assertIn("### Claim: AI framing may increase disclosure.", scaffold)
        self.assertIn("| Relationship | Study | Finding | Locator | Appraisal |", scaffold)
        self.assertEqual(json.loads(self.invoke(["next", "--json"]).stdout)["phase"], "position")
        article_file = self.write_file(
            "article.json",
            json.dumps(
                {
                    "title": "Interviewing at Scale",
                    "audience": "Economists",
                    "abstract": "A synthesis of the evidence.",
                    "motivation": ["Adaptive interviews are costly."],
                    "field_context": ["Interviewing trades standardization against depth."],
                    "central_question": "When does automation improve interview evidence?",
                    "thesis": "Automation changes costs but does not ensure validity.",
                    "contribution": ["Connects design choices to measurement."],
                    "scope_includes": ["Automated research interviews."],
                    "scope_excludes": ["Customer service."],
                    "literatures": [{"stream_id": "disclosure", "label": "Disclosure", "description": "Evaluation apprehension.", "source_ids": [source_id], "relationship_to_review": "Supplies a mechanism."}],
                    "source_positions": [{"source_id": source_id, "role": "foundational", "contribution": "Identifies the mechanism.", "claim_ids": [claim["claim_id"]], "caveat": "One setting."}],
                    "timeline": [{"year": 2024, "label": "Experimental test", "significance": "Tests the mechanism.", "source_ids": [source_id]}],
                    "sections": [{"heading": "Disclosure", "purpose": "Synthesize the mechanism.", "theme_ids": [theme["theme_id"]], "claim_ids": [claim["claim_id"]]}],
                    "conclusion": ["Validate against independent criteria."],
                }
            ),
        )
        result = self.invoke(["report", "article-set", "--file", str(article_file), "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(json.loads(result.stdout)["article"]["title"], "Interviewing at Scale")
        result = self.invoke(["report", "brief", "--output", ".dewey/synthesis/article-brief.md", "--json"])
        self.assertEqual(result.exit_code, 0)
        brief = (self.root / ".dewey/synthesis/article-brief.md").read_text(encoding="utf-8")
        self.assertIn("## Study map", brief)
        self.assertIn("## Timeline", brief)
        self.assertIn("Automation changes costs but does not ensure validity.", brief)
        guarded_theme = self.invoke(["theme", "delete", theme["theme_id"], "--json"])
        self.assertEqual(json.loads(guarded_theme.stdout)["error"]["code"], "theme_has_claims")
        self.assertEqual(self.invoke(["claim", "delete", claim["claim_id"]]).exit_code, 0)
        self.assertEqual(self.invoke(["theme", "delete", theme["theme_id"]]).exit_code, 0)

        guarded = self.invoke(["study", "delete", study_id, "--json"])
        self.assertEqual(guarded.exit_code, 2)
        self.assertEqual(json.loads(guarded.stdout)["error"]["code"], "study_has_evidence")
        deleted = self.invoke(["study", "delete", study_id, "--cascade", "--json"])
        self.assertEqual(deleted.exit_code, 0)
        self.assertEqual(json.loads(deleted.stdout)["deleted"], {"studies": 1, "findings": 1, "appraisals": 1})

    def test_evidence_templates_are_writable_json(self) -> None:
        self.init_repo()
        for group in ("study", "finding", "appraisal", "theme", "claim"):
            output = f"templates/{group}.json"
            result = self.invoke([group, "template", "--output", output, "--json"])
            self.assertEqual(result.exit_code, 0)
            payload = json.loads((self.root / output).read_text(encoding="utf-8"))
            self.assertIsInstance(payload, dict)
        result = self.invoke(["report", "article-template", "--output", "templates/article.json", "--json"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("source_positions", json.loads((self.root / "templates/article.json").read_text()))

    def test_report_render_is_markdown_first(self) -> None:
        self.init_repo()
        markdown = self.write_file("article.md", "# Article\n\nSubstantive prose.\n")
        with patch("dewey.cli.render_with_pandoc") as render:
            result = self.invoke(["report", "render", str(markdown), "--output", "article.html", "--json"])
        self.assertEqual(result.exit_code, 0)
        render.assert_called_once_with(markdown, Path("article.html"), None)

    def test_embed_explorer_creates_single_html_document(self) -> None:
        report = self.write_file(
            "report.html",
            '<html><body><figure id="explorer-embed"><iframe id="literature-explorer" src="explorer.html"></iframe></figure><a href="../ai-interviewers-explorer.html#source=src_test">Explorer record</a></body></html>',
        )
        explorer = self.write_file("explorer.html", "<html><body><script>function showSource(id){}</script></body></html>")
        embed_explorer(report, explorer)
        rendered = report.read_text(encoding="utf-8")
        self.assertIn("srcdoc=", rendered)
        self.assertIn("data-explorer-source=\"src_test\"", rendered)
        self.assertNotIn('src="explorer.html"', rendered)


if __name__ == "__main__":
    unittest.main()
