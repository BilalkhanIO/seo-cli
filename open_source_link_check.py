#!/usr/bin/env python3
"""Run pinned Lychee against explicit articles or the complete published inventory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent

def inventory_inputs():
    from article_competitor_audit import published_posts
    report = json.loads((BASE/'reports/article_competitor_latest.json').read_text())
    source = Path(report['inventory_source'])
    posts, _ = published_posts(json.loads(source.read_text()))
    if not posts:
        raise ValueError('No published inventory available')
    folder=BASE/'reports/link_inputs'; folder.mkdir(parents=True,exist_ok=True)
    sources={}
    for post in posts:
        # Content-addressed files let a report retain the exact input it checked.
        digest=hashlib.sha256((post['url']+post.get('content','')).encode()).hexdigest()
        path=folder/(digest+'.html')
        path.write_text(post.get('content',''))
        sources[str(path)]=post['url']
    return sources

def extracted_references(path):
    """Read URL references locally; Lychee --dump does not request those URLs."""
    result=subprocess.run([str(BASE/'.tools/lychee/lychee-v0.24.2/lychee'),
        '--config',str(BASE/'lychee.toml'),'--dump','--format','json',str(path)],
        capture_output=True,text=True,cwd=BASE,timeout=30,check=True)
    # Lychee's dump format is one normalized URL per line (despite the format flag).
    return {line.strip() for line in result.stdout.splitlines()
            if line.strip() and not line.strip().lower().startswith('file://')}

def reuse_unchanged(previous, sources):
    """Reuse dated HTTP results only when the exact source reference set is safe."""
    if previous.get('exit_code') not in (0,2) or not previous.get('input_sources'):
        raise ValueError('No successful manifest-backed link report to reuse')
    old_sources=previous['input_sources']
    old_by_url={url:path for path,url in old_sources.items()}
    new_by_url={url:path for path,url in sources.items()}
    if set(old_by_url)!=set(new_by_url):
        raise ValueError('Published article inventory changed; a fresh network audit is required')
    error_map={}
    changed=[]
    for url,new_path in new_by_url.items():
        old_path=old_by_url[url]
        if Path(old_path).name==Path(new_path).name:
            if old_path in previous.get('error_map',{}):
                error_map[new_path]=previous['error_map'][old_path]
            continue
        old_file,new_file=Path(old_path),Path(new_path)
        if not old_file.is_file() or not new_file.is_file():
            raise ValueError(f'Cannot compare saved references for {url}; a fresh network audit is required')
        old_refs=extracted_references(old_file)
        new_refs=extracted_references(new_file)
        if not new_refs.issubset(old_refs):
            additions=sorted(new_refs-old_refs)
            raise ValueError(f'Article added {len(additions)} unseen link(s); a fresh network audit is required')
        # Retain only old measurements for URLs still present in the edited article.
        retained=[]
        for item in previous.get('error_map',{}).get(old_path,[]):
            target=item.get('url')
            if target in new_refs:
                row=dict(item)
                row['original_span']=row.pop('span',None)
                retained.append(row)
        if retained: error_map[new_path]=retained
        changed.append({'url':url,'removed_references':len(old_refs-new_refs)})
    now=datetime.now(timezone.utc).isoformat()
    data={key:value for key,value in previous.items()}
    data['error_map']=error_map
    data['input_sources']=sources
    data['explicit_targets']=[]
    data['source_evidence_at']=previous.get('source_evidence_at') or previous.get('created_at')
    data['reconciled_at']=now
    data['reconciliation']={
        'mode':'reused_unchanged_reference_sets',
        'network_requests_this_run':0,
        'changed_inputs':changed,
        'note':'HTTP status checks retain their original measurement date; changed articles were compared locally and no new references were found.'
    }
    # Old aggregate counts describe the original request, not this reconciled view.
    data.pop('total',None); data.pop('unique',None); data.pop('successful',None)
    data.pop('unknown',None); data.pop('unsupported',None); data.pop('redirects',None)
    data.pop('cached',None); data.pop('duration',None); data.pop('detailed_stats',None)
    return data

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('targets',nargs='*',help='Explicit public URLs or article HTML/Markdown')
    parser.add_argument('--published-inventory',action='store_true')
    parser.add_argument('--reuse-unchanged',action='store_true',
        help='Reuse dated link results when the published inventory is unchanged and edited articles only remove links')
    args=parser.parse_args()
    if args.reuse_unchanged and (not args.published_inventory or args.targets):
        parser.error('--reuse-unchanged requires --published-inventory and no explicit targets')
    for target in args.targets:
        if not target.startswith(('https://','http://')) and Path(target).suffix not in ('.html','.md'):
            parser.error('Only article HTML/Markdown files or public URLs are allowed')
    sources=inventory_inputs() if args.published_inventory else {}
    targets=list(dict.fromkeys([*args.targets,*sources]))
    if not targets: parser.error('Supply targets or --published-inventory')
    folder=BASE/'reports'; folder.mkdir(exist_ok=True)
    output=folder/'lychee_latest.json'
    if args.reuse_unchanged:
        try:
            previous=json.loads(output.read_text())
            data=reuse_unchanged(previous,sources)
        except (OSError,ValueError,subprocess.SubprocessError) as exc:
            print(f'Offline link reconciliation refused: {exc}')
            print('The prior valid report is retained; run a fresh network audit when appropriate.')
            return 1
        raw=output.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        backup=folder/'link_evidence'/f'{digest}.json'
        backup.parent.mkdir(parents=True,exist_ok=True)
        if not backup.exists(): shutil.copyfile(output,backup)
        data['parent_evidence']=str(backup)
        output.write_text(json.dumps(data,indent=2))
        print(f'Reconciled {len(sources)} published articles offline; HTTP evidence date={data["source_evidence_at"]}; report={output}')
        return 0
    try:
        result=subprocess.run([str(BASE/'.tools/lychee/lychee-v0.24.2/lychee'),
            '--config',str(BASE/'lychee.toml'),'--format','json',*targets],
            capture_output=True,text=True,cwd=BASE,timeout=900)
    except subprocess.TimeoutExpired:
        print('Link audit exceeded its 15-minute deadline; the prior valid report is retained.')
        return 1
    (folder/'lychee_latest.log').write_text(result.stderr)
    try:
        data=json.loads(result.stdout)
        if not isinstance(data,dict) or 'error_map' not in data: raise ValueError('No valid Lychee result')
    except (ValueError,TypeError):
        print('Link measurement failed; the prior valid report is retained.')
        return result.returncode or 1
    data['input_sources']=sources
    data['explicit_targets']=args.targets
    data['created_at']=datetime.now(timezone.utc).isoformat()
    data['exit_code']=result.returncode
    output.write_text(json.dumps(data,indent=2))
    print(f'Lychee exit={result.returncode}; published article inputs={len(sources)}; report={output}')
    print('404/410 are broken; 403/429/timeouts remain unverified.')
    return result.returncode

if __name__=='__main__': raise SystemExit(main())
