# -*- coding: utf-8 -*-
"""
prism - fetch multi-country news from Google News RSS.

Usage:
  python fetch_news.py top
      Fetch top stories for every configured country edition -> data/top_<date>.json

  python fetch_news.py search
      Read data/queries.json (per-country localized queries for ONE event),
      search each country's edition -> data/event_<date>.json

No dependencies beyond the Python standard library.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

# Country editions: (label, hl, gl, ceid)
EDITIONS = [
    ("US",      "en-US",  "US", "US:en"),
    ("UK",      "en-GB",  "GB", "GB:en"),
    ("India",   "en-IN",  "IN", "IN:en"),
    ("Japan",   "ja",     "JP", "JP:ja"),
    ("France",  "fr",     "FR", "FR:fr"),
    ("Germany", "de",     "DE", "DE:de"),
    ("Brazil",  "pt-BR",  "BR", "BR:pt-419"),
    ("Russia",  "ru",     "RU", "RU:ru"),
    ("Egypt",   "ar",     "EG", "EG:ar"),
    ("China",   "zh-CN",  "CN", "CN:zh-Hans"),
]

DATA = Path(__file__).parent / "data"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) prism-prototype/0.1"


def fetch_rss(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read()
    root = ET.fromstring(raw)
    items = []
    for item in root.iter("item"):
        src = item.find("source")
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "source": (src.text.strip() if src is not None and src.text else ""),
            "link": (item.findtext("link") or "").strip(),
            "pubDate": (item.findtext("pubDate") or "").strip(),
        })
    return items


def top_url(hl: str, gl: str, ceid: str) -> str:
    return f"https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}"


def search_url(query: str, hl: str, gl: str, ceid: str) -> str:
    q = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={ceid}"


def run_top() -> None:
    out = {}
    for label, hl, gl, ceid in EDITIONS:
        try:
            items = fetch_rss(top_url(hl, gl, ceid))[:20]
            out[label] = items
            print(f"  {label:8s} {len(items)} items")
        except Exception as e:
            out[label] = []
            print(f"  {label:8s} FAILED: {e}")
        time.sleep(1)
    path = DATA / f"top_{date.today().isoformat()}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path}")


def run_search() -> None:
    queries = json.loads((DATA / "queries.json").read_text(encoding="utf-8"))
    # queries.json: {"event": "...", "queries": {"US": "...", "Japan": "...", ...}}
    out = {"event": queries.get("event", ""), "countries": {}}
    editions = {label: (hl, gl, ceid) for label, hl, gl, ceid in EDITIONS}
    for label, q in queries["queries"].items():
        hl, gl, ceid = editions[label]
        try:
            items = fetch_rss(search_url(q, hl, gl, ceid))[:12]
            out["countries"][label] = {"query": q, "items": items}
            print(f"  {label:8s} q={q!r} -> {len(items)} items")
        except Exception as e:
            out["countries"][label] = {"query": q, "items": [], "error": str(e)}
            print(f"  {label:8s} FAILED: {e}")
        time.sleep(1)
    path = DATA / f"event_{date.today().isoformat()}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "top"
    if mode == "top":
        run_top()
    elif mode == "search":
        run_search()
    else:
        print(__doc__)
