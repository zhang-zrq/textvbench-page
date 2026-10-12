const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');

module.exports = async function browserChecks(browser, base) {
  const report = [];
  const context = await browser.newContext({viewport: {width: 1366, height: 900}, permissions: ['clipboard-read', 'clipboard-write']});
  const page = await context.newPage();
  const errors = [], failed = [], requests = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('response', r => { if (r.status() >= 400) failed.push(`${r.status()} ${r.url()}`); });
  page.on('request', r => requests.push(r.url()));
  await page.goto(base, {waitUntil: 'networkidle'});
  const config = JSON.parse(await fs.readFile('data/site.json', 'utf8'));
  assert.equal(await page.title(), config.title);
  assert.equal(await page.locator('#paper-title').getAttribute('aria-label'), config.title);
  assert.equal(await page.locator('.author-names a, .author-names span').count(), config.authors.length);
  assert.match(await page.locator('.author-names').innerText(), /Ruiqiang Zhang/);
  assert.match(await page.locator('.affiliations').innerText(), /Anhui Province Key Laboratory/);
  assert.equal(await page.locator('a[href^="mailto:"]').count(), 0);
  assert.equal(await page.locator('.video-placeholder').count(), 0);
  assert.equal(await page.locator('video').count(), 1);
  assert.equal(await page.locator('.resource-link[href="https://arxiv.org/abs/2610.13412"]').count(), 1);
  assert.match(await page.locator('#bibtex').innerText(), /@misc\{zhang2026textvbenchevaluatingtextrendering/);
  assert.match(await page.locator('#bibtex').innerText(), /eprint=\{2610\.13412\}/);
  assert.equal(await page.locator('video source').getAttribute('src'), config.video.src);
  assert.equal(await page.locator('video').getAttribute('poster'), config.video.poster);
  assert.equal(await page.locator('video').getAttribute('preload'), 'none');
  assert.equal(await page.locator('video').evaluate(v => v.paused && !v.autoplay && v.controls && v.playsInline), true);
  assert.equal(await page.locator('.results-table tbody tr').count(), 12);
  assert.equal(await page.locator('.sample-card').count(), 4);
  assert.equal(await page.locator('[aria-disabled="true"][href]').count(), 0);
  await page.locator('#evaluation').scrollIntoViewIfNeeded();
  const demo = page.frameLocator('#walkthrough-t2v iframe');
  const root = demo.locator('[data-motion-root]');
  await root.locator('.intro-panel').waitFor();
  const assertStage = async (frame, step) => {
    assert.equal(await frame.locator('[data-motion-root]').getAttribute('data-step-current'), String(step));
    const selected = frame.getByRole('tab', {selected: true});
    assert.equal(await selected.count(), 1);
    assert.equal(await selected.getAttribute('data-step-tab'), String(step));
    assert.equal(await selected.getAttribute('tabindex'), '0');
    assert.equal(await frame.getByRole('tabpanel').count(), 1);
    const panel = frame.locator(`#${await selected.getAttribute('aria-controls')}`);
    assert.equal(await panel.isVisible(), true);
    assert.equal(await panel.getAttribute('aria-labelledby'), await selected.getAttribute('id'));
  };
  const checkTabs = async frame => {
    // The landing/replay view must show the same generated image as step 1.
    // Previously only step 1 was updated, so first-time visitors saw old SVG art.
    const intro = frame.locator('.intro-panel');
    assert.equal(await intro.isVisible(), true);
    const source = await intro.locator('.target-layout image').getAttribute('href');
    assert.match(source, /^data:image\/webp;base64,/);
    assert.equal(await frame.locator('.stage-1 .target-layout image').getAttribute('href'), source);
    const track = (await frame.locator('.lesson-title').innerText()).startsWith('Ref2V') ? 'ref2v-' : '';
    const asset = await fs.readFile(`assets/images/${track}define-targets-layout.webp`);
    assert.deepEqual(Buffer.from(source.split(',')[1], 'base64'), asset);
    assert.equal(await frame.getByRole('tab').count(), 6);
    for (const step of [6, 2, 4, 1]) {
      await frame.locator(`[data-step-tab="${step}"]`).click();
      await assertStage(frame, step);
    }
    await frame.locator('[data-motion-action="play"]').click();
    await frame.locator('[data-step-tab="3"]').click();
    assert.equal(await frame.locator('[data-motion-root]').evaluate(el => el.classList.contains('is-playing')), false);
    await page.waitForTimeout(1350);
    await assertStage(frame, 3);
    const keySteps = [['ArrowRight', 4], ['End', 6], ['ArrowRight', 1], ['ArrowLeft', 6], ['Home', 1]];
    for (const [key, expected] of keySteps) {
      await frame.getByRole('tab', {selected: true}).press(key);
      await assertStage(frame, expected);
      assert.equal(await frame.getByRole('tab', {selected: true}).evaluate(el => el === document.activeElement), true);
    }
    await frame.getByRole('tab', {selected: true}).press('Tab');
    assert.equal(await frame.getByRole('tabpanel').evaluate(el => el === document.activeElement), true);
    await frame.locator('[data-motion-action="next"]').click();
    await assertStage(frame, 2);
    await frame.locator('[data-motion-action="prev"]').click();
    await assertStage(frame, 1);
    await frame.locator('[data-motion-action="prev"]').click();
    assert.equal(await frame.getByRole('tab', {selected: true}).count(), 0);
    assert.equal(await frame.locator('.intro-panel').isVisible(), true);
    assert.equal(await intro.locator('.target-layout image').getAttribute('href'), source);
  };
  await checkTabs(demo);
  const heights = [];
  for (let step = 1; step <= 6; step++) {
    await demo.locator('[data-motion-action="next"]').click();
    assert.equal(await root.getAttribute('data-step-current'), String(step));
    assert.equal(await demo.locator('.stage-pane:visible').count(), 1);
    assert.equal(await demo.locator(`.stage-${step}`).isVisible(), true);
    await assertStage(demo, step);
    const content = await demo.locator(`.stage-${step} .explanation`).innerText();
    assert.match(content, /Purpose/i); assert.match(content, /Input/); assert.match(content, /Output/);
    await demo.locator(`.stage-${step} .example-data summary`).click();
    assert.equal(await demo.locator(`.stage-${step} pre`).isVisible(), true);
    JSON.parse(await demo.locator(`.stage-${step} pre`).innerText());
    await demo.locator(`.stage-${step} .example-data summary`).click();
    heights.push(await root.evaluate(el => el.getBoundingClientRect().height));
  }
  assert.equal(await demo.locator('[data-motion-action="next"]').isDisabled(), true);
  assert.match(await demo.locator('.stage-6 .score-hero').innerText(), /87\.15/);
  await demo.locator('[data-motion-action="prev"]').click();
  assert.equal(await root.getAttribute('data-step-current'), '5');
  await demo.locator('[data-motion-action="prev"]').press('ArrowLeft');
  assert.equal(await root.getAttribute('data-step-current'), '4');
  assert.match(await demo.locator('.stage-4 .selected-evidence').innerText(), /JU1CE/);
  await demo.locator('.stage-4 .why-detail summary').click();
  assert.match(await demo.locator('.stage-4 .why-detail').innerText(), /wrong|belongs|carrier/i);
  await demo.locator('.stage-4 .why-detail summary').click();
  report.push('All six stages, JSON payloads, candidate explanations, final scores, previous/next and keyboard controls.');

  await demo.locator('[data-motion-action="play"]').click();
  await page.locator('[data-track="ref2v"]').click();
  assert.equal(await root.evaluate(el => el.classList.contains('is-playing')), false);
  const ref = page.frameLocator('#walkthrough-ref2v iframe');
  const refRoot = ref.locator('[data-motion-root]');
  await refRoot.waitFor();
  await checkTabs(ref);
  for (let i = 0; i < 3; i++) await ref.locator('[data-motion-action="next"]').click();
  await ref.locator('.stage-3 .example-data summary').click();
  assert.deepEqual(JSON.parse(await ref.locator('.stage-3 pre').innerText()), {matched_ref_ids: ['R01', 'R02']});
  await ref.locator('[data-motion-action="next"]').click();
  await ref.locator('.stage-4 .example-data summary').click();
  const response = JSON.parse(await ref.locator('.stage-4 pre').innerText());
  assert.equal(response.vlm_response.matches[0].slot_id, 'T0001');
  assert.deepEqual(response.vlm_response.matches[0].selected_ids, ['P001', 'P002']);
  await page.locator('[data-track="t2v"]').click();
  assert.equal(await root.getAttribute('data-step-current'), '4');
  await page.locator('[data-track="ref2v"]').click();
  assert.equal(await refRoot.getAttribute('data-step-current'), '4');
  await ref.locator('[data-motion-action="next"]').click();
  await ref.locator('[data-motion-action="next"]').click();
  assert.match(await ref.locator('.stage-6 .score-hero').innerText(), /82\.73/);
  report.push('Independent track state; hidden playback pauses; Ref2V uses reference IDs and slot-based matching.');
  report.push('Both tracks support direct stage tabs, selected ARIA state, keyboard focus/wraparound, playback pause on selection and synchronized previous/next.');
  report.push('Both landing views and return-to-start states display the generated RGB asset used by Define targets.');

  await ref.locator('[data-motion-action="replay"]').click();
  assert.equal(await ref.locator('.intro-panel .target-layout image').isVisible(), true);
  await page.waitForTimeout(1350);
  await ref.locator('[data-motion-action="pause"]').click();
  const paused = await refRoot.getAttribute('data-step-current');
  await page.waitForTimeout(1350);
  assert.equal(await refRoot.getAttribute('data-step-current'), paused);
  await ref.locator('[data-motion-action="play"]').click();
  await ref.locator('[data-motion-root][data-frame="end"]:not(.is-playing)').waitFor({timeout: 10000});
  assert.equal(await refRoot.getAttribute('data-step-current'), '6');
  await page.waitForTimeout(1400);
  assert.equal(await refRoot.getAttribute('data-step-current'), '6');
  report.push('Replay, pause, resume and deterministic completion without looping.');

  for (const track of ['t2v', 'ref2v']) {
    await page.locator(`[data-track="${track}"]`).click();
    const frame = page.frameLocator(`#walkthrough-${track} iframe`);
    await frame.locator('[data-step-tab="5"]').click();
    const sequence = frame.locator('[data-frame-sequence]');
    const assertObservation = async index => {
      assert.equal(await sequence.getAttribute('data-frame-current'), String(index));
      assert.equal(await sequence.locator('.sampled-frame:visible').count(), 1);
      assert.equal(await sequence.locator(`[data-sequence-frame="${index}"]`).isVisible(), true);
      assert.equal(await sequence.locator('[data-frame-select][aria-pressed="true"]').count(), 2);
      assert.equal(await sequence.locator('[data-frame-cell].is-frame-current').count(), 3);
      assert.equal(await sequence.locator(`[data-frame-cell="${index}"].is-frame-current`).count(), 3);
      assert.equal(await sequence.locator(`[data-sequence-frame="${index}"] img`).evaluate(img => img.complete && img.naturalWidth > 0), true);
      await assertStage(frame, 5);
    };
    await assertObservation(0);
    const sources = await sequence.locator('.sampled-frame img').evaluateAll(imgs => imgs.map(img => img.src));
    assert.equal(new Set(sources).size, 4, 'Each timestamp needs a distinct rendered image');
    await sequence.locator('.frame-times [data-frame-select="2"]').click();
    await assertObservation(2);
    assert.match(await sequence.locator('tbody [data-frame-cell="2"]').first().innerText(), /Inactive/);
    await sequence.locator('thead [data-frame-select="3"]').click();
    await assertObservation(3);
    assert.match(await sequence.locator('tbody [data-frame-cell="3"]').last().innerText(), /Missing/);
    await sequence.locator('thead [data-frame-select="3"]').press('ArrowRight');
    await assertObservation(0);
    assert.equal(await sequence.locator('thead [data-frame-select="0"]').evaluate(el => el === document.activeElement), true);
    await sequence.locator('[data-frame-play]').click();
    await frame.locator('[data-frame-current="1"]').waitFor();
    await sequence.locator('[data-frame-play]').click();
    const pausedFrame = await sequence.getAttribute('data-frame-current');
    await page.waitForTimeout(1200);
    assert.equal(await sequence.getAttribute('data-frame-current'), pausedFrame);
    await sequence.locator('[data-frame-play]').click();
    await frame.locator('[data-frame-current="3"]:not(.frames-playing)').waitFor();
    await assertObservation(3);
    // Leaving the stage or track cancels the sequence clock.
    await sequence.locator('[data-frame-play]').click();
    await frame.locator('[data-step-tab="4"]').click();
    await page.waitForTimeout(1200);
    assert.equal(await sequence.getAttribute('data-frame-current'), '0');
    assert.equal(await sequence.locator('[data-frame-play]').getAttribute('aria-pressed'), 'false');
    await frame.locator('[data-step-tab="5"]').click();
    await sequence.locator('[data-frame-play]').click();
    await page.locator(`[data-track="${track === 't2v' ? 'ref2v' : 't2v'}"]`).click();
    await page.waitForTimeout(1200);
    assert.equal(await sequence.getAttribute('data-frame-current'), '0');
    assert.equal(await sequence.locator('[data-frame-play]').getAttribute('aria-pressed'), 'false');
  }
  report.push('Both four-frame sequences load distinct RGB frames, synchronize time buttons/table columns, support keyboard selection and finite playback, and pause when leaving the stage or track.');

  const zoom = page.locator('[data-enlarge]').first();
  await zoom.click();
  assert.equal(await page.locator('.image-dialog').isVisible(), true);
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('.image-dialog').isVisible(), false);
  assert.equal(await zoom.evaluate(el => el === document.activeElement), true);
  await page.locator('[data-copy-citation]').click();
  assert.match(await page.evaluate(() => navigator.clipboard.readText()), /@misc\{zhang2026textvbenchevaluatingtextrendering/);
  report.push('Figure dialog, Escape, focus return and clipboard copying.');

  for (const width of [320, 390, 768, 1440]) {
    await page.setViewportSize({width, height: 900});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `Page overflow at ${width}px`);
    for (const track of ['t2v', 'ref2v']) {
      await page.locator(`[data-track="${track}"]`).click();
      const frame = page.frameLocator(`#walkthrough-${track} iframe`);
      for (const step of [1, 2, 3, 4, 5, 6]) {
        await frame.locator(`[data-step-tab="${step}"]`).click();
        await assertStage(frame, step);
        assert.equal(await frame.locator('html').evaluate(el => el.scrollWidth > innerWidth), false, `${track} step ${step} overflow at ${width}px`);
      }
    }
  }
  report.push('Direct tabs work on both tracks without document overflow at 320, 390, 768 or 1440 px.');

  const standalone = await context.newPage();
  await standalone.goto(new URL('assets/diagrams/evaluation-t2v.html?motion=static', base).href);
  assert.equal(await standalone.locator('.stage-pane:visible').count(), 6);
  assert.equal(await standalone.locator('[data-motion-controls]').isVisible(), false);
  assert.equal(await standalone.getByRole('tab').count(), 0);
  assert.equal(await standalone.locator('[data-step-tab]:disabled').count(), 6);
  assert.equal(await standalone.locator('.sampled-frame:visible').count(), 4);
  assert.equal(await standalone.locator('[data-frame-play]').isVisible(), false);
  await standalone.screenshot({path: '.preview/static-a.png', fullPage: true});
  await standalone.screenshot({path: '.preview/static-b.png', fullPage: true});
  assert.deepEqual(await fs.readFile('.preview/static-a.png'), await fs.readFile('.preview/static-b.png'));
  await standalone.goto(new URL('assets/diagrams/evaluation-t2v.html?motion=step&step=4', base).href);
  assert.equal(await standalone.locator('.stage-pane:visible').count(), 1);
  assert.equal(await standalone.locator('.stage-4').isVisible(), true);
  await standalone.emulateMedia({media: 'print'});
  assert.equal(await standalone.locator('.stage-pane:visible').count(), 6);
  assert.equal(await standalone.locator('.sampled-frame:visible').count(), 4);
  report.push('Complete static/print views, stable pixel-identical static captures, and exact-step views.');

  const reduced = await browser.newContext({reducedMotion: 'reduce'});
  const reducedPage = await reduced.newPage();
  await reducedPage.goto(new URL('assets/diagrams/evaluation-ref2v.html', base).href);
  assert.equal(await reducedPage.locator('.stage-pane:visible').count(), 6);
  assert.equal(await reducedPage.locator('[data-motion-controls]').isVisible(), false);
  assert.equal(await reducedPage.locator('[data-motion-root]').getAttribute('data-motion-state'), 'reduced');
  assert.equal(await reducedPage.getByRole('tab').count(), 0);
  assert.equal(await reducedPage.locator('.sampled-frame:visible').count(), 4);
  assert.equal(await reducedPage.locator('[data-frame-play]').isVisible(), false);
  await reducedPage.emulateMedia({reducedMotion: 'no-preference'});
  await reducedPage.locator('[data-step-tab="4"]').click();
  await assertStage(reducedPage, 4);
  await reducedPage.emulateMedia({reducedMotion: 'reduce'});
  assert.equal(await reducedPage.locator('.stage-pane:visible').count(), 6);
  await reduced.close();
  const noJS = await browser.newContext({javaScriptEnabled: false});
  const noJSPage = await noJS.newPage();
  await noJSPage.goto(base);
  assert.equal(await noJSPage.locator('.results-table tbody tr').count(), 12);
  assert.equal(await noJSPage.locator('.sample-card').count(), 4);
  await noJSPage.goto(new URL('assets/diagrams/evaluation-t2v.html', base).href);
  assert.equal(await noJSPage.locator('.stage-pane:visible').count(), 6);
  assert.equal(await noJSPage.locator('[data-motion-controls]').isVisible(), false);
  assert.equal(await noJSPage.locator('.sampled-frame:visible').count(), 4);
  await noJS.close();
  report.push('No-JavaScript and reduced-motion fallbacks preserve the complete teaching content.');

  // Mimic a GitHub Pages project path without changing or copying the site.
  const rootDir = path.resolve('.');
  const mime = {'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.webp':'image/webp','.jpg':'image/jpeg','.png':'image/png','.svg':'image/svg+xml'};
  const server = http.createServer(async (req, res) => {
    try {
      const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
      if (!pathname.startsWith('/paper-site/')) {res.writeHead(404).end();return;}
      const local = path.resolve(rootDir, pathname.slice('/paper-site/'.length) || 'index.html');
      if (!local.startsWith(rootDir + path.sep)) {res.writeHead(403).end();return;}
      const file = await fs.readFile(local);
      res.writeHead(200, {'Content-Type': mime[path.extname(local)] || 'application/octet-stream'}).end(file);
    } catch {res.writeHead(404).end();}
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const nested = await context.newPage();
    const nestedFailures = [];
    nested.on('response', r => {if (r.status() >= 400) nestedFailures.push(r.url());});
    const nestedBase = `http://127.0.0.1:${server.address().port}/paper-site/`;
    await nested.goto(nestedBase, {waitUntil: 'networkidle'});
    await nested.locator('#evaluation').scrollIntoViewIfNeeded();
    await nested.frameLocator('#walkthrough-t2v iframe').locator('[data-motion-action="next"]').click();
    await nested.locator('[data-track="ref2v"]').click();
    await nested.frameLocator('#walkthrough-ref2v iframe').locator('[data-motion-action="next"]').click();
    await nested.locator('#results').scrollIntoViewIfNeeded();
    assert.deepEqual(nestedFailures, []);
    await nested.close();
  } finally {await new Promise(resolve => server.close(resolve));}
  report.push('Simulated /paper-site/ GitHub Pages prefix: both tracks and assets load successfully.');
  assert.deepEqual(errors, []); assert.deepEqual(failed, []);
  assert.equal(requests.some(u => /\.(mp4|webm)(\?|$)/.test(u)), false);
  assert.equal(requests.some(u => !u.startsWith(base)), false);
  report.push('Official title and local promotional video are present, with a poster and native controls.');
  report.push('No page errors, HTTP failures, external runtime requests or automatic video downloads.');
  await context.close();
  await fs.writeFile('.preview/browser-report.json', JSON.stringify({passed: report, stageHeights: heights}, null, 2) + '\n');
  return report;
};
