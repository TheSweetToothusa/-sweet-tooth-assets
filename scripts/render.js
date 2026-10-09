// Render a page in headless Chromium and save its HTML and/or a screenshot.
// Usage: node scripts/render.js <url> <out.html> [screenshot.png]
const { chromium } = require('playwright');
(async () => {
  const [url, outHtml, shot] = process.argv.slice(2);
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
  const page = await browser.newPage({ userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36', viewport: { width: 1280, height: 900 } });
  const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(4000);
  if (outHtml) require('fs').writeFileSync(outHtml, await page.content());
  if (shot) await page.screenshot({ path: shot, fullPage: true });
  console.log(resp ? resp.status() : 'no response', url);
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
