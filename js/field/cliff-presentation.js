/* CliffPresentation: optional CG/dialogue presentation layer.
 * No story flags or save writes. Missing images fail closed without blocking the scene.
 * Modes: show({src,alt,mode:'full'|'dialogue'}), hide().
 */
(function () {
  'use strict';
  const APPROVED_PREFIX = 'assets/approved/game/cliff/';
  let root = null, image = null, current = 0;
  function ensure() {
    if (root) return root;
    root = document.createElement('div');
    root.id = 'cliff-cg-layer';
    root.setAttribute('aria-hidden', 'true');
    root.style.cssText = 'position:fixed;inset:0;z-index:120;pointer-events:none;display:none;background:#061326;';
    image = document.createElement('img');
    image.style.cssText = 'display:block;width:100%;height:100%;object-fit:contain;';
    image.alt = '';
    root.appendChild(image);
    document.body.appendChild(root);
    return root;
  }
  function hide() {
    current++;
    if (!root) return;
    root.style.display = 'none';
    root.setAttribute('aria-hidden', 'true');
    root.classList.remove('cliff-cg--dialogue');
    image.removeAttribute('src');
  }
  function allowed(src) {
    return typeof src === 'string' &&
      src.startsWith(APPROVED_PREFIX) &&
      /^assets\/approved\/game\/cliff\/[a-z0-9_-]+\.png$/.test(src);
  }
  function show(options) {
    const opts = options || {};
    if (!allowed(opts.src)) return Promise.resolve(false);
    const id = ++current;
    return new Promise(resolve => {
      const preload = new Image();
      let done = false;
      const finish = ok => {
        if (done) return;
        done = true;
        if (id !== current || !ok) return resolve(false);
        ensure();
        image.src = opts.src;
        image.alt = String(opts.alt || '');
        root.style.display = 'block';
        root.style.background = opts.mode === 'dialogue' ? 'transparent' : '#061326';
        root.classList.toggle('cliff-cg--dialogue', opts.mode === 'dialogue');
        image.style.objectFit = 'contain';
        root.setAttribute('aria-hidden', opts.mode === 'dialogue' ? 'true' : 'false');
        resolve(true);
      };
      preload.onload = () => finish(true);
      preload.onerror = () => finish(false);
      preload.src = opts.src;
      if (preload.complete) finish(preload.naturalWidth > 0);
    });
  }
  window.CliffPresentation = Object.freeze({show, hide, allowed});
})();
