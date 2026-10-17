// Screenshots every page at 1280 and 390 pixels wide, in light and dark,
// with reduced motion, so each diagram shows the still frame that holds its
// claim, from a running preview: bun run build && bun run preview, then
//   bun run shots -- <dir> [base URL, default http://localhost:4321/eddy/]
// Chromium is Playwright's, from the devenv shell (PLAYWRIGHT_BROWSERS_PATH).
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const [dir = 'shots', base = 'http://localhost:4321/eddy/'] = process.argv.slice(2);
const pages = ['', 'how-it-works/', 'how-it-fits/', 'design/', 'roadmap/'];
mkdirSync(dir, { recursive: true });
const browser = await chromium.launch({ channel: 'chromium' });
for (const theme of ['light', 'dark']) {
  for (const width of [1280, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 900 }, colorScheme: theme, reducedMotion: 'reduce' });
    await page.addInitScript((t) => localStorage.setItem('starlight-theme', t), theme);
    for (const path of pages) {
      await page.goto(base + path, { waitUntil: 'networkidle' });
      const name = (path.replace(/\/$/, '') || 'start').replace(/\//g, '-');
      await page.screenshot({ path: `${dir}/${name}-${width}-${theme}.png`, fullPage: true });
    }
    await page.close();
  }
}
await browser.close();
