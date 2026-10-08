# SHIJI V2 implementation report

## P0 — baseline
Clean main at `488d39e`, created `feat/shiji-v2-motion-ui`. Kit extracted without replacing existing source. Python: **197 passed** (28.499s); Node: **32 groups passed**; native core + desktop ZIP interop: **passed**. All tests use temporary stores. QA service uses independent temporary `shiji-v2-qa-*` data and OS-selected port; no production library or credentials modified. The incidental early Mac window selection is disclosed under P3.

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
Mac uses dark system appearance and neutral native glass with lime foreground and an availability fallback. The initial tinted implementation was corrected during P5. iPhone adds native brand geometry and editorial typography, semantic dark/light palettes, explicit dark/light/system and Studio/Calm settings, native iOS 18 zoom navigation with iOS 17/reduced-motion fallback. System Form, QuickLook, App Group and sync data semantics remain intact. Accessibility text sizes omit the decorative Hero.
Validation: native core checks passed including presentation derivation and unchanged raw schema. macOS build **passed**; iOS Debug simulator build **passed**, bundle/App Group/opaque accent checks **passed**. Installed on pre-existing agent-owned `Shiji iPhone QA` simulator (five QA records), actual dark gallery screenshot `evidence/p3-iphone-dark.png`. No real phone used.
Native inspection limitation: the first Mac UI binding selected an existing same-bundle window displaying port 8782; inspection was stopped without resource/pairing actions. A separate `local.silver.shiji.v2.qa` bundle with temporary-data LSEnvironment was created; native pipe then closed before validating its contents. Do not use that first window as QA evidence. Light/Dynamic Type and dedicated Mac screenshots remain in the final acceptance queue.

## P4 — real Quick Capture
Files: desktop `quick_capture.py`, Store mixin and `/api/resources/:id/enrich` routing, `static/quick-capture.js`, real app entry hooks/modal, motion success flight; backend/UI tests. iOS existing editor gains a minimal URL mode and offline fallback titles, durable-save confirmation banner; Swift tests cover offline persistence.
Desktop POST `/api/resources` completes before confirmation or metadata request. Metadata enrich is a separate bounded (four requests) operation using existing public-fetch validation, outside the global lock; ID/URL/updatedAt and attachment baseline checked atomically before guarded title/description updates. Any intervening edit skips enrichment. No favicon, remote thumbnail, cover download, Chrome capture or preview-worker activation is added. Duplicate 409 retains input; full editor, code/prompt and file entries remain reachable.
Validation: **202 Python tests passed**, **35 Node groups passed**, Swift core + desktop ZIP interop **passed**, updated iOS Debug **build passed**. Actual browser saved a new URL (count 6→7), then attempted the same URL: visible duplicate error and retained URL, no second record or success. Screenshots `evidence/p4-capture-success.png`, `p4-capture-duplicate.png`. Separate enrich request returned 200 after persistence. Failure/concurrent manual title/notes/tags/license/cover tests preserve the saved resource. iPhone remains offline-first; public-web enrichment is desktop-only.

## P5 — local regression, actual UI evidence and motion completion

Files: `desktop-app/desktop/App.swift`, `static/app.js`, `static/index.html`, `static/resource-bits.js`, `static/shiji-v2-motion.js`, `static/shiji-v2.css`, `static/quick-capture.js`, `tests/test_shiji_motion.js`, new `test_motion_studio_effects.js` and `test_quick_capture_recovery.js`; `mobile-app/App/ShijiApp.swift`; both `DESIGN.md` and `.impeccable/design.json`; `SURFACE_BRIEF.md`, `VALIDATION.md`, this report and evidence.

The user supplied `shiji_v2_motion_studio.html` again and requested its full animation language. Its SHA-256 matches the committed reference: `15de2911546549f71132f9fb7d50702e189221ff9b1eb8d6742cbaebfc8fde2b`. This follow-up extends the P2/P3 implementation, retaining the approved composition and all real business handlers.

| Approved effect | Production implementation |
| --- | --- |
| Brand curtain, rotating brand, blurred headline, replay/skip | Nonblocking, inert/aria-hidden 1370ms Web curtain; 800ms brand and 840ms delayed headline. SwiftUI curtain and replay/skip, one-shot task and background cancellation. |
| Continuous geometry, floating bookmark, morphing cutout, tracer, sparkle, ticker | Lifecycle-paused WAAPI loops; cached-rect/coalesced pointer parallax and spotlight. Native geometry Timeline capped at 30 updates/s and paused for Calm, background and offscreen. |
| Category stamp, particle ring, pill settling, count entry | 910ms bounded Web stamp, six particles and ring; category settle/count CSS. Native category stamp/burst and spring list transitions. |
| Card entry, FLIP rearrangement and exit | Existing Bits is the only owner: 850ms blur/depth entrance, 680ms FLIP and up to nine inert 500ms exiting preview proxies. Native keyed LazyVStack entry/exit. |
| Hover tilt, sheen, spotlight and control feedback | Existing image-only Bits tilt; preview sheen/spotlight and navigation/favorite/button feedback. Touch keeps native interactions rather than synthetic mouse tracking. |
| Search, modal and staggered text | The real search keeps its query and Escape focus restoration. Existing dialogs receive 400ms entry plus bounded stagger, and details receive text stagger. Native system search/Form stay native. |
| Continuous detail expansion | One 710ms Web visual proxy, with real detail panel immediately operable. Native iOS 18 zoom; iOS 17/Calm/reduced-motion navigation fallback. |
| Capture flight, save burst, favorite burst | Real durable save precedes the 900ms flight and 15-particle ring; favorite burst only follows successful API edit. Native URL-save flight/burst and successful favorite feedback. Failed writes do not claim success. |
| Studio / Calm / OS reduced motion | Effective mode cancels decoration, proxies, particles and loops. Main-frame loopback-only WebKit preference bridge also disables Mac dock spring. iPhone native preference and system setting gate native effects. |

Demo-specific animated illustrations remain reference media; real resource covers, snippets and local attachments are preserved instead of being replaced by the Demo's invented cover content. UI particle shapes use CSS/SVG geometry. There is no new animation runtime dependency or parallel FLIP/tilt system.

P5 also fixes readable dark error messages and detail icons, narrow Hero overflow, native capture contrast, and a 15-second Quick Capture recovery deadline. Unconfirmed requests are tracked by normalized URL (bounded to 16), retries reconcile against the real resource list, and late results preserve a newer draft. A→B→A timeout retry is covered; merely switching URLs cannot permit a duplicate write.

Final screenshot inspection also corrected an inherited list-thumbnail margin that covered title beginnings. The list now has a measured 14px separation, a refreshed actual screenshot, and repeated passing Node/macOS checks. The motion review preceded this layout-only fix.

Actual UI checks used isolated services and the agent-owned iPhone simulator. Desktop capture increased the real QA record count from 7 to 8 before flight; Calm left zero decorative overlays; the browser error console was empty. Narrow Web client/scroll width was 382/382. Native geometry, category switching and OS reduced motion were checked in the running app. An 18-second recording contains actual native brand replay/category interaction; it does not claim to demonstrate every save or recovery path.

Regression/build outcomes and the viewport/evidence matrix are in [VALIDATION.md](VALIDATION.md). All available local automated checks passed. Independent review status is recorded there at its actual scope, with the remaining platform and acceptance limits. This is not a claim that all devices, old OS versions or the existing Share Extension have passed acceptance.

## Remaining acceptance limits

- Existing iPhone Share Extension blank-page behavior remains unresolved; this work does not claim to fix sharing end to end.
- Mac inactive-window glass, physical iPhones, other iPhone classes and older OS fallback branches have not been inspected in those runtime environments.
- No measured 60fps/frame-time, battery or memory benchmark is claimed. The 1000-resource case demonstrates bounded rendered cards and batching, not a complete performance certification.
- Delayed-save/recovery and rapid cancellation are automated with real controllers in JSDOM; actual delayed-network UI recovery has not been recorded. The final native QA app was switched to Calm and its dock expanded successfully (`motion-native-mac-calm.png`); bridge propagation is controller-tested, but absence of spring motion was not instrumented.
- Browser extension and sync regressions are automated, including real ephemeral HTTPS/pinning tests; no production credential or live cross-device pairing was used.


## Rollback
All changes remain local on `feat/shiji-v2-motion-ui`; no remote push or merge was performed. Stage commits: P1 `83623ca`, P2 `2451274`, P3 `1b9db9f`, P4 `9f61271`; the final motion/acceptance commit follows these. To undo on a clean checkout, revert the final commit first, then the stage commits in reverse order (`9f61271`, `1b9db9f`, `2451274`, `83623ca`). Review each revert before continuing; do not reset uncommitted user work.

Database schema 3 and ZIP manifest 2 remain unchanged, so no data migration or rollback is required. Keep production library and pairing credentials outside QA builds. Build artifacts are local and ignored by Git; rebuild the chosen revision when switching branches.
