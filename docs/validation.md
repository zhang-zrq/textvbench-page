# Local validation

Validated on 2026-10-09. Static site served at `http://127.0.0.1:8080/` with
`scripts/serve.py`, which supports HTTP byte-range responses for local video
seeking. GitHub Pages provides the equivalent static-file serving behavior.
Browser: Chromium 156 through Playwright. Checks use desktop and mobile
viewport sizes; they are not physical-device Safari/Firefox tests.

## Passed

- All six stages for the T2V walkthrough, stage-specific purpose/input/output,
  expandable valid JSON, previous/next controls and keyboard navigation.
- Independent T2V / Ref2V state. Switching tracks pauses hidden playback.
- Initial landing views for both tracks load the same generated WebP as step 1.
  Asset bytes are checked against the served WebP; return-to-start and replay
  also show the generated image. Intro and step-1 SVG IDs are unique.
- Direct navigation through six stage tabs in both tracks, synchronized selected
  states and playback controls, keyboard focus and wraparound, and automatic
  pause when selecting a stage during playback.
- Reference routing uses `matched_ref_ids`; Ref2V candidate selection uses
  `slot_id`. Both demonstrations retain the erroneous `JU1CE` observation.
- Play, pause, resume, replay and a stable final state without repeated loops.
- Both four-frame RGB sequences support time selection, table-column highlights,
  keyboard selection, pause/resume and finite playback. Playback pauses when
  switching stages or tracks. All four frames remain available in static,
  print, reduced-motion and no-JavaScript views.
- Eight distinct 768 × 512 RGB frames visually illustrate camera/object motion,
  JU1CE errors, inactive first carriers, and missing text on active second
  carriers. Scene lettering is generated in the raster images. Prompts,
  source sheets, the Ref2V first-frame replacement and crop hashes are saved.
- Correct illustrative aggregate scores: T2V **87.151051625239** and Ref2V
  **82.730046460024**, verified against independent rational-number fixtures.
  Inactive observations are excluded; active missing matches contribute zero.
- All 12 paper result rows and 4 released input examples are present. Input
  fields and original asset source hashes were verified against the workspace.
- Figure enlargement, Escape dismissal, focus return and BibTeX clipboard copy.
- No page or walkthrough document overflow at 320, 390, 768 and 1440 px.
- T2V Define targets uses a validated 1536 × 1024 RGB WebP compressed from
  the gpt-image-2 source with target lettering generated directly in the image. The sign
  and poster text were visually checked; desktop/mobile captures verify display
  without overlaid lettering. The illustration is explicitly labeled.
- Ref2V Define targets uses a second validated 1536 × 1024 RGB WebP compressed
  from the gpt-image-2 source. The R01 carton and R02 can have directly generated ORANGE JUICE and ZERO
  SUGAR lettering. Spelling, left/right reference association and display were
  visually checked in desktop/mobile captures taken through the main site.
- Complete static and print walkthrough views; two static screenshots were
  pixel-identical. Deterministic `?motion=step&step=4` is supported.
- Reduced-motion and no-JavaScript views retain the full teaching content.
- A temporary server mounted the site under `/paper-site/` to exercise the
  GitHub Pages project-prefix case. Both walkthroughs and assets loaded.
- No JavaScript errors, HTTP resource failures, external runtime requests or
  video downloads during the browser run.
- The official paper title is rendered in the document title, Open Graph title,
  hero heading, and generated BibTeX template.
- The bundled promotional MP4 is served from a relative project path. Chromium
  loaded its metadata (1920 × 1080, 317.589 s), played it, and sought both to
  2 s and near the end successfully. The poster is a local WebP extracted at
  2 s; initial page loads keep `preload="none"` and do not request the MP4.
- Raster illustration payloads were converted to quality-88 WebP while keeping
  their displayed dimensions. The image directory fell from about 16 MiB to
  2.3 MiB, and the generated walkthrough HTML fell from about 23 MiB to 1.6 MiB.
- The diagram-design skill's `self_check.py` reports only its strict canonical
  controller mismatch for each diagram. The local controller deliberately
  extends that template to support the requested direct stage tabs; SVG,
  asset and structural checks report no other issues. The browser suite checks
  the customized controller, including its static and reduced-motion fallbacks.

## Artifacts

The local `.preview/` directory (ignored by Git) contains desktop/mobile
screenshots, matching-step screenshots, static comparison captures and
`browser-report.json`. The served assets total approximately 40.3 MiB including the unchanged MP4, with
lazy loading for figures and walkthrough frames.

## Pending content

Authors, affiliations, the arXiv Paper URL, and the formal citation are filled.
Code, Dataset, and the canonical site URL remain unfilled. The project-page
source repository is `https://github.com/zhang-zrq/textvbench-page`; it is
separate from the evaluator code resource. GitHub Pages hosting is not enabled
by the repository push. See `open-source-audit.md` for the publication review.
