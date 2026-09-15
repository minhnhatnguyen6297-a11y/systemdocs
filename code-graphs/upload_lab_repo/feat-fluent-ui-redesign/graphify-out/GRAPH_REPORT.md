# Graph Report - D:\systemdocs\code-graphs\upload_lab_repo\feat-fluent-ui-redesign  (2026-09-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 690 nodes · 1711 edges · 19 communities (18 shown, 1 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 251 edges (avg confidence: 0.76)
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

## God Nodes (most connected - your core abstractions)
1. `UploadLabMainWindow` - 89 edges
2. `NamDinhUploaderSession` - 81 edges
3. `PlaywrightUploaderQueueTests` - 28 edges
4. `extract()` - 27 edges
5. `UploadWorker` - 27 edges
6. `run_batch_scan()` - 24 edges
7. `QtUIStructureTests` - 24 edges
8. `analyze_contract_book()` - 24 edges
9. `UploadLabExtractContractTests` - 20 edges
10. `load_uploader_settings()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `_raw_excerpt()` --calls--> `read_docx()`  [INFERRED]
  review_regex_samples.py → extract_contract.py
- `_review_file()` --calls--> `extract()`  [INFERRED]
  review_regex_samples.py → extract_contract.py
- `extract_one_file()` --calls--> `extract()`  [INFERRED]
  folder_workflow_service.py → extract_contract.py
- `EnvironmentCheckServiceTests` --uses--> `UploaderSettings`  [INFERRED]
  test_environment_check_service.py → playwright_uploader.py
- `_canonical_contract_no()` --calls--> `normalize_contract_no_for_compare()`  [INFERRED]
  scan_classification_service.py → playwright_uploader.py

## Import Cycles
- None detected.

## Communities (19 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (17): default_export_from_date(), default_export_to_date(), probe_playwright_runtime(), Path, QTableWidget, QWidget, Run non-browser checks, then probe login in the shared browser thread., UploadLabMainWindow (+9 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (68): Connection, append_error(), choose_folder_via_dialog(), collect_batch_files(), connect_registry(), emit_progress(), ensure_registry_schema(), fetch_registry_records_for_run() (+60 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (16): get_row_by_id(), load_uploader_settings(), normalize_contract_no_for_compare(), read_exported_contract_numbers(), save_uploader_env(), split_records_by_existing_contract_nos(), _EmptyLocator, _FakeBrowserForContext (+8 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (61): _append_docx_body_lines(), _append_party_display(), _append_table_lines(), _append_text_lines(), _build_payload_generic(), _clean_title_line(), _dedupe_preserve_order(), _detect_document_kind_and_title() (+53 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (9): download_contract_book_export(), field_value_matches(), _fold_value(), get_field_value_candidates(), NamDinhUploaderSession, PreparedBrowserTab, Launch/probe the login page while retaining the same browser session.          T, UploaderSettings (+1 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (26): QtUIStructureTests, FakeRecord, ScanClassificationServiceTests, color_hex(), dump_widget(), load_offscreen_fonts(), main(), Path (+18 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (14): extract(), find_tai_san(), main(), _normalize_plain_text_for_extract(), Tim so cong chung trong noi dung file .docx hoac .doc.     .doc dung IFilter (nh, scan_docx_for_contract_no(), make_docx(), Path (+6 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (25): ContractBookAuditTests, Path, _allowed_years(), analyze_contract_book(), _annotate_missing_numbers(), _build_missing_numbers(), ContractBookDisplayRow, ContractBookIssueKind (+17 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (25): EnvironmentCheckServiceTests, _check_dependencies(), _check_disk_space(), _check_network(), _check_operating_system(), _check_proxy(), _check_workspace(), EnvironmentCheckStep (+17 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (9): EnvironmentCheckWorker, FolderScanWorker, Path, Called only by the dedicated Playwright thread., Run non-Playwright pre-login checks away from the Qt event loop., Run every Playwright call on one normal Python thread.      Playwright's synchro, Safe to call directly from the GUI thread., UploadWorker (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.25
Nodes (23): ArgumentParser, approve_corpus(), _changed(), cluster_id_for(), _excerpt(), _extractor_fingerprint(), _fold(), _golden_records() (+15 more)

### Community 11 - "Community 11"
Cohesion: 0.30
Nodes (19): CompletedProcess, _current_process_uses_venv(), ensure_dependencies(), ensure_runtime_layout(), ensure_venv(), get_python_identity(), is_python_compatible(), launch_ui() (+11 more)

### Community 12 - "Community 12"
Cohesion: 0.24
Nodes (9): Path, WebListServiceTests, ContractListRow, ContractLookupResult, find_missing_contract_numbers(), lookup_exported_contract_no(), MissingContractNo, Path (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.21
Nodes (3): row(), UploadSelectionServiceTests, UploadSelection

### Community 14 - "Community 14"
Cohesion: 0.28
Nodes (11): main(), Path, _raw_excerpt(), _review_file(), _review_flags(), run_review(), _write_csv(), _write_xlsx() (+3 more)

### Community 15 - "Community 15"
Cohesion: 0.30
Nodes (3): make_docx(), Path, RegexLabTests

### Community 16 - "Community 16"
Cohesion: 0.50
Nodes (3): Test package for standalone upload_lab repo., Shared UI services for Upload Lab., UI-facing service helpers.

## Knowledge Gaps
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NamDinhUploaderSession` connect `Community 4` to `Community 0`, `Community 1`, `Community 2`, `Community 8`, `Community 9`?**
  _High betweenness centrality (0.366) - this node is a cross-community bridge._
- **Why does `UploadLabMainWindow` connect `Community 0` to `Community 1`, `Community 4`, `Community 5`, `Community 9`, `Community 13`?**
  _High betweenness centrality (0.318) - this node is a cross-community bridge._
- **Why does `extract()` connect `Community 6` to `Community 1`, `Community 3`, `Community 14`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `UploadLabMainWindow` (e.g. with `QtUIStructureTests` and `.test_close_event_allows_close_when_no_scan_running()`) actually correct?**
  _`UploadLabMainWindow` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `NamDinhUploaderSession` (e.g. with `EnvironmentCheckServiceTests` and `.test_preflight_returns_browser_error_on_cp1252_console()`) actually correct?**
  _`NamDinhUploaderSession` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `extract()` (e.g. with `_review_file()` and `.test_extract_does_not_fill_web_contract_no_from_short_form_only()`) actually correct?**
  _`extract()` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `UploadWorker` (e.g. with `EnvironmentCheckServiceTests` and `.test_upload_worker_runs_preflight_on_browser_worker()`) actually correct?**
  _`UploadWorker` has 6 INFERRED edges - model-reasoned connections that need verification._