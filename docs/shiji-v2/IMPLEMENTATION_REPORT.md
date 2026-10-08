# SHIJI V2 implementation report

## P0 — baseline
Clean main at `488d39e`, created `feat/shiji-v2-motion-ui`. Kit extracted without replacing existing source. Python: **197 passed** (28.499s); Node: **32 groups passed**; native core + desktop ZIP interop: **passed**. All tests use temporary stores. QA service uses independent temporary `shiji-v2-qa-*` data and OS-selected port; no production library or credentials accessed.

## P1 — desktop visual integration
Files: `static/shiji-v2.css`, `static/shiji-v2.js`, `static/index.html`, `static/app.js`, `tests/test_shiji_v2.js`, existing browse-window test loads the new presentation dependency.
Independent final theme layer, approved dark/lime/violet Hero and ticker, contextual Hero visibility, real resource card types, retained business IDs, two-column masonry, compact navigation at 1279px. No demo data imported into business logic. QA fixture contains six explicitly marked test records.
Validation: baseline Python/native unchanged; Node **33 groups passed**. Real browser opened the ephemeral QA service; screenshot `evidence/p1-desktop.png`. Browser reports no document horizontal overflow. macOS was initially locked; in-app browser became available after continuing. Native UI inspection pending.
Limit: motion controls are wired in P2; no P2 behavior is claimed here. Responsive and full feature matrix continues in P5.

## Pending stages
P2 motion lifecycle → P3 native visual integration → P4 persist-first capture → P5 complete regression and visual acceptance.

## Rollback
Local stage commits can be reverted in reverse order. Database schema 3 and ZIP manifest 2 remain unchanged. Do not point a QA build at the production library.
