# Resource Query API v1

All routes use the existing local Host/Origin validation. Invalid input is 400; a stale cursor/selection is 409 with a user-readable error. No pairing/sync credentials or protocols change. Existing resource/capture/backup endpoints remain available.

## GET /api/library

Returns `queryVersion:1`, `version:3`, monotonic local `revision`, counts for all/favorite/inbox/assets/snippets/trash, category/tag/project/smart collection counts, collections/collectionMeta/smartCollections and `search` capabilities. Search capabilities include `fts5`, `tokenizer`, `version`, `derived`, `indexing`, `pending`. `version:3` is existing resource compatibility; search index version is separate.

## POST /api/query

Example request:

```json
{"scope":"all","scopeValue":"","filters":{"search":"React 动效","tags":["组件"],"collection":"创作"},"sort":"relevance","limit":60}
```

Scopes: all, favorite, inbox, assets, snippets, trash, category, collection, smart, health. Existing normalized filters cover category/kind, AND tags, project descendants, price/license/linkStatus, notes, file/media, source domain, UTC inclusive date range and nearby resource/attachment colors. Category/collection/smart defaults apply when `filters` is omitted. An explicitly supplied filters object represents edited current conditions and may remove original defaults.

Sorts: relevance, new, updated, name; each ends with stable ID. Search accepts at most 200 Unicode characters, case-insensitive literal substring terms joined with AND; paired double quotes group phrases. SQL/FTS operators are never interpreted from user text. Empty search retains current filters. `limit` is 1–100 (default60).

Response: `resources` summary array, `total`, `revision`, `nextCursor`, `previousCursor`, `terms`, `kindCounts`. Send the unchanged query and returned cursor to continue. Cursors are signed, bound to canonical query and revision; on 409 restart from page one rather than appending mismatched data. `anchor:resourceId` opens its page; `edge:"last"` obtains the last page. `mediaOnly:true` and `projection:"media"` support the existing ordered attachment gallery.

Summaries carry `_summary:true`, attachmentCount, bounded display fields, at most eight attachment previews plus selected cover, `_excerpt` and Unicode-code-point `_highlights`. Media projection retains owner attachment metadata. Never send a summary to authoritative resource save; fetch full details before editing. Backend rejects summary replay.

## Detail and bounded lookups

- `GET /api/resources/:id`: full existing resource plus minimal parent/children titles.
- `POST /api/resources/summaries`: `{ids:[...]}`, maximum500 IDs; optional media projection.
- `POST /api/resources/lookup`: `{url:"https://example.com/..."}`; normalized exact active URL, returns full resource or null. Used only to reconcile uncertain capture results, not fuzzy search.

## Full-match selection

`POST /api/query/ids` accepts the query and returns **all** matching IDs (maximum100,000) plus revision, independent of current page. Optional `linksOnly:true` narrows to link checking candidates. Selection order is stable ID, not ranked presentation order.

`POST /api/query/organization` accepts selected IDs and revision; returns tags/projects membership projections, tag counts and collection tree. No full code/notes transfer.

`POST /api/query/batch`:

```json
{"operation":"batch","revision":123,"body":{"ids":["resource-uuid"],"action":"organized"}}
```

Operations: batch, tags, projects, removeProjects. Each delegates to existing business writers and validates revision **inside** their existing atomic write transaction. Stale selection causes no partial action. Existing legacy API limits are retained; guarded query operations allow up to100,000 selected IDs.

## Search UI

120ms input debounce, AbortController plus request epochs, lightweight busy/indexing/error feedback, title/detail text-node highlights, relevance/time/name sorting and exact total. Cmd/Ctrl+K focuses search. ArrowDown enters results; Enter opens the first current result, then existing card keyboard navigation selects other results. Escape clears search, then exits focus. Last eight queries remain local. Current filters combine with the query; recent history is never synchronized.
