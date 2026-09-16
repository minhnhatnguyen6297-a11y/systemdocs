# Graph Report - code-graphs\upload_lab\monorepo  (2026-09-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 874 nodes · 2070 edges · 39 communities (30 shown, 9 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 323 edges (avg confidence: 0.76)
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
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34

## God Nodes (most connected - your core abstractions)
1. `NamDinhUploaderSession` - 94 edges
2. `UploadLabMainWindow` - 90 edges
3. `PlaywrightUploaderQueueTests` - 31 edges
4. `UploadWorker` - 29 edges
5. `extract()` - 27 edges
6. `QtUIStructureTests` - 25 edges
7. `run_batch_scan()` - 24 edges
8. `analyze_contract_book()` - 24 edges
9. `load_uploader_settings()` - 23 edges
10. `CommandRegistry` - 21 edges

## Surprising Connections (you probably didn't know these)
- `_baseline_text()` --calls--> `read_docx()`  [INFERRED]
  ../../../upload_lab/poc/conversion_benchmark/harness.py → ../../../upload_lab/extract_contract.py
- `_raw_excerpt()` --calls--> `read_docx()`  [INFERRED]
  ../../../upload_lab/review_regex_samples.py → ../../../upload_lab/extract_contract.py
- `_review_file()` --calls--> `extract()`  [INFERRED]
  ../../../upload_lab/review_regex_samples.py → ../../../upload_lab/extract_contract.py
- `extract_one_file()` --calls--> `extract()`  [INFERRED]
  ../../../upload_lab/ui/services/folder_workflow_service.py → ../../../upload_lab/extract_contract.py
- `EnvironmentCheckServiceTests` --uses--> `UploaderSettings`  [INFERRED]
  ../../../upload_lab/tests/test_environment_check_service.py → ../../../upload_lab/playwright_uploader.py

## Import Cycles
- None detected.

## Communities (39 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (17): default_export_from_date(), default_export_to_date(), probe_playwright_runtime(), Path, QTableWidget, QWidget, Run non-browser checks, then probe login in the shared browser thread., UploadLabMainWindow (+9 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (9): download_contract_book_export(), NamDinhUploaderSession, PreparedBrowserTab, Return (cdp_session, window_id, window_state) for the shared Chromium window., Keep the visible browser tab on the contract-book list after an export., Launch/probe the login page while retaining the same browser session.          T, UploaderSettings, UploadRecord (+1 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (43): Any, Queue-only adapter around UploadWorker's public slots and Qt signals.      This, UploadWorkerBridge, CommandError, CommandRequest, Job, Any, utc_now() (+35 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (48): append_error(), choose_folder_via_dialog(), collect_batch_files(), connect_registry(), emit_progress(), ensure_registry_schema(), fetch_registry_records_for_run(), file_identity_key() (+40 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (62): _append_docx_body_lines(), _append_party_display(), _append_table_lines(), _append_text_lines(), _build_payload_generic(), _clean_title_line(), _dedupe_preserve_order(), _detect_document_kind_and_title() (+54 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (26): QtUIStructureTests, FakeRecord, ScanClassificationServiceTests, color_hex(), dump_widget(), load_offscreen_fonts(), main(), Path (+18 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (28): _parse_export_date_input(), ContractBookAuditTests, Path, _FakeSelectLocator, _allowed_years(), analyze_contract_book(), _annotate_missing_numbers(), _build_missing_numbers() (+20 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (25): EnvironmentCheckServiceTests, _check_dependencies(), _check_disk_space(), _check_network(), _check_operating_system(), _check_proxy(), _check_workspace(), EnvironmentCheckStep (+17 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (31): _baseline_text(), load_persistent_golden(), materialize_golden(), _provenance_status(), Any, Path, Read with the existing local stack only where an honest baseline exists., Create only synthetic inputs; callers keep the manifest/report outside productio (+23 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (9): EnvironmentCheckWorker, FolderScanWorker, Path, Called only by the dedicated Playwright thread., Run non-Playwright pre-login checks away from the Qt event loop., Run every Playwright call on one normal Python thread.      Playwright's synchro, Safe to call directly from the GUI thread., UploadWorker (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (7): extract(), find_tai_san(), main(), make_docx(), make_docx_with_blocks(), Path, UploadLabExtractContractTests

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (20): append_log_line(), build_requester_lookup_keys(), build_upload_form_data(), _extract_lookup_year(), field_value_matches(), _fold_value(), _format_env_value(), _format_requester_person() (+12 more)

### Community 12 - "Community 12"
Cohesion: 0.25
Nodes (23): ArgumentParser, approve_corpus(), _changed(), cluster_id_for(), _excerpt(), _extractor_fingerprint(), _fold(), _golden_records() (+15 more)

### Community 13 - "Community 13"
Cohesion: 0.10
Nodes (4): _FakeExportDateInputs, _FakeExportDialog, _FakeExportLocator, _FakeExportPage

### Community 14 - "Community 14"
Cohesion: 0.30
Nodes (19): _current_process_uses_venv(), ensure_dependencies(), ensure_runtime_layout(), ensure_venv(), get_python_identity(), is_python_compatible(), launch_ui(), load_setup_state() (+11 more)

### Community 15 - "Community 15"
Cohesion: 0.24
Nodes (9): Path, WebListServiceTests, ContractListRow, ContractLookupResult, find_missing_contract_numbers(), lookup_exported_contract_no(), MissingContractNo, Path (+1 more)

### Community 16 - "Community 16"
Cohesion: 0.21
Nodes (3): row(), UploadSelectionServiceTests, UploadSelection

### Community 17 - "Community 17"
Cohesion: 0.37
Nodes (5): get_row_by_id(), load_upload_queue(), make_output_json(), PlaywrightUploaderQueueTests, Path

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (3): load_uploader_settings(), _EmptyLocator, _FakeComboLocator

### Community 19 - "Community 19"
Cohesion: 0.28
Nodes (11): main(), Path, _raw_excerpt(), _review_file(), _review_flags(), run_review(), _write_csv(), _write_xlsx() (+3 more)

### Community 20 - "Community 20"
Cohesion: 0.29
Nodes (10): _default_uploader_env_values(), ensure_uploader_env_file(), get_uploader_setup_status(), _normalize_env_value(), Path, Update selected settings while stripping legacy username/password keys., read_uploader_env(), _resolve_tool_relative_path() (+2 more)

### Community 21 - "Community 21"
Cohesion: 0.29
Nodes (10): cancelButton, formatJob(), isTerminal(), TERMINAL_STATUSES, output, pollUpload(), render(), scanButton (+2 more)

### Community 22 - "Community 22"
Cohesion: 0.18
Nodes (3): _FakeAnchorPage, _FakeBrowserForContext, _FakeChromiumForContext

### Community 24 - "Community 24"
Cohesion: 0.30
Nodes (3): make_docx(), Path, RegexLabTests

### Community 25 - "Community 25"
Cohesion: 0.18
Nodes (10): devDependencies, electron, main, name, private, scripts, start, test (+2 more)

### Community 27 - "Community 27"
Cohesion: 0.44
Nodes (6): createClient(), SENSITIVE_KEYS, startElectron(), startSidecar(), validatePayload(), waitForSidecar()

## Knowledge Gaps
- **11 isolated node(s):** `name`, `private`, `type`, `main`, `test` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NamDinhUploaderSession` connect `Community 1` to `Community 0`, `Community 6`, `Community 7`, `Community 9`, `Community 11`, `Community 13`, `Community 17`, `Community 18`, `Community 20`, `Community 22`, `Community 23`, `Community 26`?**
  _High betweenness centrality (0.322) - this node is a cross-community bridge._
- **Why does `UploadLabMainWindow` connect `Community 0` to `Community 1`, `Community 5`, `Community 9`, `Community 16`, `Community 20`?**
  _High betweenness centrality (0.239) - this node is a cross-community bridge._
- **Why does `UploadWorker` connect `Community 9` to `Community 0`, `Community 1`, `Community 2`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `NamDinhUploaderSession` (e.g. with `EnvironmentCheckServiceTests` and `.test_preflight_returns_browser_error_on_cp1252_console()`) actually correct?**
  _`NamDinhUploaderSession` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `UploadLabMainWindow` (e.g. with `QtUIStructureTests` and `.test_close_event_allows_close_when_no_scan_running()`) actually correct?**
  _`UploadLabMainWindow` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `UploadWorker` (e.g. with `create_worker_backed_registry()` and `_FakeUploadWorker`) actually correct?**
  _`UploadWorker` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `extract()` (e.g. with `_review_file()` and `.test_extract_does_not_fill_web_contract_no_from_short_form_only()`) actually correct?**
  _`extract()` has 19 INFERRED edges - model-reasoned connections that need verification._