// The four sampled observations have their own clock, separate from lesson steps.
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const print = matchMedia('print');
  document.querySelectorAll('[data-frame-sequence]').forEach(sequence => {
    const root = sequence.closest('[data-motion-root]');
    const figures = [...sequence.querySelectorAll('[data-sequence-frame]')];
    const selectors = [...sequence.querySelectorAll('[data-frame-select]')];
    const cells = [...sequence.querySelectorAll('[data-frame-cell]')];
    const playButton = sequence.querySelector('[data-frame-play]');
    const status = sequence.querySelector('[data-frame-status]');
    let current = 0, timer = 0, playing = false, available = false;

    function pauseFrames() {
      clearTimeout(timer);
      timer = 0;
      playing = false;
      sequence.classList.remove('frames-playing');
      playButton.setAttribute('aria-pressed', 'false');
      playButton.textContent = 'Play frames';
    }

    function render(index, announce = false) {
      current = Math.max(0, Math.min(figures.length - 1, index));
      sequence.dataset.frameCurrent = String(current);
      figures.forEach((figure, i) => {
        figure.classList.toggle('is-frame-current', i === current);
        if (available) figure.setAttribute('aria-hidden', String(i !== current));
        else figure.removeAttribute('aria-hidden');
      });
      selectors.forEach(button => button.setAttribute('aria-pressed', String(available && Number(button.dataset.frameSelect) === current)));
      cells.forEach(cell => cell.classList.toggle('is-frame-current', available && Number(cell.dataset.frameCell) === current));
      if (announce) status.textContent = figures[current].querySelector('figcaption').textContent;
      if (available && root.dataset.stepCurrent === '5') revealColumn();
    }

    function pauseLesson() {
      root.querySelector('[data-motion-action="pause"]').click();
    }

    function select(index, announce = true) {
      pauseLesson();
      pauseFrames();
      render(index, announce);
    }

    function revealColumn() {
      // Reveal only within the horizontal table scroller, without moving the page.
      const scroller = sequence.querySelector('.sequence-scroll');
      const cell = sequence.querySelector(`th[data-frame-cell="${current}"]`);
      const box = cell.getBoundingClientRect(), viewport = scroller.getBoundingClientRect();
      const left = viewport.left + sequence.querySelector('.sequence-table th').getBoundingClientRect().width;
      if (box.left < left) scroller.scrollLeft -= left - box.left;
      else if (box.right > viewport.right) scroller.scrollLeft += box.right - viewport.right;
    }

    function tick() {
      if (!playing || !available) return;
      render(current + 1, false);
      if (current === figures.length - 1) {
        pauseFrames();
        status.textContent = 'Sequence complete. ' + figures[current].querySelector('figcaption').textContent;
      } else timer = setTimeout(tick, 1100);
    }

    function syncAvailability() {
      const next = !reduce.matches && !print.matches && !root.dataset.motionState;
      if (next !== available) {
        pauseFrames();
        available = next;
        sequence.classList.toggle('frames-interactive', available);
        playButton.disabled = !available;
        selectors.forEach(button => { button.disabled = !available; });
        render(current);
      }
      if (root.dataset.stepCurrent !== '5' || root.classList.contains('is-playing')) pauseFrames();
    }

    sequence.addEventListener('click', event => {
      if (!available) return;
      const selector = event.target.closest('[data-frame-select]');
      if (selector) select(Number(selector.dataset.frameSelect));
      if (event.target.closest('[data-frame-play]')) {
        if (playing) { pauseFrames(); return; }
        pauseLesson();
        if (current === figures.length - 1) render(0, true);
        playing = true;
        sequence.classList.add('frames-playing');
        playButton.setAttribute('aria-pressed', 'true');
        playButton.textContent = 'Pause frames';
        timer = setTimeout(tick, 1100);
      }
    });

    sequence.addEventListener('keydown', event => {
      if (!event.target.closest('.frame-player, .timeline-data')) return;
      // Local controls and horizontal table scrolling must not change lesson steps.
      event.stopPropagation();
      if (!available || event.ctrlKey || event.metaKey || event.altKey) return;
      const button = event.target.closest('[data-frame-select]');
      if (!button) return;
      const keys = {ArrowLeft: (current + 3) % 4, ArrowRight: (current + 1) % 4, Home: 0, End: 3};
      if (!(event.key in keys)) return;
      event.preventDefault();
      select(keys[event.key]);
      button.closest('.frame-times, thead').querySelector(`[data-frame-select="${current}"]`).focus();
    });

    root.addEventListener('click', event => {
      if (event.target.closest('[data-motion-action], [data-step-tab]')) pauseFrames();
    });
    new MutationObserver(syncAvailability).observe(root, {attributes: true, attributeFilter: ['data-step-current', 'data-motion-state', 'class']});
    reduce.addEventListener('change', syncAvailability);
    print.addEventListener('change', syncAvailability);
    document.addEventListener('visibilitychange', () => { if (document.hidden) pauseFrames(); });
    syncAvailability();
  });
})();
