# Cover Studio 3.0 — whole-branch code review

Reviewed range: `31eeea27547ae9c00a1c88212a5bbc2f70ed268f..bb8a46002f1777b3ae39e750a79099872fe10630`.

This is the one completed fresh whole-branch code review. The original assigned reviewer stopped at an account/model usage limit without delivering its whole-branch verdict; this review replaces that incomplete attempt. It is not a second review of a fix pass. The two findings passed on from that attempt were independently reproduced here. No subagents were used. Only this report was written; production code, source data, index, HEAD and branch state were left unchanged.

The review used SPEC.md, PLAN.md (especially Review Focus), ARCHITECTURE.md, API.md, the progress ledger and its Ruling entries, the supplied `review-31eeea2..af8341d.diff`, the final `af8341d..bb8a460` delta, and current implementation/test sources. Passes covered the portable configuration contract, Store/API and existing attachment publication, backup/query/capture integration, web editor and bounded presentation ownership, native editor/AppGroup persistence, sync semantics and acceptance tooling.

## Strengths

- Preferences are real optional resource data. Python, JavaScript and Swift share bounded versioned values; absent/null automatic values and opaque future versions are supported without a schema 3, ZIP manifest 2 or sync protocol 1 bump. Unknown keys survive normalization and exchange. Original resource titles remain separate from cover text.
- `CoverOperations.update_cover` and `LibraryFiles.updateCover` compare the two relevant field baselines under the existing storage lock/coordinator, merge unrelated current fields, reuse intact same-resource bytes, and clean up newly published paths on ordinary transaction/write failure. Upload verification is performed before the Store lock. Identical retries avoid another attachment and avoid an unnecessary native JSON rewrite.
- Integration reuses `coverId` and the existing ZIP remapping and raw-resource sync paths. The focused cases exercise actual bytes, restart, stale edits, rollback, legacy omission, explicit reset, future values, collision remapping and HTTPS exchange rather than relying only on renderer mocks.
- The gallery changes retain the incumbent window, Bits and Motion owners. Stable image nodes retain decode state while their crop styles update; custom cover titles are excluded from source-title search offsets. The HTML cache remains capped, and offscreen saves use the existing residency machinery rather than injecting another card or globally rebuilding the page.
- Recommendations are deterministic and content-scored, with exact known-host matches and explicit seed changes. Artwork uses escaped real fields and bounded excerpts. The native UI is SwiftUI and uses the existing AppGroup library, not a separate library or embedded editor.

## Issues

### Critical

None found.

### Important

1. **[P1] Keep the save operation owned until asynchronous presentation completes.**

   File: `desktop-app/static/cover-studio.js:45–47` (also the operation token at lines 40/44 and `close`/`open` at lines 37/59).

   `submit` clears `busy` before awaiting `onSaved`. The real callback, `applyCoverResource`, can await a query reload, particularly for an upload or updated-order view (`app.js:80`). Escape therefore succeeds during that await. A different resource/draft can then be opened, but the original completion still calls unconditional `close()` and discards the new draft. The token is checked before the await and is never rechecked afterward.

   Reproduction: delay `onSaved`; save resource A; resolve the save request while leaving `onSaved` pending; press Escape; open B and enter a custom cover title; resolve A's `onSaved`. B's dialog closes and its unsaved changes are lost. This exact sequence was reproduced using the actual editor module in JSDOM, with an asynchronous callback.

   Fix: retain operation ownership through `onSaved`, and check `dead`/the operation token again after every await before closing or displaying completion. Either keep all dismiss/open paths busy until completion, or explicitly permit navigation while ensuring an old completion can only close its own dialog generation. Add a delayed asynchronous `onSaved` case; the current editor test uses a synchronous callback and misses this window.

2. **[P2] A pending uploaded image overrides an explicit website source in both editors.**

   Files: `desktop-app/static/app.js:32`, `desktop-app/static/cover-studio.js:20`, `mobile-app/App/CoverStudio.swift:123`.

   The web preview uses any pending `blob:` image unless the selected source is `poster`. The native preview makes the same choice whenever a `pendingImage` exists and the source is not `poster`. Changing the source to `website` leaves the pending upload present, so the preview continues showing the upload even though the saved renderer will select the website image (or its fallback). The user saves a visibly different result from the one they approved.

   Reproduction: open a resource with a website thumbnail/cached website image; choose an uploaded image; then select 网站预览. The editor still shows the upload. Save/reopen displays the website image. With no available website image it changes to artwork instead. The actual web `preview` function was evaluated with `imageSource=website` and a pending blob: `ShijiBoard.cover` selected the website URL, while `preview` emitted the blob URL. The corresponding native branch was verified in source.

   Fix: resolve transient uploads under the same image-source policy as saved images. Use the pending image for local-image selection (and automatic selection if intended), but allow `website` and `poster` to use their selected sources. Keep preview resolution shared or explicitly equivalent across editor and saved display. Cover upload → website → save/reopen on web and native.

3. **[P2] Native code layouts silently discard the explicit subtitle control.**

   Files: `mobile-app/App/CoverStudio.swift:33`, `mobile-app/App/ShijiApp.swift:220–225`.

   `StudioPoster` suppresses the subtitle for every `developer/a` cover, including a nonempty user `customSubtitle`. The native original-V5 code branch also renders only a custom title and source code; it never renders `caption`/`customSubtitle`. The editor still exposes and persists the subtitle field in both cases. On desktop these same choices display an explicit subtitle, so syncing a valid preference can make the user's text disappear on the phone.

   Reproduction: on a code resource select 程序化海报, Developer, 构图 1; enter a distinct subtitle and save/reopen. The persisted subtitle is present but has no native `Text` branch. Selecting 原版 V5 for the same code resource also omits it. This is confirmed by the renderer conditions; no additional native UI run was performed for this finding.

   Fix: distinguish an omitted automatic excerpt from explicit custom text. Preserve the compact code composition when no custom subtitle exists, and provide bounded space for a nonempty custom subtitle in both native branches. Add a native rendering/foreground assertion for these two choices.

### Minor

None raised.

## Verification and compatibility audit

Review-only executions passed: 12 focused Python cover configuration/API/persistence cases and five focused Node groups (configuration, direction, artwork, editor, presentation). Two additional in-memory probes reproduced issues 1 and 2 without writing test/source files or using formal resources. An initial direct Python invocation lacked `PYTHONPATH=desktop-app` and failed during import; the corrected invocation passed. No heavyweight suite or new native foreground run was launched by this review.

The existing `desktop-app/dist/v64-full-tests.json` records exit 0 for all eight local gates: portable Python, Node, native Python, Swift/ZIP exchange, HTTPS sync, macOS build, gallery browser and cover editor browser. The associated Swift and HTTPS logs contain the real exchange assertions. These are existing acceptance results, not eight fresh executions by this reviewer, and their green status does not cover the sequences above.

The final QR-test delta only adds `usesCPUOnly=true` to the Vision request. It retains the rendered QR generation and the exact decoded-payload assertion. The prior native log records Vision Code 9 for a missing ANE model blob; the subsequent native partition passed. This is a proportionate host-test adjustment and does not certify ANE execution.

The explicit Review Focus audit found no additional blocker in field-level cover baselines, ordinary upload rollback/deduplication, attachment ownership, original-title separation, legacy omission/null/future retention, ZIP coverId remapping, raw sync conflict retention, window remount/cache invalidation, or reuse of existing focus/motion/layout owners. This is a code/targeted-test conclusion, not a claim of exhaustive device or performance acceptance.

## Recommendations

Fix the three issues in the planned single meaningful code-fix pass. Extend the smallest relevant tests to exercise asynchronous completion ownership, transient-versus-saved image resolution and explicit native code subtitles, then rerun affected gates. Preserve the existing source/schema/attachment architecture; these findings do not require a new protocol or data model.

## Declined to judge

- Comparative artwork quality, mobile visual polish and screenshot-by-screenshot acceptance: assigned to the separate visual review; this report judges renderer/control behavior and safety only.
- Quantitative 1K/5K/20K/50K speed, scroll timing and memory regression: assigned to the separate before/after performance matrix; no performance verdict is inferred from bounded code structures or green tests.
- Physical-iPhone foreground interaction, camera/photos permissions and real-device sync UX: outside this review's available executions; simulator/build/Foundation evidence does not certify them.
- The inherited V6.3 native first-detail 246 ms risk: explicitly retained by PLAN/ARCHITECTURE, with no claim that Cover Studio fixes it.
- Optional ANE QR execution on this host: unavailable model error is documented; CPU decoding preserves the test's payload contract and ANE runtime validation remains separate.
- Final candidate GitHub Actions/publication status: orchestration/final-delivery responsibility; no push, merge, publish or remote CI invocation was performed here.

## Assessment

**Ready to merge? With fixes.**

The persistence and compatibility architecture is sound at the reviewed boundaries, but an old save completion can discard a new draft, and two preview/control paths violate explicit user choices. Fix issues 1–3 and complete the separately assigned visual, performance and final acceptance reports before treating this candidate as fully accepted.
