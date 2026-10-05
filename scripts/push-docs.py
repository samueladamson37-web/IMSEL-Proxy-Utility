#!/usr/bin/env python3
"""Checked fast-forward publication to the two documentation remotes only."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTES = {
    "origin": "https://github.com/samueladamson37-web/IMSEL-Proxy-Utility.git",
    "gitlab": "https://gitlab.com/samueladamson37/imsel-proxy-utility.git",
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def check_remote(name, url):
    for option in ((), ("--push",)):
        if git("remote", "get-url", *option, "--all", name).splitlines() != [url]:
            raise ValueError(f"Unexpected remote destination: {name}")


def check_update_config(tip, commit, allow):
    if not allow:
        changes = git("diff", "--name-only", tip, commit, "--", "update-config.json")
        history = git("log", "--format=%H", f"{tip}..{commit}", "--", "update-config.json")
        if changes or history:
            raise ValueError("update-config.json changed; separate explicit authorization required")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-update-config", action="store_true")
    parser.add_argument("--mdbook", default="mdbook")
    args = parser.parse_args()
    if Path(git("rev-parse", "--show-toplevel")).resolve() != ROOT.resolve():
        raise ValueError("Not the documentation Git root")
    if git("branch", "--show-current") != "main" or git("status", "--porcelain"):
        raise ValueError("Publication requires clean main, including untracked files")
    commit = git("rev-parse", "HEAD")
    for name, url in REMOTES.items():
        check_remote(name, url)
        subprocess.run(["git", "fetch", "--no-tags", name, "main"], cwd=ROOT, check=True)
        tip = git("rev-parse", "FETCH_HEAD")
        subprocess.run(["git", "merge-base", "--is-ancestor", tip, commit], cwd=ROOT, check=True)
        check_update_config(tip, commit, args.allow_update_config)
    subprocess.run([sys.executable, "scripts/validate-docs.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/build-docs.py", "--mdbook", args.mdbook], cwd=ROOT, check=True)
    subprocess.run(["git", "diff", "--check"], cwd=ROOT, check=True)
    if git("status", "--porcelain") or git("rev-parse", "HEAD") != commit:
        raise ValueError("Repository changed during validation")
    if not args.execute:
        print(f"[READY] {commit}: validated for both remotes; nothing pushed")
        return
    completed = []
    try:
        for name, url in REMOTES.items():
            if git("status", "--porcelain") or git("rev-parse", "HEAD") != commit:
                raise ValueError("Repository changed before push")
            check_remote(name, url)
            subprocess.run(["git", "-c", "core.hooksPath=.githooks", "push", name,
                            f"{commit}:refs/heads/main"], cwd=ROOT, check=True)
            completed.append(name)
        for name in REMOTES:
            lines = git("ls-remote", "--heads", name, "refs/heads/main").splitlines()
            if len(lines) != 1 or lines[0].split()[0] != commit:
                raise ValueError(f"Remote changed or failed verification: {name}")
    except Exception:
        print(f"[PARTIAL] Confirmed pushes: {completed}; rerun after resolving errors, never force-push", file=sys.stderr)
        raise
    print(f"[OK] Both documentation remotes contain {commit}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError, FileNotFoundError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        raise SystemExit(1)
