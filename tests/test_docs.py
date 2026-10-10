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
        for text in ("lib/main.dart", "SubscriptionService", "WorkManager", "v2rayNG",
                     "Shadowrocket", "v2rayN", "expireDate", "нативной поддержки ядра",
                     "парсер строит конфиг", "Main.java", "build.gradle.kts", "main.cpp"):
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
        for name in ("main.dart", "Main.java", "Main.JAVA", "Main.kt", "build.gradle",
                     "build.gradle.kts", "App.swift", "main.c", "main.cc", "main.cpp",
                     "main.h", "main.hpp", "App.m", "App.mm", "main.cs", "main.go",
                     "main.rs", "generated.cmake", "project.pbxproj", "App.xcconfig",
                     "App.xcscheme", "App.podspec", "App.vcxproj", "App.sln", "App.rc",
                     "App.entitlements", "Main.storyboard", "release.jks", "release.keystore",
                     "CMakeLists.txt", "pubspec.yaml", "pubspec.lock", "AndroidManifest.xml",
                     "Podfile", "Podfile.lock", "gradlew", "gradlew.bat", "gradle.properties"):
            with self.subTest(name=name):
                path = self.root / "unlisted" / name
                path.parent.mkdir(exist_ok=True)
                path.write_text("private application material", encoding="utf-8")
                try:
                    self.assertIn(
                        f"Private application material in public repository: unlisted/{name}",
                        validator.validate(self.root),
                    )
                finally:
                    path.unlink()

    def test_documentation_tooling_is_allowed_but_not_published(self):
        names = ("scripts/validate-docs.py", "scripts/check.sh", "tests/test_docs.py",
                 ".github/workflows/pages.yml", ".gitlab-ci.yml", "book.toml")
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("documentation tooling", encoding="utf-8")
        self.assertEqual(validator.validate(self.root), [])
        stage = builder.prepare(self.root)
        self.assertEqual({p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()},
                         {"README.md", "SUMMARY.md"})

    def test_public_subscription_formats_are_allowed(self):
        (self.root / "README.md").write_text(
            "# Welcome\n```http\nsubscription-userinfo: expire=1700000000\n"
            "routing: imsel://routing/onadd/ZXhhbXBsZQ==\n```\n"
            '```json\n{"allowInsecure": false}\n```\n', encoding="utf-8")
        self.assertEqual(validator.validate(self.root), [])

    def test_implementation_code_blocks_are_rejected(self):
        for language in ("dart", "kotlin", "swift", "java", "python", "go", "c", "cpp",
                         "objective-c", "csharp", "rust"):
            with self.subTest(language=language):
                (self.root / "README.md").write_text(
                    f"# Welcome\n```{language}\nimplementation\n```\n", encoding="utf-8")
                self.assertIn("README.md: source-code example is not public documentation",
                              validator.validate(self.root))

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
