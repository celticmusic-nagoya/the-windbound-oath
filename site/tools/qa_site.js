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
        unrevealed: document.querySelectorAll('img[data-defer]').length,
      };
    });
    rec(`${tag} 画像表示`, img.broken.length === 0, `${img.total}枚, 失敗=${JSON.stringify(img.broken)}`);
    rec(`${tag} 画像寸法指定(CLS対策)`, img.noDims.length === 0, JSON.stringify(img.noDims));
    rec(`${tag} 画像の縦横比維持`, img.ratio.length === 0, JSON.stringify(img.ratio));
    rec(`${tag} 遅延読み込み`, img.lazy >= 10 && img.unrevealed === 0, `loading=lazy ${img.lazy}枚 / スクロール後の未読込 ${img.unrevealed}枚`);
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

  // Hero: no overlap between logo / figure / copy / buttons, and buttons inside the first screen
  for (const [w, h] of [[360, 640], [360, 740], [390, 664], [390, 844], [844, 390], [1024, 768], [1440, 900]]) {
    const { ctx, p } = await page(b, { viewport: { width: w, height: h }, isMobile: w < 800, hasTouch: w < 800 });
    const r = await p.evaluate(() => {
      const g = (s) => document.querySelector(s).getBoundingClientRect();
      const boxes = { logo: g('.hero__logo'), catch: g('.hero__catch'), actions: g('.hero__actions'), aidan: g('.hero__aidan') };
      const hit = (a, b) => a.left < b.right - 1 && b.left < a.right - 1 && a.top < b.bottom - 1 && b.top < a.bottom - 1;
      const pairs = []; const k = Object.keys(boxes);
      for (let i = 0; i < k.length; i++) for (let j = i + 1; j < k.length; j++) if (hit(boxes[k[i]], boxes[k[j]])) pairs.push(k[i] + '×' + k[j]);
      const btn = [...document.querySelectorAll('.hero__actions .btn')].map((e) => ({ sw: e.scrollWidth, cw: e.clientWidth }));
      return { pairs, actionsBottom: Math.round(boxes.actions.bottom), vh: innerHeight, btnOverflow: btn.some((x) => x.sw > x.cw + 1),
        ratio: (() => { const i = document.querySelector('.hero__aidan'); const r = i.getBoundingClientRect(); const s = Math.min(r.width / i.naturalWidth, r.height / i.naturalHeight); return Math.abs((i.naturalWidth * s) / (i.naturalHeight * s) - i.naturalWidth / i.naturalHeight) < 0.01; })() };
    });
    rec(`HERO重なりなし ${w}x${h}`, r.pairs.length === 0 && r.actionsBottom <= r.vh && !r.btnOverflow && r.ratio,
      `重なり=${JSON.stringify(r.pairs)} ボタン下端=${r.actionsBottom}/${r.vh} ボタン文字はみ出し=${r.btnOverflow} 縦横比=${r.ratio}`);
    await ctx.close();
  }

  // prefers-reduced-motion: reduce
  {
    const { ctx, p } = await page(b, { viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
    await p.evaluate(() => document.getElementById('gallery').scrollIntoView());
    await p.waitForTimeout(600);
    await p.hover('.gallery-item >> nth=0');
    await p.waitForTimeout(400);
    const r = await p.evaluate(() => {
      const img = document.querySelector('.gallery-item img');
      const cs = getComputedStyle(img);
      const anyTransition = [...document.querySelectorAll('*')].some((e) => { const d = getComputedStyle(e).transitionDuration; return d && d.split(',').some((x) => parseFloat(x) > 0); });
      return { transform: cs.transform, scroll: getComputedStyle(document.documentElement).scrollBehavior, anyTransition, mq: matchMedia('(prefers-reduced-motion: reduce)').matches };
    });
    rec('動きを減らす設定(reduce)', r.mq && r.transform === 'none' && r.scroll === 'auto' && !r.anyTransition,
      `media=${r.mq} hover拡大=${r.transform} scroll-behavior=${r.scroll} transitionあり=${r.anyTransition}`);
    await ctx.close();
  }

  // JavaScript disabled
  {
    const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, javaScriptEnabled: false });
    const p = await ctx.newPage();
    await p.route(/fonts\.(googleapis|gstatic)\.com/, (r) => r.abort());
    await p.goto(BASE);
    await p.evaluate(() => 0).catch(() => {});
    for (let y = 0; y < 7000; y += 400) { await p.mouse.wheel(0, 400); await p.waitForTimeout(80); }
    await p.waitForTimeout(1500);
    const shot = await p.screenshot({ fullPage: true });
    // Count visible <img> boxes with a decoded image via accessibility of layout (JS off: use locator API)
    const vis = await p.locator('noscript + img, img').evaluateAll(() => 0).catch(() => null);
    const shown = await p.locator('.char-card__figure img:visible, .gallery-item img:visible, .story__bg:visible').count();
    rec('JavaScript無効時の画像表示', shown >= 12, `表示された遅延対象画像 ${shown}/12（noscriptフォールバック）`);
    await ctx.close();
  }

  // Compact menu fits (or scrolls) on short screens; Esc returns focus to the toggle
  for (const [w, h, m] of [[844, 390, true], [390, 844, true], [360, 640, true], [768, 1024, false]]) {
    const { ctx, p } = await page(b, { viewport: { width: w, height: h }, isMobile: m, hasTouch: m });
    await p.click('.nav-toggle'); await p.waitForTimeout(300);
    const r = await p.evaluate(() => {
      const nav = document.getElementById('site-nav');
      const last = nav.querySelector('li:last-child a');
      nav.scrollTop = nav.scrollHeight;
      const lb = last.getBoundingClientRect(); const nb = nav.getBoundingClientRect();
      return { lastBottom: Math.round(lb.bottom * 100) / 100, navBottom: Math.round(nb.bottom), vh: innerHeight, scrollable: nav.scrollHeight > nav.clientHeight };
    });
    await p.keyboard.press('Escape');
    const focusBack = await p.evaluate(() => document.activeElement.classList.contains('nav-toggle'));
    rec(`メニュー全体表示 ${w}x${h}`, r.lastBottom <= r.vh && r.navBottom <= r.vh && focusBack,
      `最終リンク下端=${r.lastBottom}/${r.vh} パネル下端=${r.navBottom} 内部スクロール=${r.scrollable} Esc後フォーカス=${focusBack}`);
    await ctx.close();
  }

  // Responsive images: declared sizes vs rendered width, and chosen candidate per DPR
  {
    const fails = []; const rows = [];
    for (const w of [1440, 1280, 1190, 1024, 900, 844, 768, 390, 360]) for (const dpr of [1, 2, 3]) {
      const { ctx, p } = await page(b, { viewport: { width: w, height: 900 }, deviceScaleFactor: dpr, isMobile: w < 800 });
      await scrollAll(p); await p.waitForTimeout(800);
      const r = await p.evaluate(() => {
        const evalSizes = (sizes) => {
          for (const part of sizes.split(/,(?![^(]*\))/)) {
            const t = part.trim(); const m = t.match(/^(\(.*\))\s+(.+)$/);
            if (!m || matchMedia(m[1]).matches) {
              const d = document.createElement('div'); d.style.cssText = 'position:absolute;visibility:hidden;width:' + (m ? m[2] : t);
              document.body.append(d); const v = d.getBoundingClientRect().width; d.remove(); return v;
            }
          }
        };
        return [...document.querySelectorAll('.gallery-item img:not(noscript img), .char-card__figure img')].filter((i) => i.srcset).map((i) => {
          const cands = i.srcset.split(',').map((c) => { const [u, wd] = c.trim().split(/\s+/); return { u, w: parseInt(wd) }; }).sort((a, b) => a.w - b.w);
          const box = i.closest('.gallery-item, .char-card__figure').getBoundingClientRect().width;
          const declared = evalSizes(i.sizes);
          const chosen = cands.find((c) => i.currentSrc.endsWith(c.u)) || {};
          const need = box * devicePixelRatio;
          const ideal = cands.find((c) => c.w >= need) || cands[cands.length - 1];
          return { kind: i.closest('.gallery-item') ? 'gallery' : 'char', box: Math.round(box), declared: Math.round(declared), dev: Math.abs(declared - box) / box, chosen: chosen.w, ideal: ideal.w };
        });
      });
      for (const kind of ['gallery', 'char']) {
        const k = r.filter((x) => x.kind === kind); if (!k.length) continue;
        const worst = k.reduce((a, x) => (x.dev > a.dev ? x : a));
        const under = k.filter((x) => x.chosen < x.ideal);
        rows.push(`${kind} ${w}@${dpr}x 実幅${worst.box} 申告${worst.declared} 選択${k[0].chosen}w`);
        if (worst.dev > 0.06 || under.length) fails.push(`${kind} ${w}@${dpr}x dev=${(worst.dev * 100).toFixed(1)}% chosen<ideal=${under.length}`);
      }
      await ctx.close();
    }
    rec('画像sizesと実表示幅・DPR別の候補選択', fails.length === 0, fails.join(' | ') || rows.filter((x, i) => i % 6 === 0).join(' / ') + ` …（${rows.length}条件、乖離6%以内・候補不足0）`);
  }

  await b.close();
  console.log(JSON.stringify(results, null, 1));
  const fail = results.filter((r) => r.result === 'FAIL').length;
  console.log(`\n${results.length - fail} PASS / ${fail} FAIL`);
  process.exit(fail ? 1 : 0);
})();
