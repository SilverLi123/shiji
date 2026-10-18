# Cover Studio 3.0 — audit and compatibility contract

Baseline:31eeea27547ae9c00a1c88212a5bbc2f70ed268f, fetched2026-10-18; clean linked worktree, newfeat/shiji-v6.4-cover-studio. V6.3 latest Actions38924079337 passed all5jobs. Fresh baseline portable282 and Node59 passed. Existing native246ms first-detail risk remains open; no assertion that this feature fixes it. All runtime tests use disposable Store/AppGroup roots, ephemeral ports and one-shot credentials.

## Incumbent audit

- `ShijiBoard.cover` chooses coverId→thumbnail→bundled fixed homepage capture. `preview()` combines real-image markup and `ShijiV5.coverMarkup` fallback; `attachImageFallbacks` preserves the fallback when loading fails. Static captures are not user attachments.
- V5's12poster compositions use real fields; `posterKind` mainly selects by host/category/keywords, one layout per kind. Original V5 remains a selectable renderer, not deleted or forked into a second cover engine.
- `ShijiBits` owns pack/FLIP/tilt, `ShijiMotion` owns artwork/detail motion, `ShijiCards` patches stable nodes. Gallery residency/height/cache belongs to `gallery-window.js`; pressed global updates are fenced. Cover editing must reuse these owners and invalidate only affected presentation.
- SQLite resources store extensible JSON payloads. `validate` merges existing data and preserves unknown fields. Guarded editing has an explicit field allowlist. Full ZIP2 carries whole resources and immutable attachments; restore remaps existing coverId. JSON intentionally omits attachment bytes and clears coverId.
- Phone `Resource.raw` and AppGroup JSON preserve unknown fields. Swift save merges fields with a guarded baseline; SyncMerge compares whole semantic payloads, preserves explicit conflicts and aliases resource IDs. Desktop protocol1 validates/merges raw fields in one revision-guarded transaction. No need to alter schema/protocol versions.
- Capture jobs compare resource revision and attachment/cover baseline before committing. Automatic changes merge current resource fields. A manual cover update must never re-authorize stale jobs or overwrite original title/category/tags.

## Resource extension, not a new model

Optional `coverConfig` resides in the existing resource payload. Missing/null means automatic. Saved configuration is explicit user preference; system recommendations and resolved presentation are derived, never authoritative database/index fields. No localStorage persistence of cover preferences.

Version1 bounded JSON object (maximum8KiB, depth4): style(auto/editorial/spatial/developer/kinetic/minimal/v5), template(auto/a/b/c), seed(uint32), palette(auto/acid/paper/violet/cyan/coral/ink), primary(empty or6-digithex), customTitle≤200, customSubtitle≤240, titlePosition(auto/top/center/bottom), density(balanced/compact/bold), imageSource(auto/image/website/poster), imageFit(fill/fit), imageX/imageY0…100. Defaults are canonicalized only when a preference is saved; old resources do not gain synthetic preferences. Unknown bounded keys round-trip. A future version is preserved opaque, rendered through original V5 and protected from accidental editing; explicit reset remains possible.

**No new attachment reference field.** Explicit attachment choice uses existing coverId, atomically with config. Full ZIP collision remapping and sync therefore keep working even in older clients that preserve unknown config. `imageSource=poster` hides the photo without deleting its attachment or coverId. `auto` keeps real cover priority; `website` may use the existing real thumbnail path. Actual downloaded images remain local attachments. JSON import loses local image bytes by existing design, preserves all typography/style settings and falls back safely when coverId is cleared.

Old clients preserve unknown payload keys. An old-client partial save omitting coverConfig must preserve the current value. New editor reset is explicit null/tombstone, not an omitted field. Swift semantic comparisons treat null/missing automatic consistently. No destructive migration; rollback to V6.3 retains preferences in JSON but displays its old cover rendering. Old-client editing during sync retains existing whole-resource conflict semantics; no silent field-wise auto-merge is invented.

## Local art direction

Extend the existing V5 renderer using a pure shared value module and scored rule catalog. Score actual title/description/tags/category/language/kind and exact known hosts; explanations are suggestions, not claims of AI understanding. Stable content features choose among three authored layouts in each of five families. Seed only varies within appropriate art direction and changes solely on explicit regeneration. No per-mount randomness, external API or copied Demo records.

Editorial: asymmetric type/grid, typographic stack, offset editorial frame. Spatial: orbital volume, exploded engineering planes, isometric construction. Developer: real terminal/code, repository monogram/technical specimen, split syntax diagram. Kinetic: typographic trails, orbit/tension, sequential strips. Minimal: photo-led crops and quiet poster fallback. Every face uses escaped actual data; absent metadata is omitted. Foreground automatically achieves≥4.5:1 against the chosen main background. Photography is real; geometric/texture material uses bounded CSS/SVG. Original V5 remains unchanged as a selectable style.

## Editing and atomic save

Operate-mode dialog workspace from resource details: central gallery-sized preview, left style/layout thumbnails, right appearance/text/image controls. Narrow view stacks preview before controls. Local draft/objectURL only until Save; cancel writes nothing, including uploads. Save is busy-guarded. POST `/api/resources/:id/cover` accepts config, coverId, exact field baselines and optional≤5MiB verified image upload. Reuse existing Store attachment writer, immutable publishing and hash deduplication in one transaction; compare preferences and coverId before commit, rollback newly published bytes on failure. Retry of an already committed identical choice is idempotent. Network uncertainty is checked against persistent state, not assumed failure or blind duplicate attachment creation.

On success update existing resource/cache references, the mounted article, affected detail preview and at most the existing three-item deck. No global app render per slider or cover save. Geometry uses the existing packer and stable IDs; presentation keys include resolved cover preference, cached image ratios invalidate safely, and scrolled anchor remains stable. Canonical query/revision rules still reject stale page/bulk writes; a query refresh is required only when cover changes alter an active filter/order's membership, not on each preview tweak.

## Cross-platform and acceptance

Python validates persisted preferences; Swift retains/validates the same bounded structure and renders an adapted native cover. Native controls save through guarded existing AppGroup resource methods, not embedded HTML. ZIP2 and protocol1 fixtures test customized config, attachment bytes, collisions, old payload omission/null, conflicts, restart and automatic metadata races. Native/device visual acceptance is separate from Foundation/HTTPS/build success.

Desktop/mobile screenshots cover13real-Store fixture classes and all15authored layouts, failed photos, longCJK, mixed titles, code/Prompt, editor save/cancel/reset, repeated changes, Calm/ReduceMotion, window remount and scrolled resize. Use1K/5K/20K/50K isolated datasets and the V6.3 benchmark/trace tools; record actual loaded/mounted counts and raw rounds, not a60FPS claim. Large recordings/traces stay ignored or in CI artifacts. Native foreground/device gaps remain explicit.
