# Storefront chat widget

`st-chat-widget.liquid` is a mirror of the chat widget that runs on
thesweettooth.com. The live copy is **not version-controlled** — it lives in the
Shopify theme (Online Store → Themes → Edit code), and the file here was pulled
off the rendered page so changes to it can be reviewed as a diff before anyone
edits the theme.

Keep the two in sync by hand. After editing the theme, re-pull with:

    curl -sL https://thesweettooth.com/ | sed -n '/<div id="st-chat"/,/^<\/script>/p'

## Applying the current fix by hand

If you would rather not paste the whole block, the fix is three edits to the
existing widget in the theme.

**1. Delete the hint element** (in the markup, just under `<div id="st-chat" …>`):

```html
<div id="st-chat-hint" hidden>📦 Track my order</div>
```

**2. Delete the hint CSS**, both the `#st-chat-hint{…}` rule and the
`#st-chat-hint[hidden]{display:none}` line that follows it, plus the
`#st-chat-hint{bottom:…}` line inside the `@media(max-width:749px)` block.

**3. In that same media query**, replace the `#st-chat-toggle` rule with:

```css
#st-chat-toggle{bottom:calc(84px + env(safe-area-inset-bottom));right:16px;
  width:48px;height:48px;min-width:48px;padding:0;gap:0;border-radius:50%;
  justify-content:center;box-shadow:0 2px 10px rgba(0,0,0,.22)}
#st-chat-toggle-label{display:none}
```

**4. In the script**, delete the `var hint = …` line, the `try{…}catch(e){}`
block that auto-shows it, and the `hint.onclick = …` line — then remove the
lone `hint.hidden=true;` inside `function open(){…}`. Nothing else references
`hint`, so the widget keeps working.

## Why

The launcher had grown into a wide labelled pill, and `#st-chat-hint` popped a
second black pill for six seconds on every new mobile session. The hint sits at
`right:76px` while the toggle sits at `right:16px` and is far wider than 60px,
so the hint landed *underneath* the toggle — same `z-index`, hint first in the
DOM. All it ever showed was a stray dark edge and a 📦 peeking out from behind
the chat button. Both are gone; desktop keeps the labelled pill.
