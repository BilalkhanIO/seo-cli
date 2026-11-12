#!/usr/bin/env python3
"""Preview supported sitemap and Bing submission tasks; --apply performs submissions."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
from googleapiclient.discovery import build
from weekly_report import creds, BLOGS

BASE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        for name, site, *_ in BLOGS:
            print(f'{name}: submit {site}sitemap.xml to GSC; submit published sitemap URLs to Bing when configured.')
        print('Preview only. Use --apply for submission. Google blog recrawl requests require Search Console UI; submission does not establish indexing.')
        return
    sc = build('searchconsole', 'v1', credentials=creds(), cache_discovery=False)
    key_path = BASE / 'bing_key.txt'
    key = key_path.read_text().strip() if key_path.exists() else ''
    for name, site, *_ in BLOGS:
        sitemap = site + 'sitemap.xml'
        try:
            sc.sitemaps().submit(siteUrl=site, feedpath=sitemap).execute()
            print(f'{name}: GSC sitemap submitted; index inclusion remains unconfirmed.')
        except Exception as exc:
            print(f'{name}: sitemap submission unavailable ({type(exc).__name__})')
        if not key:
            print(f'{name}: Bing key unavailable'); continue
        try:
            with urlopen(sitemap, timeout=30) as response:
                root = ET.fromstring(response.read())
            urls = list(dict.fromkeys([site] + [n.text for n in root.iter() if n.tag.endswith('}loc') and n.text]))
            # Only same-property page URLs; nested sitemap files are not page submissions.
            urls = [u for u in urls if u.startswith(site) and not u.endswith('.xml')]
            endpoint = 'https://ssl.bing.com/webmaster/api.svc/json/SubmitUrlbatch?' + urlencode({'apikey':key})
            for offset in range(0,len(urls),100):
                request = Request(endpoint, data=json.dumps({'siteUrl':site.rstrip('/'), 'urlList':urls[offset:offset+100]}).encode(), headers={'Content-Type':'application/json'})
                with urlopen(request, timeout=40) as response: response.read()
            print(f'{name}: {len(urls)} URLs submitted to Bing; index inclusion remains unconfirmed.')
        except Exception as exc:
            print(f'{name}: Bing submission unavailable ({type(exc).__name__})')

if __name__ == '__main__': main()
