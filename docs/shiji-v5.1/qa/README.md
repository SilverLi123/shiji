# V5.1 isolated acceptance tools

These are opt-in QA tools; normal HTML and App.swift do not load them. Run from repository root after installing the existing development test dependencies. All fixtures are explicitly labelled QA, saved by the real Store. No formal database, fixed service port or real pairing credentials is used.

```sh
python3 docs/shiji-v5.1/qa/web.py --count 1000
python3 docs/shiji-v5.1/qa/web.py --count 1000 --baseline
python3 desktop-app/desktop/build.py
python3 docs/shiji-v5.1/qa/make_native.py --count 1000 --tag v51
```

The server prints only its disposable root/count/random loopback port. Native generation prints its copied bundle, random port and temporary data directory. Use the approved CUA interface to launch/select that exact App and perform actual actions, one QA App at a time. `--baseline` serves the d7a6749 scripts. `--ab` modifies only the QA response for exploratory no-blur/no-ghost/no-stagger/stable-gutter comparisons; none is a production fix. `make_native.py` copies and compiles an instrumented ad-hoc QA App; WKWebView private process-ID introspection and the activation/profile button are confined to this copy. Do not ship the QA copy.

The ordinary runtime diagnostics whitelist forwards bounded timings/counts/phase metadata. `trace.js` measures detail endpoints, cloning, HTML, animation setup and first RAF callbacks. Its optional metadata-race button updates only a chosen QA record via the real API during the next pointer press. It is not a replacement renderer or data model. Normal builds never load it. The real capture regression is separately automated in `tests/test_v3_foundation.py` and `tests/v51_capture_click.cjs`.

Compile the process and recording helpers:

```sh
clang -O2 docs/shiji-v5.1/qa/process_sample.c -o /tmp/shiji-v51-process-sample
xcrun swiftc -parse-as-library docs/shiji-v5.1/qa/record.swift -o /tmp/shiji-v51-record
xcrun swiftc -parse-as-library docs/shiji-v5.1/qa/verify_video.swift -o /tmp/shiji-v51-verify-video
```

Read the positively identified QA host, owned Python and WKWebView WebContent PID before sampling. Process helper usage is `helper 30 HOST_PID WEB_PID PYTHON_PID`; it records 31 rows across 30 seconds. Recording helper usage is `helper HOST_PID ABSOLUTE_OUTPUT.mp4 SECONDS`; it records only the QA window named “拾集 · 开发资源库”, no audio/cursor. A successful `recording-finished` result and readable video are required; compilation alone is not recording verification.

The verification helper accepts `ABSOLUTE_VIDEO.mp4 ABSOLUTE_FRAME_PREFIX` and decodes frames at 0/8/16/24 seconds, printing actual track dimensions/duration/nominal capture rate. Use a recording longer than24 seconds; its decoded frames verify that the artifact contains real changing UI. Capture rate is not a displayed application FPS measurement.

Wait for compilation/tests to finish, use QA · Activate / Profile, and leave the App foreground without UI-tree reads or captures for 30 seconds. Repeat Studio/3D and Calm/Flat. Keep raw process rows, runtime events and profile-end data. Report RAF callback gaps rather than claiming displayed FPS. Real sleep/wake and physical-input limits must be explicit.
