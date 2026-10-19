# Cover preference API (candidate)

`POST /api/resources/{id}/cover` uses existing local-origin/Host protection. Request:

```json
{"config":{"version":1,"style":"editorial","template":"b","customTitle":"Cover only"},"coverId":"","expected":{"coverConfig":null,"coverId":""}}
```

`config` is null for explicit reset, or the bounded versioned object documented in ARCHITECTURE.md. Missing fields in a version1 object take canonical defaults. The original resource title is independent. `coverId` is the existing same-resource image attachment reference, empty if none. There is no new nested image reference.

Optional `upload` is `{name,mime,base64}`. PNG/JPEG/GIF/WebP bytes must pass existing actual-image structural verification, at most5MiB; JSON request retains existing12MiB cap. Image decoding/validation occurs before Store locking. Cancelled editor drafts do not reach this route. One transaction publishes the attachment and both preference fields; failure rolls back newly created bytes. An intact existing same-resource image with the same bytes is reused even with a different filename.

Both expected fields are required: null represents an absent/automatic config. On unrelated source-title/notes/category edits the cover update merges only its fields. Stale cover values produce409 with existing `resource` and `conflicts`; an identical committed retry returns `{resource,changed:false}` without another attachment/write. Invalid body/image/config returns400, forbidden origin403, unknown method404. The client must reconcile an uncertain network response against persisted resource state or safely retry the identical guarded operation.

Future config versions are bounded and round-trip opaque. This route allows unchanged future preferences or explicit null reset, and refuses accidental replacement with version1. Original V5 is their safe visual fallback. Full resource reads/exports/summaries carry the optional payload property; omission by old partial writers preserves it. Explicit null is the reset tombstone. SQLite user_version3, ZIPmanifest2 and syncprotocol1 are unchanged.

## Desktop editor and update boundary

Resource details → 封面设计. Draft controls and file reads remain local; thumbnails are static. The modal offers five families plus Auto/originalV5, three layouts, palettes/custom color, independent text/position/density, actual attachment/website/poster source, fit/fill/focal coordinates, explicit regenerate, reset and gallery-sized preview. Cancel/ESC discards; Save protects its in-flight state. Failed writes retain the draft and exact original field baseline. On a dropped response the client checks persisted config and selected image hash before proposing retry.409 offers an explicit load-latest action.

Saved presentation replaces only that resource in existing state/cache, updates its mounted stable article, detail image and existing three-item deck, and reuses existing gallery/Bits layout. Offscreen changes do not inject extra cards. New actual images or concurrent source changes can change filter membership, and updated sorting changes order; those use the canonical query refresh. Cursor/selection revision is never forged. Custom cover text does not receive unrelated source-title search highlight offsets.

Actual isolated browser acceptance: persisted save/cancel, dropped response reconciliation, malformed image rejection, decoded-file cancel without upload, upload/focal/fit, poster without attachment deletion, reset, reload, stable nodes, narrow layout and screenshots. Existing real-gallery browser regression also passed. This is browser acceptance, not native iPhone acceptance.

## Native implementation

The iPhone detail view exposes the same independent editor through a native SwiftUI Form. It pins the opening resource as its field baseline and uses `LibraryFiles.updateCover` under the existing AppGroup coordinator. Upload selection is draft-only; local decode is bounded and asynchronous. Unknown values, reset and hash deduplication use the same contract. System navigation, sharing, QuickLook, sync and import are preserved. Native success feedback follows actual persistence and is a lightweight status, not a blocking confirmation.
