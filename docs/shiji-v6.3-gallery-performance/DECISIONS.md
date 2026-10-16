# Execution decisions and deferred review finding

These decisions preserve the requested isolation and evidence standard. They are recorded in order; native acceptance is not inferred from automated tests.

- Ruling: User requests full direct implementation and actual remote Actions; execute inline without plan approval pause and push only this isolated candidate to trigger CI. Cost if misunderstood: independent candidate published; no main/shared branch changes.

- Ruling: Task2 uses isolated automated Chrome tests/profiling as explicitly requested by user (actualDOM regressions/ChromePerformance), with a fresh temporary browser profile; never attach real browsing profile. CUA remains for live/native interactions. Add Playwright only as devDependency because CI must execute real layout, not JSDOM geometry; apppackaging excludes node_modules. Cost: dev test install/browser download, no app runtime dependency.

- Task6 Ruling: Dispatch the required one fresh whole-branch review while the final quiet performance matrix runs; shipping changes were complete at245639d, no browser/build/test allowed for reviewer. Cost if wrong: documentation may need an executor-only acceptance update; no duplicate review seat. Reviewer gpt-6-astra read-only returned two Important interaction races, one Minor fallback edge; both Important findings enter the one RED→GREEN fix pass after the matrix.

- Final: minor (deferred): positive-width but zero-card-measurement secondary no-geometry fallback can leave the grid empty; normal zero-layout tests are gated before controller creation and actual supported CSS geometry is measured. Documented in REPORT; dedicated fallback support remains future work.

- Final: Ruling: Native246ms detail latency remains unresolved; preserve actual native sample and original investigation rather than claim a gallery fix. Cost: native detail responsiveness remains imperfect.

- Final: Ruling: Reviewer did not certify ongoing scale/native/CI/report evidence; executor must finish these checks and qualify missing ones. Cost if wrong: overstated acceptance, mitigated by raw revision/visibility/round provenance.

- Final: Ruling: Keyboard Tab coverage does not certify VoiceOver virtual cursor traversal; retain explicit manual accessibility item. Cost: assistive browsing beyond mounted nodes still requires actual verification.

- Final: Ruling: BFCache restoration was considered but eligibility was not established; do not issue speculative fix or claim browser-back coverage. Cost: a cache-eligible embed would need a restoration-specific test.

- Final: Ruling: List/board windowing stays out of scope and keeps the existing local rendering path. Cost: those views retain their accumulated DOM scaling limit.

- Final: Ruling: Revision-conflicted selections may remain visible while the server rejects stale writes; keep existing safety behavior. Cost: user must refresh/reselect after a conflict, no silent mounted-only bulk operation.

- Final: Ruling: Final-report completeness is executor acceptance work, not certified by read-only code review. Cost if wrong: incomplete delivery; keep checklist and verified evidence explicit.
