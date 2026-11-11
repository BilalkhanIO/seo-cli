#!/usr/bin/env python3
"""Run pinned Lychee against explicit public article files/URLs and save JSON."""
import argparse
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("targets", nargs="+", help="Public article URLs or local draft HTML/Markdown; never key files")
    args = parser.parse_args()
    for target in args.targets:
        if not target.startswith(("https://", "http://")) and Path(target).suffix not in (".html", ".md"):
            parser.error("Only article HTML/Markdown files or public URLs are allowed")
    folder = BASE / "reports"; folder.mkdir(exist_ok=True)
    run = subprocess.run([str(BASE / ".tools/lychee/lychee-v0.24.2/lychee"),
                          "--config", str(BASE / "lychee.toml"), "--format", "json", *args.targets],
                         capture_output=True, text=True, cwd=BASE)
    (folder / "lychee_latest.json").write_text(run.stdout)
    (folder / "lychee_latest.log").write_text(run.stderr)
    print(f"Lychee exit={run.returncode}; report={folder / 'lychee_latest.json'}")
    print("Treat 404/410 as broken; 403/429/timeouts need manual verification.")
    return run.returncode


if __name__ == "__main__": raise SystemExit(main())
