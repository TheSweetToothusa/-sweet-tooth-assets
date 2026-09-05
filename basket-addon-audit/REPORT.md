# Build-a-Basket Add-On Audit — Status Report

**Date:** 2026-09-05
**Status:** BLOCKED on order data. Everything that can be prepared without it is done and tested. No website or Shopify changes were made.

## 1. Where this stands

The audit needs line-item order history from Shopify (`thesweettoothfl.myshopify.com`). This session has no Shopify credential and no Shopify connector, and it is not allowed to read the stored token, so the only authorized route is the GitHub Actions secret already used by the bi-monthly order audit.

**What is ready:**

- A one-off, read-only export workflow on branch `claude/basket-addon-export` of the private repo `TheSweetToothusa/sweet-tooth-order-audit`. It pulls every order since 2024-08-01 (24+ months) plus the product catalog, strips all PII (no names, emails, phones, addresses, gift messages), hashes the customer id so repeat buying can still be measured, and commits the result to that same branch.
- `analyze.py` in this folder. It computes every metric in the brief for every add-on and is smoke-tested on a synthetic fixture (`make_fixture.py`).

**What Mike needs to do (2 minutes):**

1. Open https://github.com/TheSweetToothusa/sweet-tooth-order-audit/actions/workflows/export-orders.yml
2. Click **Run workflow**, choose branch **claude/basket-addon-export**, leave the date as is, click **Run workflow**.
3. Tell me it ran. I will pull the export, run the analysis, and complete this report. (A scheduled check-in also looks for it automatically.)

If the run reports `likely_missing_read_all_orders_scope: true`, the token can only see 60 days of orders and the Shopify app that owns it needs the `read_all_orders` scope added. In that case the alternative is a manual CSV: Shopify admin → Orders → Export → "All orders", "CSV for Excel", dropped into Google Drive.

## 2. Current add-on lineup (verified from the live builder page, 2026-09-05)

The live Build-a-Basket step 3 shows these, in this order:

| # | Add-on | Price | Shopify variant(s) | Notes |
|---|---|---|---|---|
| 1 | Large Chocolate Plaque (replaces the free plaque) | $20 | 6 occasions × Dairy/Vegan | Dairy only in the UI when Parve/Vegan basket is chosen |
| 2 | Gourmet Cookies (6-pack) | $15 | choc-chip, white-choc, oatmeal, mixed | |
| 3 | Chocolate Chip Brownies (6-pack) | $15 | 48000994312447 | |
| 4 | Pecan Pralines (6-pack) | $18 | 48000994509055 | |
| 5 | Assorted Truffles (9-pack) | $18 | dairy / vegan | |
| 6 | Marshmallow Sticks (3-pack) | $18 | 48494364328191 | |
| 7 | Mucho Gusto Munch | $12 | 48000994574591 | |
| 8 | Gluten-Free Dipped Oreos (6-pack) | $18 | 48000994607359 | dietary |
| 9 | Vegan/Parve Dipped Oreos (6-pack) | $18 | 48000994640127 | dietary |
| 10 | Biscoff Dipped Cookies (6-pack) | $15 | 49090491351295 | added 2026; kosher/parve status of Lotus Biscoff is UNVERIFIED per Open Loops |
| 11 | Sonny's Black & White Cookies (6-pack) | $18 | 49090492956927 | bought-in product |
| 12 | Make the entire basket gluten-free | $20 (Small–XL), $30 Grand Oval, $40 Jumbo, $50 Ultimate, $70 Supreme | 5 variants | dietary; was unpublished until 2026-08-21 |

Not on the regular builder but sold as basket add-ons and tracked by the analysis: Dipped Oreos 6-pack ($18), Dipped Pretzels 6-pack ($18), Large/Mini Shofars, Rosh Hashanah Apple Lollipop, Classic Red Candy Apple. The old repo builder also sold a Dubai Chocolate Bar as an add-on; the analysis captures it if it appears in history.

Basket sizes and dairy/vegan variants are mapped in `variant_map.json` (28 basket variants, 31 add-on variants).

## 3. Facts already known that will shape the classification

These come from the basket-making guides in Drive and the builder code, not from sales data.

- **Cookies and brownies are no longer inside the standard baskets, but pralines are.** The 2025 factory guide (`BASKET MAKING 2025`) packed cookies and brownies into every size, but the current contents matrix (`basket_contents_matrix.xlsx`, updated 2026-08-26) and the live page description list only Oreos, pretzels, truffles/bark, graham crackers/wafers/tea biscuits, dipped fruit, and pecan pralines from Medium up. So the $15 cookie and brownie add-ons are genuine upsells today, while the $18 praline add-on adds more of something Medium-and-up buyers already get. Attach rate by basket size will show whether pralines sell mainly to Small-basket buyers who otherwise get none.
- **Large plaque is dairy-only in the UI**, so every Vegan/Parve basket order is structurally locked out of the highest-priced upgrade. The data will show the vegan share of orders and thus the revenue being left on the table.
- **The GF upgrade was unpublished for part of 2026** and one add-on being set to draft on 2026-07-28 broke every checkout. Any add-on kept in the lineup is a checkout dependency; fewer live SKUs means fewer ways to break the builder.
- **Rosh Hashanah builder plan (Open Loops, 2026-08-18)** already narrows the "Add More Treats" group to five items: Pretzels 6-pack, Oreos 6-pack, Truffles 9-pack, Cookies 6-pack, Brownies 6-pack. That is the working hypothesis for group A; the data will confirm or overturn it.

## 4. Cost and margin data: NOT available

No per-item cost data exists in Drive, Notion, the repos, or the pricing skill (the pricing skill only has chocolate cost per lb and mold/wrap/pack labor rates for wholesale squares). No margins are estimated in this report. To calculate gross profit, gross margin % and gross profit per 100 Build-a-Basket orders, I need from Mike, per add-on:

| Add-on | What I need |
|---|---|
| Cookies, Brownies | ingredient + bake labor cost per 6-pack, packaging |
| Pralines | pecan + sugar + labor per 6-pack |
| Truffles | cost per 9 truffles (dairy and vegan), box |
| Marshmallow Sticks | cost per 3 sticks (marshmallow, chocolate, stick, sleeve) |
| Mucho Gusto Munch | cost per bag |
| GF Oreos, Vegan Oreos | cookie cost + chocolate + labor per 6 |
| Biscoff | Lotus cookie cost + chocolate + labor per 6 |
| Sonny's B&W cookies | purchase price per 6 from Sonny's |
| Large plaque | chocolate weight (g) and type, mold labor, box; and the cost of the free plaque it replaces |
| GF upgrade | cost delta of swapping to GF items by basket size |

A single number per row is enough (e.g. "cookies 6-pack costs us $4.10 all-in").

## 5. Operational signals to be checked in the export

The export keeps refund line items, refund notes (keyword only), order notes (keyword only) and special-instruction keywords, so the analysis reports per add-on: refunded units, orders with any refund, and mentions of "substitut", "missing", "melted", "broken", "wrong", "allerg", "gluten", "no nuts" etc. Out-of-stock and manual-staff-work data does not exist in Shopify; those need Mike's or staff input.

## 6. Deliverables pending the data

Sections 1–10 of the requested final report (ranked table, A/B/C/D classification, prominent list, See More list, dietary list, removals with evidence, new add-ons to test, revenue-at-risk, page layout) will be written from `out/metrics.json` once the export exists. No classification is being proposed on guesswork.

## 7. Nothing was changed on the website

No Shopify product, theme, or page was modified. The only writes were: this folder on branch `claude/sweet-tooth-basket-audit-yvsini`, and the export workflow on branch `claude/basket-addon-export` of the private audit repo (delete that branch after the audit if you prefer).
