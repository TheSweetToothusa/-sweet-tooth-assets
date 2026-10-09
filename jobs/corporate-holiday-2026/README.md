# Corporate holiday gifting 2026

- `backup/`: the three blog articles and their SEO metafields as they were on Oct 9 2026, before the refresh. Restore by PUTting `body_html`, `title` and the metafields back through the Shopify Admin API.
- Job notes (progress and checks) live in Notion, not here, because this repo is public.

Content gate used for every piece:
1. `scripts/rule_check.py` must return PASS (zero hard hits).
2. `scripts/blind_pack.py` builds a masked, shuffled pack: our page plus the pages that outrank it.
3. `.claude/agents/sweet-tooth-content-judge.md` scores the pack, run twice on two different models.
4. Pass bar: both overall scores 8.0 or higher, no criterion under 6, our page ranked #1.
