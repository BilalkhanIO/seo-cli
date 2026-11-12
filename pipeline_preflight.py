#!/usr/bin/env python3
"""Check local pipeline dependencies without calling APIs or revealing credentials."""
import importlib.util
import json
import os
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parent
for folder in ('python','research-python','competitor-deps'):
    sys.path.insert(0,str(BASE/'.tools'/folder))

def main():
    modules={}
    for name in ('bs4','trafilatura','flask','textstat','googleapiclient','google.auth','google_auth_oauthlib','pytrends'):
        try: modules[name]=importlib.util.find_spec(name) is not None
        except (ImportError,ValueError,ModuleNotFoundError): modules[name]=False
    tools={name:(BASE/path).is_file() for name,path in {'lychee':'.tools/lychee/lychee-v0.24.2/lychee','vale':'.tools/vale/v3.25.1/vale'}.items()}
    credentials={'google_saved_login':Path.home().joinpath('.config/claude-seo/oauth-token.json').is_file(),
        'serpapi':bool(os.environ.get('SERPAPI_API_KEY')) or ((BASE/'serpapi_key.txt').is_file() and bool((BASE/'serpapi_key.txt').read_text().strip()))}
    value={'modules':modules,'local_tools':tools,'credential_presence_only':credentials,
        'note':'Credential presence does not establish API access. SERP discovery is optional and requires an explicit search budget.',
        'ready_for_local_checks':all(modules.values()) and all(tools.values())}
    print(json.dumps(value,indent=2))
    return 0 if value['ready_for_local_checks'] else 1
if __name__=='__main__': raise SystemExit(main())
