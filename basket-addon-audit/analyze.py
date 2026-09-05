#!/usr/bin/env python3
"""
Build-a-Basket add-on audit.

Input : a PII-scrubbed Shopify order export (orders.jsonl.gz + products.json.gz)
        produced by the export workflow in TheSweetToothusa/sweet-tooth-order-audit
        (branch claude/basket-addon-export), plus variant_map.json in this folder.
Output: out/metrics.json, out/*.csv and out/tables.md (all aggregate, no PII).

Usage : python3 analyze.py --export /path/to/export [--since 2024-09-01] [--out out]
"""
import argparse, csv, gzip, json, os, re, statistics, sys, datetime as dt
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- add-on groups (order = default display order in tables) -------------
GROUPS = {
    "plaque":        "Large Chocolate Plaque ($20)",
    "cookies":       "Gourmet Cookies 6-pack ($15)",
    "brownies":      "Chocolate Chip Brownies 6-pack ($15)",
    "pralines":      "Pecan Pralines 6-pack ($18)",
    "truffles":      "Assorted Truffles 9-pack ($18)",
    "marshmallow":   "Marshmallow Sticks 3-pack ($18)",
    "mucho-gusto":   "Mucho Gusto Munch ($12)",
    "gf-oreos":      "Gluten-Free Dipped Oreos 6-pack ($18)",
    "vegan-oreos":   "Vegan/Parve Dipped Oreos 6-pack ($18)",
    "biscoff":       "Biscoff Dipped Cookies 6-pack ($15)",
    "bw-cookies":    "Sonny's Black & White Cookies 6-pack ($18)",
    "gf-upgrade":    "Gluten-Free Basket Upgrade ($20-$70)",
    # not on the regular builder today but sold as basket add-ons (Rosh Hashanah step / older setups)
    "oreos-6pk":     "Chocolate-Dipped Oreos 6-pack (RH add-on, $18)",
    "pretzels-6pk":  "Chocolate-Dipped Pretzels 6-pack (RH add-on, $18)",
    "shofar":        "Chocolate Shofar (RH add-on)",
    "rh-apple":      "Rosh Hashanah Apple Lollipop / Candy Apple (RH add-on)",
    "dubai-bar":     "Dubai Chocolate Bar (former add-on)",
    "other-addon":   "Other item tagged basket-add-on",
}

TITLE_RULES = [  # (regex on line title, group) — fallback when variant id is unknown
    (r"large chocolate plaque|large plaque|chocolate house key", "plaque"),
    (r"gluten.?free.*(basket|upgrade|conversion)|make .*gluten.?free", "gf-upgrade"),
    (r"gluten.?free.*oreo", "gf-oreos"),
    (r"(vegan|parve).*oreo", "vegan-oreos"),
    (r"oreo", "oreos-6pk"),
    (r"pretzel", "pretzels-6pk"),
    (r"biscoff", "biscoff"),
    (r"black\s*(&|and)\s*white", "bw-cookies"),
    (r"brownie", "brownies"),
    (r"praline", "pralines"),
    (r"truffle", "truffles"),
    (r"marshmallow", "marshmallow"),
    (r"mucho gusto|munch", "mucho-gusto"),
    (r"cookie", "cookies"),
    (r"shofar", "shofar"),
    (r"apple", "rh-apple"),
    (r"dubai", "dubai-bar"),
]

BASKET_TITLE_RE = re.compile(r"build.?a.?basket|basket builder|bassinet|custom (gift )?basket", re.I)
ADDON_TITLE_RE = re.compile(r"basket add-?on|add-?on", re.I)

# Approximate holiday windows (14 days before through the holiday). Treat as indicative only.
HOLIDAYS = {
    "Rosh Hashanah":   [("2024-09-18", "2024-10-04"), ("2025-09-08", "2025-09-24"), ("2026-08-28", "2026-09-13")],
    "Hanukkah":        [("2024-12-11", "2025-01-02"), ("2025-11-30", "2025-12-22")],
    "Christmas/NY":    [("2024-12-11", "2024-12-31"), ("2025-12-11", "2025-12-31")],
    "Valentine's Day": [("2025-01-31", "2025-02-14"), ("2026-01-31", "2026-02-14")],
    "Purim":           [("2025-02-27", "2025-03-14"), ("2026-02-16", "2026-03-03")],
    "Passover":        [("2025-03-29", "2025-04-20"), ("2026-03-18", "2026-04-09")],
    "Mother's Day":    [("2025-04-27", "2025-05-11"), ("2026-04-26", "2026-05-10")],
    "Teacher Appreciation": [("2025-04-28", "2025-05-09"), ("2026-04-27", "2026-05-08")],
    "Father's Day":    [("2025-06-01", "2025-06-15"), ("2026-06-07", "2026-06-21")],
    "Thanksgiving":    [("2024-11-14", "2024-11-28"), ("2025-11-13", "2025-11-27")],
}


def f(x):
    try:
        return float(x or 0)
    except Exception:
        return 0.0


def load(export):
    orders = []
    with gzip.open(os.path.join(export, "orders.jsonl.gz"), "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                orders.append(json.loads(line))
    products = []
    pp = os.path.join(export, "products.json.gz")
    if os.path.exists(pp):
        with gzip.open(pp, "rt", encoding="utf-8") as fh:
            products = json.load(fh)
    return orders, products


def build_maps(products):
    vm = json.load(open(os.path.join(HERE, "variant_map.json")))
    basket_v = {int(k): v for k, v in vm["baskets"].items()}
    addon_v = {int(k): v for k, v in vm["addons"].items()}
    tagged_addon_products = set()
    for p in products:
        tags = p.get("tags") or ""
        if isinstance(tags, list):
            tags = ",".join(tags)
        is_addon = "basket-add-on" in tags.lower() or (p.get("product_type") or "").lower() in ("basket add-on", "holiday add-ons")
        if is_addon:
            tagged_addon_products.add(p["id"])
    return basket_v, addon_v, tagged_addon_products


def classify_line(li, basket_v, addon_v, tagged_addon_products):
    vid = li.get("variant_id")
    title = f"{li.get('title') or ''} {li.get('variant_title') or ''}"
    props = {p.get("name"): p.get("value") for p in li.get("properties", []) if "value" in p}
    prop_names = {p.get("name") for p in li.get("properties", [])}
    if vid in basket_v:
        name, diet, _ = basket_v[vid]
        return ("basket", name, diet, props)
    if "Basket Size" in prop_names or BASKET_TITLE_RE.search(li.get("title") or ""):
        size = props.get("Basket Size") or re.sub(r"\s*-\s*\$.*$", "", li.get("variant_title") or "") or "Unknown"
        vt = (li.get("variant_title") or "").lower()
        diet = "vegan" if ("vegan" in vt or "parve" in vt) else ("dairy" if "dairy" in vt else "unknown")
        return ("basket", size, diet, props)
    if vid in addon_v:
        _, group, sub, _ = addon_v[vid]
        return ("addon", group, sub, props)
    if li.get("product_id") in tagged_addon_products or ADDON_TITLE_RE.search(title) or "Upgrade for" in prop_names or "Upgrade" in prop_names:
        for rx, g in TITLE_RULES:
            if re.search(rx, title, re.I):
                return ("addon", g, None, props)
        return ("addon", "other-addon", None, props)
    return ("other", None, None, props)


def holiday_for(date):
    d = date.strftime("%Y-%m-%d")
    for h, wins in HOLIDAYS.items():
        for a, b in wins:
            if a <= d <= b:
                return h
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--since", default="2024-09-01")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    orders, products = load(args.export)
    basket_v, addon_v, tagged = build_maps(products)

    bab = []
    standalone_addons = Counter()
    all_orders = 0
    excluded = Counter()
    for o in orders:
        created = dt.datetime.fromisoformat(o["created_at"]).astimezone(dt.timezone.utc)
        if created.strftime("%Y-%m-%d") < args.since:
            continue
        all_orders += 1
        if o.get("cancelled_at") or o.get("financial_status") in ("voided",):
            excluded["cancelled/voided"] += 1
            continue
        if f(o.get("total_price")) <= 0 and f(o.get("subtotal_price")) <= 0:
            excluded["zero total"] += 1
            continue
        baskets, addons, others = [], [], []
        for li in o.get("line_items", []):
            kind, a, b, props = classify_line(li, basket_v, addon_v, tagged)
            rec = {"li": li, "a": a, "b": b, "props": props, "qty": int(li.get("quantity") or 0),
                   "net": f(li.get("price")) * int(li.get("quantity") or 0) - f(li.get("total_discount"))}
            (baskets if kind == "basket" else addons if kind == "addon" else others).append(rec)
        refunded_line_qty = Counter()
        refunded_amt = 0.0
        for rf in o.get("refunds", []):
            for r in rf.get("line_items", []):
                refunded_line_qty[r.get("line_item_id")] += int(r.get("quantity") or 0)
            for t in rf.get("transactions", []):
                if t.get("kind") == "refund" and t.get("status") == "success":
                    refunded_amt += f(t.get("amount"))
        if not baskets:
            for a in addons:
                standalone_addons[a["a"]] += a["qty"]
            excluded["no basket line"] += 1
            continue
        na = {p["name"]: p.get("value") for p in o.get("note_attributes", [])}
        occasion = None
        for bk in baskets:
            occasion = occasion or bk["props"].get("Occasion")
        occasion = occasion or na.get("Occasion") or "Unknown"
        gf_prop = any(str(bk["props"].get("Gluten-Free Upgrade", "")).lower().startswith("yes") for bk in baskets)
        bab.append({
            "id": o["id"], "created": created, "month": created.strftime("%Y-%m"),
            "total": f(o.get("total_price")), "subtotal": f(o.get("subtotal_price")),
            "refunded": refunded_amt, "refunded_line_qty": refunded_line_qty,
            "source": o.get("source_name"),
            "customer": o.get("customer_hash"), "cust_orders": o.get("customer_orders_count"),
            "size": baskets[0]["a"], "diet": baskets[0]["b"], "occasion": occasion, "gf_prop": gf_prop,
            "basket_rev": sum(b["net"] for b in baskets),
            "baskets": baskets, "addons": addons, "others": others,
            "note_kw": (o.get("note_kw") or []) + [k for li in o.get("line_items", []) for p in li.get("properties", []) for k in (p.get("kw") or [])],
            "holiday": holiday_for(created),
        })

    N = len(bab)
    if N == 0:
        print("No Build-a-Basket orders found. Check variant_map.json / classification rules.")
        sys.exit(1)

    cust_counts = Counter(o["customer"] for o in bab if o["customer"])
    repeat_custs = {c for c, n in cust_counts.items() if n > 1}
    months = sorted({o["month"] for o in bab})
    sizes = Counter(o["size"] for o in bab)
    occ = Counter(o["occasion"] for o in bab)

    metrics = {}
    aov_all = statistics.mean(o["total"] for o in bab)
    for g, label in GROUPS.items():
        with_ = [o for o in bab if any(a["a"] == g for a in o["addons"]) or (g == "gf-upgrade" and o["gf_prop"])]
        with_ids = {o["id"] for o in with_}
        without = [o for o in bab if o["id"] not in with_ids]
        units = sum(a["qty"] for o in with_ for a in o["addons"] if a["a"] == g)
        rev = sum(a["net"] for o in with_ for a in o["addons"] if a["a"] == g)
        refunded_units = sum(o["refunded_line_qty"].get(a["li"]["id"], 0) for o in with_ for a in o["addons"] if a["a"] == g)
        if not with_ and units == 0 and standalone_addons.get(g, 0) == 0:
            continue
        aov_with = statistics.mean(o["total"] for o in with_) if with_ else 0
        aov_without = statistics.mean(o["total"] for o in without) if without else 0
        lift_ctrl, wsum = 0.0, 0
        for s in sizes:
            w = [o["total"] for o in with_ if o["size"] == s]
            wo = [o["total"] for o in without if o["size"] == s]
            if w and wo:
                lift_ctrl += (statistics.mean(w) - statistics.mean(wo)) * len(w)
                wsum += len(w)
        lift_ctrl = lift_ctrl / wsum if wsum else None
        avg_spend = rev / len(with_) if with_ else 0
        by_size = Counter(o["size"] for o in with_)
        metrics[g] = {
            "label": label,
            "units": units,
            "orders": len(with_),
            "attach_rate": len(with_) / N,
            "revenue": round(rev, 2),
            "revenue_per_100_bab_orders": round(rev / N * 100, 2),
            "avg_qty_per_order": round(units / len(with_), 2) if with_ else 0,
            "avg_addon_spend_when_selected": round(avg_spend, 2),
            "aov_with": round(aov_with, 2), "aov_without": round(aov_without, 2),
            "aov_lift_naive": round(aov_with - aov_without, 2),
            "aov_lift_size_controlled": round(lift_ctrl, 2) if lift_ctrl is not None else None,
            "halo_beyond_own_price": round(lift_ctrl - avg_spend, 2) if lift_ctrl is not None else None,
            "repeat_customer_share": round(sum(1 for o in with_ if o["customer"] in repeat_custs) / len(with_), 3) if with_ else None,
            "returning_customer_share": round(sum(1 for o in with_ if (o["cust_orders"] or 0) > 1) / len(with_), 3) if with_ else None,
            "refunded_units": refunded_units,
            "orders_with_any_refund": sum(1 for o in with_ if o["refunded"] > 0),
            "standalone_units_non_basket_orders": standalone_addons.get(g, 0),
            "by_month": {m: sum(a["qty"] for o in with_ if o["month"] == m for a in o["addons"] if a["a"] == g) for m in months},
            "by_size": dict(by_size),
            "by_occasion": dict(Counter(o["occasion"] for o in with_).most_common(8)),
            "by_diet": dict(Counter(o["diet"] for o in with_)),
            "by_holiday": dict(Counter(o["holiday"] or "non-holiday" for o in with_)),
            "by_variant": dict(Counter(a["b"] for o in with_ for a in o["addons"] if a["a"] == g and a["b"])),
            "size_attach": {s: round(by_size[s] / sizes[s], 3) for s in sizes},
        }

    any_addon = [o for o in bab if o["addons"] or o["gf_prop"]]
    any_ids = {o["id"] for o in any_addon}
    cross = Counter()
    cross_rev = Counter()
    cross_orders = Counter()
    for o in bab:
        seen = set()
        for x in o["others"]:
            t = x["li"].get("title") or "?"
            if x["li"].get("gift_card") or re.search(r"delivery|shipping|tip|fee", t, re.I):
                continue
            cross[t] += x["qty"]
            cross_rev[t] += x["net"]
            if t not in seen:
                cross_orders[t] += 1
                seen.add(t)
    kw = Counter(k for o in bab for k in o["note_kw"])
    overall = {
        "window_since": args.since, "orders_in_window_total": all_orders, "excluded": dict(excluded),
        "bab_orders": N, "bab_customers": len(cust_counts), "repeat_bab_customers": len(repeat_custs),
        "aov_all_bab": round(aov_all, 2),
        "aov_with_any_addon": round(statistics.mean(o["total"] for o in any_addon), 2) if any_addon else None,
        "aov_no_addon": round(statistics.mean(o["total"] for o in bab if o["id"] not in any_ids), 2) if len(any_addon) < N else None,
        "any_addon_attach_rate": round(len(any_addon) / N, 3),
        "addon_revenue_total": round(sum(a["net"] for o in bab for a in o["addons"]), 2),
        "basket_revenue_total": round(sum(o["basket_rev"] for o in bab), 2),
        "orders_by_month": {m: sum(1 for o in bab if o["month"] == m) for m in months},
        "addon_attach_by_month": {m: round(sum(1 for o in any_addon if o["month"] == m) / max(1, sum(1 for o in bab if o["month"] == m)), 3) for m in months},
        "orders_by_size": dict(sizes.most_common()), "orders_by_occasion": dict(occ.most_common(15)),
        "orders_by_diet": dict(Counter(o["diet"] for o in bab)),
        "orders_by_holiday": dict(Counter(o["holiday"] or "non-holiday" for o in bab).most_common()),
        "orders_by_source": dict(Counter(o["source"] for o in bab).most_common(6)),
        "note_keywords": dict(kw.most_common(25)),
        "cross_sell_candidates": [{"title": t, "units": u, "orders": cross_orders[t], "orders_share": round(cross_orders[t] / N, 4), "revenue": round(cross_rev[t], 2)} for t, u in cross.most_common(25)],
        "standalone_addon_units": dict(standalone_addons),
    }

    json.dump({"overall": overall, "addons": metrics}, open(os.path.join(args.out, "metrics.json"), "w"), indent=2, default=str)

    ranked = sorted(metrics.items(), key=lambda kv: kv[1]["revenue"], reverse=True)
    cols = ["label", "units", "orders", "attach_rate", "revenue", "revenue_per_100_bab_orders", "avg_qty_per_order",
            "avg_addon_spend_when_selected", "aov_with", "aov_without", "aov_lift_naive", "aov_lift_size_controlled",
            "halo_beyond_own_price", "repeat_customer_share", "returning_customer_share", "refunded_units",
            "standalone_units_non_basket_orders"]
    with open(os.path.join(args.out, "addons_ranked.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["group"] + cols)
        for g, m in ranked:
            w.writerow([g] + [m.get(c) for c in cols])
    with open(os.path.join(args.out, "addons_by_month.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["group"] + months)
        w.writerow(["BAB orders"] + [overall["orders_by_month"][m] for m in months])
        for g, m in ranked:
            w.writerow([g] + [m["by_month"][mm] for mm in months])
    lines = ["## Ranked add-ons (window since %s, %d Build-a-Basket orders)\n" % (args.since, N),
             "| # | Add-on | Units | Orders | Attach | Revenue | Rev/100 BAB | Avg qty | AOV with | AOV w/o | Lift (size-ctrl) | Halo | Refunded units |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, (g, m) in enumerate(ranked, 1):
        lines.append(f"| {i} | {m['label']} | {m['units']} | {m['orders']} | {m['attach_rate']:.1%} | ${m['revenue']:,.0f} | ${m['revenue_per_100_bab_orders']:,.0f} | {m['avg_qty_per_order']} | ${m['aov_with']:,.0f} | ${m['aov_without']:,.0f} | {m['aov_lift_size_controlled']} | {m['halo_beyond_own_price']} | {m['refunded_units']} |")
    lines.append("\n## Attach rate by basket size\n")
    size_list = [s for s, _ in sizes.most_common()]
    lines.append("| Add-on | " + " | ".join(f"{s} (n={sizes[s]})" for s in size_list) + " |")
    lines.append("|---|" + "---|" * len(size_list))
    for g, m in ranked:
        lines.append(f"| {m['label']} | " + " | ".join(f"{m['size_attach'].get(s, 0):.1%}" for s in size_list) + " |")
    lines.append("\n## Overall\n")
    for k, v in overall.items():
        if not isinstance(v, (dict, list)):
            lines.append(f"- {k}: {v}")
    open(os.path.join(args.out, "tables.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:len(ranked) + 3]))
    print(json.dumps({k: v for k, v in overall.items() if not isinstance(v, (dict, list))}, indent=2))


if __name__ == "__main__":
    main()
