# SHIJI V2 execution ledger

Goal: integrate the approved Motion Studio reference into the existing apps.
Architecture: existing SwiftUI/WKWebView + stdlib Python/SQLite + native iOS.
Spec: IMPLEMENTATION_PLAN.md and CODEX_MASTER_PROMPT.md take precedence over inherited visual rules.
Baseline: 488d39ef948ccba920bcf0edbee9bd9e6d6beb0c, clean main; branch feat/shiji-v2-motion-ui. The supplied kit was added without replacing existing files.

## Global constraints
No production data, production ports, pairing credentials, schema/manifest changes, runtime dependencies, remote push or removal of legacy features. Tests use temporary stores and ephemeral ports. Stages are serial.

## Tasks
- [x] P0: Python / Node / Swift baseline; inspect references, rendering and storage lifecycle; isolated QA service.
- [x] P1: shiji-v2.css tokens, real Hero/sidebar/gallery/detail; presentation-only card types; DOM tests and responsive captures.
- [x] P2: independent motion controller; coordinate existing Bits/Glass, lifecycle/cancellation/reduced motion tests and interactive captures.
- [x] P3: native semantic palettes and SwiftUI brand/gallery; retain native system flows; build both platforms and inspect supported native surfaces.
- [x] P4: persist-first capture, deferred guarded metadata; concurrency/error/duplicate tests; no implicit cover download or preview-worker enable.
- [x] P5: available local regressions/builds, actual desktop/tablet/mobile/empty/large/reduced-motion UI matrix; bounded independent review and design documentation. Unverified platform cases and inherited Share Extension issue remain listed in VALIDATION.md.
- [x] Follow-up: port the supplied Motion Studio animation language into real Web/macOS and native iPhone surfaces; capture actual interaction evidence and test lifecycle/recovery.

## Review focus
Stable resource nodes and 60-item browsing; exact tags; search/filter/project/preview/list/board/select/edit/import/backup/trash/undo/extensions/sync preserved. No second card FLIP/tilt. Capture feedback follows persistence; async metadata must not overwrite manual edits. Reduced motion wins over preferences. iPhone Share Extension blank-page limitation remains explicitly documented unless independently verified fixed.

## DOM / business boundaries
app.js owns real state/render/API actions; ShijiCards owns keyed nodes and focus; ShijiBits owns masonry and card transforms; ShijiGlass owns category indicator. V2 presentation derives type from kind/category/media; V2 motion owns only decorative overlays and preferences. Keep all existing IDs and delegated actions.
