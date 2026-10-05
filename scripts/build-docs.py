#!/usr/bin/env python3
"""Build mdBook from only the explicitly permitted public pages."""
import argparse
import importlib.util
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("docs_validator", ROOT / "scripts/validate-docs.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def prepare(root=ROOT):
    errors = validator.validate(root)
    if errors:
        raise ValueError("\n".join(errors))
    stage = root / ".build" / "site-src"
    if (root / ".build").is_symlink() or stage.is_symlink():
        raise ValueError("Unsafe symlink at build directory")
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    for name in ["SUMMARY.md", *validator.public_pages(root)]:
        dest = stage / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, dest)
    return stage


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mdbook", default="mdbook")
    args = parser.parse_args()
    prepare()
    output = ROOT / "public"
    if output.is_symlink():
        raise ValueError("Unsafe output symlink")
    if output.exists():
        shutil.rmtree(output)
    subprocess.run([args.mdbook, "build", str(ROOT)], check=True)
    for private in ("AGENTS.md", "update-config.json", "scripts", "tests", "docs-internal"):
        if (output / private).exists():
            raise ValueError(f"Unexpected private build artifact: {private}")
