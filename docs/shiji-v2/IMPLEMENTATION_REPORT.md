# SHIJI V2 implementation report

## P0 — baseline
Clean main at `488d39e`, created `feat/shiji-v2-motion-ui`. Kit extracted without replacing existing source. Python: **197 passed** (28.499s); Node: **32 groups passed**; native core + desktop ZIP interop: **passed**. All tests use temporary stores. QA service uses independent temporary `shiji-v2-qa-*` data and OS-selected port; no production library or credentials accessed.

## P1 — desktop visual integration
Files: `static/shiji-v2.css`, `static/shiji-v2.js`, `static/index.html`, `static/app.js`, `tests/test_shiji_v2.js`, existing browse-window test loads the new presentation dependency.
Independent final theme layer, approved dark/lime/violet Hero and ticker, contextual Hero visibility, real resource card types, retained business IDs, two-column masonry, compact navigation at 1279px. No demo data imported into business logic. QA fixture contains six explicitly marked test records.
Validation: baseline Python/native unchanged; Node **33 groups passed**. Real browser opened the ephemeral QA service; screenshot `evidence/p1-desktop.png`. Browser reports no document horizontal overflow. macOS was initially locked; in-app browser became available after continuing. Native UI inspection pending.
Limit: motion controls are wired in P2; no P2 behavior is claimed here. Responsive and full feature matrix continues in P5.

## P2 — motion orchestration
Files: `shiji-v2-motion.js`, V2 CSS/HTML, explicit app hooks, Bits/Glass preference coordination, motion controller tests. Brand intro is nonblocking and skippable/replayable, geometry/ticker pause for panels/background/offscreen; pointer parallax measures only on entry. Existing Bits exclusively owns card FLIP and image tilt; Calm cancels Bits/Glass too. Single detail proxy (560ms), eight bounded success particles, root preference is separate from business data. System reduced motion always wins.
Validation: **34 Node groups passed**, including OS preference changes, rapid detail replacement, cleanup, bounded particles, 1000-card two-flush layout and legacy regressions. Actual browser Calm button disables replay, detail opens with resource-first heading, closing restores source focus and leaves **0 proxies**. `evidence/p2-detail.png`. No remote push.

## P3 — native visual integration
Files: Mac `desktop/App.swift`; iOS `App/ShijiApp.swift`, accent assets, `Shared/iOSImage.swift`, derived presentation in `Shared/Library.swift`, corresponding native core assertions.
Mac uses dark system appearance and lime-tinted native glass with availability fallback. iPhone adds native brand geometry and editorial typography, semantic dark/light palettes, explicit dark/light/system and Studio/Calm settings, native iOS 18 zoom navigation with iOS 17/reduced-motion fallback. System Form, QuickLook, App Group and sync data semantics remain intact. Accessibility text sizes omit the decorative Hero.
Validation: native core checks passed including presentation derivation and unchanged raw schema. macOS build **passed**; iOS Debug simulator build **passed**, bundle/App Group/opaque accent checks **passed**. Installed on pre-existing agent-owned `Shiji iPhone QA` simulator (five QA records), actual dark gallery screenshot `evidence/p3-iphone-dark.png`. No real phone used.
Native inspection limitation: the first Mac UI binding selected an existing same-bundle window displaying port 8782; inspection was stopped without resource/pairing actions. A separate `local.silver.shiji.v2.qa` bundle with temporary-data LSEnvironment was created; native pipe then closed before validating its contents. Do not use that first window as QA evidence. Light/Dynamic Type and dedicated Mac screenshots remain in the final acceptance queue.

## P4 — real Quick Capture
Files: desktop `quick_capture.py`, Store mixin and `/api/resources/:id/enrich` routing, `static/quick-capture.js`, real app entry hooks/modal, motion success flight; backend/UI tests. iOS existing editor gains a minimal URL mode and offline fallback titles, durable-save confirmation banner; Swift tests cover offline persistence.
Desktop POST `/api/resources` completes before confirmation or metadata request. Metadata enrich is a separate bounded (four requests) operation using existing public-fetch validation, outside the global lock; ID/URL/updatedAt and attachment baseline checked atomically before guarded title/description updates. Any intervening edit skips enrichment. No favicon, remote thumbnail, cover download, Chrome capture or preview-worker activation is added. Duplicate 409 retains input; full editor, code/prompt and file entries remain reachable.
Validation: **202 Python tests passed**, **35 Node groups passed**, Swift core + desktop ZIP interop **passed**, updated iOS Debug **build passed**. Actual browser saved a new URL (count 6→7), then attempted the same URL: visible duplicate error and retained URL, no second record or success. Screenshots `evidence/p4-capture-success.png`, `p4-capture-duplicate.png`. Separate enrich request returned 200 after persistence. Failure/concurrent manual title/notes/tags/license/cover tests preserve the saved resource. iPhone remains offline-first; public-web enrichment is desktop-only.

## Pending stages
P5 complete regression and visual acceptance.

## Rollback
Local stage commits can be reverted in reverse order. Database schema 3 and ZIP manifest 2 remain unchanged. Do not point a QA build at the production library.
