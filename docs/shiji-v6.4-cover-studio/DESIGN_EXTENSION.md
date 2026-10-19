# Cover Studio 3.0 — design-system extension

## Overview

This is an ordinary extension of the incumbent SHIJI world. [SPEC.md](SPEC.md) preserves the V5 Hero, Spatial Deck, gallery, Motion Studio / Calm, Space 3D / Flat and brand; [design/SURFACE.md](design/SURFACE.md) defines the added cover families and protected editor. It does not authorize a replacement identity. The desktop and native `PRODUCT.md`, `DESIGN.md` and `.impeccable/design.json` remain unchanged by this documentation pass. This file records the additions without creating a second global token source.

The baseline read was [desktop PRODUCT](../../desktop-app/PRODUCT.md), [desktop DESIGN](../../desktop-app/DESIGN.md) and [desktop sidecar](../../desktop-app/.impeccable/design.json). Native comparisons also used [mobile DESIGN](../../mobile-app/DESIGN.md), [mobile PRODUCT](../../mobile-app/PRODUCT.md) and its existing sidecar. The desktop sidecar is dated 2026-10-10; the native sidecar is dated 2026-10-08. Their age and V5 / native V2 names are retained, rather than silently refreshed.

Implementation inspected: [cover-studio.css](../../desktop-app/static/cover-studio.css), [cover-studio.js](../../desktop-app/static/cover-studio.js), [cover-config.js](../../desktop-app/static/cover-config.js), [shiji-v5.js](../../desktop-app/static/shiji-v5.js) and [native CoverStudio.swift](../../mobile-app/App/CoverStudio.swift). This pass runs no detector, build, functional test or performance benchmark.

## Colors

The V5 page keeps its existing dark field, lime actions, violet brand stage and cyan spatial cues. Cover Studio adds a scoped artwork palette, selected by content recommendation or explicit user preference:

| Artwork role | Implemented value | Scope |
| --- | --- | --- |
| Acid | `#c5ff43` | Developer and selected cover palettes |
| Paper | `#f3efdf` | Editorial paper |
| Violet | `#b39bff` | Spatial material and contrasting geometry |
| Cyan | `#65e2e4` | Selectable artwork palette |
| Coral | `#ff8d72` | Kinetic material |
| Ink | `#17191c` | Minimal field and code terminal |

These are the actual `cover-config.js` values, distinct from the older global V5 palette. They do not replace `--lime`, `--violet` or the page's state semantics. Custom primary colors use six-digit hex; the renderer chooses a dark or light foreground against that base. This source-level foreground selection is not a claim that every composed or photographic region has received a contrast audit.

The editor uses its own opaque green-black working planes: shell `#141714`, preview stage `#1b1e18`, controls `#20241f`, stroke `#41493a`, main text `#e9eee2` and muted text `#aeb7a5`. Its lime `#c5ff43` marks Save, selected options and focus. Secondary button, label, validation and hint shades remain scoped to the editor. Native controls retain adaptive AccentColor and semantic system surfaces; fixed artwork colors stay inside the cover.

## Typography

The web extension retains incumbent Inter and system fallback behavior; no new font asset is introduced. The two detector Inter warnings concern an already approved family, so they are not grounds to replace it. New artwork uses heavy title type with tracking `-.035em`; decorative glyphs reach `-.04em`, consistent with SURFACE's new-art boundary. Code uses system monospace and actual saved lines.

Cover titles derive size from real CJK / Latin width estimates and are clamped per composition. Editorial A/B now share one flex text region with a real title/subtitle gap, three headline lines, two subtitle lines and size ceilings of `9cqw` / `7.5cqw`. Title-position and density choices act inside that region. Truncation retains the full resource name in the surrounding resource UI; custom cover text remains separate from the resource title and notes.

The editor uses a compact operational hierarchy: title `24px` (`21px` on narrow screens), section labels `14px`, field text `13px`, ordinary labels/actions `12px` and thumbnail/help text `11px`. These local steps extend the older documented ramp rather than redefining every page's typography. Native uses system Form/control text and a geometry-scaled poster renderer; its stills do not establish full Dynamic Type fitness.

## Layout

The outer V5 hierarchy and layout ownership stay intact. The supplied home capture retains the large two-line Hero, violet brand artwork, three-resource spatial scene and gallery entry. Cover art replaces preview contents within the existing stable resource/card structure. It does not introduce a new gallery grid or page shell.

The web editor is a separate dialog capped at `min(1280px,96vw)` and `94dvh`. Wide layouts have style/layout selection (`190px`), central preview (`minmax(220px,1fr)`) and properties (`290px`) with `24px` gaps. At `1000px` it moves styles above a two-column preview/properties region. At `640px` it becomes an opaque full-viewport workspace: preview first, styles second, properties third. The header and Save footer remain sticky, and the footer includes the bottom safe area. These are editor breakpoints, independent of the incumbent gallery's `620px` single-column threshold.

The central preview has an aspect ratio of `1.45`, maximum width `500px` and an optional `280px` gallery-size view. Thumbnails use static `1.25` frames. Native adapts the same controls to NavigationStack / Form, a `250pt` preview, horizontal style thumbnails and a segmented layout picker; it does not reproduce the desktop columns.

## Elevation & Depth

The editor reuses the incumbent dialog shadow (`0 24px 80px #0009`) and dark modal scrim. Its solid surfaces provide separation while the preview remains the visual focus. Artwork extends existing print-offset shadows, rotated sheets, radial spheres, orbital outlines, exploded planes and isometric blocks.

Existing Bits / Motion ownership remains a dependency: outer resource placement and interaction are not transferred to the new cover engine. New art uses the existing `art-anim` / artwork lifecycle vocabulary; thumbnail loops and sheen are disabled. No new requestAnimationFrame owner is introduced in the inspected cover files. This is an implementation observation, not motion, offscreen-layer or large-library performance acceptance. Calm, Reduced Motion and Flat remain required inherited controls.

## Shapes

The dialog retains the existing `16px` modal radius and `12px` preview language; the narrow editor is square to the viewport. The extension adds `4px` thumbnail clipping and `7px` fields/secondary controls, alongside `8px` style buttons and circular palette swatches. These scoped additions explain the detector's radius advisories; they do not change the global radius scale. Native preview clipping (`14pt`) follows its incumbent preview token, with native system Form and toolbar shapes.

## Components

| Family | A | B | C |
| --- | --- | --- | --- |
| Editorial | Newspaper rule | Tilted inset reading sheet | Offset color-separation frame |
| Spatial | Orbital sphere | Exploded planes | Isometric stack |
| Developer | Actual code terminal | Repository specimen | Interface structure |
| Kinetic | Echoed type | Tension loops | Rhythm sequence |
| Minimal | Photo aperture / caption | Inset document | Centered axis |

These fifteen authored compositions share real title, source, category, tags and available content. Decorative geometry does not fabricate technical facts. Real images remain preferred in automatic source selection; explicit image/poster and original V5 selections preserve user control. “原版 V5” calls the incumbent renderer rather than introducing another resource engine.

The independent draft editor adds style/layout thumbnails, preset/custom color, independent title/subtitle, title position, density, image source/attachment/upload, Fit / Fill and image focus. Save is the primary action; Cancel, Restore Auto, regenerate and gallery-size preview are distinct. The inspected web code stages upload bytes and draft values until Save, restores opener focus on close, exposes pressed/invalid/busy state, and keeps future-version configuration read-only except reset. These are source observations; persistence and concurrency results belong to the technical acceptance report.

The image preview now distinguishes loading, successful image display and failure. On failure the visible poster is paired with “图片不可用，已显示海报。可在‘封面来源’更换图片。” The status describes the rendered result instead of a failed source candidate.

## Do's and Don'ts

- Do preserve the V5 Hero, deck, pure-cover gallery, brand, modes, stable IDs and single Bits / Motion ownership.
- Do treat the palette, fields, breakpoints and cover typography above as scoped additions; retain the incumbent metadata rather than silently replacing it.
- Do keep automatic recommendation subordinate to explicit preferences and actual image/content availability.
- Do maintain a shared text budget and truthful image state when extending cover templates.
- Don't infer permission to repair unrelated historical drift from a detector advisory.
- Don't use static screenshots as evidence for persistence, continuous motion, 50K performance, all device sizes or physical iPhone acceptance.

### Evidence checked and limits

This documentation pass visually inspected `evidence/desktop-home.png`, `board-after.png`, `desktop-editor.png`, `mobile-editor.png`, `mobile-editor-controls.png`, `art-editor-desktop.png`, `actual-image-priority.png`, `editorial-a-mobile.png`, `editorial-b-large.png`, `native-editor-initial.png` and `native-saved-detail.png`. The board shows fifteen cover/layout positions; [art-manifest.json](evidence/art-manifest.json) reports fourteen resources because positions reuse some records. The home and blue-image captures include isolated QA content. Native captures are iPhone Simulator evidence.

[VISUAL_REVIEW.md](VISUAL_REVIEW.md) records the initial failures. [VISUAL_VERDICT.md](VISUAL_VERDICT.md) resolves its three scored material fixes: Editorial A/B text separation, mobile workspace containment and truthful failed-image status. Its `ship` disposition is scoped to those fixes. It is not blanket native, full-surface, motion or performance acceptance.

The existing `/tmp/shiji-v64-design-detector.json` was read, not rerun: two Inter warnings, thirty-five color advisories, five type advisories and four radius advisories. They compare the new scoped surface to older desktop metadata. The values above document intentional additions; no native detector exists. Existing documentation also describes fixed V5-only covers, no original-style switch and an unchanged iPhone surface. Those historical statements no longer describe this extension, but remain preserved in their incumbent files. This is a recorded documentation gap, not authorization for unrelated cleanup.

Native Developer A and original-V5 code subtitles now have an actual screenshot OCR regression: both rendered CUSTOM SUBTITLE QA in the passing two-case iPhone Simulator run (251.574s). The source fields, save/reopen, cancel and reset also passed. Light appearance, large accessibility text, physical iPhone, continuous motion and native performance remain outside this document's evidence.
