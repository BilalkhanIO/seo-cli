#!/usr/bin/env python3
"""Install pinned official GitHub binaries locally, verifying release SHA-256."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

BASE = Path(__file__).resolve().parent / ".tools"
RELEASES = [
    ("lycheeverse/lychee", "lychee-v0.24.2", "lychee-x86_64-unknown-linux-musl.tar.gz", "lychee",
     "73657a111819a30c47c08352896796f23d64e4eb2b3ed39b6d32149241566fc5"),
    ("vale-cli/vale", "v3.25.1", "vale_3.25.1_Linux_64-bit.tar.gz", "vale",
     "4bf5c5176b682b1da0830f471584d3494f1c2e27ee3029e1ad6f6661d4962182"),
]


def main():
    for repo, version, filename, binary, expected in RELEASES:
        dest = BASE / binary / version
        target = dest / binary
        if target.exists():
            print(f"Already installed: {target}")
            continue
        url = f"https://github.com/{repo}/releases/download/{version}/{filename}"
        req = urllib.request.Request(url, headers={"User-Agent": "seo-pipeline-install/1.0"})
        data = urllib.request.urlopen(req, timeout=60).read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise SystemExit(f"Checksum mismatch for {repo}; refusing installation")
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            for member in archive.getmembers():
                name = Path(member.name).name
                if member.isfile() and (name == binary or name.lower().startswith(("license", "copying"))):
                    (dest / name).write_bytes(archive.extractfile(member).read())
        if not target.exists(): raise SystemExit(f"Binary missing in archive: {repo}")
        target.chmod(0o755)
        (dest / "source.json").write_text(json.dumps({"repository": repo, "version": version,
                "download": url, "archive_sha256": expected}, indent=2))
        print(f"Installed and verified: {target}")


if __name__ == "__main__": main()
