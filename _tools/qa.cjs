// QA visual de una demo en varios tamaños reales. Uso: PWCORE=... node qa.cjs <url> <outdir>
const { chromium } = require(process.env.PWCORE);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const VPS = [['laptop-1000x560', 1000, 560], ['1280x720', 1280, 720], ['1440x900', 1440, 900], ['1920x1080', 1920, 1080], ['mobile-390', 390, 844]];
(async () => {
  const [url, out] = process.argv.slice(2);
  const b = await chromium.launch({ channel: 'chrome', headless: false, args: ['--window-position=-3000,0'] });
  for (const [name, w, h] of VPS) {
    const p = await b.newPage({ viewport: { width: w, height: h }, isMobile: w < 500, deviceScaleFactor: 1 });
    const errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.goto(url + (url.includes('?') ? '&' : '?') + 'qa=' + name); await sleep(13000);
    if (w < 500) { const l = p.frameLocator('iframe').locator('[data-lb-part="launcher"]'); try { await l.click({ timeout: 5000 }); await sleep(5000); } catch (e) { errs.push('no launcher click: ' + e.message.slice(0, 60)); } }
    await p.screenshot({ path: `${out}/qa-${name}.png` });
    await p.mouse.wheel(0, 900); await sleep(1200);
    await p.screenshot({ path: `${out}/qa-${name}-scrolled.png` });
    console.log(name, errs.length ? errs : 'ok'); await p.close();
  }
  await b.close();
})();
