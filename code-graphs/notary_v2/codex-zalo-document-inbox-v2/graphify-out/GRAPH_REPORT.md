# Graph Report - D:\systemdocs\code-graphs\notary_v2\codex-zalo-document-inbox-v2  (2026-09-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1298 nodes · 3935 edges · 53 communities (51 shown, 2 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 663 edges (avg confidence: 0.75)
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
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 43
- Community 44
- Community 46
- Community 48
- Community 50

## God Nodes (most connected - your core abstractions)
1. `_clean_text()` - 54 edges
2. `ZaloConnectorAccount` - 50 edges
3. `_account()` - 48 edges
4. `ZaloBatch` - 45 edges
5. `Customer` - 44 edges
6. `CaseStatePayloadTests` - 44 edges
7. `ZaloSource` - 43 edges
8. `InboxValidationError` - 43 edges
9. `_customer()` - 43 edges
10. `AnalyzeImagesTests` - 42 edges

## Surprising Connections (you probably didn't know these)
- `FamilyTreeApp()` --indirect_call--> `person()`  [INFERRED]
  ReactFlowApp.jsx → diagram_edges.test.mjs
- `lifespan()` --calls--> `warmup_local_ocr()`  [INFERRED]
  main.py → ocr_local.py
- `stats()` --indirect_call--> `Customer`  [INFERRED]
  main.py → models.py
- `stats()` --indirect_call--> `InheritanceCase`  [INFERRED]
  main.py → models.py
- `calculate_diagram()` --indirect_call--> `Customer`  [INFERRED]
  cases.py → models.py

## Import Cycles
- None detected.

## Communities (53 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (117): AsyncClient, analyze_images(), analyze_property_images(), analyze_property_pair(), _append_ai_doc(), _ascii_text(), _call_qwen_native_ocr_single(), _classify_property_book_type() (+109 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (83): Căn cước công dân (trước 01/10/2024) hoặc Căn cước (từ 01/10/2024)., Bộ Công an (từ 01/10/2024) hoặc Cục CSQLHC về TTXH (trước đó)., Cư trú tại' (từ 01/10/2024) hoặc 'Thường trú tại' (trước đó)., _active_persons(), _add_block_placeholders(), _add_property_placeholders(), _add_word_person_group(), _apply_diagram_nodes() (+75 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (45): createZaloClient(), finalizeQrLogin(), handleMessage(), handleQrLoginEvent(), installCommandPoll(), installSourceSyncTriggers(), isParentAlive(), listenerHeartbeatState() (+37 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (61): BackgroundTasks, BaseModel, ZaloBatch, _as_iso(), batch_page(), _batch_root(), batch_snapshot(), _batch_unfinished() (+53 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (34): Customer, 01/07/2024 — ngưỡng phân biệt CCCD cũ/mới., Bảng lưu thông tin người (sống hoặc đã chết)., as_input_value(), consonant_skeleton(), create(), create_form(), delete() (+26 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (48): applyEngineResult(), assignPersonToNode(), backendCalculationCache, BASE_NODE_DEFS, bootstrapId(), BrickCard, bridgeWorkflowUpdates(), buildAssignedNode() (+40 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (38): Base, ZaloConnectorAccount, ZaloDataSyncRun, ZaloSource, PreviewItem, _app(), _manual_watcher_threads(), _signed_command_headers() (+30 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (38): _ack_version(), confirm_batch(), create_batch(), export_filename(), freeze_outputs(), InboxLimits, InboxTerminalError, InboxValidationError (+30 more)

### Community 8 - "Community 8"
Cohesion: 0.19
Nodes (41): ZaloMedia, ZaloMessageText, _account_or_error(), ack_policy(), ack_source_sync(), apply_intake_consent(), _canonical_digest(), ingest_message_envelope() (+33 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (41): _empty_result(), _error(), _fraction_text(), _parse_death_date(), _percent_text(), _person_id(), Any, date (+33 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (3): AnalyzeImagesTests, make_upload(), UploadFile

### Community 11 - "Community 11"
Cohesion: 0.14
Nodes (30): _build_temp_participants(), calculate_diagram(), _case_state_payload(), _clean_nullable_text(), _clean_text(), _coerce_bool(), _coerce_int(), create() (+22 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (7): DiagramPayloadValidationError, _normalize_case_state_json(), _parse_case_diagram_payload(), Exception, _resolve_v2_case_state(), DiagramPayloadParserTests, _payload()

### Community 13 - "Community 13"
Cohesion: 0.19
Nodes (5): update_diagram(), CaseStatePayloadTests, _customer(), _participant(), SimpleNamespace

### Community 14 - "Community 14"
Cohesion: 0.15
Nodes (26): _address_expected(), analyze_images_local(), _append_person_raw_text(), _apply_delta_merge(), _build_summary(), _clean_doc_number(), _collect_warnings(), _count_vietnamese_diacritics() (+18 more)

### Community 15 - "Community 15"
Cohesion: 0.12
Nodes (15): InheritanceCase, InheritanceParticipant, Bảng lưu những người tham gia hồ sơ thừa kế., Bảng lưu Hồ sơ thừa kế — trung tâm của hệ thống., detail(), list_cases(), lock(), unlock() (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.14
Nodes (39): apply_connector_report(), apply_data_sync_report(), InboxConflict, start_data_sync(), update_preview(), _data_sync_account(), _data_sync_report(), _data_sync_source() (+31 more)

### Community 17 - "Community 17"
Cohesion: 0.18
Nodes (20): home(), http_timing_log(), lifespan(), Request, stats(), Property, Bảng lưu thông tin Giấy chứng nhận quyền sử dụng đất (sổ đỏ)., create() (+12 more)

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (22): InheritanceCaseProperty, Lien ket nhieu tai san cho mot ho so., Luu cac file mau Word do nguoi dung tai len de xuat van ban., WordTemplate, activate_word_template(), api_activate_template(), api_delete_template(), api_upload_template() (+14 more)

### Community 19 - "Community 19"
Cohesion: 0.27
Nodes (13): CompareEngine, _Hit, Compare Word fields against OCR text corpus and emit audit issues., WordAuditDoc, WordField, _ocr_page(), _span(), test_case_insensitive_and_punctuation_normalized() (+5 more)

### Community 20 - "Community 20"
Cohesion: 0.25
Nodes (19): api(), bindPreview(), clearNotice(), createBatch(), notice(), previewPayload(), refresh(), refreshBatch() (+11 more)

### Community 21 - "Community 21"
Cohesion: 0.20
Nodes (16): _crop_box_image(), _detect_face_proxy(), _detect_qr_proxy(), _ensure_detection(), _get_face_cascade(), _make_proxy_image(), _mrz_likelihood_score(), _normalize_box_points() (+8 more)

### Community 22 - "Community 22"
Cohesion: 0.21
Nodes (10): classify_doc_type(), cut_at_notary_anchor(), detect_word_template_type(), extract_dates(), extract_id_numbers(), has_placeholders(), is_notary_page(), normalize_for_rules() (+2 more)

### Community 23 - "Community 23"
Cohesion: 0.14
Nodes (18): ExtractedDocument, Kho luu tru du lieu da boc tach sau khi user xac nhan., _analyze_image_prepare(), _build_qr_person_data(), _coarse_doc_type_from_profile(), confirm_save(), _detect_documents(), DocCrop (+10 more)

### Community 24 - "Community 24"
Cohesion: 0.27
Nodes (15): addKinship(), buildDiagramEdges(), buildKinshipEdges(), createIndex(), getKinshipFamilyKey(), hasNode(), hasSourcePerson(), idOf() (+7 more)

### Community 25 - "Community 25"
Cohesion: 0.21
Nodes (8): AuditIssue, AuditRunMeta, Path, Write JSON and Markdown reports for the audit run., ReportWriter, main(), parse_args(), Namespace

### Community 26 - "Community 26"
Cohesion: 0.16
Nodes (14): assert_foreign_key_check(), _ensure_table_columns(), get_db(), migrate_customers_nullable(), migrate_inheritance_case_properties_schema(), migrate_inheritance_cases_schema(), migrate_properties_schema(), migrate_zalo_schema() (+6 more)

### Community 27 - "Community 27"
Cohesion: 0.23
Nodes (9): ScanSource, Path, Collect supported scan/image/word files from a folder, ignoring temps and cache., ScanLoader, Path, sample_folder(), test_scan_loader_hashes_are_stable(), test_scan_loader_ignores_temp_excel_and_cache() (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.36
Nodes (13): _connector_runtime_error(), state_snapshot(), _aware(), connector_state(), data_sync_command(), _iso(), _parse_timestamp(), public_qr() (+5 more)

### Community 29 - "Community 29"
Cohesion: 0.13
Nodes (14): dependencies, zca-js, description, engines, node, name, private, scripts (+6 more)

### Community 30 - "Community 30"
Cohesion: 0.26
Nodes (12): configure_process_logging(), _ensure_handler(), _parse_log_level(), _delete_file(), _delete_path(), _ensure_worker_logging(), _ms(), _parse_json_array() (+4 more)

### Community 31 - "Community 31"
Cohesion: 0.18
Nodes (14): _ascii_fold(), _clean_name_candidate(), _extract_anchor_block(), _extract_date_after_label(), _extract_dates(), _extract_gender_from_text(), _extract_id_12_from_mrz_text(), _extract_id_12_from_text() (+6 more)

### Community 32 - "Community 32"
Cohesion: 0.20
Nodes (4): CacheStore, Path, Filesystem cache for page images and OCR text., CacheEntry

### Community 33 - "Community 33"
Cohesion: 0.25
Nodes (9): DocumentGrouper, Group sequential OCR pages into document spans using lightweight rules., DocType, DocumentSpan, MatchType, Severity, SourceKind, Enum (+1 more)

### Community 34 - "Community 34"
Cohesion: 0.17
Nodes (17): OCRJob, Tram kiem soat tien do OCR., _ensure_local_ocr_dependencies(), get_local_job_status(), _get_rapidocr_engine(), _get_rapidocr_recognizer(), _get_vietocr_engine(), _log_timing() (+9 more)

### Community 35 - "Community 35"
Cohesion: 0.18
Nodes (5): DetectorAndCropTests, FilterTargetBoxesTests, make_box(), MergeFlowTests, ParseFullTextTests

### Community 36 - "Community 36"
Cohesion: 0.27
Nodes (5): PDFSplitter, Path, Render PDF pages to images for OCR., Path, test_full_pipeline_without_ocr_api()

### Community 37 - "Community 37"
Cohesion: 0.42
Nodes (9): Parse .docx files into normalized fields for audit., WordParser, _make_docx(), Path, test_parser_drops_notary_clause(), test_parser_empty_and_heading_safe(), test_parser_extracts_declarant_and_relative_names(), test_parser_reads_tables() (+1 more)

### Community 38 - "Community 38"
Cohesion: 0.26
Nodes (6): Return list of (page_id, text, span_doc_type)., OCRPage, PageInput, OCRRunner, Any, Call an OCR API with caching and bounded concurrency.

### Community 39 - "Community 39"
Cohesion: 0.38
Nodes (10): _columns(), _foreign_key_check(), _foreign_keys(), _fresh_zalo_schema(), _indexes(), Path, _scalar(), _table_info() (+2 more)

### Community 40 - "Community 40"
Cohesion: 0.27
Nodes (15): _box_area_ratio(), _box_bounds(), _box_center_ratio(), _box_height_ratio(), _build_raw_text(), _extract_primary_id(), filter_target_boxes(), _group_lines() (+7 more)

### Community 41 - "Community 41"
Cohesion: 0.22
Nodes (8): casesRouter, casesRouterPath, detail, detailPath, exportModal, form, formPath, modalStart

### Community 44 - "Community 44"
Cohesion: 0.53
Nodes (4): createStore(), normalizeSnapshot(), { createStore, normalizeSnapshot }, require

### Community 46 - "Community 46"
Cohesion: 0.33
Nodes (6): _cv_to_pil_gray_local(), _get_qr_detector(), Image, _qr_variants_local(), try_decode_qr(), _zxing_decode_qr_local()

### Community 48 - "Community 48"
Cohesion: 0.40
Nodes (4): baseHtml, diagramEdges, formHtml, reactFlowApp

## Knowledge Gaps
- **35 isolated node(s):** `rootElement`, `backendCalculationCache`, `BASE_NODE_DEFS`, `REQUIRED_STATIC_SLOTS`, `S` (+30 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Customer` connect `Community 4` to `Community 1`, `Community 33`, `Community 6`, `Community 11`, `Community 12`, `Community 13`, `Community 15`, `Community 17`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Why does `ZaloBatch` connect `Community 3` to `Community 33`, `Community 6`, `Community 7`, `Community 16`, `Community 28`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `run_inheritance_case()` connect `Community 9` to `Community 11`, `Community 12`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `ZaloConnectorAccount` (e.g. with `BatchCreate` and `Confirmation`) actually correct?**
  _`ZaloConnectorAccount` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `ZaloBatch` (e.g. with `batch_snapshot()` and `BatchCreate`) actually correct?**
  _`ZaloBatch` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `Customer` (e.g. with `stats()` and `calculate_diagram()`) actually correct?**
  _`Customer` has 23 INFERRED edges - model-reasoned connections that need verification._
- **What connects `rootElement`, `backendCalculationCache`, `BASE_NODE_DEFS` to the rest of the system?**
  _35 weakly-connected nodes found - possible documentation gaps or missing edges._