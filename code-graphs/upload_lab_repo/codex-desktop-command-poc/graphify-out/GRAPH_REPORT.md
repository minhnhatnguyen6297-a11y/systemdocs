# Graph Report - D:\systemdocs\code-graphs\upload_lab_repo\codex-desktop-command-poc  (2026-09-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 792 nodes · 1920 edges · 38 communities (32 shown, 6 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 294 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `38582d51`
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
- Community 35

## God Nodes (most connected - your core abstractions)
1. `UploadLabMainWindow` - 89 edges
2. `NamDinhUploaderSession` - 81 edges
3. `UploadWorker` - 29 edges
4. `PlaywrightUploaderQueueTests` - 28 edges
5. `extract()` - 27 edges
6. `run_batch_scan()` - 24 edges
7. `QtUIStructureTests` - 24 edges
8. `analyze_contract_book()` - 24 edges
9. `CommandRegistry` - 21 edges
10. `UploadLabExtractContractTests` - 20 edges

## Surprising Connections (you probably didn't know these)
- `_raw_excerpt()` --calls--> `read_docx()`  [INFERRED]
  review_regex_samples.py → extract_contract.py
- `_review_file()` --calls--> `extract()`  [INFERRED]
  review_regex_samples.py → extract_contract.py
- `extract_one_file()` --calls--> `extract()`  [INFERRED]
  folder_workflow_service.py → extract_contract.py
- `_canonical_contract_no()` --calls--> `normalize_contract_no_for_compare()`  [INFERRED]
  scan_classification_service.py → playwright_uploader.py
- `lookup_exported_contract_no()` --calls--> `normalize_contract_no_for_compare()`  [INFERRED]
  web_list_service.py → playwright_uploader.py

## Import Cycles
- None detected.

## Communities (38 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (62): _append_docx_body_lines(), _append_party_display(), _append_table_lines(), _append_text_lines(), _build_payload_generic(), _clean_title_line(), _dedupe_preserve_order(), _detect_document_kind_and_title() (+54 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (43): Any, Queue-only adapter around UploadWorker's public slots and Qt signals.      This, UploadWorkerBridge, CommandError, CommandRequest, Job, Any, utc_now() (+35 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (38): Connection, append_error(), choose_folder_via_dialog(), collect_batch_files(), connect_registry(), emit_progress(), ensure_registry_schema(), fetch_registry_records_for_run() (+30 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (4): NamDinhUploaderSession, PreparedBrowserTab, Launch/probe the login page while retaining the same browser session.          T, UploadRecord

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (28): _parse_export_date_input(), ContractBookAuditTests, Path, _FakeSelectLocator, _allowed_years(), analyze_contract_book(), _annotate_missing_numbers(), _build_missing_numbers() (+20 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (26): UploaderSettings, EnvironmentCheckServiceTests, _check_dependencies(), _check_disk_space(), _check_network(), _check_operating_system(), _check_proxy(), _check_workspace() (+18 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (9): EnvironmentCheckWorker, FolderScanWorker, Path, Called only by the dedicated Playwright thread., Run non-Playwright pre-login checks away from the Qt event loop., Run every Playwright call on one normal Python thread.      Playwright's synchro, Safe to call directly from the GUI thread., UploadWorker (+1 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (19): mark_records_uploaded_success(), now_iso(), update_registry_record_by_id(), append_log_line(), build_requester_lookup_keys(), build_upload_form_data(), _extract_lookup_year(), _format_requester_person() (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.16
Nodes (6): extract(), find_tai_san(), make_docx(), make_docx_with_blocks(), Path, UploadLabExtractContractTests

### Community 9 - "Community 9"
Cohesion: 0.25
Nodes (23): ArgumentParser, approve_corpus(), _changed(), cluster_id_for(), _excerpt(), _extractor_fingerprint(), _fold(), _golden_records() (+15 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (3): UploadLabMainWindow, open_with_windows_default(), FluentWindow

### Community 11 - "Community 11"
Cohesion: 0.17
Nodes (4): QtUIStructureTests, FolderScanRow, ScanClassification, QApplication

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (10): FakeRecord, ScanClassificationServiceTests, ContractBookAnalysis, _allowed_years(), _canonical_contract_no(), classify_scan_records(), _excel_contract_nos(), _folder_contract_issue() (+2 more)

### Community 14 - "Community 14"
Cohesion: 0.30
Nodes (19): CompletedProcess, _current_process_uses_venv(), ensure_dependencies(), ensure_runtime_layout(), ensure_venv(), get_python_identity(), is_python_compatible(), launch_ui() (+11 more)

### Community 15 - "Community 15"
Cohesion: 0.22
Nodes (13): _default_uploader_env_values(), download_contract_book_export(), ensure_uploader_env_file(), _format_env_value(), get_uploader_setup_status(), load_uploader_settings(), _normalize_env_value(), Path (+5 more)

### Community 16 - "Community 16"
Cohesion: 0.24
Nodes (9): Path, WebListServiceTests, ContractListRow, ContractLookupResult, find_missing_contract_numbers(), lookup_exported_contract_no(), MissingContractNo, Path (+1 more)

### Community 17 - "Community 17"
Cohesion: 0.16
Nodes (12): color_hex(), dump_widget(), load_offscreen_fonts(), main(), Path, run_qt_app(), _application_font(), apply_theme() (+4 more)

### Community 18 - "Community 18"
Cohesion: 0.21
Nodes (3): row(), UploadSelectionServiceTests, UploadSelection

### Community 19 - "Community 19"
Cohesion: 0.35
Nodes (5): get_row_by_id(), load_upload_queue(), make_output_json(), PlaywrightUploaderQueueTests, Path

### Community 20 - "Community 20"
Cohesion: 0.28
Nodes (11): main(), Path, _raw_excerpt(), _review_file(), _review_flags(), run_review(), _write_csv(), _write_xlsx() (+3 more)

### Community 21 - "Community 21"
Cohesion: 0.20
Nodes (7): default_export_from_date(), default_export_to_date(), configure_audit_table_scrollbars(), QTableWidget, set_checkable_upload_rows(), set_table_rows(), QTableWidgetItem

### Community 23 - "Community 23"
Cohesion: 0.16
Nodes (3): _FakeBrowserForContext, _FakeChromiumForContext, _FakeTrackedPage

### Community 24 - "Community 24"
Cohesion: 0.29
Nodes (10): cancelButton, formatJob(), isTerminal(), TERMINAL_STATUSES, output, pollUpload(), render(), scanButton (+2 more)

### Community 25 - "Community 25"
Cohesion: 0.30
Nodes (3): make_docx(), Path, RegexLabTests

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (10): devDependencies, electron, main, name, private, scripts, start, test (+2 more)

### Community 27 - "Community 27"
Cohesion: 0.27
Nodes (3): QTableWidget, QWidget, QComboBox

### Community 29 - "Community 29"
Cohesion: 0.36
Nodes (8): finalize_uploaded_records(), extract_one_file(), finalize_selected_records(), load_queue_state(), load_selected_queue_records(), Path, QueueState, records_to_rows()

### Community 30 - "Community 30"
Cohesion: 0.44
Nodes (6): createClient(), SENSITIVE_KEYS, startElectron(), startSidecar(), validatePayload(), waitForSidecar()

### Community 31 - "Community 31"
Cohesion: 0.32
Nodes (4): field_value_matches(), _fold_value(), get_field_value_candidates(), read_exported_contract_numbers()

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (5): Experimental DesktopCommand loopback POC., Isolated proof-of-concept packages; not production application modules., Test package for standalone upload_lab repo., Shared UI services for Upload Lab., UI-facing service helpers.

## Knowledge Gaps
- **11 isolated node(s):** `name`, `private`, `type`, `main`, `test` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NamDinhUploaderSession` connect `Community 3` to `Community 32`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 10`, `Community 15`, `Community 19`, `Community 22`, `Community 23`?**
  _High betweenness centrality (0.298) - this node is a cross-community bridge._
- **Why does `UploadLabMainWindow` connect `Community 10` to `Community 34`, `Community 3`, `Community 6`, `Community 11`, `Community 12`, `Community 17`, `Community 18`, `Community 21`, `Community 27`, `Community 28`?**
  _High betweenness centrality (0.255) - this node is a cross-community bridge._
- **Why does `UploadWorker` connect `Community 6` to `Community 1`, `Community 3`, `Community 5`, `Community 10`, `Community 11`, `Community 28`?**
  _High betweenness centrality (0.131) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `UploadLabMainWindow` (e.g. with `QtUIStructureTests` and `.test_close_event_allows_close_when_no_scan_running()`) actually correct?**
  _`UploadLabMainWindow` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `NamDinhUploaderSession` (e.g. with `EnvironmentCheckServiceTests` and `.test_preflight_returns_browser_error_on_cp1252_console()`) actually correct?**
  _`NamDinhUploaderSession` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `UploadWorker` (e.g. with `create_worker_backed_registry()` and `_FakeUploadWorker`) actually correct?**
  _`UploadWorker` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `extract()` (e.g. with `_review_file()` and `.test_extract_does_not_fill_web_contract_no_from_short_form_only()`) actually correct?**
  _`extract()` has 19 INFERRED edges - model-reasoned connections that need verification._