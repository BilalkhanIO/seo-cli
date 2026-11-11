#!/usr/bin/env python3
"""Collect explicit public sources and search a local SQLite evidence library.

python3 research_library.py collect URL [URL ...]
python3 research_library.py search 'course certificate'
"""
import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import socket
import sqlite3
import sys
import urllib.error
import urllib.request
from urllib.parse import urldefrag, urlparse
from urllib.robotparser import RobotFileParser

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / ".tools/research-python"))
AGENT = "StudentsTimeResearch/1.0"


def public_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Use a public HTTP(S) URL without embedded credentials")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("Private/local source addresses are not supported")
    return urldefrag(url)[0]


class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def allowed(url):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = urllib.request.build_opener(PublicRedirect()).open(
            urllib.request.Request(robots_url, headers={"User-Agent": AGENT}), timeout=15)
        with response:
            content = response.read(500_000).decode("utf-8", "replace")
        robot = RobotFileParser(); robot.parse(content.splitlines())
        return robot.can_fetch(AGENT, url)
    except urllib.error.HTTPError as e:
        return e.code in (404, 410)
    except Exception:
        return False


def database(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY, url TEXT UNIQUE NOT NULL, final_url TEXT,
            title TEXT, retrieved_at TEXT, fingerprint TEXT, text TEXT, metadata TEXT
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS source_search USING fts5(title, text, url UNINDEXED);
    ''')
    return db


def save_source(db, url, final_url, title, text, metadata):
    fingerprint = hashlib.sha256(text.encode()).hexdigest()
    stamp = datetime.now(timezone.utc).isoformat()
    previous = db.execute("SELECT fingerprint FROM sources WHERE url=?", (url,)).fetchone()
    with db:
        db.execute('''INSERT INTO sources(url,final_url,title,retrieved_at,fingerprint,text,metadata)
            VALUES(?,?,?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET final_url=excluded.final_url,
            title=excluded.title,retrieved_at=excluded.retrieved_at,fingerprint=excluded.fingerprint,
            text=excluded.text,metadata=excluded.metadata''',
            (url, final_url, title, stamp, fingerprint, text, json.dumps(metadata)))
        row_id = db.execute("SELECT id FROM sources WHERE url=?", (url,)).fetchone()[0]
        db.execute("DELETE FROM source_search WHERE rowid=?", (row_id,))
        db.execute("INSERT INTO source_search(rowid,title,text,url) VALUES(?,?,?,?)", (row_id,title,text,url))
    return {"url": url, "title": title, "retrieved_at": stamp, "words": len(text.split()),
            "fingerprint": fingerprint, "changed": previous is not None and previous[0] != fingerprint,
            "verification": "Retrieved source text; factual claims still require editorial verification"}


def collect(db, url):
    from trafilatura import extract
    url = public_url(url)
    if not allowed(url): raise ValueError("Robots policy unavailable or disallows this source")
    with urllib.request.build_opener(PublicRedirect()).open(
        urllib.request.Request(url, headers={"User-Agent": AGENT}), timeout=30) as r:
        final_url = public_url(r.url)
        if final_url != url and not allowed(final_url):
            raise ValueError("Robots policy disallows redirected destination")
        if "html" not in r.headers.get("Content-Type", ""):
            raise ValueError("Source is not HTML; use a document importer")
        raw = r.read(3_000_001)
        if len(raw) > 3_000_000: raise ValueError("Source exceeds 3 MB collection limit")
    result = extract(raw, url=final_url, output_format="json", with_metadata=True, include_comments=False)
    if not result: raise ValueError("No main content extracted")
    metadata = json.loads(result)
    text = metadata.pop("text", "")
    if not text: raise ValueError("Extracted source has no text")
    return save_source(db, url, final_url, metadata.get("title") or final_url, text, metadata)


def search(db, query):
    terms = re.findall(r"\w+", query, flags=re.UNICODE)
    if not terms: return []
    expression = " AND ".join('"' + term + '"' for term in terms)
    return [dict(r) for r in db.execute('''SELECT title,url,snippet(source_search,1,'[',']',' … ',24) AS excerpt
        FROM source_search WHERE source_search MATCH ? ORDER BY rank LIMIT 10''', (expression,))]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--database", type=Path, default=BASE / "research/sources.sqlite")
    sub = p.add_subparsers(dest="command", required=True)
    add = sub.add_parser("collect"); add.add_argument("urls", nargs="+")
    find = sub.add_parser("search"); find.add_argument("query")
    args = p.parse_args()
    db = database(args.database)
    if args.command == "search":
        print(json.dumps(search(db, args.query), indent=2, ensure_ascii=False)); return
    rows = []
    for url in args.urls:
        try: result = collect(db, url)
        except Exception as exc: result = {"url": url, "error": str(exc)[:300]}
        rows.append(result); print(json.dumps(result, ensure_ascii=False), flush=True)
    folder = BASE / "reports"; folder.mkdir(exist_ok=True)
    (folder / "research_sources_latest.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))


if __name__ == "__main__": main()
