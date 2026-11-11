#!/usr/bin/env python3
"""Local multi-blog SEO Dashboard — Flask backend.

Run:  /home/kwikcoders/.local/share/claude-seo/.venv/bin/python dashboard/app.py
Open: http://localhost:5000
"""
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request

from flask import Flask, jsonify, request, send_from_directory

BASE = "/home/kwikcoders/seo"
VP = "/home/kwikcoders/.local/share/claude-seo/.venv/bin/python"
SEO_BIN = "/home/kwikcoders/.claude/plugins/cache/agricidaniel-claude-seo/claude-seo/2.2.4/bin/claude-seo"
CONF = os.path.expanduser("~/.config/claude-seo")
BING = "https://ssl.bing.com/webmaster/api.svc/json"

app = Flask(__name__)

SITES = {
    "studenttimepk": {
        "name": "Students Time", "blog_id": "8491425780932094856",
        "url": "https://studenttimepk.blogspot.com/", "domain": "studenttimepk.blogspot.com",
        "gsc": "sc-domain:studenttimepk.blogspot.com", "bing": "https://studenttimepk.blogspot.com",
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
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    tok = json.load(open(os.path.join(CONF, "oauth-token.json")))
    c = Credentials(token=tok["access_token"], refresh_token=tok.get("refresh_token"),
                    token_uri=tok["token_uri"], client_id=tok["client_id"],
                    client_secret=tok["client_secret"], scopes=tok.get("scopes"))
    if not c.valid:
        c.refresh(Request())
    return c


def run_seo(args, timeout=120):
    env = dict(os.environ, PYTHONWARNINGS="ignore")
    out = subprocess.run([SEO_BIN, "run"] + args, capture_output=True, text=True, env=env, timeout=timeout)
    try:
        return json.loads(out.stdout)
    except Exception:
        return {}


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


@app.route("/api/overview")
def overview():
    s = site_cfg()
    tools = {
        "Search Console": bool(s["gsc"]),
        "Bing": bool(s["bing"]),
        "PageSpeed": os.path.exists(os.path.join(BASE, "psi_key.txt")),
        "AdSense": os.path.exists(os.path.join(CONF, "oauth-token.json")),
        "Trends": True, "Rank Checker": os.path.exists(os.path.join(BASE, "cse_cx.txt")),
    }
    clicks = impressions = 0
    stage = 0  # 0 submitted, 1 discovered, 2 indexed, 3 ranking
    if s["gsc"]:
        d = run_seo(["gsc_query.py", "query", "-p", s["gsc"], "--days", "28",
                     "--dimensions", "query", "--limit", "1", "--json"], timeout=60)
        t = d.get("totals", {})
        clicks, impressions = t.get("clicks", 0), t.get("impressions", 0)
        stage = 3 if impressions > 0 else 1  # submitted+discovered baseline
    pillars = len(s["pillars"])
    return jsonify({
        "site": {"key": request.args.get("site", "studenttimepk"), "name": s["name"], "domain": s["domain"]},
        "tools": tools,
        "signal": {"stage": stage, "clicks": clicks, "impressions": impressions},
        "counts": {"pillars": pillars, "has_queue": s["has_queue"]},
    })


@app.route("/api/gsc")
def gsc():
    s = site_cfg()
    if not s["gsc"]:
        return jsonify({"connected": False})
    d = run_seo(["gsc_query.py", "query", "-p", s["gsc"], "--days", "28",
                 "--dimensions", "query", "--limit", "50", "--json"], timeout=60)
    rows = d.get("rows", [])
    def kw(r):
        return r.get("keys", [""])[0] if isinstance(r.get("keys"), list) else r.get("query", "")
    top = [{"kw": kw(r), "clicks": r.get("clicks", 0), "impr": r.get("impressions", 0),
            "pos": round(r.get("position", 0), 1)} for r in rows[:10]]
    strike = sorted([{"kw": kw(r), "pos": round(r.get("position", 0), 1), "impr": r.get("impressions", 0)}
                     for r in rows if 8 <= r.get("position", 99) <= 20], key=lambda x: -x["impr"])[:10]
    return jsonify({"connected": True, "totals": d.get("totals", {}),
                    "row_count": d.get("row_count", 0), "top": top, "striking": strike})


@app.route("/api/index")
def index_status():
    s = site_cfg()
    pages = s["pillars"] or [("Homepage", s["url"])]
    site_url = s["gsc"] if (s["gsc"] and s["gsc"].startswith("http")) else s["url"]
    out = []
    for name, url in pages[:8]:
        r = run_seo(["gsc_inspect.py", url, "-s", site_url, "--json"], timeout=45)
        out.append({"name": name, "url": url,
                    "coverage": (r.get("index_status") or {}).get("coverage_state", "unknown")})
    return jsonify({"pages": out})


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
            metrics=["ESTIMATED_EARNINGS", "PAGE_VIEWS", "CLICKS", "IMPRESSIONS"]).execute()
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
    cx, key = read("cse_cx.txt"), (read("cse_key.txt") or read("psi_key.txt"))
    if not cx:
        return jsonify({"ok": False, "msg": "Add a Custom Search Engine ID first."})
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
                                for i, it in enumerate(items[:5], 1)]})
    except Exception as e:
        m = str(e)
        if "403" in m:
            return jsonify({"ok": False, "msg": "Allow 'Custom Search API' on your API key (propagating)."})
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
