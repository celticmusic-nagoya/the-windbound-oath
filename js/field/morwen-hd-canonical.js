/* MORWEN-HD-CANONICAL-V2: read-only registry for the Morwen HD canonical v2 images.
 * Pure data access; not loaded by index.html and not connected to the field, battle, SAVE or Android.
 * The registry JSON (data/morwen-hd-canonical-v2.json) is the single source of paths and anchors.
 * Superseded images (old left profile, chibi walk candidates) are never returned. */
(function (root) {
  'use strict';
  const DIRECTIONS = ['front', 'left', 'right', 'back'];

  function create(registry) {
    if (!registry || registry.schema !== 'windbound.morwen-hd-canonical/2') {
      throw new Error('MorwenHDCanonical: unexpected registry schema');
    }
    const assets = registry.assets || {};
    const superseded = new Set((registry.superseded || []).map((s) => s.sha256).filter(Boolean));
    const display = registry.display;

    function asset(key) {
      const a = assets[key];
      if (!a) throw new Error('MorwenHDCanonical: unknown asset ' + key);
      if (superseded.has(a.sha256)) throw new Error('MorwenHDCanonical: superseded asset ' + key);
      return a;
    }

    /* Placement of a 1200x1600 display derivative so that the ground anchor lands on (footX, footY).
     * height: rendered canvas height in CSS px. anchorCorrection: apply the measured per-direction boot-centre offset. */
    function placeDisplay(direction, options) {
      if (!DIRECTIONS.includes(direction)) throw new Error('MorwenHDCanonical: bad direction ' + direction);
      const opts = options || {};
      const a = asset('display.pixel.' + direction);
      const height = Number(opts.height) || display.canvas[1];
      const scale = height / display.canvas[1];
      const dx = opts.anchorCorrection ? (a.measured && a.measured.anchor_dx) || 0 : 0;
      const footX = Number(opts.footX) || 0;
      const footY = Number(opts.footY) || 0;
      return {
        src: a.path,
        sha256: a.sha256,
        width: display.canvas[0] * scale,
        height: height,
        left: footX - (display.ground_anchor[0] - dx) * scale,
        top: footY - display.ground_anchor[1] * scale,
        scale: scale,
        anchorDx: dx
      };
    }

    return Object.freeze({
      directions: DIRECTIONS.slice(),
      canonicalLeft: registry.canonicalLeft || registry.canonical_left,
      display: display,
      asset: asset,
      original: (style, direction) => asset(style + '.' + direction),
      placeDisplay: placeDisplay,
      isSuperseded: (sha) => superseded.has(sha)
    });
  }

  async function load(url) {
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error('MorwenHDCanonical: registry HTTP ' + res.status);
    return create(await res.json());
  }

  const api = { create: create, load: load, DIRECTIONS: DIRECTIONS };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.MorwenHDCanonical = api;
})(typeof window !== 'undefined' ? window : globalThis);
