(() => {
  'use strict';
  const wrappers = [...document.querySelectorAll('.walkthrough-wrap')];
  const tabs = [...document.querySelectorAll('[data-track]')];
  function activateTrack(track) {
    tabs.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.track === track)));
    wrappers.forEach(wrapper => {
      const active = wrapper.id === `walkthrough-${track}`;
      if (!active) {
        wrapper.querySelector('iframe').contentDocument?.querySelector('[data-motion-action="pause"]')?.click();
      }
      wrapper.hidden = !active;
    });
  }
  tabs.forEach(button => button.addEventListener('click', () => activateTrack(button.dataset.track)));
  activateTrack('t2v');

  const resizeCallbacks = [];
  document.querySelectorAll('[data-walkthrough]').forEach(frame => {
    function connectFrame() {
      const doc = frame.contentDocument;
      if (!doc?.body || !doc.querySelector('[data-motion-root]')) return;
      const resize = () => {
        if (frame.parentElement.hidden && !matchMedia('print').matches) return;
        frame.style.height = `${Math.ceil(doc.body.getBoundingClientRect().height) + 4}px`;
      };
      new ResizeObserver(resize).observe(doc.body);
      resizeCallbacks.push(resize);
      resize();
    }
    frame.addEventListener('load', connectFrame);
    if (frame.contentDocument?.readyState === 'complete') connectFrame();
  });
  tabs.forEach(button => button.addEventListener('click', () => requestAnimationFrame(() => resizeCallbacks.forEach(fn => fn()))));
  window.addEventListener('beforeprint', () => resizeCallbacks.forEach(fn => fn()));
  window.addEventListener('afterprint', () => resizeCallbacks.forEach(fn => fn()));

  const dialog = document.querySelector('.image-dialog');
  let trigger;
  document.querySelectorAll('[data-enlarge]').forEach(button => {
    button.addEventListener('click', () => {
      trigger = button;
      const source = button.querySelector('img');
      const target = dialog.querySelector('img');
      target.src = source.currentSrc || source.src;
      target.alt = source.alt;
      dialog.showModal();
      document.body.style.overflow = 'hidden';
    });
  });
  dialog.querySelector('[data-close-dialog]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => { document.body.style.overflow = ''; trigger?.focus(); });

  document.querySelector('[data-copy-citation]').addEventListener('click', async () => {
    const citation = document.querySelector('#bibtex');
    const status = document.querySelector('.copy-status');
    try {
      await navigator.clipboard.writeText(citation.textContent);
      status.textContent = 'BibTeX copied.';
    } catch {
      const range = document.createRange();
      range.selectNodeContents(citation);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = 'Citation selected. Press Ctrl+C or ⌘C to copy.';
    }
  });

  const navLinks = [...document.querySelectorAll('.site-header nav a')];
  const observer = new IntersectionObserver(entries => {
    const current = entries.find(entry => entry.isIntersecting);
    if (!current) return;
    navLinks.forEach(link => {
      if (link.hash === `#${current.target.id}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }, {rootMargin: '-15% 0px -65% 0px'});
  navLinks.forEach(link => observer.observe(document.querySelector(link.hash)));
})();
