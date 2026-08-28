# Storefront chat widget

`st-chat-widget.liquid` is a mirror of the chat widget that runs on
thesweettooth.com. The live copy is **not version-controlled** — it lives in the
Shopify theme (Online Store → Themes → Edit code), and the file here was pulled
off the rendered page so changes can be reviewed as a diff before anyone edits
the theme.

To apply: replace the whole existing block in the theme — the
`<div id="st-chat">…</div>` plus the `<style>` and `<script>` that follow it —
with this file. It is plain HTML/CSS/JS, no Liquid.

To re-pull after a theme edit:

    curl -sL https://thesweettooth.com/ | sed -n '/<div id="st-chat"/,/^<\/script>/p'

## Design notes

The bottom-right corner is shared with the HikeOrders accessibility widget, so
the launcher is built to sit *with* it rather than compete:

- **Launcher** is a 44×44 tile on mobile, matching that widget's footprint and
  radius, stacked on the same right-hand axis with a 12px gap — one column of
  equal tiles instead of two mismatched shapes. Desktop keeps the labelled pill.
- **Clearance** is held by two variables at the top of the stylesheet,
  `--st-a11y-clear-y` and `--st-a11y-clear-x`. They keep the launcher above the
  accessibility widget and the send button out from under it, on every
  breakpoint. **If that widget moves, retune these two numbers** — its position
  is set in the app, not here.
- **Material** is `rgba(29,29,31,.92)` over a backdrop blur, with a hairline
  inner border and a two-layer shadow, so the control reads as floating glass
  rather than a solid slab. Falls back to flat `#1D1D1F` where
  `backdrop-filter` is unsupported.
- **The launcher tucks away** while the reader scrolls down and returns on the
  way back up, the way a browser toolbar does. This is the main "less intrusive"
  mechanism — it is absent from the page for most of a reading session.
- **The panel rises as a sheet** on mobile (rounded top, grabber, scrim,
  tap-outside and Escape to dismiss) instead of swapping the screen out.
- **Motion** uses the iOS sheet curve `cubic-bezier(.32,.72,0,1)` with
  press-state scaling, and is disabled entirely under
  `prefers-reduced-motion`.

Brand constraints observed: near-black `#1D1D1F` (never pure black), neutrals,
one 36px gold `#D4AF37` hairline as the only accent, restrained shadows, and no
emoji in on-site copy — the `📦`/`🚗`/`👋` that were in the quick replies and the
greeting are gone.

## Known issue this does not fix

The accessibility widget overlaps the chat panel's bottom-right corner at
**every** breakpoint, not just mobile. The clearance variables work around it,
but the real fix is to move that widget to the bottom-**left** in the HikeOrders
app settings, which frees the corner entirely and lets the clearance values drop
back to zero.
