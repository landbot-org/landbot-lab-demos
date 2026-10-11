// Recorre la demo DENTRO del widget de la página, con capturas por paso. Uso: PWCORE=... node qa-walk.cjs <page-url> <outdir> <w> <h> <answers separados por |>
const { chromium } = require(process.env.PWCORE);
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const [url, out, w, h, answers] = process.argv.slice(2);
  const b = await chromium.launch({ channel: 'chrome', headless: false, args: ['--window-position=-3000,0'] });
  const p = await b.newPage({ viewport: { width: +w, height: +h }, isMobile: +w < 500 });
  await p.goto(url + '?walk=' + Date.now()); await sleep(13000);
  const fr = () => p.frames().find(f => f !== p.mainFrame() && f.url() !== 'about:blank') || p.frames()[1];
  if (+w < 500) { for (const f of p.frames()) { try { await f.locator('[data-lb-part="launcher"]').click({ timeout: 3000 }); break; } catch (e) {} } await sleep(6000); }
  let i = 0; await p.screenshot({ path: `${out}/walk-${w}-${i++}.png` });
  for (const a of answers.split('|')) {
    let done = false;
    for (const f of p.frames()) {
      try {
        const btn = f.locator('[data-lb-part="option-button"]', { hasText: a });
        if (await btn.count()) { await btn.last().click({ timeout: 5000 }); done = true; break; }
        const inp = f.locator('[data-lb-part="input-field"] textarea, [data-lb-part="input-field"] input, [data-lb-part="text-input"] input, [data-lb-part="text-input"] textarea');
        if (await inp.count()) { await inp.last().click(); await inp.last().fill(a); await inp.last().press('Enter'); done = true; break; }
      } catch (e) {}
    }
    await sleep(6500); await p.screenshot({ path: `${out}/walk-${w}-${i++}.png` });
    if (!done) console.log('could not answer:', a);
  }
  await b.close(); console.log('done', i);
})();
