#!/usr/bin/env python3
"""
google_dork_to_urls.py

Uses SerpAPI to extract URLs from a Google dork
and export them to a text file.

Example dork:
  site:target.com filetype:pdf
"""

import os
import sys
import time
import requests

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
if not SERPAPI_KEY:
    print("[!] Set SERPAPI_KEY environment variable")
    sys.exit(1)

DORK = "site:target.com filetype:pdf"
OUTPUT_FILE = "target_pdfs.txt"

def fetch_results(start=0):
    params = {
        "engine": "google",
        "q": DORK,
        "api_key": SERPAPI_KEY,
        "start": start,
        "num": 10
    }
    r = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    found = set()
    start = 0

    print(f"[+] Running dork: {DORK}")

    while True:
        data = fetch_results(start)
        results = data.get("organic_results", [])

        if not results:
            break

        for r in results:
            link = r.get("link")
            if link and link.lower().endswith(".pdf"):
                found.add(link)

        start += 10
        time.sleep(1)  # polite rate limiting

    with open(OUTPUT_FILE, "w") as f:
        for url in sorted(found):
            f.write(url + "\n")

    print(f"[+] Saved {len(found)} PDF URLs to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

