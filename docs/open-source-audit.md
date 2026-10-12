# Open-source publication review

Reviewed on 2026-10-12 for `zhang-zrq/textvbench-page`.
This is the static project-page repository, separate from the TextVBench
evaluator and complete dataset. The directory had no Git history before this
review; publication starts with a new, reviewed `main` branch.

## Checks and results

- Gitleaks **8.30.1**, using its default rules and fully redacted output,
  found no secrets in the staged release snapshot. The official Windows
  archive was verified against its published SHA-256 checksum before use.
- `scripts/audit_publication.py` checked the Git index for credential files,
  private keys, known token formats, literal credentials, credentials in URLs,
  absolute user paths, private-network URLs, and files larger than 50 MiB.
  No findings remained. Only the reviewed website files are included.
- Runtime scripts do not call credential-bearing APIs. Resource links and
  author information are public project metadata configured in `data/site.json`.
  The local preview binds to loopback; its port is configurable. Illustrative
  scenes, sample IDs, and analytical fixtures intentionally contain fixed data.
- Local previews, screenshots, caches, dependencies, environment files,
  credential stores, keys, editor settings, and intermediate PNG frames are
  excluded by `.gitignore`. Original illustrative PNG sources in `figures/`
  are intentionally retained. No source archive, private manuscript, model
  weights, raw experiments, or unrelated workspace files are included.
- All 20 published raster images were checked: no EXIF/GPS tags were present.
  Remaining image metadata consists of rendering/color-profile information.
  The MP4 metadata contains an FFmpeg encoder identifier, with no local path
  or account metadata found. The video is about 37.6 MiB, below the repository's
  50 MiB review threshold.
- The two dataset reference images were visually inspected. One depicts
  branded packaging; the other is an illustrative floor plan. They remain
  separately identified as third-party dataset inputs.
- Build and content/score validation passed. Repeated builds produced identical
  bytes, with explicit UTF-8 and LF output across platforms.
- The existing Playwright suite passed with Microsoft Edge: both walkthroughs,
  keyboard/ARIA controls, frame playback, video, image enlargement, clipboard,
  static/print, reduced-motion/no-JavaScript behavior, four viewport widths,
  and a simulated GitHub Pages project path. It reported no page errors,
  HTTP failures, external runtime requests, or automatic video downloads.

## Changes made before publication

- Added the MIT code license and clarified separate rights for paper content,
  data records, reference imagery, video, and generated illustrations.
  Preserved the supplied motion-controller attribution and MIT notice.
- Replaced maintainer-specific source-directory assumptions with explicit
  importer parameters and logical provenance paths. Removed internal image
  generation request IDs while retaining prompts, model information and hashes.
- Updated the optional importer to retain existing independent manifest records
  such as the promotional video, emit WebP reference images consistently, and
  write portable forward-slash paths. Its CLI help was checked; a complete
  re-import was not run because the original paper sources and PyMuPDF are not
  present in this checkout.
- Added explicit UTF-8 text I/O and LF generation. This also makes walkthrough
  cache-version hashes reproducible between Windows and Linux.
- Added a focused Git-index publication check, a pinned Gitleaks pre-commit
  hook, and a read-only GitHub Actions workflow for audit, build, validation,
  and generated-file consistency. Pre-commit requires local installation;
  GitHub Actions runs automatically on pushes and pull requests.
- Configured the initial commit to use the GitHub noreply email address.
  GitHub authentication is supplied by the existing local credential helper;
  no access token is placed in repository files or remote URLs.

## Review boundaries

Secret scanners and metadata inspection cannot prove the absence of all
sensitive content, including text rendered inside every frame of the video.
The existing promotional video was retained byte-for-byte and was not manually
reviewed frame by frame. Public author names and affiliation were retained as
intended publication information.

Provenance does not establish a blanket redistribution or reuse license for
third-party imagery, trademarks, paper material, or media. The MIT code license
does not grant those rights. The motion-controller's upstream MIT attribution
is retained from the supplied notice; the original skill snapshot is not
available here to independently verify additional upstream copyright notices.
See `THIRD_PARTY_NOTICES.md` and `asset-sources.md` before reusing content.

GitHub Pages hosting is a separate setting and is not enabled by this repository
push. The canonical site URL and evaluator Code/Dataset links remain unset
until their corresponding resources are ready.

## Repeat before a later publication

```bash
git add .
python3 scripts/audit_publication.py
python3 scripts/build.py
python3 tests/validate.py
git diff --exit-code
gitleaks git --redact --no-banner .
```

When reviewing an uncommitted release, export the Git index to an isolated
directory with `git checkout-index --all --prefix=/absolute/release-snapshot/`
and run `gitleaks dir /absolute/release-snapshot --redact --no-banner`.
History scanning covers committed content; index and snapshot scanning cover
the intended next release. Audit reports and local publication helpers stay
in the ignored `.preview/` directory.
