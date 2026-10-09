# SHIJI V2 · Desktop card restoration

2026-10-09 · base `feat/shiji-v2-motion-ui` / `cc91d1a` · candidate `feat/shiji-v2-card-restoration`.

## Visual gap and result

| Aspect | Pinned Motion Studio Demo | V2 baseline | Candidate |
| --- | --- | --- | --- |
| Cover composition | Large type, cropping, geometric depth, purposeful empty space | Centered domain/icon or small text panel | Saved names, source and content compose complete posters |
| Type distinctions | Separate visual languages for tools, motion, design, Prompt | Most missing covers share a dark placeholder | Eight derived templates; real images remain first |
| Type hierarchy | Resource name participates in the artwork | Name mainly below a largely empty cover | Container-sized display type, real code and editorial copy |
| Gallery rhythm | Three columns and a two-column feature | Two equal wide columns | Three/two/one responsive columns; deterministic Tool features |
| Feedback | Cover identity continues into interaction | Fallback detail proxy flattens to text | Same poster/image moves into detail, with no duplicated text layer |

The full original `shiji-v2.css` is an exact byte prefix of the new stylesheet. The only `index.html` change is `data-gallery-columns="2"` → `"3"`. Hero size, structure, typography, purple stage, ticker and brand animation implementation remain unchanged. The candidate updates the older two-column design contract in DESIGN.md / Surface Brief under the user's latest instruction.

## Actual code

- `desktop-app/static/shiji-v2.js`: eight CSS/SVG/HTML poster templates. Tool reads actual title/domain/language/tags; Design and Motion use separate compositions; Code preserves real indentation and locally colors escaped tokens; Prompt uses saved text; Article uses actual name/source; Audio uses decorative signal geometry; other File uses a folded shape. No fake Demo resources, project metrics, fabricated technologies, remote artwork or resource mutations.
- `desktop-app/static/app.js`: real attachment / thumbnail / bundled website preview still wins. The next-sibling image-error contract and decoded-image reuse are preserved. Failed images expose the new poster instead of an icon. Card ID, actions, selections and metadata remain on the same business path.
- `desktop-app/static/shiji-v2.css`: poster materials, title-length adaptation, geometric clipping, quiet metadata and matching detail covers. The design uses the approved system font; code uses the installed monospace stack. No remote font dependency.
- `desktop-app/static/resource-bits.js`: its existing packer supports contiguous spans. Saved technical information (`language`) makes Tool cards a feature in a three-column comfortable/frame view. Sorting, filters, paging and favourite changes do not reassign the role. Compact/fit and narrow views use equal widths. All widths and feature flags are written before reading heights; all positions are written before reading rectangles: two bounded measurement phases, including a 1000-node regression.
- `desktop-app/static/shiji-v2-motion.js`: its existing detail proxy clones the actual visible image/poster, preserves wide-cover context and restores the target on completion, cancellation, Calm and disposal. The target is hidden during the proxy flight to avoid double text. There is no second FLIP/Tilt system.
- New pointer layers reuse Bits' existing pointer listener, bounded to 6px; no additional ambient loop. Calm and system Reduce Motion disable the internal movement/transition.
- `desktop-app/tests/test_cover_design.js`, `test_masonry_batch.js`, `test_shiji_motion.js`, `test_shiji_v2.js`: escaping/content/image fallback, deterministic features, span geometry, bounded layout passes, fit/compact, rich proxies and cancellation.
- `desktop-app/DESIGN.md`, `PRODUCT.md`, `docs/shiji-v2/SURFACE_BRIEF.md`: scoped cover materials and new gallery contract.

SQLite schema 3 and ZIP manifest 2 are untouched. Storage, capture, backups, pairing, sync and extension code are unchanged. No third-party runtime dependencies were added.

## Running visual evidence

These are screenshots of the actual app JavaScript, Python APIs and SQLite Store, not a parallel HTML demo. All records and attachments live in disposable QA directories. The small collection uses the user's named websites and repository plus self-written code/Prompt/long-title input; saved categories and descriptions are test input, not scraped claims. The two site subpaths intentionally exercise missing previews and are not verified destination pages. The broken thumbnail is deliberate. The 1000-record set is explicitly labelled synthetic QA pressure data. No official records were read or altered.

| Type | Before | After |
| --- | --- | --- |
| GitHub / tool | [before](evidence/before-tool.png) | [after](evidence/after-tool.png) |
| Design inspiration | [before](evidence/before-design.png) | [after](evidence/after-design.png) |
| Motion resource | [before](evidence/before-motion.png) | [after](evidence/after-motion.png) |
| Actual code | [before](evidence/before-code.png) | [after](evidence/after-code.png) |
| Prompt | [before](evidence/before-prompt.png) | [after](evidence/after-prompt.png) |
| Long Chinese article / note | [before](evidence/before-article.png) | [after](evidence/after-article.png) |
| Website's actual preview | [before](evidence/before-website-image.png) | [after](evidence/after-website-image.png) |
| Local image attachment | [before](evidence/before-local-image.png) | [after](evidence/after-local-image.png) |
| Audio reference | [before](evidence/before-audio.png) | [after](evidence/after-audio.png) |
| Broken image recovery | [before](evidence/before-broken-image.png) | [after](evidence/after-broken-image.png) |

Gallery: [before desktop](evidence/before-desktop-wide.png), [after desktop](evidence/after-desktop-wide.png), [full after gallery](evidence/after-gallery-wide-full.png), [original full gallery](evidence/before-gallery.png).

Other actual states: [390px web](evidence/after-mobile.png), [1024px web frame](evidence/after-tablet.png), [empty](evidence/after-empty.png), [1000 records / desktop frame](evidence/after-1000-desktop.png), [Calm](evidence/after-calm.png).

[Actual interaction recording](evidence/card-motion.mp4): 46 CUA screenshots at their original timestamps, 8.73 seconds. It shows classification changes and poster-to-detail expansion. This is a sampled recording (~5.3 captured frames/s), not a 60 FPS performance recording.

Visual judgment: the candidate now shares the Demo's poster-sized typography, contrasting materials, cropped geometry, varied card proportions and featured rhythm. Actual content naturally changes the composition; it is not a pixel copy of Demo seed artwork. Real image cards keep their own appearance. No screenshot alone establishes smooth animation or accessibility.

## Tests and measured performance

Baseline: 202 Python tests and 37 Node groups passed before changes. Final results are recorded in [test-results.txt](evidence/test-results.txt).

Node regression coverage includes eight templates, literal escaped source, hostile names/tags, unchanged records, exact image precedence and error/load recovery, stable roles under reordering/favourite toggles, mixed-span non-overlap in 1/2/3 columns with 1000 records, two measurement phases and detail cancellation. Existing backup, editing, tags, search, projects, preview, capture and extension suites remain in the run. Native Foundation tests exercise ZIP exchange with the desktop format. macOS packaging copies these static files into the existing WKWebView app.

Actual browser checks: the 1000-record Store displays 60 DOM cards initially and 120 after “continue browsing”; matching stays 1000. Measured layout has zero overlap and no horizontal overflow. A real favourite write followed by undoing that write leaves the feature at the same width/height. 390px frame width is measured rather than inferred from the screenshot; no horizontal overflow. Details retain source/authorization and real content. Main-page console error capture was empty.

[Fixed desktop measurement](evidence/performance-desktop-1440.json) uses the running app in a 1440×900 CSS-pixel iframe and `requestAnimationFrame` intervals. Classification: 99 intervals, median 16.7ms, P95 17.6ms, max 166.1ms, 3 over 25ms. Scroll: 80 intervals, median 16.7ms, P95 17.6ms, max 66.7ms, 3 over 25ms. Scope reset P95 17.6ms. Nine long tasks were observed, max 133ms; these are not attributed exclusively to app code. This is a single local run, not a guaranteed 60 FPS result.

The earlier [multi-page capture run](evidence/performance.json) had classification P95 150ms and many long tasks while other QA pages, captures and builds ran. [Focused repeat](evidence/performance-focused.json) was cleaner but its measured viewport unexpectedly became 652px; it is not used as desktop evidence. The final fixed frame removes that size ambiguity. Raw measurements are preserved, including the adverse run. A dedicated native WKWebView profiling session is still needed for native performance claims.

The new cover work adds no infinite animation. Existing Hero loop ownership is retained. Calm was checked in the live browser; OS Reduce Motion precedence/cancellation is covered by tests and CSS, not by changing the user's system preference.

Source detector ran once: [detector.json](evidence/detector.json), 1 primary warning and 64 advisories. The primary is the **unchanged** pinned brand easing at original CSS line 45. Advisories include existing tokens/typography and poster palette additions, now recorded in DESIGN.md. The detector is not clean and is not proof of visual quality; the pinned Hero was not altered to silence it.

## Reproduction and remaining boundaries

```sh
cd desktop-app
python3 -m unittest discover -s tests -p 'test_*.py' -q
npm test # jsdom is development-only; install existing locked dev dependencies if needed
python3 desktop/build.py
cd ..
python3 mobile-app/Tests/run.py
python3 docs/shiji-v2/card-restoration/qa/run.py --count 11
# or --count 0 / --count 1000
```

The QA launcher always creates a temporary Store and selects an unused loopback port. It does not start the official service. `/qa-frame?w=1440&h=900` or 390/1024 frame widths expose the actual app; the QA metrics script is injected by the QA handler only and is not linked in the shipped app.

This delivery prioritizes desktop. The existing macOS app compiles and packages the changes; running visual evidence comes from the actual local web workspace in the in-app browser. No separate native WKWebView screenshot/VoiceOver session was performed. 390px evidence is responsive web, not a native iPhone screenshot. Native iPhone templates remain unchanged and are the next optional stage. Existing Share Extension issues are outside this card-only change. No remote push or main merge was performed.
