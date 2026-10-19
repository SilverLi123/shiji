# SHIJI V6.4 — Cover Studio 3.0

Candidate: `feat/shiji-v6.4-cover-studio`; base `31eeea27547ae9c00a1c88212a5bbc2f70ed268f`. Runtime implementation through `7bc01cb`; the post-review web geometry short-circuit is separately covered by regression and measurement. Native UI source remains `748d8af`. No main merge, formal library access or real pairing-credential changes. This is a reviewable feature candidate, not a physical-device release certification.

## Delivered implementation

| Boundary | Actual change | Verification |
|---|---|---|
| Cover value contract | Python/JS/Swift bounded optional coverConfig, null reset, unknown/future retention, readable color | shared vectors, malformed/bounded inputs, restart and actual exchange |
| Art direction | five families ×3 distinct compositions; scored content rules; explicit original V5 | real15-pair Store/page board; exact-host and content regressions |
| Desktop editor | protected draft, static thumbnails, style/layout/seed/palette/color/text/position/density, local/website/upload/poster, Fit/Fill/focus | actual HTTP/UI save, cancel, failed upload, uncertain response, reset, reload, narrow screens |
| Atomic preference save | existing coverId/config transaction, field guards, hash reuse and cleanup | stale/two-writer cases, unrelated source edits, retry, rollback, actual image bytes |
| Gallery integration | existing stable article/cache/window/deck owners, one-resource patch, custom-title highlight protection | actual keyboard/pointer/update/resize/selection/gallery tests; offscreen/remount tests |
| Native adaptation | SwiftUI cover families/editor, pinned opening baseline, asynchronous bounded local image decode, actual persisted-success feedback | iPhone Simulator2-case actual UI run; code subtitles verified with screenshot OCR |
| Compatibility | schema3, ZIPmanifest2, AppGroup JSON and syncprotocol1 unchanged | actual ZIP collision remapping and native↔desktop exchange; HTTPS conflict/TLS regression |

Entry: resource details → **封面设计**. Changes remain a draft until Save; cover text never renames the source. Auto keeps real-image priority. Selecting Poster keeps real attachment bytes; Reset returns to automatic. Original V5 is an editor choice, not an obsolete whole-product V2 switch. The large Hero, Spatial Deck, pure-cover gallery, Motion Studio/Calm and Space3D/Flat remain.

See [ARCHITECTURE.md](ARCHITECTURE.md), [API.md](API.md), [COMPATIBILITY.md](COMPATIBILITY.md), [ART_CATALOG.md](ART_CATALOG.md), [DESIGN_EXTENSION.md](DESIGN_EXTENSION.md) and the original [SPEC.md](SPEC.md).

## Confirmed defects and fixes

1. Save cleared its busy fence before asynchronous gallery presentation completed. A delayed callback could close a subsequently opened draft. A failing event-loop regression now verifies ownership through completion; no second click or global reload workaround.
2. Pending uploads shadowed an explicit Website selection in web/native preview. The draft now follows the saved source policy; cancelled drafts never publish bytes.
3. Native Developer A and original-V5 code covers suppressed explicit subtitles. Actual saved-cover OCR first failed to find the text, then passed for both renderers. Automatic code excerpts can stay suppressed while explicit text remains visible.
4. Actual art inspection caught inherited CSS collapsing the rhythm composition, spatial ink colliding with its subject, and Editorial A/B CJK title/subtitle overlap. Scoped layout/type fixes and shared text regions preserve the V5 art. Actual browser checks all title positions/densities and recaptured mobile/large states.
5. Existing modal entrance opacity exposed underlying details during the mobile editor's opening frames. The single Motion owner keeps this protected workspace opaque while retaining its motion. The actual frame sampler first observed0.4, then minimum1.
6. Failed images incorrectly left “已有真实图片” beside a poster. Current connected-image load/error events now describe loading, real image or poster fallback accurately.
7. First CI exposed an old outbox test assuming Promise.all call order equalled async pairing-hash completion order. A controlled gate reproduced the failure; it now protects the actual sending record. Outbox runtime was not changed.
8. Gallery CI measured a decode anchor while the prior Fit-profile FLIP was moving. A new readiness assertion reproduced this at progress0.346 with a654px transform. It now waits for decoded mounted images and finite outer-card motion over three RAF polls; the original3px anchor assertion remains. No fixed sleep, larger timeout or disabled product motion.

9. The final50K batch measurement exposed repeated cover normalization for unmeasured offscreen rows. A dependency-count regression first observed1000unneeded resolutions. The geometry cache now short-circuits only when there is no measured height/decoded ratio to validate; real-image cache invalidation stays intact. Full artwork and motion are retained. Optimized timings are in PERFORMANCE.md.

The first async polling attempt was itself incorrect for installed Playwright1.64: its Promise was truthy before a false result could request another poll. Inspection of the installed polling implementation led to a synchronous readiness predicate. Failed attempts are not relabeled as passes.

## Actual test results

- Python: **294 portable +2 native tests passed**; baseline was282 portable. Native QR verification initially hit a host Vision missing-ANE-model error on unchanged baseline code. CPU Vision decoding still verifies the actual rendered QR payload and passes; optional ANE execution is not certified.
- Node: **65 groups passed**, including preserved legacy Cover Studio tests and new draft/source/image-status regressions.
- Swift Core, shared cover vectors, actual desktop/native ZIP exchange and disposable HTTPS sync: **passed**.
- macOS ad-hoc build: **passed**. iOS Simulator build and actual UI: **passed**. Two actual UI cases took251.574s with zero failures and a normal runner exit, including source-field preservation, Save/reopen, Cancel, Reset and native code-subtitle OCR.
- Actual desktop browser editor and gallery regression: **passed**; desktop/mobile, real image/failure fallback, remount, keyboard/pointer, sorting/filtering/full selection and reduced-motion paths exercised existing business APIs.
- GitHub Actions **39223634532**, head `7bc01cb`: **all five jobs passed** — Python, Node, browser, native and100-URL abrupt-death recovery. [Verified run](https://github.com/SilverLi123/shiji/actions/runs/39223634532). Earlier failed runs remain part of the investigation, not the final acceptance claim.

The latest local macOS package was rebuilt after the geometry optimization; its bundled gallery module matches the source hash (`evidence/package.json`). The compact results/provenance are in `evidence/ci.json`, `native-ui.json`, `art-manifest.json`, `scale-optimized-summary.json` and the final test report. Raw large logs, videos and xcresult bundles remain outside Git in ignored build/dist paths. `evidence/recordings.json` records local browser video paths and hashes; no clean native MP4 is claimed.

## Visual evidence

- [Original V5 board](evidence/board-before.png) / [15 authored covers](evidence/board-after.png).
- [Desktop editor](evidence/desktop-editor.png), [mobile editor](evidence/mobile-editor.png), [scrolled mobile controls](evidence/mobile-editor-controls.png).
- [Editorial A mobile](evidence/editorial-a-mobile.png), [Editorial B mobile](evidence/editorial-b-mobile.png), corresponding large previews in evidence.
- [Actual image priority](evidence/actual-image-priority.png), [failure editor](evidence/art-editor-desktop.png).
- [Native editor](evidence/native-editor-spatial.png), [saved native detail](evidence/native-saved-detail.png), [Developer code subtitle](evidence/native-code-subtitle.png), [original-V5 code subtitle](evidence/native-v5-code-subtitle.png).

Screenshots are actual temporary Store/AppGroup app states, not a new demo data model. The board assembles actual page captures. The independent visual reviewer scored its three original material fixes resolved; its **ship** verdict is scoped to those fixes, not universal device/performance acceptance. See VISUAL_REVIEW.md and VISUAL_VERDICT.md.

## Performance and remaining acceptance

[PERFORMANCE.md](PERFORMANCE.md) reports1K/5K/20K/50K before/optimized-after samples, three contexts per size/mode, all stages and raw hashes. Large browsing scenes retain bounded mounted cards rather than thousands of permanent DOM covers. At50K/2040-loaded Studio, append-render median changed17→21.2ms (pre-optimization34.8ms); Calm changed16.7→15.2ms. At20K Studio it changed15.5→21.6ms. These remaining regressions are disclosed. Some complex-cover batches cost more than V6.3; no universal speedup or60FPS claim is made. JS heap/rAF observations do not certify native CPU, RSS, GPU ownership or compositor frames.

Unresolved/manual:

- Physical iPhone, Photos/file permissions, real-device sync, VoiceOver, large Dynamic Type and light-appearance acceptance.
- Inherited native first-detail roughly246ms long-frame risk, native sleep/wake, touchpad inertia and quiet native CPU/GPU profiling; Cover Studio does not claim to fix them.
- A clean native MP4 was not obtained. Concurrent simctl capture stalled startup/finalization and produced0bytes, so that attempt was rejected and the extra recorder removed. Successful native PNGs and separate actual browser recording are the evidence; screenshots/compilation are not substituted for native motion certification.
- Existing large-ZIP safety caps remain.50K gallery tests do not certify a50K ZIP restore.

The original whole-branch reviewer stopped at a usage limit; a fresh replacement completed the review. Three important findings were fixed with RED→GREEN tests. No minor findings were raised. Full review/rulings are in CODE_REVIEW.md and RULINGS.md. Native/visual/readiness harness corrections do not authorize a main merge.

## Follow-up

Complete physical-iPhone and native-performance acceptance first. Add future cover mothers only after actual-content design-board review, then extend shared semantic vectors and cross-end image/source tests. Reuse existing Search/Capture engines and sync/backup contracts; do not introduce a second resource or cover authority.
