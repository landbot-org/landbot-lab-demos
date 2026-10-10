// Captura la home de un prospecto (escritorio + móvil) para usarla como fondo de su demo.
// Uso: PWCORE=... node capture.cjs <url> <outdir>
const { chromium } = require(process.env.PWCORE);
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function shot(b, url, vp, file, mobile) {
  const p = await b.newPage({ viewport: vp, isMobile: mobile, deviceScaleFactor: mobile ? 2 : 1,
    userAgent: mobile ? 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' : undefined });
  await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }); await sleep(6000);
  // cerrar banners de cookies/chat habituales sin aceptar nada en nombre de nadie: solo se ocultan
  await p.addStyleTag({ content: '#onetrust-banner-sdk,#onetrust-consent-sdk,.cky-consent-container,#CybotCookiebotDialog,[id*="cookie" i][class*="banner" i],iframe[title*="chat" i],#hubspot-messages-iframe-container,.intercom-lightweight-app{display:none!important}' });
  await p.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } window.scrollTo(0, 0); });
  await sleep(2500);
  const h = await p.evaluate(() => document.documentElement.scrollHeight);
  await p.screenshot({ path: file, fullPage: true, clip: { x: 0, y: 0, width: vp.width, height: Math.min(h, mobile ? 2600 : 3200) }, type: 'jpeg', quality: 78 });
  await p.close();
}
(async () => {
  const [url, out] = process.argv.slice(2);
  const b = await chromium.launch({ channel: 'chrome', headless: false, args: ['--window-position=-2000,0'] });
  await shot(b, url, { width: 1440, height: 900 }, out + '/site-desktop.jpg', false);
  await shot(b, url, { width: 390, height: 844 }, out + '/site-mobile.jpg', true);
  await b.close();
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
