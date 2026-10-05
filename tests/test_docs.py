import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load("validator", ROOT / "scripts/validate-docs.py")
builder = load("builder", ROOT / "scripts/build-docs.py")
publisher = load("publisher", ROOT / "scripts/push-docs.py")


class PublicationBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "public-pages.json").write_text(json.dumps(["README.md"]), encoding="utf-8")
        (self.root / "README.md").write_text("# Welcome\n\nPublic guide.\n", encoding="utf-8")
        (self.root / "SUMMARY.md").write_text("# Summary\n\n* [Home](README.md)\n", encoding="utf-8")
        (self.root / "AGENTS.md").write_text("Private tooling instructions", encoding="utf-8")
        (self.root / "update-config.json").write_text('{"not-a-page": true}', encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_pages(self):
        self.assertEqual(validator.validate(self.root), [])

    def test_private_markdown_is_rejected_even_if_unlisted(self):
        (self.root / "internal.md").write_text("Internal notes", encoding="utf-8")
        self.assertTrue(validator.validate(self.root))

    def test_code_and_client_names_are_rejected(self):
        for text in ("lib/main.dart", "SubscriptionService", "WorkManager", "v2rayNG", "парсер строит конфиг"):
            (self.root / "README.md").write_text(text, encoding="utf-8")
            self.assertTrue(validator.validate(self.root), text)

    def test_links_cannot_reference_service_files_or_parent(self):
        for target in ("AGENTS.md", "../private.md", "missing.md", "README.md#absent"):
            (self.root / "README.md").write_text(f"# Welcome\n[Link]({target})", encoding="utf-8")
            self.assertTrue(validator.validate(self.root), target)

    def test_summary_and_manifest_must_match(self):
        (self.root / "SUMMARY.md").write_text("# Summary", encoding="utf-8")
        self.assertTrue(validator.validate(self.root))

    def test_manifest_cannot_publish_agent_rules_or_escape(self):
        for pages in (["AGENTS.md"], ["../README.md"], ["README.md", "README.md"]):
            (self.root / "public-pages.json").write_text(json.dumps(pages), encoding="utf-8")
            self.assertTrue(validator.validate(self.root))

    def test_prepared_source_contains_only_public_pages(self):
        stage = builder.prepare(self.root)
        self.assertEqual({p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()},
                         {"README.md", "SUMMARY.md"})
        self.assertFalse((stage / "AGENTS.md").exists())
        self.assertFalse((stage / "update-config.json").exists())

    def test_push_rejects_application_remote(self):
        with patch.object(publisher, "git", return_value="https://gitlab.com/samueladamson37/imsel-vpn.git"):
            with self.assertRaises(ValueError):
                publisher.check_remote("origin", publisher.REMOTES["origin"])

    def test_push_checks_fetch_and_push_destinations(self):
        with patch.object(publisher, "git", return_value=publisher.REMOTES["origin"]) as git:
            publisher.check_remote("origin", publisher.REMOTES["origin"])
            self.assertEqual(git.call_count, 2)

    def test_private_source_is_rejected_even_when_not_a_page(self):
        (self.root / "main.dart").write_text("private source", encoding="utf-8")
        self.assertTrue(validator.validate(self.root))

    def test_update_config_changes_need_separate_authorization(self):
        for results in (["update-config.json", ""], ["", "changed-commit"]):
            with patch.object(publisher, "git", side_effect=results):
                with self.assertRaises(ValueError):
                    publisher.check_update_config("old", "new", False)
        with patch.object(publisher, "git") as git:
            publisher.check_update_config("old", "new", True)
            git.assert_not_called()


if __name__ == "__main__":
    unittest.main()
