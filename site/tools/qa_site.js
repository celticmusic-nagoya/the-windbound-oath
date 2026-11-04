// Site QA (Playwright). Usage: serve repo root on :8765, then
//   NODE_PATH=$(npm root -g) node site/tools/qa_site.js
// Google Fonts requests are blocked here to make the result independent of the network;
// font-loading over the network must be checked separately on GitHub Pages.
const { chromium } = require('playwright');
const BASE = process.env.SITE_URL || 'http://localhost:8765/site/';
const results = [];
const rec = (name, ok, detail = '') => { results.push({ name, result: ok ? 'PASS' : 'FAIL', detail }); };

async function page(b, opt) {
  const ctx = await b.newContext(opt);
  const p = await ctx.newPage();
  p.errs = [];
  p.on('pageerror', (e) => p.errs.push('pageerror: ' + e.message));
  p.on('console', (m) => { if (m.type() === 'error' && !/ERR_FAILED/.test(m.text())) p.errs.push('console: ' + m.text()); });
  p.on('requestfailed', (r) => { if (!/fonts\.g/.test(r.url())) p.errs.push('requestfailed: ' + r.url()); });
  p.on('response', (r) => { if (r.status() >= 400) p.errs.push(`http ${r.status()}: ${r.url()}`); });
  await p.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.abort());
  await p.addInitScript(() => {
    window.__cls = 0;
    new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__cls += e.value; })
      .observe({ type: 'layout-shift', buffered: true });
  });
  await p.goto(BASE);
  await p.waitForTimeout(1200);
  return { ctx, p };
}
const scrollAll = (p) => p.evaluate(async () => {
  for (let y = 0; y < document.body.scrollHeight; y += 300) { scrollTo(0, y); await new Promise((r) => setTimeout(r, 100)); }
  scrollTo(0, 0);
});

(async () => {
  const b = await chromium.launch();

  // Horizontal overflow at several widths
  for (const w of [1440, 1280, 1024, 768, 390, 360]) {
    const { ctx, p } = await page(b, { viewport: { width: w, height: 900 }, hasTouch: w <= 768, isMobile: w <= 768 });
    await scrollAll(p);
    const m = await p.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
    rec(`横スクロールなし ${w}px`, m.sw <= m.cw, `scrollWidth=${m.sw} clientWidth=${m.cw}`);
    await ctx.close();
  }

  for (const [tag, opt] of [['PC 1440', { viewport: { width: 1440, height: 900 } }], ['SP 390', { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true }]]) {
    const { ctx, p } = await page(b, opt);
    await scrollAll(p);
    await p.waitForTimeout(1500);
    const img = await p.evaluate(() => {
      const all = [...document.querySelectorAll('img')].filter((i) => i.getAttribute('src'));
      return {
        total: all.length,
        broken: all.filter((i) => !i.complete || i.naturalWidth === 0).map((i) => i.getAttribute('src')),
        noDims: all.filter((i) => !i.getAttribute('width') || !i.getAttribute('height')).map((i) => i.getAttribute('src')),
        ratio: all.filter((i) => i.naturalWidth && Math.abs(i.naturalWidth / i.naturalHeight - i.width / i.height) > 0.02 && getComputedStyle(i).objectFit === 'fill').map((i) => i.getAttribute('src')),
        lazy: all.filter((i) => i.loading === 'lazy').length,
      };
    });
    rec(`${tag} 画像表示`, img.broken.length === 0, `${img.total}枚, 失敗=${JSON.stringify(img.broken)}`);
    rec(`${tag} 画像寸法指定(CLS対策)`, img.noDims.length === 0, JSON.stringify(img.noDims));
    rec(`${tag} 画像の縦横比維持`, img.ratio.length === 0, JSON.stringify(img.ratio));
    rec(`${tag} 遅延読み込み`, img.lazy >= 10, `loading=lazy ${img.lazy}枚`);
    const cls = await p.evaluate(() => window.__cls);
    rec(`${tag} レイアウトシフト`, cls < 0.1, `CLS=${cls.toFixed(4)}`);

    const font = await p.evaluate(async () => {
      await document.fonts.ready;
      const body = getComputedStyle(document.body).fontFamily;
      const h = getComputedStyle(document.querySelector('.section-head__ja')).fontFamily;
      return { body, h, sansJP: document.fonts.check('16px "Noto Sans CJK JP"', 'あ'), serifJP: document.fonts.check('16px "Noto Serif CJK JP"', 'あ') };
    });
    rec(`${tag} 日本語フォント指定`, /Noto Sans JP/.test(font.body) && /Noto Serif JP/.test(font.h), `body=${font.body.split(',')[0]} / 見出し=${font.h.split(',')[0]}`);

    // Navigation
    const sections = ['news', 'story', 'system', 'characters', 'gallery', 'play'];
    let navOk = true; const navDetail = [];
    for (const id of sections) {
      if (tag.startsWith('SP')) { await p.click('.nav-toggle'); await p.waitForTimeout(200); }
      await p.click(`.site-nav a[href="#${id}"]`);
      await p.waitForTimeout(900);
      const top = await p.evaluate((i) => Math.round(document.getElementById(i).getBoundingClientRect().top), id);
      const ok = Math.abs(top - (tag.startsWith('SP') ? 56 : 64)) <= 4;
      if (!ok) { navOk = false; navDetail.push(`${id}:${top}`); }
    }
    rec(`${tag} ナビゲーション`, navOk, navDetail.join(' ') || '6リンクとも該当セクションへ移動');
    if (tag.startsWith('SP')) {
      await p.click('.nav-toggle');
      const ex = await p.getAttribute('.nav-toggle', 'aria-expanded');
      await p.keyboard.press('Escape');
      const ex2 = await p.getAttribute('.nav-toggle', 'aria-expanded');
      rec('SP 390 メニュー開閉(aria-expanded/Esc)', ex === 'true' && ex2 === 'false', `open=${ex} afterEsc=${ex2}`);
    }

    // Buttons
    const hrefs = await p.$$eval('.btn', (bs) => bs.map((x) => x.getAttribute('href')));
    rec(`${tag} ボタンのリンク先`, hrefs.every((h) => h === '../' || h === '#story'), JSON.stringify(hrefs));

    // Lightbox via mouse
    await p.evaluate(() => document.getElementById('gallery').scrollIntoView());
    await p.click('.gallery-item >> nth=1');
    await p.waitForTimeout(800);
    let lb = await p.evaluate(() => { const d = document.querySelector('.lightbox'); const i = d.querySelector('img'); return { open: d.open, src: i.getAttribute('src'), nw: i.naturalWidth, cap: d.querySelector('figcaption').textContent }; });
    const okOpen = lb.open && lb.nw > 0;
    await p.click('.lightbox__next'); await p.waitForTimeout(600);
    const s2 = await p.getAttribute('.lightbox__img', 'src');
    await p.click('.lightbox__prev'); await p.waitForTimeout(600);
    const s3 = await p.getAttribute('.lightbox__img', 'src');
    await p.click('.lightbox__close'); await p.waitForTimeout(300);
    const closed = await p.evaluate(() => !document.querySelector('.lightbox').open);
    rec(`${tag} ライトボックス`, okOpen && s2 !== lb.src && s3 === lb.src && closed, `open=${lb.open} 画像=${lb.src}(${lb.nw}px) 次/前/閉じる=${s2 !== lb.src}/${s3 === lb.src}/${closed}`);

    // Keyboard
    if (tag.startsWith('PC')) {
      await p.goto(BASE); await p.waitForTimeout(800); // fresh focus state
      await p.keyboard.press('Tab');
      const first = await p.evaluate(() => document.activeElement.className);
      await p.focus('.gallery-item >> nth=0');
      await p.keyboard.press('Enter'); await p.waitForTimeout(600);
      const kOpen = await p.evaluate(() => document.querySelector('.lightbox').open);
      const s1 = await p.getAttribute('.lightbox__img', 'src');
      await p.keyboard.press('ArrowRight'); await p.waitForTimeout(400);
      const sR = await p.getAttribute('.lightbox__img', 'src');
      await p.keyboard.press('ArrowLeft'); await p.waitForTimeout(400);
      const sL = await p.getAttribute('.lightbox__img', 'src');
      await p.keyboard.press('Escape'); await p.waitForTimeout(400);
      const back = await p.evaluate(() => ({ open: document.querySelector('.lightbox').open, focus: document.activeElement.classList.contains('gallery-item') }));
      rec('PC キーボード操作', first === 'skip-link' && kOpen && sR !== s1 && sL === s1 && !back.open && back.focus,
        `Tab先頭=${first} Enterで開く=${kOpen} ←→=${sR !== s1}/${sL === s1} Escで閉じる=${!back.open} フォーカス復帰=${back.focus}`);
    }
    rec(`${tag} コンソールエラー`, p.errs.length === 0, p.errs.join(' | ') || 'なし（Google Fontsは遮断して除外）');
    await ctx.close();
  }
  await b.close();
  console.log(JSON.stringify(results, null, 1));
  const fail = results.filter((r) => r.result === 'FAIL').length;
  console.log(`\n${results.length - fail} PASS / ${fail} FAIL`);
  process.exit(fail ? 1 : 0);
})();
