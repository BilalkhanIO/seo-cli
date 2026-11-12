#!/usr/bin/env python3
"""Editable local memory for blog goals, audiences, key pages, and research."""
import argparse
from datetime import date, datetime
import json
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
PATH = BASE / "research" / "project_context.json"
SITES = {
    "st": ("Students Time", "https://studenttimepk.blogspot.com/"),
    "ll": ("Learner's Link", "https://learners-link.blogspot.com/"),
}


def today():
    return datetime.now(ZoneInfo("Asia/Karachi")).date().isoformat()


def empty_context():
    return {"schema_version": 1, "updated_at": None, "sites": {}}


def load_context():
    if not PATH.exists():
        return empty_context()
    data = json.loads(PATH.read_text())
    if data.get("schema_version") != 1 or not isinstance(data.get("sites"), dict):
        raise ValueError(f"Unsupported or invalid project context: {PATH}")
    return data


def save_context(data):
    PATH.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = datetime.now(ZoneInfo("Asia/Karachi")).isoformat()
    temporary = PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(PATH)


def site_context(key):
    if key not in SITES:
        return None
    data = load_context()
    return data.get("sites", {}).get(key)


def render_site_context(key):
    context = site_context(key)
    if not context:
        return "Project context has not been recorded."
    audience = context.get("audience", {})
    audience_text = audience.get("value", "Not recorded")
    if audience.get("confidence") == "inferred":
        audience_text += " (inferred; confirm before relying on it)"
    lines = [f"Audience: {audience_text}"]
    active = []
    for goal in context.get("goals", []):
        status = goal.get("status", "active")
        due = goal.get("due_date")
        if status == "active" and due and due < today():
            status = "expired"
        if status == "active":
            active.append(goal)
    lines.append("Current goals:")
    if active:
        for goal in active:
            target = goal.get("target")
            target_text = f" ({target['currency']} {target['value']:g})" if target else ""
            due = f" by {goal['due_date']}" if goal.get("due_date") else ""
            lines.append(f"- {goal['description']}{target_text}{due}")
    else:
        lines.append("- None currently active")
    pages = context.get("key_pages", [])
    if pages:
        lines.append("Key pages:")
        lines.extend(f"- {p.get('role', 'page')}: {p['url']} ({p.get('topic', 'topic not set')})" for p in pages)
    competitors = context.get("competitors", [])
    lines.append("Competitors: " + (", ".join(c.get("domain", "") for c in competitors) if competitors else "not configured"))
    return "\n".join(lines)


def resolve_key(args):
    return args.site


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("show", help="Show saved context")
    show.add_argument("--site", choices=("st", "ll", "both"), default="both")
    goal = sub.add_parser("set-goal", help="Add or update a site goal")
    goal.add_argument("--site", choices=("st", "ll"), required=True)
    goal.add_argument("--id", required=True)
    goal.add_argument("--description", required=True)
    goal.add_argument("--due-date")
    goal.add_argument("--target", type=float)
    goal.add_argument("--currency", default="USD")
    audience = sub.add_parser("set-audience", help="Set audience and its confidence/source")
    audience.add_argument("--site", choices=("st", "ll"), required=True)
    audience.add_argument("--value", required=True)
    audience.add_argument("--confidence", choices=("user-confirmed", "inferred", "unconfirmed"), required=True)
    audience.add_argument("--evidence", required=True)
    page = sub.add_parser("add-key-page", help="Add or update a priority page")
    page.add_argument("--site", choices=("st", "ll"), required=True)
    page.add_argument("--url", required=True)
    page.add_argument("--role", choices=("hub", "spoke", "growth-candidate", "money", "other"), required=True)
    page.add_argument("--topic", required=True)
    page.add_argument("--evidence", required=True)
    log = sub.add_parser("log-research", help="Append a dated research note")
    log.add_argument("--site", choices=("st", "ll"), required=True)
    log.add_argument("--summary", required=True)
    log.add_argument("--source", required=True)
    args = parser.parse_args()

    data = load_context()
    if args.command == "show":
        keys = SITES if args.site == "both" else (args.site,)
        for key in keys:
            name, url = SITES[key]
            print(f"## {name} — {url}\n{render_site_context(key)}\n")
        print(f"Context file: {PATH}")
        return

    context = data.setdefault("sites", {}).setdefault(args.site, {
        "name": SITES[args.site][0], "url": SITES[args.site][1],
        "audience": {"value": "Not recorded", "confidence": "unconfirmed"},
        "goals": [], "competitors": [], "key_pages": [], "research_log": [],
    })
    if args.command == "set-goal":
        if args.due_date:
            date.fromisoformat(args.due_date)
        target = {"value": args.target, "currency": args.currency.upper()} if args.target is not None else None
        item = {"id": args.id, "description": args.description, "target": target,
                "due_date": args.due_date, "status": "active", "provenance": "user", "recorded_at": today()}
        goals = context.setdefault("goals", [])
        context["goals"] = [g for g in goals if g.get("id") != args.id] + [item]
    elif args.command == "set-audience":
        context["audience"] = {"value": args.value, "confidence": args.confidence,
                               "evidence": args.evidence, "recorded_at": today()}
    elif args.command == "add-key-page":
        parsed = urlparse(args.url)
        if parsed.scheme != "https" or parsed.netloc != urlparse(context["url"]).netloc:
            parser.error("Key page must be an HTTPS URL on the selected blog")
        item = {"url": args.url, "role": args.role, "topic": args.topic,
                "evidence": args.evidence, "recorded_at": today()}
        pages = context.setdefault("key_pages", [])
        context["key_pages"] = [p for p in pages if p.get("url") != args.url] + [item]
    elif args.command == "log-research":
        context.setdefault("research_log", []).append({
            "date": today(), "summary": args.summary, "source": args.source,
        })
    save_context(data)
    print(f"Saved {args.command} for {context['name']} to {PATH}")


if __name__ == "__main__":
    main()
