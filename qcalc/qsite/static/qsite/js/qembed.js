// Embed widget: host-page loader (replaces [data-qcalc] with an iframe) and
// in-frame resizer (script tag carries data-child) in one file.
(function () {
  const me = document.currentScript;

  if (me.hasAttribute('data-child')) {
    new ResizeObserver(() =>
      parent.postMessage({ qcalc: document.body.scrollHeight }, '*')).observe(document.body);
    return;
  }

  const origin = new URL(me.src).origin;
  document.querySelectorAll('[data-qcalc]').forEach(el => {
    const f = document.createElement('iframe');
    f.src = `${origin}/calc/core/${encodeURIComponent(el.dataset.qcalc)}/?embed=1` +
            (el.dataset.run === 'false' ? '' : '&run') +
            (el.dataset.query ? '&' + el.dataset.query : '');  // e.g. token=... or example=1
    f.title = el.dataset.qcalc;
    f.loading = 'lazy';
    f.style.cssText = `width:100%;border:0;min-height:${parseInt(el.dataset.height, 10) || 480}px`;
    el.replaceWith(f);
  });

  addEventListener('message', e => {
    if (e.origin !== origin || !e.data || !e.data.qcalc) return;
    document.querySelectorAll('iframe').forEach(f => {
      if (f.contentWindow === e.source) f.style.height = e.data.qcalc + 'px';
    });
  });
})();
