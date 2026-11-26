/* Delivery channel: explicit development origins only; query parameters cannot grant DEV.
 * Local loopback remains enabled for existing automated regression and local development.
 * This is a UI/runtime gate, not authentication; public source code remains public. */
(() => {
  'use strict';
  const {protocol, hostname, pathname} = window.location;
  const rawPreview = protocol === 'https:' && hostname === 'raw.githack.com' &&
    pathname.startsWith('/celticmusic-nagoya/the-windbound-oath/');
  const localQA = (protocol === 'http:' || protocol === 'https:') &&
    ['localhost', '127.0.0.1', '[::1]'].includes(hostname);
  Object.defineProperty(window, 'WINDBOUND_DEV', {
    value: rawPreview || localQA, writable: false, configurable: false
  });
  document.documentElement.classList.toggle('windbound-dev', window.WINDBOUND_DEV);
})();
