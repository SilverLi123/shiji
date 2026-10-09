# Cover Studio 2.0 · P0–P3 review

2026-10-09. Branch: `feat/shiji-cover-studio-2`. Clean starting point: `3327d4426a70471d955ba9f7099ea9662e306307` (latest pushed card/tactile restoration). Changes are local; no remote push or main merge.

## Scope and visual evidence

Completed P0–P3: upgrade the existing production cover renderer, then run it against temporary SQLite records in both the actual application and a comparison page. P4–P9 remain gated on the user's art-direction approval. This is not a replacement application or a demo data backend.

The repository's V2 Motion Studio HTML, desktop reference and previous gallery captures were inspected. V3 Poster Lab / V5 Spatial Poster files were not found in the repository or the searched local reference filenames; this delivery does not claim to reproduce an unseen V5.

Before: one fixed composition/color per type; typography selected by title length; mutable motion tags could switch template families; no same-type variation. The existing Hero, three-column masonry, featured footprints, stable IDs and whole-card drag/tilt already worked and were retained.

After: saved-resource semantics select a template family; immutable identity independently selects composition and palette; local measured typography fills that composition. Color changes and structural changes are separate. Source, language, tags, excerpts and code are only saved fields. Empty metadata never generates stars, technologies or licenses.

## Actual code and composition families

| Family | Variant 1 | Variant 2 | Variant 3 |
| --- | --- | --- | --- |
| GitHub / development tools / AI tools | Type monument and cropped slab | Asymmetric title and signal columns | Monospace terminal atlas and spatial ring |
| UI / design / art | Cropped counter-ring, lower title | Swiss cross and offset square | Print registration and shaded disc |
| Motion resources | Italic headline and cropped disc | Vertical ribbon, split title | Successive tilted graphic frames |
| Code | Actual numbered editor rows | Annotated paper and margin rule | Angled floating editor |
| Prompt | Large type and cropped star | Serif margin story and quote orbit | Cut paper with title and actual excerpt |
| Article / website | Editorial headline and rule | Serif magazine with colored column | Vertical spine and inset headline |
| Audio | Decorative signal line | Cropped record disc | Three signal columns |
| Other files | Folded corner | Offset paper stack | Registration margin and shaded disc |

All 24 structures are implemented in `desktop-app/static/shiji-v2.js` and scoped CSS in `desktop-app/static/shiji-v2.css`. Audio graphics are decorative, not fabricated analysis of audio files. Geometry uses CSS/SVG and local system fonts, with no downloaded imagery or runtime dependency.

Nine palettes: Cream / Ink, Lime / Charcoal, Violet / Deep Blue, Cyan / Navy, Coral / Burgundy, Yellow / Black, Monochrome, Chrome, and dark Navy. Core SHIJI colors remain unchanged. Chrome uses a static gradient; paper/printing layouts use registration, small dot fields, offset shapes and soft directional shadows. No new perpetual animation or pointer controller was added.

`coverProfile()` hashes the saved ID first, then a canonical URL when no ID exists. URL canonicalization removes hash/tracking parameters and sorts query keys. Favorite, tags, title, description, position, sort, pagination and viewport do not select a new variant/theme. Type/category changes intentionally select the relevant family. Stateless seeding cannot guarantee that arbitrary adjacent records never share colors; it avoids list-order-dependent cover reshuffling.

## Typography and safety

Native Canvas `measureText()` measures local sans/serif/mono fonts; three reusable contexts and a bounded 512-entry measurement cache avoid canvas allocation per card. CJK glyphs, spaces, CamelCase and path separators form wrap opportunities. Binary search estimates the width needed to pack those words into the selected row count, rather than relying on string length or average line width. Container width and each composition's safe height jointly bound the final size. Browser text balancing preserves the editorial appearance.

Titles use 16–96px, restrained negative tracking and 1.1 line height. Serif variants use Georgia / Songti SC; terminal/code use system monospace; other variants keep the accepted local system sans. Source/caption stay secondary, code retains real indentation, and long names remain available in the existing accessible card/detail title. Extremely long unbroken strings may still need a bounded cover excerpt; the complete resource name remains outside the cover.

Two real-browser defects were corrected: legacy `.cover-code` variables made ordinary code white on light paper; long-title compositions had overly optimistic row/height estimates. The final QA records have no title content-height excess above 8px at the five tested widths; small font ascender/descender rounding is not treated as a missing row. This is a geometry check plus screenshot inspection, not proof that every arbitrary font/string is covered.

All user strings are escaped before HTML insertion. Only numeric measured values enter inline CSS; themes/variant classes come from finite internal lists. No injected SVG IDs, URLs, script handlers or interactive controls are generated inside covers. Existing real-image priority and load-error fallback still use the app's existing preview path. No schema, manifest, storage, sync, credentials or API business behavior was changed.

## Run and review

From the repository root:

```sh
python3 docs/cover-studio-2/qa/run.py
```

The runner creates a disposable `shiji-cover-studio-*` directory and selects a loopback ephemeral port; read the printed JSON for its address. The current review is at `http://127.0.0.1:54891/cover-studio`; the actual application is at `http://127.0.0.1:54891/`.

36 persisted QA records include same-type repositories, Chinese/English/mixed and very short/long titles, actual code and prompts, design/motion/audio/files, a bundled real website image, a local cover attachment and a deliberately broken image address. These are manually supplied QA inputs, not claims of metadata scraping. The comparison page additionally tests an empty-title renderer fallback; Store still requires nonempty saved titles. No formal library was touched.

The old renderer/CSS are frozen from `3327d44` and isolated in shadow roots on the read-only comparison page. They are QA-only files, not an alternative shipped runtime. The page compares the same saved records and offers all-types, same-type GitHub, title-boundary and before/after views. The first 12 QA records produce 10 structural combinations and 5 themes (more than the required five structures). Gallery/detail retain the same cover variant/theme.

| Browser screenshots | Purpose |
| --- | --- |
| [comparison.png](evidence/comparison.png) | Same SHIJI resource, old and new |
| [all-types-before.png](evidence/all-types-before.png), [all-types-after.png](evidence/all-types-after.png) | All persisted types and title boundaries, original vs new |
| [github-before.png](evidence/github-before.png), [github-after.png](evidence/github-after.png) | Eight same-type repository inputs |
| [gallery-after.png](evidence/gallery-after.png) | Mixed new poster compositions |
| [app-320.png](evidence/app-320.png), [app-390.png](evidence/app-390.png), [app-768.png](evidence/app-768.png), [app-1024.png](evidence/app-1024.png), [app-1440.png](evidence/app-1440.png) | Actual application in fixed-width responsive QA frames |
| [detail.png](evidence/detail.png) | Actual drawer / matching cover identity |
| [calm.png](evidence/calm.png) | Actual 1000-record QA app in Calm, 60 rendered cards |
| [pressure-1000.png](evidence/pressure-1000.png) | Preliminary paginated load |

Screenshots were captured from the real browser. Nominal frame viewports are exactly 320/390/768/1024/1440px; the scrollbar reserves 8px of client width. [responsive.json](evidence/responsive.json) records zero horizontal page overflow and no missing title rows for all 36 records at all five widths. These are web/WKWebView presentation evidence, not native iPhone screenshots.

## Verification and preliminary performance

Baseline: 39 Node groups and 202 Python tests passed. Final: 40 Node groups passed, including new deterministic identity, canonical URL, three structures per family, palettes, glyph widths, uneven-word packing, real-field rendering and injection regressions. Existing gesture, stable-card, failed-cover, business and accessibility regressions are retained.

Final Python rerun: **202 passed in 27.831s**, including the existing compiled Swift `PhoneSyncModel`/Vision QR test. The first final run had one SIGTRAP in that native test; an isolated rerun passed (1 test, 4.616s), then the entire suite passed. The failure's precise cause was not established; no native workaround or unrelated source change was made. Fresh iOS simulator/device acceptance is outside this phase.

Commands:

```sh
NODE_PATH=/Users/silver/shiji/desktop-app/node_modules npm --prefix desktop-app test
cd desktop-app
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

`git diff --check` passed. A manual type detector reported documented-system-font/type-ramp mismatches, including existing Hero styles. The cover's intentionally local serif/mono families and container-dependent 16–96px title ramp are documented here; the detector cannot validate measured dynamic sizing. Browser inspection provides the missing layout evidence.

The 1000-record runner (`--count 1000`) uses a separate temporary Store. The actual browser rendered the existing 60-card page budget, not all 1000 nodes. [browser-1000-smoke.json](evidence/browser-1000-smoke.json) recorded a 141ms initial long task; the brief 33-sample scroll window had 16.7ms median and 33.3ms p95. This is a smoke check, **not a 60 FPS claim or full P9 performance acceptance**. [markup-performance.json](evidence/markup-performance.json) records a single Node generation pass for 1000 covers (24.3ms); it excludes native font measurement, layout, paint and scrolling. No memory/long-session conclusion is inferred.

## Files and next phase

Runtime changes: `desktop-app/static/shiji-v2.js`, `desktop-app/static/shiji-v2.css`.

Regression: `desktop-app/tests/test_cover_studio.js`.

Design documentation: `desktop-app/DESIGN.md`, `docs/shiji-v2/SURFACE_BRIEF.md`, this report.

QA: `docs/cover-studio-2/qa/{run.py,compare.html,compare.js,compare.css,baseline.js,baseline.css}` and browser evidence. No runtime app code imports QA assets.

Pending user visual approval: P4 internal layered spatial motion under ShijiBits; P5 priority acceptance expansion; P6 safe customization/compatibility evaluation; P7 expanded semantics/security matrix; P8 complete visual, empty-data and accessibility matrix; P9 full performance/memory/cancellation/background acceptance. Existing whole-card tactile interaction, Hero and Calm/Reduce Motion code remain intact. No speculative AI interface, cover-settings persistence or new animation system was introduced.
