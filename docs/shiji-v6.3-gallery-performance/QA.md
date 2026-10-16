# Reproduce the isolated acceptance

Run from the repository root. No command below points at a normal library. QA fixture manifests and credentials live only under system temporary directories. The fixture copies use real Store records and real local attachments; the application is the actual V5 page and query API, not a separate mock component.

## Functional and CI checks

`python3 desktop-app/tests/run-ci.py --suite portable`

`npm --prefix desktop-app test`

`SHIJI_QA_VIDEO=1 python3 desktop-app/tests/run_gallery_browser.py`

`python3 docs/shiji-v6.3-gallery-performance/qa/mutation_pressed.py` must reject removal of the press fence at the exact single-click name-sort assertion; unrelated failures do not qualify.

The browser regression starts its own ephemeral HTTP service, uses a new browser profile, and verifies real CSS geometry, bounded mounting after 1020 summaries, pointer-down/edit/pointer-up, keyboard movement beyond mounted boundaries, detail cancellation, focus/scroll return, missing covers, fit ratios, responsive widths, all-match selection, search, list/board fallback, Reduced Motion and immediate saved-card opening. A development browser installation is required; see the browser job in `.github/workflows/tests.yml`. Videos and raw screenshots are emitted to ignored `desktop-app/dist/v63-browser-regression*` and uploaded by Actions, never packed into the app.

The existing native, Swift exchange and HTTPS test commands are unchanged; the native CI job and `CI.md` identify their runners. Automated DOM tests cannot certify physical touchpad, sleep/wake or VoiceOver behavior.

## Scale comparison

1. The fixtures reuse the disposable V6.2 dataset manifest `/tmp/shiji-v62-after.json`. On a clean machine, first run `python3 docs/shiji-v6.2-search-scale/qa/baseline.py` and `python3 docs/shiji-v6.2-search-scale/qa/measure.py` to recreate that manifest (these are substantial isolated Store benchmarks). Then `python3 docs/shiji-v6.3-gallery-performance/qa/prepare_fixtures.py` copies and decorates those disposable 1K/5K/20K/50K libraries. Some rows intentionally belong to Trash; active counts are 941/4705/18823/47058.
2. `python3 docs/shiji-v6.3-gallery-performance/qa/run_matrix.py --phase before` serves an immutable archive of 579d447.
3. Close the owned QA native app and avoid builds/tests while measuring. Run the same command with `--phase after`. The server creates a new copy for every dataset and binds an ephemeral port. Capture workers are not started. Never substitute a formal data path.
4. `python3 docs/shiji-v6.3-gallery-performance/qa/summarize.py` validates completed rounds and emits round-level compact evidence and a median table. Individual raw artifacts include actual counts, browser versions, hidden/focus flags, input→render→double-rAF milestones, request parsing, Server-Timing, style/layout/script and JS heap. Do not relabel rAF as compositor FPS.

The browser driver resumes only completed, non-interfered rounds. Use a fresh output prefix or `SHIJI_QA_FRESH=1` after changing product source or probe methodology. `SHIJI_QA_TRACE=1` captures a separate instrumented diagnostic; never mix it into untraced medians. `SHIJI_QA_PROCESS_SAMPLER` accepts the compiled existing process sampler and records only the launched QA browser's process IDs. Physical footprint, RSS and JS heap are different quantities. A missing measure is unavailable, not zero.

## Native

`python3 docs/shiji-v6.3-gallery-performance/qa/native.py --size 5000 [--before]` builds a separately identified QA shell. It copies only the fixture DB/files, assigns random service ports, removes URL handlers, uses separate preferences/credentials, and never opens the installed app's library. The QA-only WebContent PID diagnostic does not modify shipping Swift source.

Launch one QA app at a time. A native foreground sample requires `document.hidden=false`; an accessible background window does not qualify. The injected “QA · 原生对照运行” is explicitly automated DOM clicks and programmatic scrolling. Physical coordinate clicking and its recording are separate evidence. Read `runtime-events.jsonl` and its rotated predecessor from the manifest's disposable data directory. Compile the existing physical-footprint sampler with `xcrun clang docs/shiji-v5.1/qa/process_sample.c -o /tmp/shiji-v63-process-sample`; start `qa/watch_native.py MANIFEST OUTPUT` before clicking the scenario button to capture the actual identified Host/WebContent/backend during each 30-second idle scene. Keep large recordings and Instruments traces in ignored dist or CI artifacts. The existing V5.2 native detail long-frame investigation remains open.

## Recovery and rollback

No database, exchange, backup or sync structure changes. Removing the gallery-window script and its existing Bits/app integration restores the prior DOM path; no data rollback is required. A missing-layout/JSDOM environment and list/project-board explicitly retain legacy rendering. Windowing limits DOM for loaded grid summaries; geometry still grows with summaries loaded by existing pagination, and list/board are not newly virtualized.
