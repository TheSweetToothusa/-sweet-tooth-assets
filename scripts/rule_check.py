#!/usr/bin/env python3
"""Hard-rule checker for Sweet Tooth customer-facing pages.

Mechanical checks only. Opinions belong to the blind judge, not here.
A HARD hit fails the page no matter how well it is written.

Usage:
  SHOPIFY_TOKEN=... python3 scripts/rule_check.py draft.html \
      [--answer-bank answers.json] [--title "..."] [--meta "..."] [--no-links]

answers.json: [{"question": "...", "answer": "..."}] exported from the
Answer Bank (Ready or Published rows only).
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser

STORE = os.environ.get("SHOPIFY_STORE", "thesweettoothfl.myshopify.com")
SITE = "https://thesweettooth.com"
API = "2025-01"

# Stored as a hash so the name itself never appears in this public repo.
BANNED_NAME_HASHES = {"5380b4faddb75750e020755413bd44fa783bd0a7c7c6bb09ee03c6944bbe881b"}

HARD_PATTERNS = {
    "phone number": r"\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b",
    "other certifier": r"\b(OU|Kof-?K|Star-?K|CRC|OK[- ]kosher|OK[- ]certified)\b",
    "banned noun": r"(?i)\b(chocolate makers?|chocolatiers?|studio|workshop|kitchen|lab)\b",
    "year-count or ownership claim": r"(?i)(four generations|four decades|\b\d{2}\+?[- ]years?\b|family[- ]owned since|same family|same location|operating since|\bestablished\b)",
    "price-minimising word": r"(?i)\b(cheapest|best value|value|discounts?|affordable|budget-friendly)\b",
    "tax topic": r"(?i)\b(IRS|tax|taxes|deductible|deductions?|deduct)\b",
    "banned opener": r"(?i)(In today's|It's important to|When it comes to|Have you ever wondered|Did you know)",
    "dead-end contact": r"(?i)\b(contact us|get in touch)\b",
}
OUT_WORDS = r"(?i)\b(artisanal|curated|decadent|gourmet|indulgent|elevate[sd]?|unparalleled|chocolate lover's dream|kindly note|monogram\w*|boxed by the dozen|same dip)\b"
CAPS = {  # max uses per page, visible text only
    "The Sweet Tooth": (r"The Sweet Tooth", 2),
    "since 1979": (r"(?i)since 1979", 1),
    "North Miami Beach": (r"North Miami Beach", 1),
    "same-day": (r"(?i)same[- ]day", 1),
    "Kosher Miami": (r"Kosher Miami", 1),
}


class Page(HTMLParser):
    """Collects visible text, headings, links, table rows, blocks and FAQ items."""

    BLOCKS = {"p", "li", "tr", "h1", "h2", "h3", "h4", "td", "th", "figcaption", "summary", "dd", "dt"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.text = []
        self.headings = []
        self.links = []
        self.rows = []
        self.blocks = []
        self._row = None
        self._block = []
        self._block_tag = []
        self._h = None
        self.jsonld = []
        self._in_ld = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True
            self.jsonld.append("")
            return
        if tag in ("script", "style"):
            self.skip += 1
            return
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self._row is not None:
                self._row["links"].append(a["href"])
            if self._block:
                self._block[-1]["links"].append(a["href"])
        if tag == "tr":
            self._row = {"text": "", "links": []}
        if tag in self.BLOCKS and tag != "tr":
            self._block.append({"tag": tag, "text": "", "links": []})
        if tag in ("h1", "h2", "h3", "h4"):
            self._h = [tag, ""]

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld:
            self._in_ld = False
            return
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
            return
        if tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None
        if tag in self.BLOCKS and tag != "tr" and self._block:
            b = self._block.pop()
            self.blocks.append(b)
            if self._block:
                self._block[-1]["text"] += b["text"]
                self._block[-1]["links"] += b["links"]
        if tag in ("h1", "h2", "h3", "h4") and self._h:
            self.headings.append((self._h[0], self._h[1].strip()))
            self._h = None

    def handle_data(self, data):
        if self._in_ld:
            self.jsonld[-1] += data
            return
        if self.skip:
            return
        self.text.append(data)
        if self._row is not None:
            self._row["text"] += data + " "
        if self._block:
            self._block[-1]["text"] += data
        if self._h:
            self._h[1] += data


def get_json(url, token):
    req = urllib.request.Request(url, headers={"X-Shopify-Access-Token": token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def live_products(handles, token):
    out = {}
    for h in sorted(handles):
        url = f"https://{STORE}/admin/api/{API}/products.json?handle={h}&fields=id,title,handle,status,published_at,variants"
        try:
            ps = get_json(url, token).get("products", [])
        except Exception as e:  # noqa: BLE001
            out[h] = {"error": str(e)}
            continue
        if not ps:
            out[h] = {"error": "not found"}
            continue
        p = ps[0]
        out[h] = {
            "title": p["title"],
            "status": p["status"],
            "published": bool(p.get("published_at")),
            "prices": sorted({float(v["price"]) for v in p["variants"]}),
        }
    return out


def http_status(url):
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0 rule-check"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, url
    except Exception as e:  # noqa: BLE001
        return f"error: {e}", url


def norm(s):
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def dollars(s):
    return [float(x.replace(",", "")) for x in re.findall(r"\$(\d[\d,]*(?:\.\d\d)?)", s)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--answer-bank")
    ap.add_argument("--title", default="")
    ap.add_argument("--meta", default="")
    ap.add_argument("--no-links", action="store_true")
    args = ap.parse_args()

    raw = open(args.file, encoding="utf-8").read()
    pg = Page()
    pg.feed(raw)
    visible = norm(" ".join(pg.text))
    hard, warn = [], []

    def hit(kind, detail, is_hard=True):
        (hard if is_hard else warn).append(f"{kind}: {detail}")

    scan = visible + " " + norm(args.title) + " " + norm(args.meta)
    for word in set(re.findall(r"[a-z]+", scan.lower())):
        if hashlib.sha256(word.encode()).hexdigest() in BANNED_NAME_HASHES:
            hit("banned name", "prior owner surname found")
    for kind, pat in HARD_PATTERNS.items():
        for m in re.finditer(pat, scan):
            ctx = scan[max(0, m.start() - 40): m.end() + 40]
            hit(kind, f"'{m.group(0)}' in '...{ctx}...'")
    for m in re.finditer(OUT_WORDS, scan):
        hit("out word", f"'{m.group(0)}'")
    premium = len(re.findall(r"(?i)\bpremium\b", scan))
    if premium > 1:
        hit("out word", f"'premium' used {premium} times (sparingly at most)")
    for m in re.finditer(r"(?i)\bultimate\b", visible):
        after = visible[m.end(): m.end() + 12]
        if not (m.group(0) == "Ultimate" and re.match(r"\s*(basket|\(|\||,|\.|$| and| or| at| holds| serves)", after)):
            hit("out word", f"'ultimate' used as a word, not the basket name: '...{visible[max(0, m.start()-30):m.end()+30]}...'")

    for name, (pat, cap) in CAPS.items():
        n = len(re.findall(pat, visible))
        if n > cap:
            hit("repetition cap", f"'{name}' appears {n} times (max {cap})")

    first_block = next((b["text"] for b in pg.blocks if b["tag"] == "p" and norm(b["text"])), "")
    for where, txt in (("title", args.title), ("meta", args.meta), ("first paragraph", first_block)):
        if re.search(r"(?i)kosher", txt or ""):
            hit("kosher placement", f"'kosher' in the {where}")
    for tag, h in pg.headings:
        if tag == "h1" and re.search(r"(?i)kosher", h):
            hit("kosher placement", "'kosher' in an H1")

    if "—" in visible:
        hit("style", f"{visible.count(chr(0x2014))} em dash(es)", is_hard=False)
    for m in re.finditer(r"\b2025\b", visible):
        hit("stale year", f"'...{visible[max(0, m.start()-40):m.end()+30]}...'", is_hard=False)
    for m in re.finditer(r"\[NEED[^\]]*\]", visible):
        hit("open gap", m.group(0), is_hard=False)
    for em in set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", visible)):
        if em.lower() != "orders@thesweettooth.com":
            hit("email", f"unexpected address {em}")

    # FAQ: the section titled "What Customers Ask Us"
    faq = []
    faq_html = re.search(r"(?is)<h2[^>]*>\s*What Customers Ask Us\s*</h2>(.*?)(?=<h2|\Z)", raw)
    if faq_html:
        pairs = re.findall(r"(?is)<h3[^>]*>(.*?)</h3>\s*(.*?)(?=<h3|\Z)", faq_html.group(1))
        for q, a in pairs:
            q = norm(re.sub(r"<[^>]+>", " ", q))
            a_txt = norm(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<script.*?</script>", " ", a)))
            faq.append((q, a_txt))
            if dollars(a_txt):
                hit("price in FAQ answer", f"'{q}'")
    if args.answer_bank:
        bank = {norm(x["question"]).lower(): norm(x["answer"]) for x in json.load(open(args.answer_bank))}
        for q, a in faq:
            if q.lower() not in bank:
                hit("FAQ not in Answer Bank", f"'{q}'")
            elif not a.startswith(bank[q.lower()][: max(20, len(bank[q.lower()]) - 2)]):
                hit("FAQ answer differs from Answer Bank", f"'{q}'")
    for blob in pg.jsonld:
        try:
            json.loads(blob)
        except Exception as e:  # noqa: BLE001
            hit("invalid JSON-LD", str(e))
        if re.search(r"\$\d", blob) and '"FAQPage"' in blob:
            hit("price in FAQ schema", "a $ amount sits inside FAQPage JSON-LD")

    # Prices: every $ amount next to a product link must be a live variant price
    handles = set()
    for href in pg.links:
        m = re.search(r"/products/([a-z0-9-]+)", href)
        if m:
            handles.add(m.group(1))
    token = os.environ.get("SHOPIFY_TOKEN")
    prods = live_products(handles, token) if (token and handles) else {}
    if handles and not token:
        hit("prices", "SHOPIFY_TOKEN not set, prices not checked")
    for h, p in prods.items():
        if "error" in p:
            hit("product link", f"/products/{h}: {p['error']}")
        elif p["status"] != "active" or not p["published"]:
            hit("product link", f"/products/{h} is {p['status']}, published={p['published']}")
    checked = 0
    for unit in pg.rows + [b for b in pg.blocks if b["tag"] in ("p", "li")]:
        hs = {re.search(r"/products/([a-z0-9-]+)", l).group(1) for l in unit["links"] if "/products/" in l}
        amounts = dollars(unit["text"])
        if len(hs) == 1 and amounts:
            h = hs.pop()
            p = prods.get(h, {})
            for amt in amounts:
                checked += 1
                if "prices" in p and amt not in p["prices"]:
                    hit("price mismatch", f"${amt:g} next to /products/{h}; live prices {p['prices']}")
        elif len(hs) > 1 and amounts:
            hit("price check", f"block with {len(hs)} product links and prices, check by hand: '{norm(unit['text'])[:80]}'", is_hard=False)
    total = len(dollars(visible))
    if total > checked:
        hit("price check", f"{total - checked} $ amount(s) not tied to a single product link; verify by hand", is_hard=False)

    if not args.no_links:
        for href in sorted(set(pg.links)):
            if href.startswith("mailto:") or href.startswith("#"):
                continue
            url = href if href.startswith("http") else SITE + href
            code, final = http_status(url)
            if code != 200:
                hit("link", f"{url} returned {code}")
            elif final.rstrip("/") != url.rstrip("/") and "thesweettooth.com" in url:
                hit("link redirects", f"{url} -> {final}", is_hard=False)

    report = {
        "file": args.file,
        "words": len(visible.split()),
        "headings": pg.headings,
        "faq_questions": [q for q, _ in faq],
        "products_checked": prods,
        "hard": hard,
        "warn": warn,
        "verdict": "PASS" if not hard else "FAIL",
    }
    print(json.dumps(report, indent=1))
    sys.exit(0 if not hard else 1)


if __name__ == "__main__":
    main()
