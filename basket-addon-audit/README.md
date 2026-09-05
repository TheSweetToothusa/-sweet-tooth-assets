# basket-addon-audit

Analysis toolkit for auditing The Sweet Tooth's Build-a-Basket add-ons.

- `REPORT.md` — the audit report (status and findings).
- `analyze.py` — computes attach rate, revenue, AOV lift, seasonality, size/occasion/diet splits, refunds and cross-sell candidates for every add-on.
- `variant_map.json` — Shopify variant ids for basket sizes and add-ons, taken from the live builder page on 2026-09-05.
- `make_fixture.py` — generates a synthetic export for smoke tests only. Its numbers mean nothing.

Run:

```
python3 analyze.py --export /path/to/export --since 2024-09-01
```

The export comes from the `export-orders.yml` workflow on branch `claude/basket-addon-export` of `TheSweetToothusa/sweet-tooth-order-audit` (PII-scrubbed). Outputs land in `out/` and are git-ignored until reviewed.
