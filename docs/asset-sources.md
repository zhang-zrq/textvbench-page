# Content provenance

The website uses a local paper snapshot dated 2026-10-08. `asset-sources.json`
records logical source paths, source SHA-256 hashes, destination paths, and
transformations. Raster site images use quality-88 WebP copies where noted;
the original source hashes remain recorded separately. No API configurations,
debug bundles, or experimental videos are included. `paper/`, `dataset/`,
`metrics/`, and `media/` identify source categories rather than a maintainer's
private directory layout. Source documents are not required to build or host
the bundled site. Provenance records do not grant media reuse rights; see
`THIRD_PARTY_NOTICES.md` for the scope of the MIT code license.

- Paper figures are rendered from the current local LaTeX figure PDFs to WebP.
  Their captions retain the distinction between synthetic illustrations and
  empirical results.
- Reference images for samples `0050` and `0150` are quality-88 WebP copies of
  Ref2V dataset inputs. Their original source hashes are retained separately.
  They are inputs, not model-generated outputs.
- The two T2V records preserve both bilingual prompts, target strings,
  carrier definitions, and sample IDs without rewriting.
- Results retain full precision in `data/results.json`. Tables round to three
  decimals, matching the paper. Model rows are sorted by TextVScore separately
  for each track; small Ref2V differences are explicitly contextualized.
- The abstract is copied from the local paper, with LaTeX markup removed and
  the paper-name macro expanded. The official title is **TextVBench: Evaluating
  Text Rendering and Preservation in Video Generation**. The authors,
  affiliation, and arXiv publication metadata are shown on the project page.
- The user-supplied promotional video is copied byte-for-byte from
  the logical source `media/TextVBench_full.mp4` into
  `assets/videos/TextVBench_full.mp4`. The source and bundled copy have matching
  SHA-256 hashes. `assets/images/video-poster.webp` is a compressed WebP frame extracted at
  2 seconds. Both files ship with the site and use relative URLs; playback has
  no dependency on the original workspace or an external video host.

The interactive walkthrough is newly authored SVG/HTML. Its examples are
illustrative, not observations from a model run. Matching payload shapes were
checked against the released evaluator prompts:

- T2V carrier association: `carriers[].carrier_id`, `present`, `candidate_ids`.
- T2V candidate selection: `matches[].i`, `selected_ids`.
- Ref2V routing: `matched_ref_ids`.
- Ref2V candidate selection: `matches[].slot_id`, `selected_ids`.

The simplified lesson data views are not a full public API specification.
Instructional explanations are authored annotations. Real matching responses
select IDs and do not return those explanations or corrected OCR strings.

Frame-level candidates are associated independently. Stable target IDs group
the resulting observations; the diagram does not introduce an OCR tracker.
Scores in the walkthrough are analytically checked by `tests/validate.py`.

The motion controller is credited in `THIRD_PARTY_NOTICES.md`.

T2V's first stage uses `assets/images/define-targets-layout.webp`, a compressed
WebP copy of the generated
1536 × 1024 RGB scene from **paper-figure-gen / gpt-image-2**. The storefront
sign and window poster follow a layout prompt, with FRESH ORANGE JUICE and
OPEN DAILY generated directly in the image as physical lettering. There is
no overlaid target text or bounding box in this first-stage image. The page
identifies it as an AI-generated illustration of intended targets, with target
IDs and carrier descriptions in the cards below. Later stages remain analytical
diagrams of the illustrative observations. `generated-assets.json` records the request,
actual output metadata and image SHA-256 separately from imported paper assets.

Ref2V's first stage uses `assets/images/ref2v-define-targets-layout.webp`, also
a compressed WebP copy of a 1536 × 1024 RGB image from **paper-figure-gen / gpt-image-2**. The diptych
contains two illustrative reference product photographs: R01 on the left is
a carton reading ORANGE JUICE; R02 on the right is a can reading ZERO SUGAR.
The model generated the lettering directly on the packaging. The first stage
adds no visible text or bounding-box overlays; reference and target IDs appear
in the cards underneath. These teaching references are distinct from the
released dataset images in the benchmark examples. Its prompt and output
metadata are recorded alongside the T2V generated image.

Both Follow targets scenes use four RGB frames from gpt-image-2. The served
`assets/images/sequences/*.webp` files are quality-88 WebP copies of the
original RGB frames. The two
1536 × 1024 contact sheets in `figures/` show different camera and object
configurations, cropped into 768 × 512 RGB frames with `scripts/split_sequence.py`.
T2V uses all four quadrants. Ref2V uses a separately generated first frame
because the contact sheet incorrectly spelled the first observation JU1CE;
the replacement correctly reads JUICE and is downsampled without retouching.
The prompt, generation metadata and hashes are in `generated-assets.json`;
per-frame transforms and semantic states are in `data/sequence-assets.json`.

All packaging/sign lettering is generated in the image pixels. The 0.5/1.5 s
first-target error, 1.0 s inactive carrier, 1.5 s missing second target, and
unassigned duplicate phrase on the second carrier were visually checked.
These are illustrative sampled motion scenes, not frames from a measured
video-model run. Minor generative appearance variations are not benchmark
measurements. The existing analytical table and scores remain authoritative.
