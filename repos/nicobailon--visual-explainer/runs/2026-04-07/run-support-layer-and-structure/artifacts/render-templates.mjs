import { chromium } from 'playwright';
import { mkdirSync, statSync } from 'fs';

const templates = ['architecture.html', 'data-table.html', 'mermaid-flowchart.html', 'slide-deck.html'];
const browser = await chromium.launch();
const results = [];
mkdirSync('shots', { recursive: true });

for (const t of templates) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  // Block all network resources to avoid CDN timeout in sandbox
  await page.route('**/*', (route) => {
    const url = route.request().url();
    if (url.startsWith('file://')) return route.continue();
    return route.abort();
  });
  const errors = [];
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message.slice(0,150)}`));

  const src = `/tmp/visual-explainer/plugins/visual-explainer/templates/${t}`;
  try {
    await page.goto('file://' + src, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await page.waitForTimeout(1000);
  } catch (e) { results.push({ template: t, error: e.message.slice(0,200) }); await page.close(); continue; }

  const title = await page.title();
  const visibleText = await page.evaluate(() => document.body.innerText.length);
  const slideCount = await page.evaluate(() => document.querySelectorAll('.slide').length);
  const sectionCount = await page.evaluate(() => document.querySelectorAll('section').length);
  const shotPath = `shots/${t.replace('.html','.png')}`;
  await page.screenshot({ path: shotPath, fullPage: false });
  results.push({ template: t, title, visibleTextLen: visibleText, slides: slideCount, sections: sectionCount, screenshotKB: Math.round(statSync(shotPath).size/1024), pageErrors: errors });
  await page.close();
}
await browser.close();
console.log(JSON.stringify(results, null, 2));
