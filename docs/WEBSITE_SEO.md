# Website SEO pages

Added 10 Oct 2026. Four static pages sit alongside the home page in `website/`: `/window-installers`, `/roofers`, `/kitchen-fitters` (one per trade, same "quotation" layout as the home page, each with a "What your customers receive" section pulled from `docs/delivery/08_homeowner_messages.md`) and `/faq` (eight questions installers ask, marked up with FAQPage JSON-LD so Google and AI answer engines can quote them). The home page now carries Organization JSON-LD, a nav link to the FAQ and a "Trades" block linking to all four pages; every page has a unique title and meta description, one H1, a canonical tag and under 600 words of visible text; `sitemap.xml` and `robots.txt` are new. Nothing on these pages implies a track record: no clients, results, testimonials or price (only "a fee per booked survey, agreed before we start"), and the FAQ answers are taken from the pilot agreement, export-request email and audit template in `docs/delivery/`. The goal is to own the empty search "quote follow-up for window installers" and to give cold-email recipients something credible to find when they google Velarqo. Cloudflare Workers static assets (`wrangler.jsonc`, default `html_handling`) serve clean URLs (`/roofers` → `roofers.html`), which the canonicals and sitemap assume. The `_headers` rules are global and unchanged.

## Deploy

Not deployed yet. From the repo root:

```bash
npx wrangler deploy
```

Then check `https://velarqo.com/faq` renders, `https://velarqo.com/roofers.html` redirects to `/roofers`, and submit `https://velarqo.com/sitemap.xml` in Google Search Console. Test the FAQ markup at https://search.google.com/test/rich-results.

## Local preview

`.claude/launch.json` "website" now runs `npx serve` (clean URLs, like the live site) instead of Python's http.server, which cannot map `/roofers` to `roofers.html`.
