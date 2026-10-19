# SHIJI V6.4 Cover Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline. Steps use checkbox syntax. The user's complete implementation request authorizes proceeding through the plan without a separate approval pause.

**Goal:** Integrate content-directed, user-controlled, persistent covers into existing SHIJI.
**Architecture:** Extend V5 presentation, existing resource JSON and coverId; pure config/rule modules, atomic guarded Store save, draft editor, existing Bits/Motion/window ownership and native SwiftUI adaptation.
**Tech Stack:** Existing Python/SQLite, vanillaJS/CSS, SwiftUI/WKWebView. No runtime dependency or cloud API.
**Spec:** docs/shiji-v6.4-cover-studio/SPEC.md. Design/compatibility: ARCHITECTURE.md.

## Global Constraints
- Base31eeea27547ae9c00a1c88212a5bbc2f70ed268f; independent feat/shiji-v6.4-cover-studio; no main merge or overwritten user changes.
- Preserve schema3, ZIPmanifest2, AppGroupJSON and syncprotocol1. Preferences are user data; never localStorage-only or search-index authority.
- Preserve large Hero, SpatialDeck, V5 art, pure covers, single Bits/Motion owners, windowing, Calm/Flat and ReducedMotion.
- Tempdata/randomports/one-shotcredentials only. No formal resources or pairing access. Candidate-only push when necessary for requested Actions, no main/shared merge.
- Original resource title/notes/tags remain distinct from cover text. Explicit user preferences outrank background work.
- Real screenshots and raw timing evidence; untested native/device actions are not certified. V6.3 native246ms risk remains open.

## Review Focus
- Delayed save/metadata/URL or attachment changes must not overwrite user preference or create orphan/duplicate bytes (Tasks3/4/5).
- Unknown config fields/future version and null reset must round-trip across old clients, JSON/ZIP and phone conflicts (Tasks1/3/5).
- Selected images and uploads must reuse existing coverId remapping; no independent attachment authority (Tasks3/5).
- Custom titles, malicious strings/colors, longCJK and missing metadata must stay safe, legible and separate from original search highlights (Tasks1/2/4).
- Window remount, pressed/focused nodes, above-anchor decode, modified covers outside the viewport and Calm modes must retain geometry and lifecycle ownership (Tasks4/6).

### Task 1: Configuration value contract
**Files:** cover_config.py; static/cover-config.js; tests/test_cover_config.py, test_cover_config.js; shared JSON vectors.
**Interfaces:** normalize_config(value)->dict|None; JS normalize(value), read(resource), colors(config,direction); version1 enums/defaults/bounds in ARCHITECTURE. Original values are not mutated. Future bounded JSON preserved, renderer marks unsupported.
- [x] Write matching cross-language vectors for absent/null, defaults, unknown fields/future versions, invalid enums/types/NaN/depth/8KiB, hex escaping and contrast≥4.5.
- [x] Run focused tests: expected RED missing modules; implement pure validation/contrast contract; expect GREEN and Node suite; commit.

### Task 2: Content direction and five authored families
**Files:** static/cover-direction.js, shiji-v5.js, cover-studio.css; tests/test_cover_direction.js, test_cover_art.js; committed design surface brief.
**Interfaces:** recommend(resource,config)->ranked[{style,template,palette,reasons,score}]; existing ShijiV5.coverMarkup(resource) renders resolved preference or originalV5. No resource persistence in renderer.
- [x] RED deterministic matching for GitHub/AI/robot/UI/motion/design/code/Prompt/CJK/missing, exact-host safety and metadata changes; same config/remount stable, regenerate only explicit seed.
- [x] Implement scored catalog and15different layouts using actual fields, escaped content and existing art lifecycle. Preserve existing V5 renderer, real image priority and long-title boundaries. Read craft-floor immediately before UI edits.
- [x] Run pure Node/actual markup tests, record completed cover families, commit. Visual acceptance is reserved for Task6, not inferred from tests.

### Task 3: Atomic resource persistence and cover API
**Files:** cover_preferences.py, storage.py, edits.py, server.py; tests/test_cover_preferences.py, test_cover_http.py, compatibility fixtures.
**Interfaces:** Store.update_cover(rid,body)->{resource,changed}; POST/api/resources/:id/cover with config,coverId,expected:{coverConfig,coverId},optional upload{name,mime,base64}. Config validation reused by all resource writes. Save uploads only after confirmation,≤5MiB real-image verification.
- [x] RED persistence/restart, no-op retry, stale fields, source edit preservation, duplicate bytes, malformed/oversize upload, transactional rollback and future config roundtrip.
- [x] Add optional payload field with guarded missing/null comparison; atomic upload/pref save through existing attachment writer. No SQL version/protocol bump or second resource model.
- [x] RED→GREEN fullZIP remapping/JSON fallback/backup old resource/legacy omission/capture late response; existing portable suite; commit.

### Task 4: Editor workspace and bounded presentation updates
**Files:** static/cover-studio.js/css, app.js,index.html,board-model.js,stable-cards.js,gallery-window.js,query-integration.js; real browser editor runner/tests plus Node contracts.
**Interfaces:** ShijiCoverStudio.create({document,preview,save,onSaved,notice}).open(resource); draft-only fields and objectURL. applyCoverResource updates existing state/cache and existing layout/motion owners, no global render on preview/save. Existing resource-query authority remains.
- [x] RED draft/cancel/no-upload, Save/busy/error/uncertain outcome/retry, all controls, rapid edits/late responses, reset, actual crop/source and gallery preview.
- [x] Implement styles/layout thumbnails, palette/customcontrast, customtitle/subtitle/density/position, image selection/upload/fit/fill/focus, regenerate and gallery preview. Real-image fallback preserves artwork. Keyboard/focus/errors/narrow screens included.
- [x] RED→GREEN remount/metadata edit/per-card cache/detail/deck update, customtitle highlight safety, offscreen save/scrolled anchor and window residency; run Node+real browser; commit.

### Task 5: SwiftUI presentation/editing and exchange compatibility
**Files:** mobile-app/Shared/CoverConfiguration.swift,Library.swift,SyncMerge.swift; native cover/editor views and project/test build references; Python/Swift/HTTPS/ZIP tests.
**Interfaces:** Resource cover config derived from raw JSON; pure Foundation validation matches vectors. Native editor commits existing raw resource through baseline-guarded LibraryFiles, preserves unknown prefs. Existing native navigation/share/import/sync untouched.
- [x] RED native config/roundtrip/null/unknown/future, title separation, field retention, semantic conflicts and actual cross-endZIP/sync.
- [x] Implement native cover families/controls inside existing SwiftUI; existing image decode limits, accessibility/dynamic type and system reduced motion apply.
- [x] Foundation, HTTPS, native build and available simulator screenshots; true device/foreground gaps explicit; commit.

### Task 6: Actual art/interaction/performance acceptance
**Files:** qa/,evidence/,REPORT.md,PERFORMANCE.md,API.md; workflow/checks only as needed.
**Interfaces:** Real Store13sample types, V5 page/HTTP,15layouts, real local images/failures,1K/5K/20K/50K matching V6.3 runs and bounded DOM.
- [x] Batch actual desktop/mobile/editor/detail/Calm screenshots; inspect every capture. Fix material defects in one batch and confirm once; run Impeccable detector once, preserve pinned V5 language.
- [x] Run actual Save/cancel/reset/remount/late response/source/upload/backup/sync scenarios, complete Python/Node/Swift/HTTPS/macOS build and actual candidate Actions. Preserve raw recordings/traces outside Git.
- [x] Required fresh whole-branch code review plus skill-required visual finish review at their scopes; one meaningful code fix pass with RED→GREEN. Record remaining minor/manual risks.
- [x] Publish architecture/API/compatibility/performance/evidence and separate implemented, automated, native/device accepted, unverified; module commits, no main merge.

## Completion boundary
All six implementation tasks are delivered and evidenced. Native Simulator UI is accepted for the two recorded cases; physical iPhone, native motion recording/performance, Photos permissions, VoiceOver and large Dynamic Type remain unaccepted as listed in REPORT.md. Completed task checkboxes do not certify these manual/device checks. Tested runtime7bc01cb, all five Actions jobs success; final evidence-only commits do not change that runtime.
