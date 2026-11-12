#!/usr/bin/env python3
"""Read-only published-article comparison with sourced SERP imports and bounded discovery."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from urllib.request import Request, build_opener, urlopen

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / '.tools/competitor-deps'))
from bs4 import BeautifulSoup
from research_library import public_url, PublicRedirect, allowed, AGENT

REPORTS = BASE / 'reports'
CACHE = BASE / 'research/competitor_cache'
STOP = set('a an the and or to of for in on with is are how what why when your you our best top guide free'.split())

def now():
    return datetime.now(timezone.utc).isoformat()

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temp.replace(path)

def canonical(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path,
        urlencode([(k,v) for k,v in parse_qsl(p.query) if k != 'm' and not k.startswith('utm_')]), ''))

def published_posts(inventory):
    posts = inventory if isinstance(inventory, list) else [p for s in inventory.values() for p in s['posts']]
    unique = {}; excluded = Counter()
    for post in posts:
        if post.get('status') != 'LIVE':
            excluded[post.get('status', 'unspecified_status')] += 1
            continue
        url = canonical(post.get('url', ''))
        if not url.startswith(('https://', 'http://')):
            excluded['missing_url'] += 1
            continue
        if url in unique:
            excluded['duplicate_url'] += 1
            if post.get('updated', '') <= unique[url].get('updated', ''):
                continue
        unique[url] = {**post, 'url': url}
    return list(unique.values()), dict(excluded)

def measure(html, fragment=False):
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup.select('script,style,nav,footer,header,aside,form,noscript'):
        node.decompose()
    body = next((soup.select_one(s) for s in ('.post-body', '[itemprop="articleBody"]', 'article', 'main') if soup.select_one(s) is not None), None)
    method = 'explicit_article_container'
    if fragment:
        body = body if body is not None else soup
        method = 'blogger_api_body'
    text = None
    if not fragment:
        try:
            from trafilatura import extract
            text = extract(html, include_comments=False, include_tables=True)
            if text:
                method = 'trafilatura'
        except ImportError:
            pass
    if not text and body is not None:
        text = body.get_text(' ', strip=True)
    if not text or not text.strip():
        return {'status': 'extraction_unavailable', 'words': None, 'headings': []}
    scope = body if body is not None else soup
    return {'status': 'measured', 'words': len(re.findall(r"\b[\w’'-]+\b", text)),
        'headings': [{'level': h.name, 'text': h.get_text(' ', strip=True)} for h in scope.select('h1,h2,h3')],
        'images': len(scope.select('img')), 'tables': len(scope.select('table')),
        'extraction_method': method, 'headings_scope': 'article' if body is not None else 'document',
        'content_hash': hashlib.sha256(text.encode()).hexdigest(),
        '_tokens': sorted(set(re.findall(r'[a-z0-9]+', text.lower())))}

def fetch(url, cache_days=7):
    stamp = now()
    try:
        public_url(url)
        path = CACHE / ('page-' + hashlib.sha256(url.encode()).hexdigest() + '.json')
        if path.exists():
            value = json.loads(path.read_text())
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(value['retrieved_at'])).total_seconds()
            if 0 <= age < cache_days * 86400:
                return {**value, 'cached': True}
        if not allowed(url):
            raise ValueError('Robots policy unavailable or disallows source')
        with build_opener(PublicRedirect()).open(Request(url, headers={'User-Agent': AGENT}), timeout=25) as r:
            final_url = public_url(r.url)
            if final_url != url and not allowed(final_url):
                raise ValueError('Robots policy disallows redirected source')
            if 'html' not in r.headers.get('Content-Type', ''):
                raise ValueError('Unsupported content type')
            raw = r.read(3_000_001)
            if len(raw) > 3_000_000:
                raise ValueError('Page exceeds extraction limit')
            result = {**measure(raw.decode(r.headers.get_content_charset() or 'utf-8', 'replace')),
                      'final_url': final_url, 'http_status': r.status, 'retrieved_at': stamp, 'cached': False}
        if result['status'] == 'measured':
            write_json(path, result)
        return result
    except Exception as exc:
        return {'status': 'fetch_unavailable', 'error': type(exc).__name__,
                'words': None, 'headings': [], 'retrieved_at': stamp}

def topic_candidates(mine, rows):
    counts = Counter(); examples = {}
    mine_tokens = set(mine.get('_tokens', []))
    for row in rows:
        per_page = set()
        for heading in row.get('headings', []):
            words = [w for w in re.findall(r'[a-z0-9]+', heading['text'].lower()) if w not in STOP and len(w) > 2]
            for i in range(len(words)-1):
                phrase = ' '.join(words[i:i+2]); per_page.add(phrase)
                examples.setdefault(phrase, heading['text'])
        counts.update(per_page)
    return [{'topic': phrase, 'competitor_pages': n, 'example_heading': examples[phrase],
             'review_cue': 'Check whether this concept belongs in the article; lexical coverage is only a heuristic.'}
            for phrase, n in counts.most_common(30) if n >= 2 and not set(phrase.split()) <= mine_tokens]

def comparison_status(packet, rows):
    if not rows:
        return 'pending_search_results'
    if not any(r.get('status') == 'measured' for r in rows):
        return 'comparison_unavailable'
    positions = [r.get('position') for r in rows]
    provenance = all(packet.get(k) for k in ('source', 'engine', 'country', 'language', 'device', 'observed_at'))
    try:
        date = datetime.fromisoformat(packet.get('observed_at', '').replace('Z', '+00:00'))
        dated = date.tzinfo is not None and date <= datetime.now(timezone.utc)
    except (ValueError, TypeError):
        dated = False
    complete = (len(rows) == 10 and all(type(x) is int for x in positions)
                and set(positions) == set(range(1,11)) and provenance and dated
                and packet.get('result_type') == 'organic_ranked' and packet.get('query_reviewed') is True
                and all(r.get('status') == 'measured' for r in rows))
    return 'comparison_complete' if complete else 'comparison_partial'

def compare(post, packet, do_fetch=False):
    mine = measure(post.get('content', ''), fragment=True)
    rows = []; seen = set()
    for item in packet.get('results', []):
        target = canonical(item.get('url', ''))
        if target in seen or not target.startswith(('http://', 'https://')):
            continue
        seen.add(target)
        if target == post['url']:
            metrics = {**mine, 'measurement_source': 'cached_own_article'}
        else:
            metrics = fetch(target) if do_fetch else {'status':'pending_fetch', 'words':None, 'headings':[]}
        rows.append({**item, 'url':target, **metrics})
        if len(rows) == 10:
            break
    competitors = [r for r in rows if r['url'] != post['url']]
    words = [r['words'] for r in competitors if r.get('words') is not None]
    topics = topic_candidates(mine, competitors)
    for row in [mine, *rows]:
        row.pop('_tokens', None)
    return {'url':post['url'], 'title':post['title'], 'query':packet.get('query') or post['title'],
        'query_basis':packet.get('query_basis', 'supplied' if packet.get('query') else 'article_title_requires_review'),
        'source':packet.get('source'), 'serp_observed_at':packet.get('observed_at'),
        'serp_context':{k:packet.get(k) for k in ('engine','country','language','device','result_type','query_reviewed')},
        'status':comparison_status(packet, rows), 'mine':mine, 'competitors':rows,
        'measured_competitors':len(words), 'competitor_median_words':statistics.median(words) if words else None,
        'competitor_min_words':min(words) if words else None, 'competitor_max_words':max(words) if words else None,
        'topic_review_candidates':topics, 'post_updated_at':post.get('updated'),
        'source_html_hash':hashlib.sha256(post.get('content','').encode()).hexdigest(),
        'note':'Word counts are descriptive. Topic candidates require factual and intent review before editing.'}

def query_map():
    path = REPORTS / 'gsc_opportunities_latest.json'
    result = {}
    if path.exists():
        for site in json.loads(path.read_text()).get('sites', []):
            for q in site.get('current_queries', []):
                for page in q.get('pages', []):
                    url = canonical(page['url']); score = page.get('impressions', 0)
                    if score > result.get(url, {}).get('impressions', 0):
                        result[url] = {'query':q['query'], 'impressions':score}
    return result

def discover(query, country, language, device, cache_days=7):
    key = os.environ.get('SERPAPI_API_KEY', '')
    key_path = BASE / 'serpapi_key.txt'
    if not key and key_path.exists():
        key = key_path.read_text().strip()
    if not key:
        raise ValueError('SERPAPI_API_KEY or serpapi_key.txt is required')
    params = {'engine':'google', 'q':query, 'gl':country, 'hl':language, 'device':device}
    cache_path = CACHE / ('serp-' + hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest() + '.json')
    if cache_path.exists():
        cached = json.loads(cache_path.read_text())
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(cached['observed_at'])).total_seconds()
        if 0 <= age < cache_days * 86400:
            return {**cached, 'cached':True}
    url = 'https://serpapi.com/search.json?' + urlencode({**params, 'api_key':key})
    try:
        with urlopen(url, timeout=45) as r:
            data = json.loads(r.read())
    except Exception as exc:
        raise ValueError('SERP provider request failed: ' + type(exc).__name__) from None
    if data.get('error'):
        raise ValueError('SERP provider returned an error; check account quota and access')
    packet = {'query':query, 'source':'SerpApi', 'engine':'google', 'country':country, 'language':language,
        'device':device, 'observed_at':now(), 'result_type':'organic_ranked', 'query_reviewed':False,
        'provider_search_id':data.get('search_metadata', {}).get('id'),
        'results':[{'url':r['link'], 'position':r.get('position'), 'title':r.get('title')}
                   for r in data.get('organic_results', [])[:10] if r.get('link')]}
    write_json(cache_path, packet)
    return packet

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventory', type=Path)
    p.add_argument('--refresh-inventory', action='store_true')
    p.add_argument('--results', type=Path)
    p.add_argument('--fetch', action='store_true')
    p.add_argument('--discover', action='store_true', help='Explicitly allow bounded SERP-provider requests')
    p.add_argument('--max-searches', type=int, default=0)
    p.add_argument('--country', default='us'); p.add_argument('--language', default='en')
    p.add_argument('--device', choices=('desktop','mobile'), default='desktop')
    a = p.parse_args()
    if a.max_searches < 0 or (a.discover and a.max_searches == 0):
        p.error('Discovery requires a positive --max-searches budget')
    latest = REPORTS / 'published_inventory_latest.json'
    candidates = sorted(REPORTS.glob('blog_inventory_*.json'))
    source = a.inventory or (latest if latest.exists() else candidates[-1] if candidates else REPORTS / 'article_inventory_latest.json')
    refresh_error = None
    if a.refresh_inventory:
        try:
            from article_improver import inventory
            from upload_drafts import service
            live = inventory(service())
            live, _ = published_posts(live)
            if not live:
                raise ValueError("No LIVE articles returned; retain the previous inventory")
            write_json(latest, live); source = latest
        except Exception as exc:
            refresh_error = 'Inventory refresh unavailable: ' + type(exc).__name__
    posts, excluded = published_posts(json.loads(source.read_text()))
    if not posts:
        raise SystemExit("No published articles available; previous comparison report retained")
    result_path = a.results or REPORTS / 'competitor_results.json'
    supplied = json.loads(result_path.read_text()) if result_path.exists() else {}
    if not isinstance(supplied, dict):
        raise SystemExit('Expected result JSON keyed by article URL')
    for article_url, packet in supplied.items():
        if not isinstance(packet, dict) or not isinstance(packet.get('results', []), list):
            raise SystemExit('Each result packet must be an object containing a results list')
        if any(not isinstance(r, dict) or not isinstance(r.get('url'), str) for r in packet.get('results', [])):
            raise SystemExit('Each search result requires a URL string')
    supplied = {canonical(k):v for k,v in supplied.items()}
    gsc = query_map(); template = {}; articles = []; requests = 0; discovery_error = None
    for post in posts:
        packet = supplied.get(post['url'], {})
        query = packet.get('query') or gsc.get(post['url'], {}).get('query') or post['title']
        basis = packet.get('query_basis') or ('supplied' if packet.get('query') else 'observed_gsc' if post['url'] in gsc else 'article_title_requires_review')
        if a.discover and not packet.get('results') and requests < a.max_searches and not discovery_error:
            try:
                requests += 1
                packet = discover(query, a.country, a.language, a.device)
                supplied[post['url']] = packet
                write_json(result_path, supplied)
            except Exception as exc:
                discovery_error = str(exc)
        template[post['url']] = {'query':query, 'query_basis':basis, 'query_reviewed':False,
            'source':None, 'engine':None, 'country':a.country, 'language':a.language, 'device':a.device,
            'observed_at':None, 'result_type':'candidate_pages', 'results':[]}
        packet = {**template[post['url']], **packet}
        articles.append(compare(post, packet, a.fetch))
    report = {'schema_version':2, 'created_at':now(), 'inventory_source':str(source),
        'inventory_modified_at':datetime.fromtimestamp(source.stat().st_mtime,timezone.utc).isoformat(),
        'inventory_refresh_error':refresh_error, 'excluded_records':excluded, 'articles':articles,
        'discovery_requests':requests, 'discovery_error':discovery_error,
        'summary':dict(Counter(x['status'] for x in articles))}
    write_json(REPORTS / 'article_competitor_latest.json', report)
    write_json(REPORTS / 'competitor_results_template.json', template)
    lines = ['# Published-article competitor comparison', '', f'Published articles: {len(posts)}. Inventory: {source.name}.',
        f'Inventory source modified: {report["inventory_modified_at"]}. Excluded records: {excluded}.',
        f'Coverage: {report["summary"]}.', '',
        'Complete comparisons require ten ranked organic results, query review, search context and successful extraction. Candidate pages and partial samples remain labeled. Word count is descriptive.', '',
        '| Article | Our words | Measured competitors | Competitor median | Coverage |', '|---|---:|---:|---:|---|']
    for x in articles:
        lines.append(f"| {x['url']} | {x['mine']['words']} | {x['measured_competitors']} | {x['competitor_median_words'] if x['competitor_median_words'] is not None else 'unavailable'} | {x['status']} |")
    for x in articles:
        if not x['competitors']: continue
        lines.extend(['', f"## {x['title'].replace('|','/')} — {x['query']}", '', x['note'], ''])
        for row in x['competitors']:
            lines.append(f"- {row.get('position', 'unranked')}: {row['url']} — {row['status']}; words: {row.get('words')}")
            for h in row.get('headings', []):
                lines.append(f"  - {h['level']}: {h['text']}")
        lines.extend(['', 'Topic review candidates (lexical heuristics):'])
        lines.extend(f"- {t['topic']} — {t['competitor_pages']} competitor pages" for t in x['topic_review_candidates'])
    if refresh_error or discovery_error:
        lines.extend(['', str(refresh_error or discovery_error)])
    (REPORTS / 'article_competitor_latest.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'published_articles':len(posts), 'excluded':excluded, 'coverage':report['summary'],
                      'inventory_refresh_error':refresh_error, 'discovery_error':discovery_error}))

if __name__ == '__main__': main()
