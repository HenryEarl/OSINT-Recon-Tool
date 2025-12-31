#!/usr/bin/env python3
"""
google_dork_to_urls.py

Uses SerpAPI to extract URLs from a Google dork and export them to a file.

Examples:
  python google_dork_to_urls.py 'site:example.com filetype:pdf' -o example.com_pdfs.txt
  python google_dork_to_urls.py 'site:example.com filetype:pdf' -o example.com_pdfs.txt --stop-after 10
  python google_dork_to_urls.py 'site:example.com filetype:pdf' -o example.com_pdfs.txt --max-pages 15
"""

import os
import sys
import time
import json
import argparse
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


SERPAPI_URL = "https://serpapi.com/search.json"


def build_session(retries: int = 5, backoff: float = 0.8) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def looks_like_pdf(url: str) -> bool:
    """True if the URL path ends with .pdf (ignoring query/fragment)."""
    try:
        parsed = urlparse(url)
        return parsed.path.lower().endswith(".pdf")
    except Exception:
        return False


def fetch_results(session: requests.Session, api_key: str, query: str, start: int, num: int, timeout: int) -> dict:
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "start": start,
        "num": num,
    }
    r = session.get(SERPAPI_URL, params=params, timeout=timeout)

    if r.status_code != 200:
        raise requests.HTTPError(f"HTTP {r.status_code}: {r.text[:200]}", response=r)

    data = r.json()

    # SerpAPI may return 200 with an error message. Some errors should be treated as "end of results".
    err = data.get("error")
    if err:
        # This message appears when you page beyond available results.
        if "Google hasn't returned any results for this query" in err:
            return {"_end_of_results": True}
        raise RuntimeError(f"SerpAPI error: {err}")

    return data


def main() -> int:
    p = argparse.ArgumentParser(description="Extract URLs from a Google dork via SerpAPI.")
    p.add_argument("dork", help="Google dork query, e.g. 'site:example.com filetype:pdf'")
    p.add_argument("-o", "--output", default="results.txt", help="Output file (.txt or .json). Default: results.txt")
    p.add_argument("--api-key", default=os.getenv("SERPAPI_KEY"), help="SerpAPI key (or set SERPAPI_KEY env var)")
    p.add_argument("--num", type=int, default=10, help="Results per page (typically 10). Default: 10")
    p.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds between pages. Default: 1.0")
    p.add_argument("--timeout", type=int, default=30, help="Request timeout seconds. Default: 30")
    p.add_argument("--max-pages", type=int, default=0, help="Max pages to fetch (0 = unlimited until exhausted)")
    p.add_argument(
        "--stop-after",
        type=int,
        default=0,
        help="Stop after N consecutive pages with 0 new URLs (0 = disabled).",
    )
    p.add_argument(
        "--include-non-pdf",
        action="store_true",
        help="Save all links, not just PDF-looking URLs (useful if dork already includes filetype:pdf).",
    )
    args = p.parse_args()

    if not args.api_key:
        print("[!] Missing SerpAPI key. Set SERPAPI_KEY or use --api-key", file=sys.stderr)
        return 1

    session = build_session()

    found = set()
    start = 0
    page = 0
    no_new_pages = 0

    print(f"[+] Dork: {args.dork}")

    while True:
        page += 1
        if args.max_pages and page > args.max_pages:
            print(f"[i] Reached --max-pages {args.max_pages}")
            break

        data = fetch_results(session, args.api_key, args.dork, start=start, num=args.num, timeout=args.timeout)
        if data.get("_end_of_results"):
            print("[i] End of results (SerpAPI returned no more results).")
            break

        results = data.get("organic_results", []) or []
        if not results:
            print("[i] No more organic results.")
            break

        new_count = 0
        for r in results:
            link = r.get("link")
            if not link:
                continue
            if args.include_non_pdf or looks_like_pdf(link):
                if link not in found:
                    found.add(link)
                    new_count += 1

        print(f"[+] Page {page}: got {len(results)} results, +{new_count} new URLs (total={len(found)})")

        if new_count == 0:
            no_new_pages += 1
        else:
            no_new_pages = 0

        if args.stop_after and no_new_pages >= args.stop_after:
            print(f"[i] No new URLs for {no_new_pages} consecutive pages; stopping (--stop-after={args.stop_after}).")
            break

        start += args.num
        time.sleep(args.sleep)

    out_lower = args.output.lower()
    if out_lower.endswith(".json"):
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(sorted(found), f, indent=2)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            for url in sorted(found):
                f.write(url + "\n")

    print(f"[+] Saved {len(found)} URLs to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
