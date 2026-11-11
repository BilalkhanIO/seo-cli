#!/usr/bin/env python3
"""Google Trends keyword research for studenttimepk (free, no API key).

Usage:
  python trends_research.py "free ai course" "ai certification" [--geo PK] [--tf "today 3-m"]

Shows: trend direction + RISING related queries (breakout opportunities) + top related.
"""
import argparse
import sys

from pytrends.request import TrendReq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seeds", nargs="+", help="1-5 seed keywords")
    ap.add_argument("--geo", default="PK", help="Country code (PK, US, '' = worldwide)")
    ap.add_argument("--tf", default="today 3-m", help="Timeframe, e.g. 'today 3-m', 'today 12-m'")
    args = ap.parse_args()

    seeds = args.seeds[:5]
    pt = TrendReq(hl="en-US", tz=0)
    pt.build_payload(seeds, timeframe=args.tf, geo=args.geo)

    io = pt.interest_over_time()
    print(f"=== TREND DIRECTION (geo={args.geo or 'WW'}, {args.tf}) ===")
    if len(io):
        for s in seeds:
            if s in io:
                vals = io[s].tolist()
                first, last = vals[0], vals[-1]
                arrow = "rising ↑" if last > first else "falling ↓" if last < first else "flat →"
                print(f"  {s:<30} {first:>3} → {last:>3}  ({arrow})")
    else:
        print("  (no data — try a broader seed or geo='')")

    print("\n=== RISING queries (breakout = write about these) ===")
    rq = pt.related_queries()
    for s in seeds:
        v = rq.get(s) or {}
        rising = v.get("rising")
        print(f"\n[{s}] rising:")
        if rising is not None and len(rising):
            for _, row in rising.head(8).iterrows():
                print(f"   +{row['value']:<8} {row['query']}")
        else:
            print("   (none)")

    print("\n=== TOP related queries (established demand) ===")
    for s in seeds:
        v = rq.get(s) or {}
        top = v.get("top")
        print(f"\n[{s}] top:")
        if top is not None and len(top):
            for _, row in top.head(6).iterrows():
                print(f"   {row['value']:<5} {row['query']}")
        else:
            print("   (none)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Trends error (Google rate-limits — retry in a bit): {type(e).__name__}: {str(e)[:150]}",
              file=sys.stderr)
        sys.exit(1)
