#!/usr/bin/env python3
"""SERP analysis — the 'steal from the SERP' step (from the SEO masterclasses).
Given a keyword + the top-ranking competitor URLs, fetch each, measure word count
and extract headings, then output a target length (SERP median) + a topic checklist
(heading union) so our post covers everything and matches/beats the length.
Usage: python serp_analysis.py "keyword" <url1> <url2> ... [--mine=N]
"""
import re, sys, statistics, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}


def fetch(url):
    try:
        html = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "replace")
    except Exception as e:
        return None, f"fetch failed ({str(e)[:30]})", []
    # isolate <body>, strip script/style/nav/header/footer
    body = re.search(r"<body[^>]*>(.*)</body>", html, re.S | re.I)
    h = body.group(1) if body else html
    h = re.sub(r"<(script|style|nav|header|footer|form|noscript)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    heads = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<h2[^>]*>(.*?)</h2>", h, re.S | re.I)]
    heads = [x for x in heads if 3 < len(x) < 90][:12]
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()
    return len(text.split()), None, heads


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print('Usage: python serp_analysis.py "keyword" <url1> <url2> ...'); return
    kw, urls = args[0], args[1:]
    mine = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--mine=")), None)
    print(f"SERP analysis: '{kw}'  ({len(urls)} competitors)\n")
    counts, all_heads = [], []
    for u in urls:
        wc, err, heads = fetch(u)
        host = re.sub(r"^https?://(www\.)?", "", u).split("/")[0]
        if err:
            print(f"  {host[:28]:28}  {err}")
        else:
            counts.append(wc); all_heads += heads
            print(f"  {host[:28]:28}  {wc:>5} words | {len(heads)} H2s")
    if not counts:
        print("\n(all competitors blocked scraping — use manual word counts)"); return
    med = int(statistics.median(counts)); avg = int(statistics.mean(counts))
    lo, hi = int(med * 0.8), int(med * 1.2)
    print(f"\n=== TARGET LENGTH ===")
    print(f"  Competitor words: min {min(counts)} / median {med} / avg {avg} / max {max(counts)}")
    print(f"  Aim for SERP median ±20%: ~{lo}-{hi} words (beat median to win)")
    if mine:
        verdict = "✅ in range" if lo <= mine <= hi * 1.5 else ("⚠️ SHORT — expand" if mine < lo else "long (ok)")
        print(f"  Your draft: {mine} words → {verdict}")
    # topic checklist = frequent competitor headings
    print(f"\n=== TOPICS COMPETITORS COVER (heading union — cover these) ===")
    seen = set()
    for hd in all_heads:
        key = hd.lower()[:40]
        if key not in seen:
            seen.add(key); print(f"  - {hd[:70]}")


if __name__ == "__main__":
    main()
