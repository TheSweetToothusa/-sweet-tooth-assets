# Rosh Hashanah Basket Builder — template

Live page: https://thesweettooth.com/pages/rosh-hashanah-basket-builder
Shopify theme: LIVE SITE (theme id 161706344703)
Theme file: `templates/page.basket-builder-rosh.liquid`

Nothing in this folder deploys on its own. It is kept here so the template is
versioned and reviewable instead of living only in the Shopify theme editor.

## Files

| File | What it is |
|---|---|
| `page.basket-builder-rosh.liquid` | **Restored** template (2026-09-08). What to paste into Shopify once Mike says GO. |
| `backups/page.basket-builder-rosh.LIVE-2026-09-08.liquid` | The template exactly as it is live today, rebuilt from the rendered page. Roll back to this to undo. |
| `backups/page.basket-builder-rosh.2026-08-26.liquid` | Backup taken 2026-08-26 (from Driver-s-App PR #5), before the accordion was deleted on 2026-09-01. |
| `restore-2026-09-08.diff` | Plain diff, live → restored. 132 changed lines. |
| `screenshots/` | Before/after renders, phone (390px) and desktop (1280px). |

## What the restore changes

1. **"What's inside every basket? Tap to see" accordion is back** in the size step,
   in its original spot (under the size strip), with the markup exactly as it was on 2026-08-26.
   Shows on phones (≤768px), which is what its original CSS did.
2. **The CSS line that hid it is removed** (`.whats-inside-accordion{display:none !important;}`).
3. **The "Good to know" FAQ rail is visible again.** It was sitting inside the occasion step,
   which this page hides, so it never rendered. It is moved into the size step:
   right-hand sticky rail on desktop (≥1024px), stacked below the sizes on phones/tablets —
   the same arrangement as `/pages/build-a-basket`. The four questions and answers are unchanged.

Everything else in the template is untouched (hero, prices, add-ons, cart code).

## How to apply

1. Shopify admin → Online Store → Themes → LIVE SITE → Edit code → `templates/page.basket-builder-rosh.liquid`.
2. Replace the whole file with `page.basket-builder-rosh.liquid` from this folder. Save.
3. Check on a phone and on desktop.

To roll back, paste `backups/page.basket-builder-rosh.LIVE-2026-09-08.liquid` back in.
