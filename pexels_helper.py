#!/usr/bin/env python3
"""Reusable Pexels image fetcher for SEO posts.
Returns an <img> block (with real alt text + photographer credit) for a query.
Cloudflare blocks default python UA, so we send a browser UA."""
import urllib.request, urllib.parse, urllib.error, json
import os
from html import escape
from pathlib import Path

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def search(query, per_page=5, orientation="landscape"):
    key = os.environ.get("PEXELS_API_KEY") or Path(__file__).with_name("pexels_key.txt").read_text().strip()
    if not key:
        raise RuntimeError("Pexels API key is empty")
    q = urllib.parse.quote(query)
    url = f"https://api.pexels.com/v1/search?query={q}&per_page={per_page}&orientation={orientation}"
    req = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": _UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response).get("photos", [])
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Pexels HTTP {exc.code}: check credentials or quota") from None


def img_block(query, alt_override=None, idx=0, hero=False):
    """Return an HTML <figure> with a Pexels image, real alt text, and credit."""
    photos = search(query)
    if not photos:
        raise RuntimeError(f"Pexels returned no photos for {query!r}; choose a broader query")
    p = photos[max(0, min(idx, len(photos) - 1))]
    src = escape(p["src"].get("large2x") or p["src"]["large"], quote=True)
    alt = escape(alt_override or p.get("alt") or query, quote=True)
    credit = escape(p["photographer"])
    width = 1200
    height = round(width * p["height"] / p["width"])
    loading = 'loading="eager" fetchpriority="high"' if hero else 'loading="lazy"'
    html = (
        f'<figure style="margin:1.2em 0"><img src="{src}" alt="{alt}" '
        f'{loading} width="{width}" height="{height}" decoding="async" style="width:100%;height:auto;border-radius:10px" />'
        f'<figcaption style="font-size:.8em;color:#94a3b8;text-align:center;margin-top:.3em">'
        f'Photo by <a href="{escape(p["photographer_url"], quote=True)}" rel="noopener">{credit}</a> on '
        f'<a href="{escape(p["url"], quote=True)}" rel="noopener">Pexels</a></figcaption></figure>'
    )
    return html, alt


if __name__ == "__main__":
    import sys
    h, alt = img_block(sys.argv[1] if len(sys.argv) > 1 else "personal finance")
    print("ALT:", alt)
    print(h[:200])
