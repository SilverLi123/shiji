# V5 Spatial Poster — real App integration

The supplied `reference/spatial-poster.html` is the visual authority. Its sidebar, toolbar, large two-line Hero, purple geometric stage, spatial deck, lime ribbon and poster artwork have been ported into the existing desktop workspace. This is an integration with real saved resources, not another standalone Demo.

The latest user correction takes precedence over the Demo: gallery cards show only their covers. The duplicated title, domain, description, tags and footer below each cover are hidden; clicking the accessible cover button opens the existing complete detail drawer. The alternative list view retains information beside the thumbnail. Batch selection remains available on the cover.

## Code and architecture

- `desktop-app/static/index.html`: V5 shell, real navigation/control hooks, Hero, spatial deck, toolbar capture and mobile web navigation.
- `desktop-app/static/shiji-v5.css`: supplied visual world plus responsive and product integration rules. V5 poster sizing overrides legacy fixed heights, including in WKWebView.
- `desktop-app/static/shiji-v5.js`: actual-content poster classification and markup, stable real-resource deck, visual preference controls. Compositions include components, motion, spline, AI, tools, prompt, retro, GitHub, kinetic, atlas, code and articles.
- `desktop-app/static/app.js`: real image precedence and fallback, detail continuity, actual resource navigation/capture hooks. The approved Poly Haven photograph treatment is preserved; explicit user covers take priority.
- `desktop-app/static/resource-bits.js`: sole whole-card tilt/drag and FLIP owner, V5 deterministic masonry spacing and internal poster offsets.
- `desktop-app/static/shiji-v2-motion.js`: existing motion controller owns stage/deck parallax, finite feedback, flat-space, Calm and system reduced motion. Artwork pauses offscreen, in the background and under overlays; queued pointer frames are cancelled on teardown.
- `desktop-app/static/stable-cards.js`: existing keyed renderer accepts the deck selector while retaining the resource-ID mechanism and decoded images.
- Regression tests: `test_v5_spatial.js`, `test_v5_motion.js`, `test_browse_window.js`, `test_detail_hierarchy.js`, `test_liquid_glass.js`.

No additional runtime dependency, parallel animation engine, simulated database or Demo resource seed was introduced. SQLite schema 3 and ZIP manifest 2 remain unchanged. The native macOS container, search, capture dock, file operations and sync entry remain intact. Native iPhone SwiftUI has not been visually ported in this change.

## Safety

Branch `feat/shiji-v5-spatial-ui` began from V3 integration `549457e` in a clean candidate worktree. The primary checkout and user edits were not overwritten. No main merge or remote push was performed.

Runtime and functional checks used independent temporary databases and loopback ports. The preview at port 50461 contains eleven active QA records using real public resource URLs plus explicitly labelled edge-case fixtures. One quick-capture QA record was moved to recoverable trash after verifying persistence. It is not the formal resource library.

The isolated macOS preview uses its own bundle identifier, temporary data directory and port 58546. It does not register the formal App's URL scheme or reuse pairing credentials.

## Tests and observed results

| Check | Result |
| --- | --- |
| Python `python3 -m unittest discover -s tests` | 205 tests passed, 49.024 seconds |
| Node `node desktop-app/tests/run-node.cjs` | 46 groups passed, including the final pure-cover regression |
| Swift `python3 mobile-app/Tests/run.py` | Native persistence, capture, backup/restore, sync and desktop ZIP interoperability checks passed |
| macOS `python3 desktop/build.py` | ARM64 App build and ad-hoc signing passed |
| Whitespace `git diff --check` | Passed |

Actual UI verification: search returned the saved Poly Haven resource; gallery and spatial-deck clicks opened the actual detail record; quick capture persisted the Python asyncio URL before its success feedback. Empty data stayed empty. A 1000-record temporary library initially rendered sixty cards; search found QA0999 beyond the displayed batch. Metadata/footer hiding was checked at desktop and mobile widths; cover names remained in accessible labels. Native WKWebView loaded the eleven actual QA records.

No measured 60 FPS claim is made. Automated motion checks cover cancellation, ownership, reduced motion and pause conditions; these are not frame-time measurements or a physical iPhone motion acceptance test. The existing full iOS UI/Share Extension build and device acceptance were not repeated for this desktop-only change.

## Visual evidence

- `evidence/reference-desktop.jpg`: supplied Demo reference.
- `evidence/desktop.jpg`, `mobile.jpg`, `user-viewport.jpg`: final pure-cover gallery.
- `evidence/macos.png`, `macos-gallery.png`: actual isolated macOS App.
- `evidence/detail.jpg`, `quick-capture.jpg`: actual product workflows.
- `evidence/empty.jpg`, `1000-resources.jpg`: isolated boundary scenarios captured before the final metadata-only change.
- `evidence/round1-*.jpg`: intermediate port evidence, not the final UI.

`evidence/capture-metadata.json` records requested sizes, effective DOM dimensions and unmodified bitmap dimensions. In-app-browser scaling differs from the requested CSS sizes. Its full-page capture places the fixed mobile navigation at the original viewport bottom within the long image; the viewport supplement explains this position. Early captures with unpainted offscreen content were replaced after ordinary page scrolling loaded all cards/images. Screenshots were not stitched or repainted.

Independent finish review is recorded in `FINISH_REVIEW.md`. Its documentation finding and the subsequent native cover-fill regression were both scored resolved in `FINISH_VERDICT.md`, with disposition **ship** at the limited correction scope. This verdict is not a new whole-surface or motion-performance acceptance claim. The static detector ran once and reported legacy cascade findings plus the explicitly supplied palette, compressed poster typography, grids and geometric material. This is not a clean-detector claim; visual authority and runtime evidence were assessed separately.

## Remaining scope

Native iPhone V5 visual implementation, physical-device motion/performance profiling, App notarization and store distribution remain outside this desktop port. Native background launches occasionally did not paint WKWebView until an actual control interaction; native search and clearing it produced the expected live record counts and repainted the interface. Foreground cold-start behavior and frame timing have not been certified. The preview runs against QA data; it should not be mistaken for a migration of the formal resource library.
