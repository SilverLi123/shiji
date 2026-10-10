disposition: fix

Input limitation: no separate QUALITY BAR card was supplied. This is a code-led port of the user's pinned HTML/CSS; no generated comp, concept roll, seed key, measured comp specification, or comp-diff gate applies.

## persistence

**Fail — documentation only.** `desktop-app/PRODUCT.md` exists and describes the retained local resource workflow. `desktop-app/DESIGN.md` predates this redesign and does not yet describe the shipped V5 world: it still names V2 as canonical, says `shiji-v2.css` loads last, records obsolete sidebar breakpoints, and describes a different default cover renderer. PRODUCT's six-record QA description and earlier test totals also predate this packet. The documenter must canonicalize these after this review; this finding does not request implementation changes.

Evidence check passes. The three current required full-page images are fully painted: desktop **1375 × 2432**, mobile **367 × 4516**, user **1198 × 2411**. `capture-metadata.json` records effective DOM viewports **1412 × 980**, **382 × 608**, and **1230 × 692**, respectively; requested 1440/390/1255 sizes must not be represented as actual CSS sizes. The mobile full-page image places the fixed bottom navigation at the original viewport's bottom within the long bitmap; supplementary viewport evidence establishes actual fixed placement. The earlier reused mobile-as-user capture and unpainted mobile capture have been replaced.

The settled detail, quick-capture, empty, and 1000-resource states are present and recognizable. The latest isolated `macos.png` shows the native WKWebView shell with the correct lime quick-capture button and dark shuffle button; the earlier pale buttons were absent from the final capture. The 1000-resource image establishes a populated first viewport, not inspection of all 1000 cards. This packet covers macOS/web; mobile web captures do not certify native iPhone visuals. Reported Python/Node/Swift/ZIP checks are builder evidence, not independently rerun tests or proof of visual fidelity.

## fidelity

Authority: `docs/shiji-v5/reference/spatial-poster.html`, its reference screenshot, and the subsequent human instruction **“卡片下面不要展示文字，点击开片才展示详细信息”**.

| Salient element | Verdict | Evidence / adaptation authority |
| --- | --- | --- |
| Dark fixed sidebar and compact studio toolbar | match | Preserves the reference's 238px sidebar, brand mark, dark navigation, and compact poster/space/motion controls. |
| Sidebar resource scopes and management entries | adaptation | Real search, saved scopes, categories, projects, import/backup and management replace the Demo's illustrative collection shortcuts; PLAN requires the existing business actions. |
| Two-line Chinese lime headline and collection CTA | match | Same copy, focal scale, white/lime relationship, purple punctuation, and pill action; actual App capture retains the treatment. |
| Purple layered brand stage | match | Same green/black emblem, purple field, grid/orbit, black note and KEEP IDEAS lettering. Calm/flat captures intentionally suppress dynamic depth, as PLAN requires. |
| Three-pane spatial deck | adaptation | Same topology and overlap; up to three real matched records replace the Demo's seeded cards. No overlay metadata remains after the human correction. |
| Lime motion ribbon and dark end label | match | Same condensed italic lettering, purple accents, relative prominence, and placement between the deck and gallery. |
| Gallery composition | adaptation | Wide featured poster plus three-column masonry on desktop and one-column reflow on mobile. The user's correction authorizes removal of under-card titles, descriptions, tags, actions and footer; current captures show covers only. |
| Real covers and poster families | adaptation | Actual saved images take precedence; fallback art uses the record's real title/source/type/tags/snippet. Both photographic sources remain visible and failed-image recovery produces a usable poster. This follows PLAN's content truth requirement. |
| Detail and quick-capture surfaces | adaptation | Existing resource drawer and protected capture flow use the V5 palette. Updated detail evidence shows the full resource identity and actions after clicking a cover; unknown price/authorization remain marked for confirmation. |
| Narrow-screen controls | adaptation | Drawer navigation, fixed collection/search/manage bar, wrapped filters, and stacked Hero preserve usable access where the supplied desktop topology cannot fit. Cover buttons retain real-title accessible labels and detail IDs. |
| TYPE | match | Retains the reference's heavy sans headline, compact studio labels and compressed poster voice. Variable sizing and line limits accommodate actual Chinese titles; full identity remains in details. No unrequested replacement typeface is warranted. |
| MATERIAL | match | The authority is CSS/SVG spatial poster geometry; the port keeps that medium and adds actual saved photographic images where available. No invented raster plate or synthetic photo is required by this brief. |
| GROUND | match | The source field `#0c0d10`, sidebar `#101115` and purple/lime relationships are retained; visible desktop, user and native captures show the same dark value and temperature. This is a source/visual comparison, not a claimed pixel-diff measurement. |

The direction promises are met: first viewport retains the reference's hierarchy and memorable lime headline/purple stage; the real-record deck, ribbon and gallery keep its reading order; covers lead; details appear on click. `app.js` retains real preview precedence/error recovery and delegates keyed deck rendering to existing stable-card machinery. ShijiBits remains the card gesture/FLIP owner; sampled ShijiMotion code preserves Calm, reduced-motion, overlay/background and offscreen cancellation. Static screenshots establish settled states, not timing or gesture quality.

The craft floor does not justify deleting the user's pinned grid, grain, glow, geometric ornaments, decorative captions or inherited lettering. Controls use the existing consistent SVG icon system. No material visible craft failure remains in the reviewed final captures. The existing detector report contains **494 findings**, including static/cascade findings and intentional reference features; it was not rerun and is not characterized as clean. Undocumented V5 colors/type/radii are addressed by the persistence fix below.

## ceiling

Reached for the pinned code-led world: frame, overlap/depth, heavy lettering, ornament density, lime/purple contrast, motion controls and poster variation are retained. No new visual direction, asset production or rebuild is warranted. The separate QUALITY BAR card was not supplied; motion commitment is assessed from supplied static states and sampled controller code, not a fresh browser session.

## material_fixes

1. **Persistence / truth:** canonicalize `desktop-app/DESIGN.md` and its design-system sidecar for V5's actual load order, palette, type/radii, breakpoints, poster renderer and human-requested pure-cover gallery/detail behavior; refresh `desktop-app/PRODUCT.md` QA/evidence facts and limits so the old six-record/earlier-test/previous-ship statements cannot be mistaken for this build. No implementation polish is requested.

## keep

Keep the pinned Demo's lime headline, purple geometric stage, overlapping real-record deck, ribbon and pure-cover gallery; retain actual-image precedence, stable IDs, cover-click details, existing capture/search/filter/import/backup/sync actions and motion accessibility controls.
