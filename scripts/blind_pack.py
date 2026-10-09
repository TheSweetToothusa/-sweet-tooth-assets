#!/usr/bin/env python3
"""Build a blind judging pack: our draft + competitor pages, brands masked, shuffled.

Usage:
  python3 scripts/blind_pack.py --ours draft.html --out packdir \
      --competitor https://example.com/page --competitor https://other.com/post \
      [--mask "Extra Brand"] [--seed 7]

Writes packdir/blind/page_A.txt ... and packdir/KEY.json (which label is ours).
Hand the judge ONLY the blind/ folder. Never show it KEY.json.
"""
import argparse
import html
import json
import os
import random
import re
import urllib.request
from urllib.parse import urlparse

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
OUR_NAMES = ["The Sweet Tooth", "Sweet Tooth", "thesweettooth.com", "thesweettooth",
             "North Miami Beach", "Michael Briansky", "Chip Westwood"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "ignore")


def to_text(b):
    m = re.search(r"(?is)<article.*?</article>", b) or re.search(r"(?is)<main.*?</main>", b)
    b = m.group(0) if m else b
    b = re.sub(r"(?is)<(script|style|svg|nav|footer|header|form|noscript)[^>]*>.*?</\1>", " ", b)
    b = re.sub(r"(?i)<h[1-4][^>]*>", "\n\n## ", b)
    b = re.sub(r"(?i)</h[1-4]>", "\n", b)
    b = re.sub(r"(?i)<(p|li|tr|br|div)[^>]*>", "\n", b)
    b = re.sub(r"(?i)</t[dh]>", " | ", b)
    t = html.unescape(re.sub(r"<[^>]+>", " ", b))
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()


def mask(t, names):
    for nm in sorted(set(n for n in names if n), key=len, reverse=True):
        t = re.sub(re.escape(nm), "[BRAND]", t, flags=re.I)
    return re.sub(r"https?://\S+", "[URL]", t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ours", required=True)
    ap.add_argument("--title", default="", help="our page title, shown as the H1")
    ap.add_argument("--competitor", action="append", default=[])
    ap.add_argument("--mask", action="append", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()

    pages = []
    ours = open(a.ours, encoding="utf-8").read()
    if a.title:
        ours = f"<h1>{html.escape(a.title)}</h1>\n" + ours
    pages.append(("ours", to_text(ours), OUR_NAMES))
    for url in a.competitor:
        host = urlparse(url).netloc.replace("www.", "")
        brand = host.split(".")[0]
        pages.append((url, to_text(fetch(url)), [host, brand, brand.replace("-", " ")]))

    labels = [chr(65 + i) for i in range(len(pages))]
    random.Random(a.seed).shuffle(labels)
    os.makedirs(os.path.join(a.out, "blind"), exist_ok=True)
    key = {}
    for (src, text, names), lab in zip(pages, labels):
        with open(os.path.join(a.out, "blind", f"page_{lab}.txt"), "w") as f:
            f.write(mask(text, names + a.mask))
        key[lab] = src
        print(lab, len(text.split()), "words")
    json.dump(key, open(os.path.join(a.out, "KEY.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
