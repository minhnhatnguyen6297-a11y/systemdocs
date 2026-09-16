# Graph Report - code-graphs\shell\monorepo  (2026-09-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 451 nodes · 847 edges · 19 communities (18 shown, 1 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 122 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c207f693`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16

## God Nodes (most connected - your core abstractions)
1. `CommandError` - 43 edges
2. `el()` - 27 edges
3. `SidecarContractTest` - 24 edges
4. `_new_cmd()` - 19 edges
5. `Job` - 16 edges
6. `JobStoreTest` - 15 edges
7. `import_engine_module()` - 14 edges
8. `_db_session()` - 14 edges
9. `_result()` - 13 edges
10. `SidecarManager` - 13 edges

## Surprising Connections (you probably didn't know these)
- `_err()` --calls--> `error_object()`  [INFERRED]
  ../../../shell/sidecar/app.py → ../../../shell/sidecar/errors.py
- `submit_command()` --calls--> `validate_file_ref()`  [INFERRED]
  ../../../shell/sidecar/app.py → ../../../shell/sidecar/fileref.py
- `_preview()` --calls--> `CommandError`  [INFERRED]
  ../../../shell/sidecar/command_registry.py → ../../../shell/sidecar/errors.py
- `inspect_file()` --calls--> `existing_file()`  [INFERRED]
  ../../../shell/sidecar/command_registry.py → ../../../shell/sidecar/fileref.py
- `waiting_task()` --calls--> `CommandError`  [INFERRED]
  ../../../shell/sidecar/command_registry.py → ../../../shell/sidecar/errors.py

## Import Cycles
- None detected.

## Communities (19 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (45): awaitJob(), breakdownEl(), buildDocReviewView(), buildEngineView(), buildExcelWord(), buildOffice(), buildOverview(), buildSearch() (+37 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (41): description, devDependencies, electron, electron-builder, main, name, private, scripts (+33 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (42): engine_info(), engine_root(), import_engine_module(), _load_roots_file(), output_dir(), Engine roots — resolve duong dan repo con va import module engine that.  P6 (M, Thong tin cau hinh engine cho diagnostics — khong lo secret., Tra Path root cua engine hoac CommandError(engine_not_installed). (+34 more)

### Community 3 - "Community 3"
Cohesion: 0.16
Nodes (36): CommandError, Exception, Lỗi nghiệp vụ có cấu trúc — raise trong command handler., case_create(), case_get(), case_list(), _case_row(), customer_create() (+28 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (19): env_check(), inspect_file(), _notary(), _preview(), Command registry — handler nghiep vu cho desktopcommand.v1.  P4 co read-only c, Diagnostic command: progress + cancel + waiting semantics end-to-end., Diagnostic: vao waiting_user(review) roi tu resume sau wait_seconds.      Kiem, Diagnostic: checklist moi truong engine (MIN-32 §6 — env service). (+11 more)

### Community 5 - "Community 5"
Cohesion: 0.10
Nodes (13): error_object(), Structured error objects theo desktopcommand.v1 §4.  Flat snake_case codes khớ, CancelledByUser, Job, JobStore, _now(), Exception, Job registry in-memory theo desktopcommand.v1 §4-5.  Idempotency: command_id → (+5 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (17): { CommandClient }, crypto, _defaultOutputDir(), { EventEmitter }, freePort(), {
  HEALTHZ_TIMEOUT_MS,
  HEALTHZ_POLL_MS,
  RESTART_BACKOFF_MS,
  SHUTDOWN_GRACE_MS,
  CONTRACT_VERSION,
}, net, path (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (4): _free_port(), _new_cmd(), Contract conformance test cho sidecar desktopcommand.v1.  Chay: python test/te, SidecarContractTest

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (19): CANCELABLE_STATUS, ENGINE_STATE_LABEL, faceUnavailable(), G1_API, isTerminal(), jobDisplay(), moduleFace(), moduleHealth() (+11 more)

### Community 9 - "Community 9"
Cohesion: 0.15
Nodes (11): JobStoreTest, partial_bad(), partial_ok(), quick(), Unit test JobStore — cancel semantics + drain + partial breakdown.  Chay: pyth, Goi job.resume() tu thread khac sau delay — nhu engine nhan xong     buoc nguoi, resumer(), slow() (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (12): ALLOWLIST, HANDLERS, { listModules, moduleForCommand }, validateCommandArgs(), listModules(), moduleForCommand(), MODULES, { ALLOWLIST, HANDLERS } (+4 more)

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (9): Integration test: cac command P6 goi engine that (notary_v2/upload_lab).  Chay, MIN-69: scan/audit/env_check qua engine that (khong can browser)., Khong can engine: registry phu dung namespace da duyet., MIN-68: case/customer/property/participant/Word/Zalo qua engine that., Fixture: customer + property + case + participant → export .docx., _run(), TestNotaryAdapter, TestRegistryWiring (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (5): CommandClient, CommandHttpError, { CONTRACT_VERSION, SHELL_VERSION }, crypto, TIMEOUTS

### Community 13 - "Community 13"
Cohesion: 0.25
Nodes (4): { EventEmitter }, { JOB_POLL_MS }, JobTracker, TERMINAL

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (13): build, appId, directories, extraResources, files, productName, win, output (+5 more)

### Community 15 - "Community 15"
Cohesion: 0.22
Nodes (10): auth_boundary(), cancel_job(), _err(), get_job(), G1 shell sidecar — desktopcommand.v1 producer (FastAPI, loopback only).  Contr, Tim dict dang file_ref (co key 'path' kieu str) de validate scope/path     ngay, submit_command(), _walk_file_refs() (+2 more)

## Knowledge Gaps
- **73 isolated node(s):** `name`, `private`, `description`, `main`, `start` (+68 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CommandError` connect `Community 3` to `Community 2`, `Community 4`, `Community 5`, `Community 9`, `Community 11`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Why does `JobStoreTest` connect `Community 9` to `Community 3`, `Community 5`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `validate_file_ref()` connect `Community 2` to `Community 3`, `Community 15`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 39 inferred relationships involving `CommandError` (e.g. with `_preview()` and `waiting_task()`) actually correct?**
  _`CommandError` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Job` (e.g. with `CommandError` and `_run()`) actually correct?**
  _`Job` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `description` to the rest of the system?**
  _73 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.1099290780141844 - nodes in this community are weakly interconnected._