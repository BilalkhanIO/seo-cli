#!/usr/bin/env python3
"""Plan, suggest, apply and verify repairs to existing Blogger articles.

plan creates reviewable candidate HTML and diffs; apply only updates existing
LIVE post content after checking its original hash, status and URL.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import difflib
from html import escape, unescape
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import uuid
from urllib.parse import unquote, urlsplit, urlunsplit, parse_qsl, urlencode

from growth_report import get_url
from pexels_helper import img_block
from upload_drafts import service

BASE = Path(__file__).resolve().parent
BLOGS = {"8491425780932094856":"Students Time", "6645616362681304579":"Learner's Link"}

# Explicit editorial mappings by topic, to existing post IDs from live inventory.
INTERNAL = {
 "free-course-of-day-3-meta-social-media.html":"8810903547183312626",
 "top-free-ai-courses-high-revenue-countries.html":"5529376557926356786",
 "best-ai-tools-for-students-2026.html":"2292482914520978025",
 "free-ai-tools-for-assignment-writing-2026.html":"2825732847826113109",
 "harvard-cs50-python-free-course-certificate.html":"816136777900589184",
 "how-to-start-learning-ai-as-student.html":"2775990746297198231",
 "the-ultimate-time-management.html":"6298451892672263651",
 "your-guide-to-calm-mind-navigating.html":"8825763385792077174",
 "your-guide-to-a-calm-mind-navigating.html":"8825763385792077174",
 "why-ubuntu-is-a-developers-best-friend.html":"6427111977614522808",
}
EXTERNAL = {
 "https://consumer.ftc.gov/articles/understanding-your-credit":"https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/understand-your-credit-score/",
 "https://consumer.ftc.gov/articles/using-personal-loans-wisely":"https://www.consumerfinance.gov/ask-cfpb/what-is-a-personal-installment-loan-en-2114/",
 "https://www.finra.org/investors/insights/robo-advisors":"https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-45",
 "https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/robo-advisers":"https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-45",
 "https://www.investor.gov/introduction-investing/investing-basics":"https://www.investor.gov/introduction-investing",
 "https://www.investor.gov/introduction-investing/investing-basics/investment-products/529-plans":"https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/introduction-529-plans-investor-bulletin",
 "https://www.eba.europa.eu/activities/single-rulebook/regulatory-activities/depositor-protection":"https://www.eba.europa.eu/activities/single-rulebook/regulatory-activities/depositor-protection/deposit-guarantee-schemes-data",
 "https://learn.microsoft.com/en-us/training/paths/intro-to-artificial-intelligence/":"https://learn.microsoft.com/training/paths/ai-fluency/",
 "https://academy.openai.com/public/courses/ai-for-college-students":"https://academy.openai.com/public/search?query=AI%20for%20College%20Students&type=all",
 "https://academy.openai.com/public/courses/ai-for-educators":"https://academy.openai.com/public/search?query=AI%20for%20Educators&type=all",
 "https://www.un.org/en/artificial-intelligence-principles":"https://www.un.org/en/global-issues/artificial-intelligence",
}
ANCHOR = re.compile(r"<a\b([^>]*?)>(.*?)</a>", re.S | re.I)
HREF = re.compile(r'''\bhref\s*=\s*(["'])(.*?)\1''', re.S | re.I)


def fingerprint(text): return hashlib.sha256(text.encode()).hexdigest()


def canonical(url):
    p = urlsplit(unescape(url))
    return urlunsplit((p.scheme,p.netloc,unquote(p.path),urlencode([(k,v) for k,v in parse_qsl(p.query) if k != "m"]),""))


def plain(raw):
    raw = re.sub(r"<script\b[^>]*>.*?</script>","",raw,flags=re.S|re.I)
    return re.sub(r"\s+"," ",unescape(re.sub(r"<[^>]+>"," ",raw))).strip()


def repair_links(content, source_url, actions):
    """Change only explicitly reviewed, currently checked link targets."""
    changes = []
    def replace(match):
        attrs, inner = match.groups()
        href = HREF.search(attrs)
        if not href: return match.group()
        url = unescape(href.group(2))
        action = actions.get(url)
        if not action: return match.group()
        if action["action"] == "unlink":
            changes.append({"kind":"unlink-dead-internal","from":url,"anchor":plain(inner)})
            return inner
        target = action["to"]
        attrs = attrs[:href.start(2)] + escape(target,quote=True) + attrs[href.end(2):]
        if action.get("source_label"):
            inner = escape(action["source_label"])
        changes.append({"kind":"replace-link","from":url,"to":target})
        return "<a" + attrs + ">" + inner + "</a>"
    return ANCHOR.sub(replace,content), changes


def related_posts(post, posts, limit=3):
    stop = set("the a an for with and how to best free guide complete practical ultimate beginners beginner in of is what which choose students 2026".split())
    def terms(title): return set(re.findall(r"[a-z]+",title.lower()))-stop
    query = terms(post["title"])
    ranked = []
    for candidate in posts:
        if candidate["id"] == post["id"] or candidate["blog"]["id"] != post["blog"]["id"]: continue
        words = terms(candidate["title"])
        score = len(query & words) / max(1,len(query | words))
        if len(query & words) >= 2: ranked.append((score,candidate))
    return [p for _,p in sorted(ranked,key=lambda x:(-x[0],x[1]["id"]))[:limit]]


def inventory(api):
    result = []
    for bid in BLOGS:
        token = None
        while True:
            data = api.posts().list(blogId=bid,status="LIVE",view="ADMIN",maxResults=100,pageToken=token).execute()
            result.extend(data.get("items",[])); token=data.get("nextPageToken")
            if not token: break
    return result


def validate_candidate(content):
    for raw in re.findall(r'''<script[^>]*type=["']application/ld\+json["'][^>]*>(.*?)</script>''',content,re.S|re.I):
        json.loads(raw)
    if not plain(content): raise ValueError("Empty candidate")


def suggestions(post, growth):
    text = plain(post["content"])
    rows = []
    for site in growth.get("sites",{}).values():
        rows += [r for r in site.get("queries",[]) if canonical(r["keys"][1]) == canonical(post["url"])]
    rows.sort(key=lambda r:-r["impressions"])
    tasks = ["Verify dated claims, pricing and credentials against current primary sources.",
             "Add an original example, completed exercise or comparison that answers the reader's question."]
    if len(post["title"]) > 65: tasks.append("Review title length while preserving the main search intent.")
    if re.search(r"free certificate|certification",post["title"],re.I): tasks.append("Confirm whether the provider offers free lessons, a badge, a certificate or a paid exam; correct wording if needed.")
    if "free AI courses" in post["title"]: tasks.append("Compare overlapping course pages before adding new content; keep different reader intents distinct.")
    if "eu-ai-act" in post["url"] and "GPT" in post["title"]: tasks.append("URGENT editorial review: URL says EU AI Act but title/body describe GPT; restore coherent intent after researching history.")
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p>",post["content"],re.S|re.I)
    intro = next((plain(p) for p in paragraphs if len(plain(p)) > 80),text)
    meta = intro[:152].rsplit(" ",1)[0].rstrip(" ,;:") + "."
    return {"queries":[{"query":r["keys"][0],"impressions":r["impressions"],"clicks":r["clicks"],"position":r["position"]} for r in rows[:10]],
            "tasks":tasks,"suggested_search_description":meta,
            "description_status":"Suggested from existing text; review then paste in Blogger manually",
            "questions_to_answer":[r["keys"][0] for r in rows if re.match(r"how|what|which|can|is|does|do|when|why",r["keys"][0],re.I)]}


def plan(args):
    api = service(); posts=inventory(api); by_id={p["id"]:p for p in posts}
    growth=json.loads((BASE/"reports/growth_latest.json").read_text())
    audit={canonical(p["url"]):p for s in growth.get("sites",{}).values() for p in s.get("audit",[])}
    # Recheck every target previously reported broken; do not mutate based on stale crawl results.
    broken=set()
    for page in audit.values():
        for item in page["issues"]:
            if item.startswith(("broken link: ","broken image: ")): broken.add(item.split(": ",1)[1])
    candidates = set(broken) | set(EXTERNAL.values())
    candidates.update(p["url"] for p in posts)
    with ThreadPoolExecutor(max_workers=3) as pool:
        responses=dict(zip(candidates,pool.map(get_url,candidates)))
    live={canonical(p["url"]):p for p in posts if responses[p["url"]]["status"] == 200}
    actions={}; unresolved=[]
    for old in sorted(broken):
        if responses[old]["status"] not in (404,410):
            unresolved.append({"url":old,"reason":"Not currently confirmed 404/410","status":responses[old]["status"]}); continue
        parsed=urlsplit(old)
        if parsed.hostname in ("studenttimepk.blogspot.com","learners-link.blogspot.com"):
            mapped=by_id.get(INTERNAL.get(parsed.path.rsplit("/",1)[-1]))
            if mapped and urlsplit(mapped["url"]).hostname == parsed.hostname and canonical(mapped["url"]) in live:
                actions[old]={"action":"replace","to":mapped["url"]}
            else: actions[old]={"action":"unlink"}
        elif old in EXTERNAL and responses[EXTERNAL[old]]["status"] == 200:
            target=EXTERNAL[old]
            action={"action":"replace","to":target}
            if "consumerfinance.gov" in target: action["source_label"]="CFPB: " + ("Understand your credit score" if "credit-score" in target else "Personal installment loans")
            if "academy.openai.com" in target: action["source_label"]="OpenAI Academy: find the current course"
            actions[old]=action
        else: unresolved.append({"url":old,"reason":"No verified editorial replacement; review manually"})
    run=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder=BASE/"reports/improvements"/run; folder.mkdir(parents=True)
    packet={"created_at":datetime.now(timezone.utc).isoformat(),"gsc_evidence_date":growth.get("date"),
            "folder":str(folder),"posts":[],"unresolved_links":unresolved,"policy":"Existing LIVE posts only; content-only updates with hash conflict checks and backups"}
    for post in posts:
        before=post["content"]; after,changes=repair_links(before,post["url"],actions)
        # Title is supplied by the Blogger theme; remove only an identical duplicate body H1.
        def title_heading(m):
            if plain(m.group(1)).casefold() == plain(post["title"]).casefold():
                changes.append({"kind":"remove-duplicate-title-h1"}); return ""
            return m.group()
        after=re.sub(r"<h1\b[^>]*>(.*?)</h1>",title_heading,after,flags=re.S|re.I)
        after,n=re.subn(r"<p>\s*<strong>(?:Primary keyword|Secondary keywords|Suggested URL|Search description|Image query):</strong>.*?</p>","",after,flags=re.S|re.I)
        if n: changes.append({"kind":"remove-visible-draft-metadata","count":n})
        missing="<img" not in after.lower()
        bad_images=[url for url in broken if any(x=="broken image: "+url for x in audit.get(canonical(post["url"]),{}).get("issues",[])) and responses[url]["status"] in (404,410)]
        if missing or bad_images:
            query="online learning laptop" if post["blog"]["id"]=="8491425780932094856" else "financial planning desk"
            figure,_=img_block(query,hero=True)
            if missing: after=figure+"\n"+after
            for url in bad_images:
                for match in list(re.finditer(r"<figure\b[^>]*>.*?</figure>",after,re.S|re.I)):
                    if unescape(url) in unescape(match.group()): after=after.replace(match.group(),figure)
                after=re.sub(r"<img\b[^>]*>",lambda m: figure if unescape(url) in unescape(m.group()) else m.group(),after,flags=re.I)
            changes.append({"kind":"add-or-replace-image","query":query})
        rec=related_posts(post,posts)
        known={canonical(unescape(m.group(2))) for m in HREF.finditer(after)}
        rec=[p for p in rec if canonical(p["url"]) not in known and canonical(p["url"]) in live][:2]
        if rec and 'class="related-reading"' not in after:
            section='\n<aside class="related-reading"><h2>Related reading</h2><ul>'+"".join(f'<li><a href="{escape(p["url"],quote=True)}">{escape(p["title"])}</a></li>' for p in rec)+"</ul></aside>"
            after+=section; changes.append({"kind":"add-related-reading","targets":[p["url"] for p in rec]})
        advice=suggestions(post,growth)
        candidate=folder/f"{post['id']}.html"; candidate.write_text(after)
        diff=folder/f"{post['id']}.diff"; diff.write_text("".join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile="current.html",tofile="candidate.html")))
        errors=[]
        try: validate_candidate(after)
        except Exception as exc: errors.append(str(exc))
        record={"id":post["id"],"blog_id":post["blog"]["id"],"title":post["title"],"url":post["url"],
                "before_sha256":fingerprint(before),"after_sha256":fingerprint(after),"candidate":str(candidate),
                "changes":changes,"validation_errors":errors,"suggestions":advice}
        packet["posts"].append(record)
        brief=[f"# Improvement brief: {post['title']}","",post["url"],"",f"GSC source date: {growth.get('date')}","",
               "## Proposed technical repairs",json.dumps(changes,indent=2),"","## Search queries",json.dumps(advice["queries"],indent=2),
               "","## Editorial tasks", *["- "+t for t in advice["tasks"]],"","## Suggested description (manual)",advice["suggested_search_description"],
               "","## Source and content review","Verify factual claims and provider terms, add original examples, then review this candidate HTML/diff. No automatic rewrite or new post creation."]
        (folder/f"{post['id']}.md").write_text("\n".join(brief)+"\n")
    path=folder/"plan.json"; path.write_text(json.dumps(packet,indent=2,ensure_ascii=False))
    (BASE/"reports/improvement_plan_latest.json").write_text(json.dumps(packet,indent=2,ensure_ascii=False))
    changed=[p for p in packet["posts"] if p["before_sha256"]!=p["after_sha256"]]
    summary=["# Existing-article improvement plan","",f"Prepared {len(posts)} articles; {len(changed)} have proposed content repairs.",
             "","| Article | Proposed repairs | Review packet |","|---|---:|---|"]
    for p in packet["posts"]: summary.append(f"| {p['title']} | {len(p['changes'])} | {p['id']}.md |")
    (folder/"README.md").write_text("\n".join(summary)+"\n")
    print(f"PLAN: {path}; articles={len(posts)}; candidates={len(changed)}; unresolved_links={len(unresolved)}",flush=True)


def apply_plan(args):
    packet=json.loads(args.plan.read_text()); api=service(); results=[]
    selected=[p for p in packet["posts"] if p["before_sha256"]!=p["after_sha256"] and (not args.post or p["id"] in args.post)]
    backup_dir=Path(packet["folder"])/"backups"; backup_dir.mkdir(exist_ok=True)
    for p in selected:
        try:
            if p["validation_errors"]: raise ValueError("Candidate validation failed; review first")
            candidate=Path(p["candidate"]).read_text()
            if fingerprint(candidate)!=p["after_sha256"]: raise ValueError("Candidate changed; rebuild plan")
            validate_candidate(candidate)
            old=api.posts().get(blogId=p["blog_id"],postId=p["id"],view="ADMIN").execute()
            desired_title=p.get("proposed_title",p["title"])
            if old.get("status")!="LIVE" or old["url"]!=p["url"]:
                raise ValueError("Publication state or URL changed; review before applying")
            if fingerprint(old["content"])==p["after_sha256"] and old["title"]==desired_title:
                results.append({"id":p["id"],"status":"already-applied","url":p["url"]}); continue
            if old.get("status")!="LIVE" or old["url"]!=p["url"] or fingerprint(old["content"])!=p["before_sha256"] or old["title"]!=p["title"]:
                raise ValueError("Live article changed or publication state differs; rebuild plan")
            (backup_dir/f"{p['id']}-{p['before_sha256'][:12]}.json").write_text(json.dumps(old,indent=2,ensure_ascii=False))
            payload={"content":candidate}
            if p.get("proposed_title"): payload["title"]=desired_title
            api.posts().patch(blogId=p["blog_id"],postId=p["id"],body=payload).execute()
            saved=api.posts().get(blogId=p["blog_id"],postId=p["id"],view="ADMIN").execute()
            if fingerprint(saved["content"])!=p["after_sha256"] or saved.get("status")!="LIVE" or saved["url"]!=old["url"] or saved.get("published")!=old.get("published") or saved["title"]!=desired_title:
                raise ValueError("Post-write verification differs; backup retained for review")
            results.append({"id":p["id"],"url":p["url"],"status":"verified","changes":p["changes"]})
            from seo_workbench import connect, now
            history=connect(BASE/"research/workbench.sqlite")
            with history:
                history.execute("INSERT INTO changes(recorded_at,url,note) VALUES(?,?,?)",(now(),p["url"],"Verified article content repair: "+json.dumps(p["changes"])))
            history.close()
            print(f"VERIFIED {p['id']} {p['title']}",flush=True)
        except Exception as exc:
            results.append({"id":p["id"],"url":p["url"],"status":"blocked","error":str(exc)[:350]})
            print(f"BLOCKED {p['id']}: {str(exc)[:150]}",flush=True)
    target=Path(packet["folder"])/"apply_results.json"
    target.write_text(json.dumps(results,indent=2,ensure_ascii=False))
    archive=target.with_name("apply_results-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:8]+".json")
    archive.write_text(json.dumps(results,indent=2,ensure_ascii=False))
    (BASE/"reports/article_repairs_latest.json").write_text(json.dumps(results,indent=2,ensure_ascii=False))
    print("Results:",dict(Counter(r["status"] for r in results)),flush=True)
    return any(r["status"]=="blocked" for r in results)


def restore_revision(args):
    backup=json.loads(args.backup.read_text()); api=service()
    old=api.posts().get(blogId=backup["blog"]["id"],postId=backup["id"],view="ADMIN").execute()
    if old.get("status")!="LIVE" or old["url"]!=backup["url"] or fingerprint(old["content"])!=args.expected_current_hash:
        raise SystemExit("Current article does not match the requested restore baseline")
    if not args.apply:
        print(f"Restore preview: {backup['title']} at {backup['url']}; add --apply after review"); return
    api.posts().patch(blogId=backup["blog"]["id"],postId=backup["id"],body={"content":backup["content"],"title":backup["title"]}).execute()
    result=api.posts().get(blogId=backup["blog"]["id"],postId=backup["id"],view="ADMIN").execute()
    if fingerprint(result["content"])!=fingerprint(backup["content"]) or result.get("status")!="LIVE" or result["url"]!=old["url"]:
        raise SystemExit("Restore verification failed; inspect the saved backup")
    print(f"Restored and verified: {backup['url']}")


def stage_revision(args):
    packet=json.loads(args.plan.read_text())
    post=next((p for p in packet["posts"] if p["id"]==args.post),None)
    if not post: raise SystemExit("Post is not in this review plan")
    current=service().posts().get(blogId=post["blog_id"],postId=post["id"],view="ADMIN").execute()
    if current.get("status")!="LIVE" or current["url"]!=post["url"] or fingerprint(current["content"]) not in (post["before_sha256"],post["after_sha256"]):
        raise SystemExit("Live article changed; create a new plan before staging this revision")
    revision=args.content_file.read_text(); validate_candidate(revision)
    post["before_sha256"]=fingerprint(current["content"])
    post["title"]=current["title"]
    if args.title:
        if not (15 <= len(args.title) <= 100): raise SystemExit("Use a descriptive title between 15 and 100 characters")
        post["proposed_title"]=args.title
    Path(post["candidate"]).write_text(revision)
    Path(post["candidate"]).with_suffix(".diff").write_text("".join(difflib.unified_diff(current["content"].splitlines(True),revision.splitlines(True),fromfile="current.html",tofile="reviewed.html")))
    post["after_sha256"]=fingerprint(revision); post["validation_errors"]=[]
    post["changes"].append({"kind":"reviewed-editorial-revision","source_file":str(args.content_file)})
    for target in (args.plan,Path(packet["folder"])/"plan.json"):
        target.write_text(json.dumps(packet,indent=2,ensure_ascii=False))
    print(f"Staged reviewed content for {post['id']}; apply this post after reviewing its diff")


def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("plan")
    apply=sub.add_parser("apply"); apply.add_argument("--plan",type=Path,default=BASE/"reports/improvement_plan_latest.json"); apply.add_argument("--post",action="append")
    stage=sub.add_parser("stage"); stage.add_argument("--plan",type=Path,default=BASE/"reports/improvement_plan_latest.json"); stage.add_argument("--post",required=True); stage.add_argument("--content-file",type=Path,required=True); stage.add_argument("--title")
    restore=sub.add_parser("restore"); restore.add_argument("--backup",type=Path,required=True); restore.add_argument("--expected-current-hash",required=True); restore.add_argument("--apply",action="store_true")
    args=p.parse_args()
    if args.command=="plan": plan(args)
    else:
        from seo_workbench import lock
        with lock(BASE/"research/article-improver.lock"):
            if args.command=="stage": stage_revision(args)
            elif args.command=="restore": restore_revision(args)
            elif apply_plan(args): raise SystemExit(1)


if __name__=="__main__": main()
