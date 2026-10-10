#!/usr/bin/env python3
"""Validate the publication boundary, public text and local Markdown links."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"!?\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)")
PRIVATE_SUFFIXES = {
    ".dart", ".java", ".kt", ".kts", ".swift", ".c", ".cc", ".cpp",
    ".cxx", ".h", ".hh", ".hpp", ".m", ".mm", ".cs", ".go", ".rs",
    ".gradle", ".cmake", ".pbxproj", ".xcconfig", ".xcscheme", ".podspec",
    ".vcxproj", ".sln", ".rc", ".entitlements", ".storyboard",
    ".jks", ".keystore",
}
PRIVATE_FILENAMES = {
    "cmakelists.txt", "pubspec.yaml", "pubspec.lock", "androidmanifest.xml",
    "podfile", "podfile.lock", "gradlew", "gradlew.bat", "gradle.properties",
}
FORBIDDEN = re.compile(
    r"(?:\blib/|\bpackages/|\bbin/|\bdocs-internal/|"
    r"[\w./-]+(?:" + "|".join(re.escape(suffix) for suffix in sorted(PRIVATE_SUFFIXES)) + r")\b|"
    r"\b(?:SubscriptionService|SubscriptionCommands|SubscriptionMeta|ApiService|"
    r"ReceiveHeaderConfig|SecurePrefs|WorkManager|applyMeta|applyCommands|"
    r"overrideLinkFragment|subName|expireDate|GOMEMLIMIT)\b|"
    r"\b(?:Happ|Incy|v2rayNG|v2rayN|Hiddify|NekoBox|NekoRay|Shadowrocket|Streisand|Clash)\b|"
    r"(?:изолят|парсер|миграци)[\w]*|генераци[\w]*\s+конфиг|"
    r"архитектур[\w]*|изолированн[\w]*\s+контейнер|"
    r"нативн[\w]*\s+поддержк[\w]*\s+ядр[\w]*)", re.IGNORECASE)


def public_pages(root):
    pages = json.loads((root / "public-pages.json").read_text(encoding="utf-8"))
    if not isinstance(pages, list) or not pages or len(pages) != len(set(pages)):
        raise ValueError("public-pages.json must be a nonempty unique list")
    for name in pages:
        if not isinstance(name, str) or "\\" in name or Path(name).is_absolute():
            raise ValueError("Invalid page path")
        path = root / name
        if ".." in Path(name).parts or name == "AGENTS.md" or not name.endswith(".md"):
            raise ValueError(f"Not a public page: {name}")
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Missing or unsafe page: {name}")
    return pages


def headings(text):
    slugs = set()
    for title in re.findall(r"^#{1,6}\s+(.+)$", text, flags=re.MULTILINE):
        # mdBook/GitHub-style anchors; all local links are validated below.
        slug = re.sub(r"[^\w\s-]", "", title.lower().strip()).replace(" ", "-")
        slugs.add(slug)
    return slugs


def validate(root=ROOT):
    errors = []
    try:
        pages = public_pages(root)
    except (ValueError, TypeError, OSError) as exc:
        return [str(exc)]
    allowed = set(pages) | {"SUMMARY.md"}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts[0] in {".git", ".build", "public", "book", "__pycache__"}:
            continue
        if ("docs-internal" in relative.parts or path.suffix.lower() in PRIVATE_SUFFIXES
                or path.name.lower() in PRIVATE_FILENAMES):
            errors.append(f"Private application material in public repository: {relative.as_posix()}")
    summary = (root / "SUMMARY.md").read_text(encoding="utf-8")
    listed = [unquote(urlsplit(match).path) for match in LINK.findall(summary)]
    if len(listed) != len(set(listed)) or set(listed) != set(pages):
        errors.append("SUMMARY.md and public-pages.json must list the same pages once")
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if relative.parts[0] in {".git", ".build", "public", "book"}:
            continue
        name = relative.as_posix()
        if name == "AGENTS.md":
            continue
        if name not in allowed:
            errors.append(f"Unclassified Markdown in public repository: {name}")
    for name in sorted(allowed):
        text = (root / name).read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            if FORBIDDEN.search(line):
                errors.append(f"{name}:{number}: internal implementation or forbidden client name")
        if re.search(r"^```(?:dart|kotlin|swift|java|python|go|c|cpp|objective-c|csharp|rust)\b", text, re.MULTILINE):
            errors.append(f"{name}: source-code example is not public documentation")
        for target in LINK.findall(text):
            link = urlsplit(target)
            if link.scheme or link.netloc:
                continue
            destination = (root / name).parent / unquote(link.path) if link.path else root / name
            try:
                dest_name = destination.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                errors.append(f"{name}: link escapes repository: {target}")
                continue
            if dest_name not in allowed or not destination.is_file():
                errors.append(f"{name}: unpublished or broken local link: {target}")
            elif link.fragment and unquote(link.fragment) not in headings(destination.read_text(encoding="utf-8")):
                errors.append(f"{name}: missing heading: {target}")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    errors = validate(parser.parse_args().root)
    for error in errors:
        print(f"[FAIL] {error}")
    if not errors:
        print("[OK] Public pages, privacy boundary and local links validated")
    raise SystemExit(bool(errors))
