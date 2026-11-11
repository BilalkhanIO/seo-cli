#!/usr/bin/env python3
"""Weekly SEO monitor for studenttimepk — run on a schedule.

Pulls GSC data and surfaces:
  - Total clicks/impressions trend
  - "Striking distance" keywords (position 8-20) = quickest ranking wins
  - Index status of key pillar pages
Outputs a plain-text report to stdout + seo_report_latest.txt
"""
import json
import os
import subprocess

SEO = "/home/kwikcoders/.claude/plugins/cache/agricidaniel-claude-seo/claude-seo/2.2.4/bin/claude-seo"
PROP = "sc-domain:studenttimepk.blogspot.com"
SITE = "https://studenttimepk.blogspot.com/"
PILLARS = [
    "https://studenttimepk.blogspot.com/",
    "https://studenttimepk.blogspot.com/2026/07/free-ai-courses-with-certificates-in.html",
    "https://studenttimepk.blogspot.com/2026/07/gpt-56-goes-public-what-developers.html",
    "https://studenttimepk.blogspot.com/2026/07/google-antigravity-20-ai-agents-for.html",
]


def run(args):
    env = dict(os.environ, PYTHONWARNINGS="ignore")
    out = subprocess.run([SEO, "run"] + args, capture_output=True, text=True, env=env)
    try:
        return json.loads(out.stdout)
    except Exception:
        return {}


def main():
    lines = ["===== WEEKLY SEO REPORT — studenttimepk =====\n"]

    d = run(["gsc_query.py", "query", "-p", PROP, "--days", "28",
             "--dimensions", "query", "--limit", "100", "--json"])
    tot = d.get("totals", {})
    lines.append(f"28-day totals: {tot.get('clicks',0)} clicks / {tot.get('impressions',0)} impressions "
                 f"| avg pos {tot.get('position',0):.1f}\n")
    rows = d.get("rows", [])

    # Striking distance: position 8-20, sorted by impressions
    strike = []
    for r in rows:
        pos = r.get("position", 99)
        k = r.get("keys", [""])[0] if isinstance(r.get("keys"), list) else r.get("query", "")
        if 8 <= pos <= 20:
            strike.append((r.get("impressions", 0), pos, k))
    strike.sort(reverse=True)
    lines.append("\n--- STRIKING-DISTANCE KEYWORDS (pos 8-20 = quick wins) ---")
    if strike:
        for imp, pos, k in strike[:15]:
            lines.append(f"  pos {pos:>4.1f} | {imp:>4} impr | {k}")
    else:
        lines.append("  (none yet — site needs impressions first; keep fixing indexing/content)")

    lines.append("\n--- INDEX STATUS: pillar pages ---")
    for u in PILLARS:
        r = run(["gsc_inspect.py", u, "-s", SITE, "--json"])
        idx = r.get("index_status") or {}
        lines.append(f"  {idx.get('coverage_state','?'):<35} {u}")

    report = "\n".join(lines)
    print(report)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "seo_report_latest.txt"), "w") as f:
        f.write(report)


if __name__ == "__main__":
    main()
