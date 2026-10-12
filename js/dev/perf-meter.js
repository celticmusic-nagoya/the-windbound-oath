/* Read-only DEV performance meter. Opt-in: WINDBOUND_DEV === true and ?perf=1. */
(() => {
  'use strict';
  if (window.WINDBOUND_DEV !== true || new URLSearchParams(location.search).get('perf') !== '1') return;
  const DURATION = 60000;
  const panel = document.createElement('aside');
  panel.id = 'windboundPerfMeter';
  panel.setAttribute('aria-label', 'DEV 性能計測');
  Object.assign(panel.style, { position: 'fixed', left: 'max(8px, env(safe-area-inset-left))',
    bottom: 'max(8px, env(safe-area-inset-bottom))', zIndex: '100000', width: '270px',
    maxWidth: 'calc(100vw - 32px)', padding: '8px', background: '#101a12ee', color: '#fff',
    border: '1px solid #9dba8b', borderRadius: '6px', font: '12px/1.5 monospace', touchAction: 'auto' });
  const label = document.createElement('strong'); label.textContent = 'DEV 性能計測';
  const metrics = document.createElement('pre'); metrics.style.margin = '4px 0';
  const startButton = document.createElement('button'); startButton.id = 'windboundPerfStart';
  startButton.textContent = '60秒計測してJSONをコピー';
  const copyButton = document.createElement('button'); copyButton.id = 'windboundPerfCopy';
  copyButton.textContent = 'JSONをコピー'; copyButton.disabled = true;
  const status = document.createElement('div'); status.setAttribute('role', 'status');
  status.textContent = '同じマップで60秒間、画面を開いたまま計測します。';
  const output = document.createElement('textarea'); output.id = 'windboundPerfJson';
  output.readOnly = true; output.hidden = true; output.setAttribute('aria-label', '計測JSON');
  Object.assign(output.style, { width: '100%', height: '70px', boxSizing: 'border-box' });
  panel.append(label, metrics, startButton, copyButton, status, output); document.body.append(panel);
  let previous = null, rolling = [], session = null, lastResult = null, timer = null, raf = null;

  const number = v => typeof v === 'number' && Number.isFinite(v) ? v : null;
  const round = v => v == null ? null : Math.round(v * 1000) / 1000;
  function identity() {
    const field = window.MossForest;
    return { map_id: field && field.active ? field.mapId : null, level: field && field.active ? field.level : null };
  }
  function heap() {
    const m = performance.memory;
    return m ? { used_bytes: number(m.usedJSHeapSize), total_bytes: number(m.totalJSHeapSize),
      limit_bytes: number(m.jsHeapSizeLimit) } : null;
  }
  function navigation() {
    const s = window.FieldNavigation && window.FieldNavigation.status;
    return s ? { plans: number(s.plans), milliseconds: number(s.milliseconds), outcome: s.outcome || null } : null;
  }
  function frameStats(samples) {
    if (!samples.length) return { samples: 0, fps: { average: null, minimum: null, low_1_percent: null }, frame_ms: null };
    const values = samples.slice().sort((a, b) => a - b);
    const sum = values.reduce((a, b) => a + b, 0), slow = values.slice(-Math.max(1, Math.ceil(values.length * .01)));
    const pct = p => values[Math.max(0, Math.ceil(values.length * p) - 1)];
    return { samples: values.length, fps: { average: round(1000 * values.length / sum),
      minimum: round(1000 / values[values.length - 1]),
      low_1_percent: round(1000 * slow.length / slow.reduce((a, b) => a + b, 0)) },
      frame_ms: { average: round(sum / values.length), minimum: round(values[0]),
        median: round(pct(.5)), p95: round(pct(.95)), p99: round(pct(.99)), maximum: round(values[values.length - 1]) } };
  }
  async function copy() {
    if (!lastResult) return false;
    const text = JSON.stringify(lastResult, null, 2); output.value = text;
    try {
      if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard API unavailable');
      await navigator.clipboard.writeText(text);
      status.textContent = 'JSONをコピーしました。端末情報と合わせて貼り付けてください。'; return true;
    } catch (_) {
      output.hidden = false; output.focus(); output.select();
      let copied = false;
      try { copied = document.execCommand('copy'); } catch (_) { /* selection remains available */ }
      status.textContent = copied ? 'JSONをコピーしました。' : 'コピー権限がありません。JSONを選択してコピーするか、JSONをコピーボタンを押してください。';
      return copied;
    }
  }
  function finish() {
    if (!session) return;
    const s = session; session = null; clearTimeout(timer); timer = null;
    const end = identity(), elapsed = performance.now() - s.started;
    const invalid = [];
    if (s.hidden) invalid.push('page_hidden_during_measurement');
    if (!s.initial.map_id) invalid.push('no_active_field_at_start');
    if (s.mapChanged) invalid.push('map_changed_during_measurement');
    if (!s.frames.length) invalid.push('no_frame_samples');
    lastResult = { schema_version: 1, measured_at: new Date().toISOString(), ua: navigator.userAgent,
      screen: { width: screen.width, height: screen.height, viewport_width: innerWidth, viewport_height: innerHeight,
        device_pixel_ratio: devicePixelRatio, orientation: screen.orientation ? screen.orientation.type : null },
      map_id: s.initial.map_id, level: s.initial.level, end_map_id: end.map_id, end_level: end.level,
      target_duration_ms: DURATION, elapsed_ms: round(elapsed), valid: !invalid.length, invalid_reasons: invalid,
      frames: frameStats(s.frames), navigation: { initial: s.navInitial, last: navigation(), observed_plan_updates: s.nav },
      js_heap: { initial: s.heapInitial, final: heap(), samples: s.heaps }, field_timeline: s.timeline,
      definitions: { fps_average: '1000 / mean(rAF intervals in ms)', fps_minimum: '1000 / longest rAF interval',
        fps_low_1_percent: '1000 / mean(slowest ceil(N*0.01) rAF intervals)',
        navigation: 'Latest planner time sampled when map/plan counter changes; multiple plans in one frame may be missed.',
        js_heap: 'Optional Chromium JS heap estimate, excludes GPU/decoded image memory.', frames: 'rAF timing, not GPU presentation or Android system FPS.' } };
    output.value = JSON.stringify(lastResult, null, 2); output.hidden = false;
    startButton.disabled = false; startButton.textContent = '60秒を再計測してJSONをコピー'; copyButton.disabled = false;
    if (lastResult.valid) void copy();
    else status.textContent = '条件が変わったため無効な計測です。JSONは保存できます。同じマップで再計測してください。';
  }
  function start() {
    if (session) return false;
    const initial = identity(), navInitial = navigation();
    session = { started: performance.now(), frames: [], initial, lastIdentity: initial,
      hidden: document.hidden, mapChanged: false, navInitial, navKey: JSON.stringify([initial.map_id, navInitial && navInitial.plans]),
      nav: [], heapInitial: heap(), heaps: [], timeline: [{ elapsed_ms: 0, ...initial }] };
    previous = null; output.hidden = true; startButton.disabled = true;
    copyButton.disabled = true; status.textContent = '計測中… 60秒';
    timer = setTimeout(finish, DURATION); return true;
  }
  function tick(now) {
    if (previous != null && now > previous) {
      const dt = now - previous; rolling.push({ t: now, dt });
      if (session) session.frames.push(dt);
    }
    previous = now;
    while (rolling.length && rolling[0].t < now - 5000) rolling.shift();
    if (session) {
      const id = identity(), elapsed = now - session.started, nav = navigation();
      if (id.map_id !== session.initial.map_id) session.mapChanged = true;
      if (id.map_id !== session.lastIdentity.map_id || id.level !== session.lastIdentity.level) {
        session.timeline.push({ elapsed_ms: round(elapsed), ...id }); session.lastIdentity = id;
      }
      const key = JSON.stringify([id.map_id, nav && nav.plans]);
      if (key !== session.navKey) {
        session.navKey = key; session.nav.push({ elapsed_ms: round(elapsed), map_id: id.map_id, ...nav });
      }
    }
    raf = requestAnimationFrame(tick);
  }
  const interval = setInterval(() => {
    const s = frameStats(rolling.map(p => p.dt)), nav = navigation(), mem = heap();
    const f = v => v == null ? '取得不可' : v.toFixed(1);
    metrics.textContent = 'FPS 平均/最小/1%ロー\n' + [s.fps.average, s.fps.minimum, s.fps.low_1_percent].map(f).join(' / ') +
      '\nフレーム 平均: ' + f(s.frame_ms && s.frame_ms.average) + ' ms\n経路計算 最新: ' + f(nav && nav.milliseconds) +
      ' ms\nJSヒープ: ' + (mem && mem.used_bytes != null ? (mem.used_bytes / 1048576).toFixed(1) + ' MiB' : '取得不可');
    if (session) {
      const elapsed = performance.now() - session.started;
      status.textContent = '計測中… 残り ' + Math.max(0, Math.ceil((DURATION - elapsed) / 1000)) + '秒';
      if (mem) session.heaps.push({ elapsed_ms: round(elapsed), ...mem });
    }
  }, 1000);
  document.addEventListener('visibilitychange', () => { if (session && document.hidden) session.hidden = true; });
  startButton.addEventListener('click', start); copyButton.addEventListener('click', () => { void copy(); });
  addEventListener('pagehide', () => { cancelAnimationFrame(raf); clearInterval(interval); clearTimeout(timer); });
  window.WindboundPerf = Object.freeze({ start, copy, get lastResult() { return lastResult; }, get measuring() { return Boolean(session); } });
  raf = requestAnimationFrame(tick);
})();
