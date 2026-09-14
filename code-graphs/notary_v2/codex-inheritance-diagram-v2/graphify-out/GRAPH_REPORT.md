# Graph Report - D:\systemdocs\code-graphs\notary_v2\codex-inheritance-diagram-v2  (2026-09-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1410 nodes · 3806 edges · 67 communities (59 shown, 8 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 521 edges (avg confidence: 0.73)
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
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 52
- Community 53
- Community 55
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62

## God Nodes (most connected - your core abstractions)
1. `_clean_text()` - 55 edges
2. `Customer` - 44 edges
3. `ZaloBatch` - 44 edges
4. `CaseStatePayloadTests` - 44 edges
5. `_customer()` - 43 edges
6. `AnalyzeImagesTests` - 38 edges
7. `update_diagram()` - 36 edges
8. `build_template_mapping()` - 36 edges
9. `DiagramPayloadValidationError` - 29 edges
10. `ZaloConnectorAccount` - 28 edges

## Surprising Connections (you probably didn't know these)
- `FamilyTreeApp()` --indirect_call--> `person()`  [INFERRED]
  ReactFlowApp.jsx → diagram_edges.test.mjs
- `test_atomic_report_write_preserves_existing_file_on_replace_failure()` --calls--> `_write_json_atomically()`  [INFERRED]
  test_document_conversion_poc.py → harness.py
- `lifespan()` --calls--> `warmup_local_ocr()`  [INFERRED]
  main.py → ocr_local.py
- `DiagramPayloadValidationError` --uses--> `Customer`  [INFERRED]
  cases.py → models.py
- `update_diagram()` --indirect_call--> `Customer`  [INFERRED]
  cases.py → models.py

## Import Cycles
- None detected.

## Communities (67 total, 8 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (146): BackgroundTasks, Base, BaseModel, ZaloBatch, ZaloConnectorAccount, ZaloDataSyncRun, ZaloMedia, ZaloMessageText (+138 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (120): AsyncClient, analyze_images(), analyze_property_images(), analyze_property_pair(), _append_ai_doc(), _ascii_text(), _call_qwen_native_ocr_single(), _classify_property_book_type() (+112 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (83): Căn cước công dân (trước 01/10/2024) hoặc Căn cước (từ 01/10/2024)., Bộ Công an (từ 01/10/2024) hoặc Cục CSQLHC về TTXH (trước đó)., Cư trú tại' (từ 01/10/2024) hoặc 'Thường trú tại' (trước đó)., _active_persons(), _add_block_placeholders(), _add_property_placeholders(), _add_word_person_group(), _apply_diagram_nodes() (+75 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (55): bootstrapPage(), brandMarkup(), broadcast(), browserLauncherForPlatform(), chmodOwnerOnly(), clients, companionUrl(), computeAcceptKey() (+47 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (31): createZaloClient(), discoverSources(), finalizeQrLogin(), handleMessage(), handleQrLoginEvent(), isParentAlive(), listenerHeartbeatState(), nextGeneration() (+23 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (48): stats(), Customer, InheritanceCase, Property, Luu cac file mau Word do nguoi dung tai len de xuat van ban., 01/07/2024 — ngưỡng phân biệt CCCD cũ/mới., Bảng lưu thông tin Giấy chứng nhận quyền sử dụng đất (sổ đỏ)., Bảng lưu Hồ sơ thừa kế — trung tâm của hệ thống. (+40 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (47): applyEngineResult(), assignPersonToNode(), backendCalculationCache, BASE_NODE_DEFS, bootstrapId(), BrickCard, bridgeWorkflowUpdates(), buildAssignedNode() (+39 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (31): as_input_value(), consonant_skeleton(), create(), create_form(), delete(), detail(), edit(), edit_form() (+23 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (41): _empty_result(), _error(), _fraction_text(), _parse_death_date(), _percent_text(), _person_id(), Any, date (+33 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (23): _convert_ocr_candidate(), OcrClient, _raster_mime_type(), Local MarkItDown conversion for the isolated document-conversion POC., Return an image MIME validated by content, never by filename suffix., Explicitly policy-gated OCR boundary for raster candidates., Extract text without exposing provider transport to the router., ContentRecord (+15 more)

### Community 10 - "Community 10"
Cohesion: 0.22
Nodes (4): update_diagram(), CaseStatePayloadTests, _customer(), SimpleNamespace

### Community 11 - "Community 11"
Cohesion: 0.15
Nodes (26): _address_expected(), analyze_images_local(), _append_person_raw_text(), _apply_delta_merge(), _build_summary(), _clean_doc_number(), _collect_warnings(), _count_vietnamese_diacritics() (+18 more)

### Community 13 - "Community 13"
Cohesion: 0.22
Nodes (24): _actual_mime(), _baseline_commit(), _checks(), _comparison(), _cost_estimate(), _duration_ms(), _error(), _facts_metadata() (+16 more)

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (10): InheritanceParticipant, Bảng lưu những người tham gia hồ sơ thừa kế., add(), delete(), edit(), Session, AtomicPersistenceTests, CaseStateSchemaTests (+2 more)

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (20): Path, Create a minimal synthetic ZIP-signature DOCX fixture for routing tests., Create a strict, synthetic manifest whose paths are manifest-relative., test_atomic_report_write_preserves_existing_file_on_replace_failure(), test_classify_source(), test_docx_local_route_never_calls_ocr(), test_envelope_is_json_safe_and_has_experimental_version(), test_harness_rejects_hash_mismatch_without_converting() (+12 more)

### Community 16 - "Community 16"
Cohesion: 0.14
Nodes (8): InheritanceCaseProperty, Lien ket nhieu tai san cho mot ho so., _case_state_payload(), DiagramPayloadValidationError, _merge_case_state_diagram(), _merge_case_state_stage(), _normalize_case_state_json(), Exception

### Community 17 - "Community 17"
Cohesion: 0.21
Nodes (4): _parse_case_diagram_payload(), _resolve_v2_case_state(), DiagramPayloadParserTests, _payload()

### Community 18 - "Community 18"
Cohesion: 0.27
Nodes (13): CompareEngine, _Hit, Compare Word fields against OCR text corpus and emit audit issues., WordAuditDoc, WordField, _ocr_page(), _span(), test_case_insensitive_and_punctuation_normalized() (+5 more)

### Community 19 - "Community 19"
Cohesion: 0.42
Nodes (9): Parse .docx files into normalized fields for audit., WordParser, _make_docx(), Path, test_parser_drops_notary_clause(), test_parser_empty_and_heading_safe(), test_parser_extracts_declarant_and_relative_names(), test_parser_reads_tables() (+1 more)

### Community 20 - "Community 20"
Cohesion: 0.26
Nodes (18): api(), bindPreview(), clearNotice(), createBatch(), notice(), previewPayload(), refresh(), refreshBatch() (+10 more)

### Community 21 - "Community 21"
Cohesion: 0.25
Nodes (16): addKinship(), buildDiagramEdges(), buildKinshipEdges(), createIndex(), getKinshipFamilyKey(), hasNode(), hasSourcePerson(), idOf() (+8 more)

### Community 22 - "Community 22"
Cohesion: 0.14
Nodes (18): ExtractedDocument, Kho luu tru du lieu da boc tach sau khi user xac nhan., _analyze_image_prepare(), _build_qr_person_data(), _coarse_doc_type_from_profile(), confirm_save(), _detect_documents(), DocCrop (+10 more)

### Community 23 - "Community 23"
Cohesion: 0.17
Nodes (17): OCRJob, Tram kiem soat tien do OCR., _ensure_local_ocr_dependencies(), get_local_job_status(), _get_rapidocr_engine(), _get_rapidocr_recognizer(), _get_vietocr_engine(), _log_timing() (+9 more)

### Community 24 - "Community 24"
Cohesion: 0.21
Nodes (13): _clean_nullable_text(), _clean_text(), _coerce_bool(), _coerce_int(), _derive_case_state_json_from_participants(), _extract_diagram_participants(), _fmt_date(), _normalize_diagram_payload() (+5 more)

### Community 25 - "Community 25"
Cohesion: 0.21
Nodes (7): AuditIssue, AuditRunMeta, Path, Write JSON and Markdown reports for the audit run., ReportWriter, Path, test_full_pipeline_without_ocr_api()

### Community 26 - "Community 26"
Cohesion: 0.25
Nodes (15): fake_converter(), FakeClient, FakeCompletions, Exception, Create a synthetic raster fixture; its content is never sent to cloud., test_allowed_image_sends_one_data_url_to_fake_client(), test_denied_image_never_calls_client(), test_non_raster_ocr_candidate_never_reaches_image_provider() (+7 more)

### Community 27 - "Community 27"
Cohesion: 0.16
Nodes (14): assert_foreign_key_check(), _ensure_table_columns(), get_db(), migrate_customers_nullable(), migrate_inheritance_case_properties_schema(), migrate_inheritance_cases_schema(), migrate_properties_schema(), migrate_zalo_schema() (+6 more)

### Community 28 - "Community 28"
Cohesion: 0.20
Nodes (16): _crop_box_image(), _detect_face_proxy(), _detect_qr_proxy(), _ensure_detection(), _get_face_cascade(), _make_proxy_image(), _mrz_likelihood_score(), _normalize_box_points() (+8 more)

### Community 29 - "Community 29"
Cohesion: 0.18
Nodes (10): Return list of (page_id, text, span_doc_type)., DocumentGrouper, Group sequential OCR pages into document spans using lightweight rules., DocType, DocumentSpan, MatchType, Severity, SourceKind (+2 more)

### Community 30 - "Community 30"
Cohesion: 0.23
Nodes (9): ScanSource, Path, Collect supported scan/image/word files from a folder, ignoring temps and cache., ScanLoader, Path, sample_folder(), test_scan_loader_hashes_are_stable(), test_scan_loader_ignores_temp_excel_and_cache() (+1 more)

### Community 31 - "Community 31"
Cohesion: 0.27
Nodes (15): _box_area_ratio(), _box_bounds(), _box_center_ratio(), _box_height_ratio(), _build_raw_text(), _extract_primary_id(), filter_target_boxes(), _group_lines() (+7 more)

### Community 32 - "Community 32"
Cohesion: 0.24
Nodes (12): _app(), _signed_post(), test_connector_failure_is_sanitized_and_clears_stale_qr(), test_connector_immediate_exit_returns_a_sanitized_startup_error(), test_force_qr_clears_the_previous_qr_before_starting(), test_onboard_webhook_batch_pdf_and_safe_serialization(), test_opening_state_does_not_public_or_open_stale_qr(), test_start_connector_fails_closed_when_deployment_config_is_missing() (+4 more)

### Community 33 - "Community 33"
Cohesion: 0.13
Nodes (14): dependencies, zca-js, description, engines, node, name, private, scripts (+6 more)

### Community 34 - "Community 34"
Cohesion: 0.26
Nodes (12): configure_process_logging(), _ensure_handler(), _parse_log_level(), _delete_file(), _delete_path(), _ensure_worker_logging(), _ms(), _parse_json_array() (+4 more)

### Community 35 - "Community 35"
Cohesion: 0.18
Nodes (14): _ascii_fold(), _clean_name_candidate(), _extract_anchor_block(), _extract_date_after_label(), _extract_dates(), _extract_gender_from_text(), _extract_id_12_from_mrz_text(), _extract_id_12_from_text() (+6 more)

### Community 36 - "Community 36"
Cohesion: 0.22
Nodes (4): CacheStore, Path, Filesystem cache for page images and OCR text., CacheEntry

### Community 37 - "Community 37"
Cohesion: 0.19
Nodes (12): test_ocr_gate_denies_without_explicit_permission(), classify_source(), decide_ocr(), _has_pdf_text(), _is_webp(), OcrDecision, Path, Deterministic source routing and explicit cloud OCR permission for the POC. (+4 more)

### Community 38 - "Community 38"
Cohesion: 0.18
Nodes (5): DetectorAndCropTests, FilterTargetBoxesTests, make_box(), MergeFlowTests, ParseFullTextTests

### Community 39 - "Community 39"
Cohesion: 0.38
Nodes (11): create(), create_form(), delete(), detail(), edit(), edit_form(), inline_create(), list_properties() (+3 more)

### Community 40 - "Community 40"
Cohesion: 0.33
Nodes (5): OCRPage, PageInput, OCRRunner, Any, Call an OCR API with caching and bounded concurrency.

### Community 41 - "Community 41"
Cohesion: 0.25
Nodes (6): PDFSplitter, Path, Render PDF pages to images for OCR., main(), parse_args(), Namespace

### Community 43 - "Community 43"
Cohesion: 0.42
Nodes (7): connect(), nextReconnectDelay(), reloadAfterRecovery(), sessionKey(), setStatus(), showTombstone(), websocketUrl()

### Community 44 - "Community 44"
Cohesion: 0.22
Nodes (8): casesRouter, casesRouterPath, detail, detailPath, exportModal, form, formPath, modalStart

### Community 45 - "Community 45"
Cohesion: 0.43
Nodes (4): command_has_server_id(), is_brainstorm_server(), mark_stopped(), stop-server.sh script

### Community 46 - "Community 46"
Cohesion: 0.38
Nodes (5): home(), http_timing_log(), lifespan(), Request, FastAPI

### Community 47 - "Community 47"
Cohesion: 0.29
Nodes (4): Fast text audit pipeline for comparing Word documents against scan OCR.  Indepen, _has_provenance(), Isolated, non-production document-conversion proof of concept., ConversionEnvelope

### Community 49 - "Community 49"
Cohesion: 0.60
Nodes (5): combineGraphs(), extractDotBlocks(), extractGraphBody(), main(), renderToSvg()

### Community 50 - "Community 50"
Cohesion: 0.53
Nodes (4): createStore(), normalizeSnapshot(), { createStore, normalizeSnapshot }, require

### Community 52 - "Community 52"
Cohesion: 0.33
Nodes (6): _cv_to_pil_gray_local(), _get_qr_detector(), Image, _qr_variants_local(), try_decode_qr(), _zxing_decode_qr_local()

### Community 53 - "Community 53"
Cohesion: 0.23
Nodes (10): classify_doc_type(), cut_at_notary_anchor(), detect_word_template_type(), extract_dates(), extract_id_numbers(), has_placeholders(), is_notary_page(), normalize_for_rules() (+2 more)

### Community 55 - "Community 55"
Cohesion: 0.40
Nodes (4): baseHtml, diagramEdges, formHtml, reactFlowApp

### Community 58 - "Community 58"
Cohesion: 0.67
Nodes (3): _convert_with_markitdown(), Path, Convert through MarkItDown without enabling unclassified plugins.

## Knowledge Gaps
- **56 isolated node(s):** `crypto`, `http`, `fs`, `path`, `OPCODES` (+51 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Customer` connect `Community 5` to `Community 0`, `Community 2`, `Community 7`, `Community 9`, `Community 10`, `Community 14`, `Community 16`, `Community 17`, `Community 24`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `build_template_mapping()` connect `Community 2` to `Community 5`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `AnalyzeImagesTests` connect `Community 12` to `Community 42`, `Community 46`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Customer` (e.g. with `stats()` and `calculate_diagram()`) actually correct?**
  _`Customer` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ZaloBatch` (e.g. with `batch_snapshot()` and `BatchCreate`) actually correct?**
  _`ZaloBatch` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `CaseStatePayloadTests` (e.g. with `Customer` and `InheritanceCase`) actually correct?**
  _`CaseStatePayloadTests` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `crypto`, `http`, `fs` to the rest of the system?**
  _56 weakly-connected nodes found - possible documentation gaps or missing edges._