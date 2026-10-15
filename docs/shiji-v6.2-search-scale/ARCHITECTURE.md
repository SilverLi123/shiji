# Search architecture and compatibility

## Authority and optional data

`resources`, attachments and existing project tables remain authoritative. `PRAGMA user_version=3`, exported resource fields, ZIP manifest 2, mobile JSON and sync protocol 1 are unchanged. Existing `/api/resources`, `/api/trash`, export, capture and sync paths remain available.

Local `search_docs`, `search_fts`, `search_dirty`, `search_meta` tables are disposable. They do not enter JSON exchanges or sync resources. SQLite snapshots may contain them; archive restoration uses the existing manifest and canonical write operations. SQL triggers on resources/attachments only enqueue IDs and increment a monotonic library revision; they require no Python UDF or FTS extension, so older writers still work. Conditional insertion avoids SQLite UPSERT conflict-policy inheritance overriding trigger `OR IGNORE`.

A query flushes dirty IDs in 128-row atomic transactions, releasing the Store lock between chunks, then reads one consistent snapshot. Missing index tables and FTS-specific failures are repaired once; original resources are never deleted to repair an index. Missing rows are discovered at startup. `Store.rebuild_search()` recreates derived contents. A runtime FTS probe tests stock `unicode61` support. If absent, exact document scans preserve results; capabilities explicitly report this slower fallback.

## Chinese and code

Stock unicode61 treats contiguous Chinese as long tokens; trigram is optional and cannot alone cover one/two-character terms. The application emits ASCII Unicode unigram/bigram tokens into FTS5, then validates each literal term with `instr` against the complete lowercase source text. This retains substring, punctuation and mixed-language matches without passing user operators to FTS. Whitespace is AND; paired double quotes add phrase grouping. Maximum query length is 200 characters. SQL is parameterized. Unicode code-point highlight ranges are rendered using text nodes, never untrusted HTML.

Title exact/prefix/substring matches receive descending weights; all sorts end in stable ID. Name ordering is deterministic Unicode lowercase order rather than platform-dependent browser ICU collation. UTC dates preserve inclusive filter semantics. Search includes retained historical project notes and attachment name/author/source. Color matching includes resource and attachment palettes.

FTS candidates are materialized via a rowid subquery: joining the virtual table directly let SQLite choose repeated MATCH evaluation per resource on broad terms. Literal source verification is retained after this optimization.

## Query and selection consistency

Pages carry signed cursors bound to canonical filters/scope/sort and the library revision. Cursor offsets are valid only within that immutable revision; changes return HTTP 409 and restart browsing explicitly. No page from a different revision is appended silently. Deep offsets are measured; keyset cursors remain a possible later improvement if those measurements justify it.

A full-match ID query returns all matching IDs and the revision (maximum 100,000), not just visible rows. Guarded batch methods validate that revision inside their existing write transaction. Explicit project/tag selection reads only membership projections; it does not download all resource notes/code. Existing legacy endpoints retain their original limits.

List projections bound notes/code/description and attachment previews; full details are fetched before editing. The frontend must never replay a summary as a full resource. Global navigation counts and project ancestor counts come from server metadata. Pure-cover V5 cards, Hero and existing motion controllers are retained.

## Rollback / initialization

Use the previous application against schema 3; authoritative exchange fields remain identical. Leaving derived tables/triggers installed is safe and records old-client changes for later upgrades. To physically remove optional data in a maintenance window, drop only triggers whose names start `search_`, then `search_fts`, `search_docs`, `search_dirty`, `search_meta` and the `search_*` indexes. Do not drop canonical tables or change user_version. Next V6.2 launch initializes/rebuilds them. Never perform this maintenance against formal data as part of QA.

Index creation adds disk usage and cold-start work. Initial rebuild is not a claim of instant 50K search readiness; raw costs and fallback limitations are reported separately. Genuine raw SQLite database corruption is not treated as a disposable-index issue; existing backups/recovery remain the recovery route.
