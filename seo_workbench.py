#!/usr/bin/env python3
"""Persistent SEO audit runner with an explicit existing-article repair command.

python3 seo_workbench.py run              # ingest existing reports, no network
python3 seo_workbench.py run --refresh    # run reporting tools, then ingest
python3 seo_workbench.py run --dry-run    # print execution plan only
python3 seo_workbench.py history
python3 seo_workbench.py queue
python3 seo_workbench.py improve          # refresh and prepare review packets
python3 seo_workbench.py improve --apply  # additionally update existing live posts
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from urllib.parse import urlparse
import uuid

BASE = Path(__file__).resolve().parent
STAGES = [
    ("growth", ["growth_report.py"], "growth_latest.json", (0,), 900),
    ("competitors", ["article_competitor_audit.py", "--refresh-inventory", "--fetch"], "article_competitor_latest.json", (0,), 1800),
    ("writing", ["content_review.py"], "content_review_latest.json", (0,), 120),
    ("links", ["open_source_link_check.py", "--published-inventory"], "lychee_latest.json", (0, 2), 1200),
]


def now():
    return datetime.now(timezone.utc).isoformat()


def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript('''
      CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, started_at TEXT, finished_at TEXT,
          mode TEXT, status TEXT, artifact_dir TEXT);
      CREATE TABLE IF NOT EXISTS stages(run_id TEXT, name TEXT, status TEXT, source_modified_at TEXT,
          sha256 TEXT, artifact TEXT, error TEXT, PRIMARY KEY(run_id,name),
          FOREIGN KEY(run_id) REFERENCES runs(id));
      CREATE TABLE IF NOT EXISTS issues(id TEXT PRIMARY KEY, scope TEXT, url TEXT, kind TEXT,
          detail TEXT, priority INTEGER, state TEXT, first_run TEXT, last_seen_run TEXT, resolved_run TEXT);
      CREATE TABLE IF NOT EXISTS observations(run_id TEXT, issue_id TEXT, transition TEXT,
          PRIMARY KEY(run_id,issue_id), FOREIGN KEY(run_id) REFERENCES runs(id));
      CREATE TABLE IF NOT EXISTS changes(id INTEGER PRIMARY KEY, recorded_at TEXT, url TEXT, note TEXT);
    ''')
    return db


def issue(scope, url, kind, detail, priority):
    key = hashlib.sha256(json.dumps([scope,url,kind,detail], ensure_ascii=False).encode()).hexdigest()
    return dict(id=key, scope=scope, url=url, kind=kind, detail=detail, priority=priority)


def findings(stage, data):
    out, coverage = [], set()
    if stage == "growth":
        for name, site in data.get("sites", {}).items():
            live_urls = {page["url"] for page in site.get("audit", [])}
            for page in site.get("audit", []):
                scope = f"audit:{name}:{page['url']}"
                details = page.get("issues", [])
                if (page.get("page_status") == 200 and page.get("body_observed")) or not any(d.startswith(("unverified response", "page response")) for d in details):
                    coverage.add(scope)
                for detail in page.get("issues", []):
                    priority = 40
                    kind = "technical"
                    if detail.startswith("broken"):
                        kind = "broken-link"
                        target = detail.split(": ", 1)[-1]
                        priority = 100 if urlparse(target).hostname == urlparse(page["url"]).hostname else 75
                    elif detail.startswith("unverified"): priority = 15; kind = "verify-response"
                    elif "canonical" in detail or detail == "noindex": priority = 95
                    elif "meta description" in detail or "HTML title" in detail:
                        priority = 45; kind = "metadata-review"
                    elif "image" in detail: priority = 80
                    elif "incoming links" in detail: priority = 55
                    out.append(issue(scope, page["url"], kind, detail, priority))
            for row in site.get("indexing", []):
                scope = f"indexing:{name}:{row['url']}"
                if row.get("error") or not row.get("verdict"):
                    out.append(issue(scope, row["url"], "data-unavailable",
                                     "Google indexing inspection unavailable: " + str(row.get("error", "Missing verdict")), 85))
                    continue
                coverage.add(scope)
                if row["verdict"] != "PASS":
                    state = row.get("coverageState") or "Unspecified Google indexing state"
                    priority = 100 if row.get("pageFetchState") == "REDIRECT_ERROR" or row.get("indexingState") == "BLOCKED_BY_META_TAG" else 95
                    out.append(issue(scope, row["url"], "indexing-blocker", "Google index status: " + state, priority))
            for row in site.get("historical_url_checks", []):
                scope = f"historical-url:{name}:{row['url']}"
                if row.get("status") in (404, 410):
                    coverage.add(scope)
                    out.append(issue(scope, row["url"], "historical-url",
                                     f"Previously visible GSC URL currently returns {row['status']}", 90))
                elif row.get("status") is not None:
                    coverage.add(scope)
                    if row.get("redirected") and row.get("final_url") not in live_urls:
                        out.append(issue(scope, row["url"], "redirect-review",
                                         "Previously visible URL now redirects to " + row["final_url"], 60))
            # Opportunities are recommendations, not technical failures. Only complete GSC data can refresh them.
            if not site.get("gsc_error") and "priority_pages" in site:
                scope = f"opportunities:{name}"; coverage.add(scope)
                for page in site["priority_pages"]:
                    out.append(issue(scope, page["url"], "content-opportunity", page["action"], 45))
            for key in ("gsc_error", "ga_error", "crawl_error", "indexing_error"):
                scope = f"availability:{name}:{key}"
                coverage.add(scope)
                if site.get(key): out.append(issue(scope,name,"data-unavailable",str(site[key]),85))
    elif stage == "competitors":
        for row in data.get("articles", []):
            scope = "competitors:" + row["url"]
            coverage.add(scope)
            if row.get("status") != "comparison_complete":
                out.append(issue(scope, row["url"], "competitor-research",
                    "Competitor coverage: " + row.get("status", "unavailable"), 35))
            elif row.get("topic_review_candidates"):
                out.append(issue(scope, row["url"], "content-review",
                    "Review recurring competitor topics against reader intent and verified sources", 40))
        for key in ("inventory_refresh_error", "discovery_error"):
            scope = "availability:competitors:" + key
            coverage.add(scope)
            if data.get(key):
                out.append(issue(scope, "competitors", "data-unavailable", str(data[key]), 85))
    elif stage == "writing":
        for page in data.get("files", []):
            url = page["file"]; scope = f"writing:{url}"
            if not page.get("vale_error"):
                coverage.add(scope)
            for sentence in page.get("long_sentences_over_30_words", []):
                out.append(issue(scope,url,"writing-review","Long sentence: " + sentence,25))
            for matches in page.get("vale", {}).values():
                for match in matches:
                    detail = f"{match.get('Check')}: {match.get('Message')} [{match.get('Match', '')}]"
                    out.append(issue(scope,url,"writing-review",detail,30))
            if page.get("vale_error"):
                out.append(issue(scope,url,"data-unavailable",page["vale_error"],70))
    elif stage == "links":
        # The links stage always checks this explicit input. Missing reports never reach this branch.
        source = "pillar_free_ai_courses_2026.html"
        all_errors = [e for errors in data.get("error_map", {}).values() for e in errors]
        reliable = data.get("exit_code", 0) in (0, 2) and not data.get("timeouts") and all(e.get("status", {}).get("code") in (404,410) for e in all_errors)
        inputs = data.get("input_sources", {})
        # A completed manifest-backed run observed every supplied article body.
        # Target-specific unknown responses are preserved by reconcile's guard;
        # unrelated blocked URLs must not retain a removed iframe/link forever.
        manifest_observed = bool(inputs) and data.get("exit_code") in (0, 2)
        if manifest_observed:
            coverage.update("lychee:" + url for url in inputs.values())
        if reliable:
            coverage.update("lychee:" + url for url in inputs.values())
            for target in data.get("explicit_targets", [source] if not inputs else []):
                coverage.add("lychee:" + target)
        for source, errors in data.get("error_map", {}).items():
            source = inputs.get(source, source)
            scope = f"lychee:{source}"
            if reliable: coverage.add(scope)
            for error in errors:
                status = error.get("status", {})
                code = status.get("code")
                kind = "broken-link" if code in (404,410) else "verify-response"
                detail = f"{status.get('text', 'Link check failed')}: {error.get('url')}"
                out.append(issue(scope,source,kind,detail,75 if code in (404,410) else 15))
    return out, coverage


def reconcile(db, run_id, items, coverage):
    """Resolve only issues whose source was successfully re-evaluated in this run."""
    unique = {r["id"]: r for r in items}
    # A successfully read article can prove that a link was removed or markup
    # repaired even when a different external target blocks our crawler.
    # Keep earlier target-specific findings open when that same target is unknown.
    blocked_targets = {(r["scope"], r["detail"].split(": ", 1)[-1])
                       for r in items if r["kind"] == "verify-response"}
    counts = dict(new=0, persistent=0, reopened=0, resolved=0)
    with db:
        for key, row in unique.items():
            previous = db.execute("SELECT state FROM issues WHERE id=?", (key,)).fetchone()
            transition = "new" if previous is None else "reopened" if previous["state"] == "resolved" else "persistent"
            counts[transition] += 1
            db.execute('''INSERT INTO issues(id,scope,url,kind,detail,priority,state,first_run,last_seen_run)
                VALUES(:id,:scope,:url,:kind,:detail,:priority,'open',:run,:run)
                ON CONFLICT(id) DO UPDATE SET priority=excluded.priority,state='open',
                last_seen_run=excluded.last_seen_run,resolved_run=NULL''', {**row,"run":run_id})
            db.execute("INSERT OR REPLACE INTO observations VALUES(?,?,?)", (run_id,key,transition))
        for old in db.execute("SELECT id,scope,detail FROM issues WHERE state='open'").fetchall():
            if (old["scope"], old["detail"].split(": ", 1)[-1]) in blocked_targets:
                continue
            if old["scope"] in coverage and old["id"] not in unique:
                db.execute("UPDATE issues SET state='resolved',resolved_run=? WHERE id=?", (run_id,old["id"]))
                db.execute("INSERT OR REPLACE INTO observations VALUES(?,?,?)", (run_id,old["id"],"resolved"))
                counts["resolved"] += 1
    return counts


def validate(name, data):
    if not isinstance(data, dict): raise ValueError("Expected JSON object")
    required = {"growth":"sites", "writing":"files", "links":"error_map", "competitors":"articles"}[name]
    if required not in data: raise ValueError(f"Missing report field: {required}")


@contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try: fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise SystemExit("Another workbench job is running")
        try: yield
        finally: fcntl.flock(handle, fcntl.LOCK_UN)


def export_queue(db, path, run_id, counts):
    rows = [dict(r) for r in db.execute("SELECT * FROM issues WHERE state='open' ORDER BY priority DESC,url,kind")]
    lines = ["# SEO workbench action queue", "", f"Run: {run_id}", "",
             f"New: {counts['new']}; persistent: {counts['persistent']}; reopened: {counts['reopened']}; resolved: {counts['resolved']}.",
             "", "Analysis suggestions only. Cached evidence retains its original timestamp; an unobserved issue is not assumed fixed.",
             "", "| Priority | Page or file | Type | Action/evidence |", "|---:|---|---|---|"]
    for row in rows:
        clean = lambda s: str(s).replace("|","/").replace("\n"," ")
        lines.append(f"| {row['priority']} | {clean(row['url'])} | {row['kind']} | {clean(row['detail'])} |")
    stage_rows = [dict(r) for r in db.execute("SELECT name,status,source_modified_at,error FROM stages WHERE run_id=?", (run_id,))]
    lines.extend(["", "## Evidence availability", ""])
    for stage in stage_rows: lines.append(f"- {stage['name']}: {stage['status']}; source timestamp: {stage['source_modified_at'] or 'unavailable'}; {stage['error'] or ''}".rstrip())
    path.write_text("\n".join(lines)+"\n")
    path.with_suffix(".json").write_text(json.dumps({"run_id":run_id,"transitions":counts,"stages":stage_rows,"queue":rows},indent=2))
    return len(rows)


def run_job(args):
    if args.dry_run:
        print("Mode:", "refresh read-only measurements" if args.refresh else "import cached reports; no network")
        for name, command, artifact, _, _ in STAGES:
            print(name, " ".join([sys.executable,*command]) if args.refresh else f"reports/{artifact}")
        print("Writes local SQLite history and immutable report snapshots. No publishing commands.")
        return
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    folder = BASE / "reports/workbench" / run_id
    with lock(BASE / "research/workbench.lock"):
        db = connect(args.database)
        folder.mkdir(parents=True)
        scripts = {part for _, command, _, _, _ in STAGES for part in command if part.endswith('.py')}
        (folder / "manifest.json").write_text(json.dumps({"run_id":run_id,"created_at":now(),
            "mode":"refresh" if args.refresh else "cached", "python":sys.version,
            "script_sha256":{name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in sorted(scripts)},
            "external_mutations":False},indent=2))
        with db:
            db.execute("INSERT INTO runs VALUES(?,?,NULL,?,'running',?)", (run_id,now(),"refresh" if args.refresh else "cached",str(folder)))
        items, coverage, failed = [], set(), False
        try:
            for name, command, filename, codes, timeout in STAGES:
                source = BASE / "reports" / filename
                status = "cached"; error = None; stamp = None; digest = None; snapshot = None
                before = source.stat().st_mtime_ns if source.exists() else None
                try:
                    if args.refresh:
                        print(f"Running {name}…", flush=True)
                        process = subprocess.run([sys.executable,*command], cwd=BASE, capture_output=True,text=True,timeout=timeout)
                        (folder / f"{name}.log").write_text(process.stdout + "\n" + process.stderr)
                        if process.returncode not in codes: raise ValueError(f"Stage exited {process.returncode}; see {name}.log")
                        if not source.exists() or source.stat().st_mtime_ns == before: raise ValueError("Stage did not produce a fresh report")
                        status = "completed"
                    if not source.exists(): raise FileNotFoundError("No saved report; run with --refresh")
                    raw = source.read_bytes(); data = json.loads(raw); validate(name,data)
                    stamp = data.get("source_evidence_at") or datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat()
                    digest = hashlib.sha256(raw).hexdigest()
                    snapshot = folder / filename; snapshot.write_bytes(raw)
                    found, observed = findings(name,data); items.extend(found); coverage.update(observed)
                    if name == "competitors" and (data.get("inventory_refresh_error") or data.get("discovery_error") or any(r.get("status") != "comparison_complete" for r in data["articles"])):
                        status = "partial"; failed = True
                        error = "Competitor comparisons pending or incomplete; see article coverage report"
                    if name == "growth" and any(k.endswith("_error") for site in data["sites"].values() for k in site):
                        status = "partial"; failed = True
                except Exception as exc:
                    status = "unavailable" if isinstance(exc,FileNotFoundError) else "failed"
                    error = str(exc)[:300]; failed = True
                with db:
                    db.execute("INSERT INTO stages VALUES(?,?,?,?,?,?,?)", (run_id,name,status,stamp,digest,str(snapshot) if snapshot else None,error))
                print(f"{name}: {status}" + (f" ({error})" if error else ""), flush=True)
            counts = reconcile(db,run_id,items,coverage)
            queue = folder / "action_queue.md"
            total = export_queue(db,queue,run_id,counts)
            with db: db.execute("UPDATE runs SET finished_at=?,status=? WHERE id=?", (now(),"partial" if failed else "completed",run_id))
            for suffix in (".md",".json"):
                shutil.copyfile(queue.with_suffix(suffix), BASE / "reports" / ("action_queue_latest" + suffix))
            print(f"Saved {total} open actions: {queue}")
            print(json.dumps(counts))
        except BaseException:
            with db: db.execute("UPDATE runs SET finished_at=?,status='failed' WHERE id=?", (now(),run_id))
            raise
        finally: db.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--database",type=Path,default=BASE / "research/workbench.sqlite")
    sub = p.add_subparsers(dest="command",required=True)
    run = sub.add_parser("run"); run.add_argument("--refresh",action="store_true"); run.add_argument("--dry-run",action="store_true")
    improve = sub.add_parser("improve"); improve.add_argument("--apply",action="store_true"); improve.add_argument("--dry-run",action="store_true")
    sub.add_parser("history"); sub.add_parser("queue")
    change = sub.add_parser("record-change"); change.add_argument("url"); change.add_argument("note")
    args = p.parse_args()
    if args.command == "improve":
        commands = [[sys.executable,"seo_workbench.py","run","--refresh"],
                    [sys.executable,"article_improver.py","plan"]]
        if args.apply:
            commands.append([sys.executable,"article_improver.py","apply"])
            commands.append([sys.executable,"seo_workbench.py","run","--refresh"])
        if args.dry_run:
            for command in commands: print(" ".join(command))
            return
        for command in commands:
            subprocess.run(command,cwd=BASE,check=True)
        return
    if args.command == "run": return run_job(args)
    db = connect(args.database)
    if args.command == "history": rows = db.execute("SELECT * FROM runs ORDER BY started_at DESC LIMIT 20").fetchall()
    elif args.command == "queue": rows = db.execute("SELECT url,kind,priority,detail FROM issues WHERE state='open' ORDER BY priority DESC LIMIT 30").fetchall()
    else:
        with db: db.execute("INSERT INTO changes(recorded_at,url,note) VALUES(?,?,?)", (now(),args.url,args.note))
        print("Editorial change recorded locally"); return
    print(json.dumps([dict(r) for r in rows],indent=2))


if __name__ == "__main__": main()
