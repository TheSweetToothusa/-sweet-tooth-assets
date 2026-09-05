#!/usr/bin/env python3
"""Generate a small SYNTHETIC export (same schema as the real export) to smoke-test analyze.py.
Numbers are random and mean nothing about the business."""
import gzip, json, os, random, datetime as dt, sys

random.seed(7)
out = sys.argv[1] if len(sys.argv) > 1 else "fixture_export"
os.makedirs(out, exist_ok=True)
vm = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "variant_map.json")))
baskets = [(int(k), v) for k, v in vm["baskets"].items() if "Bassinet" not in v[0]]
addons = [(int(k), v) for k, v in vm["addons"].items()]

orders = []
start = dt.datetime(2024, 9, 1, tzinfo=dt.timezone.utc)
for i in range(600):
    created = start + dt.timedelta(days=random.randint(0, 730))
    lines = []
    oid = 1000 + i
    is_bab = random.random() < 0.7
    total = 0.0
    if is_bab:
        vid, (size, diet, price) = random.choice(baskets)
        lines.append({"id": oid * 10, "product_id": 1, "variant_id": vid, "title": "Build a Basket", "variant_title": f"{size} - {diet}",
                      "quantity": 1, "price": f"{price:.2f}", "total_discount": "0.00",
                      "properties": [{"name": "Occasion", "value": random.choice(["Birthday", "Shiva", "Thank You", "Baby", "Get Well"])},
                                     {"name": "Basket Size", "value": size}, {"name": "Special Instructions", "len": 12, "kw": ["no nut"]}]})
        total += price
        for j, (avid, (label, group, sub, aprice)) in enumerate(random.sample(addons, random.choice([0, 0, 0, 1, 1, 2, 3]))):
            q = random.choice([1, 1, 1, 2])
            lines.append({"id": oid * 10 + j + 1, "product_id": 2, "variant_id": avid, "title": label, "variant_title": sub or "",
                          "quantity": q, "price": f"{aprice:.2f}", "total_discount": "0.00", "properties": []})
            total += aprice * q
        if random.random() < 0.15:
            lines.append({"id": oid * 10 + 9, "product_id": 3, "variant_id": 99, "title": random.choice(["Dubai Chocolate Bar", "Chocolate Roses", "Candy Apple"]),
                          "variant_title": "", "quantity": 1, "price": "19.00", "total_discount": "0.00", "properties": []})
            total += 19
    else:
        lines.append({"id": oid * 10, "product_id": 4, "variant_id": 98, "title": "Chocolate Pretzel Tray", "variant_title": "",
                      "quantity": 1, "price": "39.00", "total_discount": "0.00", "properties": []})
        total += 39
    orders.append({"id": oid, "name": f"#{oid}", "created_at": created.isoformat(), "cancelled_at": None,
                   "financial_status": "paid", "subtotal_price": f"{total:.2f}", "total_price": f"{total * 1.07:.2f}",
                   "total_discounts": "0.00", "customer_hash": f"c{random.randint(1, 400)}", "customer_orders_count": random.randint(1, 4),
                   "note_kw": [], "note_attributes": [{"name": "Basket Builder", "value": "Yes"}] if is_bab else [],
                   "refunds": [], "line_items": lines, "source_name": "web", "ship_country": "US", "ship_province": "FL"})
with gzip.open(os.path.join(out, "orders.jsonl.gz"), "wt") as f:
    for o in orders:
        f.write(json.dumps(o) + "\n")
with gzip.open(os.path.join(out, "products.json.gz"), "wt") as f:
    json.dump([], f)
print("wrote", len(orders), "synthetic orders to", out)
