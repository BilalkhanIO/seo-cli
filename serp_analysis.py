#!/usr/bin/env python3
"""Measure supplied competitor article URLs. This command does not establish their ranks."""
import argparse
import statistics
from article_competitor_audit import fetch as fetch_page

def fetch(url):
    result = fetch_page(url)
    if result['status'] != 'measured':
        return None, result.get('error', result['status']), []
    return result['words'], None, [h['text'] for h in result['headings'] if h['level']=='h2']

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query'); parser.add_argument('urls', nargs='+')
    parser.add_argument('--mine', type=int, help='Measured article-body word count')
    args = parser.parse_args(); counts = []; headings = set()
    print(f'Query: {args.query}. Supplied URL sample: {len(args.urls)}.')
    for url in args.urls:
        words, error, heads = fetch(url)
        print(f'{url}: {error if error else str(words)+" article words"}')
        if words is not None: counts.append(words); headings.update(heads)
    if counts:
        print(f'Measured sample: {len(counts)}; min {min(counts)}, median {statistics.median(counts)}, max {max(counts)} words.')
    if args.mine is not None: print(f'Your measured article body: {args.mine} words.')
    print('Length is descriptive. Review reader intent, factual accuracy and useful examples before deciding to add content.')
    print('Competitor headings for editorial review:')
    for heading in sorted(headings): print('- '+heading)

if __name__ == '__main__': main()
