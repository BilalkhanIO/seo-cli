#!/usr/bin/env python3
"""Local multi-blog SEO Dashboard — Flask backend.

Run:  /home/kwikcoders/.local/share/claude-seo/.venv/bin/python dashboard/app.py
Open: http://localhost:5000
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".tools/competitor-deps"))
from flask import Flask, jsonify, request, send_from_directory

BASE = str(Path(__file__).resolve().parent.parent)
VP = os.environ.get("SEO_PYTHON", sys.executable)
SEO_BIN = os.environ.get("SEO_CLI", "claude-seo")
CONF = os.path.expanduser("~/.config/claude-seo")
BING = "https://ssl.bing.com/webmaster/api.svc/json"

app = Flask(__name__)

SITES = {
    "studenttimepk": {
        "name": "Students Time", "blog_id": "8491425780932094856",
        "url": "https://studenttimepk.blogspot.com/", "domain": "studenttimepk.blogspot.com",
        "gsc": "https://studenttimepk.blogspot.com/", "bing": "https://studenttimepk.blogspot.com",
        "pillars": [
            ("Free AI Courses w/ Certificates", "https://studenttimepk.blogspot.com/2026/07/free-ai-courses-with-certificates-in.html"),
            ("GPT-5.6 for Developers", "https://studenttimepk.blogspot.com/2026/07/gpt-56-goes-public-what-developers.html"),
            ("Google Antigravity 2.0", "https://studenttimepk.blogspot.com/2026/07/google-antigravity-20-ai-agents-for.html"),
            ("EU AI Act 2026", "https://studenttimepk.blogspot.com/2026/08/eu-ai-act-updates-what-developers-must.html"),
            ("Best AI Coding Tools", "https://studenttimepk.blogspot.com/2026/07/ai-dev-tools-boom-what-build-2026.html"),
            ("AI Security for Developers", "https://studenttimepk.blogspot.com/2026/08/ai-in-dev-why-fixing-vulnerabilities-is.html"),
            ("OpenAI Astra", "https://studenttimepk.blogspot.com/2026/08/openai-astra-next-gen-ai-model-and-what.html"),
            ("AI Agents Explained", "https://studenttimepk.blogspot.com/2025/10/mastering-ai-agent-orchestration-rise.html"),
        ],
        "has_queue": True,
    },
    "learners-link": {
        "name": "Learner's Link", "blog_id": "6645616362681304579",
        "url": "https://learners-link.blogspot.com/", "domain": "learners-link.blogspot.com",
        "gsc": "https://learners-link.blogspot.com/", "bing": "https://learners-link.blogspot.com",
        "pillars": [], "has_queue": False,
    },
    "bilalkhanio": {
        "name": "Bilal ahmad", "blog_id": "6972553316867220010",
        "url": "https://bilalkhanio.blogspot.com/", "domain": "bilalkhanio.blogspot.com",
        "gsc": None, "bing": None, "pillars": [], "has_queue": False,
    },
}


def site_cfg():
    return SITES.get(request.args.get("site", "studenttimepk"), SITES["studenttimepk"])


def creds():
    if BASE not in sys.path:
        sys.path.insert(0, BASE)
    from weekly_report import creds as shared_creds
    return shared_creds()


def run_seo(args, timeout=120):
    env = dict(os.environ, PYTHONWARNINGS="ignore")
    try:
        out = subprocess.run([SEO_BIN, "run"] + args, capture_output=True, text=True, env=env, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": "SEO CLI unavailable: " + type(exc).__name__}
    try:
        return json.loads(out.stdout)
    except Exception:
        return {"error": "SEO CLI returned invalid or unavailable data"}


def read(p):
    fp = os.path.join(BASE, p)
    return open(fp).read().strip() if os.path.exists(fp) else None


@app.route("/")
def index():
    return send_from_directory(os.path.dirname(__file__), "index.html")


@app.route("/api/sites")
def sites():
    return jsonify({"sites": [{"key": k, "name": v["name"], "domain": v["domain"],
                               "gsc": bool(v["gsc"]), "bing": bool(v["bing"])}
                              for k, v in SITES.items()]})


def saved_growth(site):
    path = Path(BASE) / "reports/growth_latest.json"
    try:
        report = json.loads(path.read_text())
        data = report.get("sites", {}).get(site["name"])
        if data is None:
            raise ValueError("No site evidence")
        return data, {"window":report.get("current_window"),
            "source_modified_at":datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(), "cached":True}
    except (OSError, ValueError):
        return {}, {"error":"Saved site measurements unavailable; refresh the workbench", "cached":True}


@app.route("/api/overview")
def overview():
    site = site_cfg(); data, evidence = saved_growth(site)
    current = data.get("current", {}) if not data.get("gsc_error") else {}
    tools = {"Search Console":bool(site["gsc"]), "Bing":bool(site["bing"]),
        "PageSpeed":bool(read("psi_key.txt")), "AdSense":True, "Trends":True,
        "Rank Checker":bool(read("cse_cx.txt") and read("cse_key.txt"))}
    return jsonify({"site":{"name":site["name"], "domain":site["domain"]}, "tools":tools,
        "signal":{"stage":None, "clicks":current.get("clicks"), "impressions":current.get("impressions")},
        "counts":{"pillars":len(site["pillars"]), "has_queue":site["has_queue"]},
        "evidence":evidence, "error":data.get("gsc_error") or evidence.get("error")})


@app.route("/api/gsc")
def gsc():
    site = site_cfg(); data, evidence = saved_growth(site)
    if not site["gsc"] or data.get("gsc_error") or not data.get("current"):
        return jsonify({"connected":False, "error":data.get("gsc_error") or evidence.get("error") or "Measurements unavailable", "evidence":evidence})
    rows = data.get("queries", [])
    grouped = {}
    for row in rows:
        query = row.get("keys", [""])[0]
        item = grouped.setdefault(query,{"kw":query,"clicks":0,"impr":0,"weight":0})
        impressions = row.get("impressions",0)
        item["clicks"] += row.get("clicks",0); item["impr"] += impressions
        item["weight"] += row.get("position",0)*impressions
    visible = [{**item, "pos":round(item["weight"]/item["impr"],1) if item["impr"] else None} for item in grouped.values()]
    visible.sort(key=lambda x:-x["impr"])
    return jsonify({"connected":True, "totals":data["current"], "row_count":len(visible),
        "top":visible[:10], "striking":[r for r in visible if r["pos"] is not None and 8<=r["pos"]<=20][:10], "evidence":evidence})


@app.route("/api/index")
def index_status():
    data,evidence = saved_growth(site_cfg())
    return jsonify({"pages":[{"name":r["url"],"url":r["url"], "coverage":r.get("coverageState") or r.get("error") or "Unavailable",
        "last_crawl":r.get("lastCrawlTime")} for r in data.get("indexing", [])],
        "evidence":evidence, "note":"Stored Google records; live-test and current index inclusion remain separate."})


@app.route("/api/bing")
def bing():
    s = site_cfg()
    k = read("bing_key.txt")
    if not k or not s["bing"]:
        return jsonify({"connected": False})
    try:
        q = json.loads(urllib.request.urlopen(
            f"{BING}/GetUrlSubmissionQuota?apikey={k}&siteUrl={s['bing']}", timeout=20).read().decode()).get("d", {})
        return jsonify({"connected": True, "daily": q.get("DailyQuota"), "monthly": q.get("MonthlyQuota")})
    except Exception as e:
        return jsonify({"connected": False, "error": str(e)[:100]})


@app.route("/api/adsense")
def adsense():
    try:
        from googleapiclient.discovery import build
        svc = build("adsense", "v2", credentials=creds(), cache_discovery=False)
        accts = svc.accounts().list().execute().get("accounts", [])
        if not accts:
            return jsonify({"connected": False, "msg": "No AdSense account."})
        acct = accts[0]["name"]
        rep = svc.accounts().reports().generate(
            account=acct, dateRange="LAST_30_DAYS",
            metrics=["ESTIMATED_EARNINGS", "PAGE_VIEWS", "CLICKS", "IMPRESSIONS"],
            filters=["DOMAIN_NAME==" + site_cfg()["domain"]]).execute()
        headers = [h.get("name") for h in rep.get("headers", [])]
        cells = [c.get("value") for c in rep.get("totals", {}).get("cells", [])]
        cur = next((h.get("currencyCode") for h in rep.get("headers", []) if h.get("currencyCode")), "")
        return jsonify({"connected": True, "account": accts[0].get("displayName", acct),
                        "currency": cur, "metrics": dict(zip(headers, cells))})
    except Exception as e:
        m = str(e)
        if "insufficient" in m.lower() or "scope" in m.lower():
            return jsonify({"connected": False, "msg": "Authorize AdSense."})
        return jsonify({"connected": False, "error": m[:160]})


@app.route("/api/rankcheck")
def rankcheck():
    s = site_cfg()
    q = request.args.get("q", "")
    cx, key = read("cse_cx.txt"), read("cse_key.txt")
    if not cx or not key:
        return jsonify({"ok": False, "msg": "Rank source unavailable. Configure an eligible existing Custom Search account or import SERP results; the comparison report shows pending coverage."})
    if not q:
        return jsonify({"ok": False, "msg": "Enter a keyword."})
    try:
        url = "https://www.googleapis.com/customsearch/v1?" + urllib.parse.urlencode(
            {"key": key, "cx": cx, "q": q, "num": 10})
        d = json.loads(urllib.request.urlopen(url, timeout=20).read().decode())
        items = d.get("items", [])
        pos = next((i for i, it in enumerate(items, 1) if s["domain"] in it.get("link", "")), None)
        return jsonify({"ok": True, "q": q, "position": pos,
                        "top": [{"pos": i, "title": it.get("title"), "link": it.get("link")}
                                for i, it in enumerate(items[:10], 1)]})
    except Exception as e:
        m = str(e)
        if "403" in m:
            return jsonify({"ok": False, "msg": "Custom Search access unavailable. Verify account eligibility, API restrictions and quota."})
        return jsonify({"ok": False, "error": m[:160]})


@app.route("/api/trends")
def trends():
    seeds = [x.strip() for x in request.args.get("seeds", "free ai course").split(",") if x.strip()]
    env = dict(os.environ, PYTHONWARNINGS="ignore")
    out = subprocess.run([VP, os.path.join(BASE, "trends_research.py")] + seeds + ["--geo", request.args.get("geo", "PK")],
                         capture_output=True, text=True, env=env, timeout=90)
    return jsonify({"output": out.stdout or out.stderr})


@app.route("/api/pagespeed")
def pagespeed():
    s = site_cfg()
    url = request.args.get("url") or (s["pillars"][0][1] if s["pillars"] else s["url"])
    key = read("psi_key.txt")
    args = ["pagespeed_check.py", url, "--strategy", "mobile", "--json"]
    if key:
        args += ["--api-key", key]
    d = run_seo(args, timeout=90)
    m = d.get("psi", {}).get("mobile", {})
    return jsonify({"scores": m.get("lighthouse_scores", {}), "error": m.get("error"), "url": url})


@app.route("/api/action/<name>", methods=["POST"])
def action(name):
    script = {"bing-submit": "bing_submit.py", "monitor": "gsc_monitor.py"}.get(name)
    if not script:
        return jsonify({"output": "unknown action"})
    env = dict(os.environ, PYTHONWARNINGS="ignore")
    out = subprocess.run([VP, os.path.join(BASE, script)], capture_output=True, text=True, env=env, timeout=180)
    return jsonify({"output": out.stdout or out.stderr})


@app.route("/api/workbench")
def workbench():
    site = site_cfg()
    def artifact(filename):
        path = Path(BASE) / filename
        try:
            value = json.loads(path.read_text())
            return value, datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(), None
        except (OSError, ValueError):
            return {}, None, "Report unavailable"
    comparison, stamp, error = artifact("reports/article_competitor_latest.json")
    rows = [r for r in comparison.get("articles", []) if urllib.parse.urlparse(r.get("url", "")).hostname == site["domain"]]
    queue, queue_stamp, queue_error = artifact("reports/action_queue_latest.json")
    actions = [r for r in queue.get("queue", []) if urllib.parse.urlparse(r.get("url", "")).hostname == site["domain"]]
    context, _, _ = artifact("research/project_context.json")
    key = {"studenttimepk":"st", "learners-link":"ll"}.get(request.args.get("site", "studenttimepk"))
    goals = context.get("sites", {}).get(key, {}).get("goals", [])
    today = datetime.now(ZoneInfo("Asia/Karachi")).date().isoformat()
    goals = [g for g in goals if g.get("status") == "active" and (not g.get("due_date") or g["due_date"] >= today)]
    return jsonify({"site":site["name"], "goals":goals,
        "competitors":{"published_articles":len(rows), "coverage":dict(Counter(r.get("status", "unavailable") for r in rows)),
            "created_at":comparison.get("created_at"), "source_modified_at":stamp,
            "inventory_modified_at":comparison.get("inventory_modified_at"),
            "inventory_refresh_error":comparison.get("inventory_refresh_error"), "error":error},
        "queue":{"run_id":queue.get("run_id"), "source_modified_at":queue_stamp,
            "stages":queue.get("stages", []), "actions":actions, "error":queue_error}})


@app.route("/api/queue")
def queue():
    s = site_cfg()
    if not s["has_queue"]:
        return jsonify({"groups": []})
    text = read("SEO-PLAYBOOK.md") or ""
    blocks = re.findall(r"\*\*→ ([^*]+)\*\* `To: ([^`]+)`\n```\n(.*?)```", text, re.S)
    return jsonify({"groups": [{"name": n.strip(), "to": t.strip(),
                                "from": [u for u in urls.strip().splitlines() if u.strip()]}
                               for n, t, urls in blocks]})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
