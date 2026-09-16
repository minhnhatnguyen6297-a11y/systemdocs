# Graph Report - code-graphs\notary_v2\monorepo  (2026-09-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1377 nodes · 4008 edges · 58 communities (49 shown, 9 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 665 edges (avg confidence: 0.74)
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
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 42
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 51
- Community 53
- Community 57

## God Nodes (most connected - your core abstractions)
1. `_clean_text()` - 56 edges
2. `Customer` - 52 edges
3. `ZaloConnectorAccount` - 50 edges
4. `_account()` - 48 edges
5. `ZaloBatch` - 45 edges
6. `AnalyzeImagesTests` - 45 edges
7. `ZaloSource` - 43 edges
8. `InboxValidationError` - 43 edges
9. `ZaloMedia` - 36 edges
10. `build_template_mapping()` - 35 edges

## Surprising Connections (you probably didn't know these)
- `stats()` --indirect_call--> `Customer`  [INFERRED]
  ../../../notary_v2/main.py → ../../../notary_v2/models.py
- `stats()` --indirect_call--> `InheritanceCase`  [INFERRED]
  ../../../notary_v2/main.py → ../../../notary_v2/models.py
- `create_live_preview()` --indirect_call--> `Customer`  [INFERRED]
  ../../../notary_v2/routers/cases.py → ../../../notary_v2/models.py
- `DiagramPayloadValidationError` --uses--> `Customer`  [INFERRED]
  ../../../notary_v2/routers/cases.py → ../../../notary_v2/models.py
- `delete()` --indirect_call--> `Customer`  [INFERRED]
  ../../../notary_v2/routers/customers.py → ../../../notary_v2/models.py

## Import Cycles
- None detected.

## Communities (58 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (140): ZaloMessageText, _account_or_error(), ack_policy(), ack_source_sync(), _ack_version(), apply_connector_report(), apply_data_sync_report(), apply_intake_consent() (+132 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (121): AsyncClient, analyze_images(), analyze_property_images(), analyze_property_pair(), _append_ai_doc(), _ascii_text(), _call_qwen_native_ocr_single(), _classify_property_book_type() (+113 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (98): BackgroundTasks, BaseModel, ZaloBatch, ZaloConnectorAccount, ZaloDataSyncRun, ZaloMedia, ZaloSource, _as_iso() (+90 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (84): Căn cước công dân (trước 01/10/2024) hoặc Căn cước (từ 01/10/2024)., Bộ Công an (từ 01/10/2024) hoặc Cục CSQLHC về TTXH (trước đó)., Cư trú tại' (từ 01/10/2024) hoặc 'Thường trú tại' (trước đó)., _active_persons(), _add_block_placeholders(), _add_property_placeholders(), _add_word_person_group(), _apply_diagram_nodes() (+76 more)

### Community 4 - "Community 4"
Cohesion: 0.07
Nodes (45): createZaloClient(), finalizeQrLogin(), handleMessage(), handleQrLoginEvent(), installCommandPoll(), installSourceSyncTriggers(), isParentAlive(), listenerHeartbeatState() (+37 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (52): applyEngineResult(), assignPersonToNode(), BASE_NODE_DEFS, bootstrapId(), BrickCard, bridgeWorkflowUpdates(), buildAssignedNode(), buildCommittedSnapshot() (+44 more)

### Community 6 - "Community 6"
Cohesion: 0.07
Nodes (31): as_input_value(), consonant_skeleton(), create(), create_form(), delete(), detail(), edit(), edit_form() (+23 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (55): bootstrapPage(), brandMarkup(), broadcast(), browserLauncherForPlatform(), chmodOwnerOnly(), clients, companionUrl(), computeAcceptKey() (+47 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (3): AnalyzeImagesTests, make_upload(), UploadFile

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (41): _empty_result(), _error(), _fraction_text(), _parse_death_date(), _percent_text(), _person_id(), Any, date (+33 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (39): Luu cac file mau Word do nguoi dung tai len de xuat van ban., WordTemplate, activate_word_template(), api_activate_template(), api_delete_template(), api_upload_template(), _build_normalized_mapping(), _build_temp_participants() (+31 more)

### Community 11 - "Community 11"
Cohesion: 0.16
Nodes (17): _clean_nullable_text(), _clean_text(), _coerce_bool(), _derive_case_state_json_from_participants(), DiagramPayloadValidationError, _extract_diagram_participants(), _normalize_case_state_json(), _normalize_diagram_payload() (+9 more)

### Community 12 - "Community 12"
Cohesion: 0.16
Nodes (17): convert_path(), _local_pdf_page_segments(), _markitdown_convert(), _ocr_inputs(), OcrClient, Path, Return OCR text for an already-approved image input., Render scanned PDF pages; never send PDF bytes as an image data URL. (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (19): Base, ExtractedDocument, InheritanceCase, InheritanceCaseProperty, InheritanceParticipant, Lien ket nhieu tai san cho mot ho so., Bảng lưu những người tham gia hồ sơ thừa kế., Kho luu tru du lieu da boc tach sau khi user xac nhan. (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.16
Nodes (19): classify_doc_type(), detect_word_template_type(), extract_dates(), extract_id_numbers(), has_placeholders(), is_notary_page(), normalize_for_rules(), Path (+11 more)

### Community 15 - "Community 15"
Cohesion: 0.20
Nodes (23): _pdf_bytes(), Path, _scanned_pdf_bytes(), test_allowed_image_sends_one_data_url_to_fake_client(), test_classify_source(), test_compatible_ocr_classifies_retryability(), test_concrete_markitdown_adapter_disables_plugins(), test_denied_image_never_calls_client() (+15 more)

### Community 16 - "Community 16"
Cohesion: 0.34
Nodes (23): CompareEngine, Compare Word fields against OCR text corpus and emit audit issues., WordField, _ocr_page(), _span(), test_address_does_not_match_only_by_shared_digit(), test_case_insensitive_and_punctuation_normalized(), test_content_before_loi_chung_remains_comparable() (+15 more)

### Community 17 - "Community 17"
Cohesion: 0.19
Nodes (19): home(), http_timing_log(), lifespan(), Request, stats(), Property, Bảng lưu thông tin Giấy chứng nhận quyền sử dụng đất (sổ đỏ)., create() (+11 more)

### Community 18 - "Community 18"
Cohesion: 0.25
Nodes (19): api(), bindPreview(), clearNotice(), createBatch(), notice(), previewPayload(), refresh(), refreshBatch() (+11 more)

### Community 19 - "Community 19"
Cohesion: 0.16
Nodes (14): Return list of (page_id, text, span_doc_type)., DocumentGrouper, Group sequential OCR pages into document spans using lightweight rules., DocType, DocumentSpan, MatchType, Severity, SourceKind (+6 more)

### Community 20 - "Community 20"
Cohesion: 0.22
Nodes (6): AuditIssue, AuditRunMeta, WordAuditDoc, Path, Write JSON and Markdown reports for the audit run., ReportWriter

### Community 21 - "Community 21"
Cohesion: 0.27
Nodes (15): addKinship(), buildDiagramEdges(), buildKinshipEdges(), createIndex(), getKinshipFamilyKey(), hasNode(), hasSourcePerson(), idOf() (+7 more)

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (7): CacheStore, Path, Filesystem cache for page images and OCR text., CacheEntry, main(), parse_args(), Namespace

### Community 23 - "Community 23"
Cohesion: 0.23
Nodes (10): ScanSource, Path, Collect supported scan/image/word files from a folder, ignoring temps and cache., ScanLoader, Path, sample_folder(), test_identical_files_keep_distinct_source_identity(), test_scan_loader_hashes_are_stable() (+2 more)

### Community 24 - "Community 24"
Cohesion: 0.16
Nodes (14): assert_foreign_key_check(), _ensure_table_columns(), get_db(), migrate_customers_nullable(), migrate_inheritance_case_properties_schema(), migrate_inheritance_cases_schema(), migrate_properties_schema(), migrate_zalo_schema() (+6 more)

### Community 25 - "Community 25"
Cohesion: 0.30
Nodes (6): _parse_case_diagram_payload(), _resolve_posted_participants(), _customer(), DiagramPayloadParserTests, _payload(), _property()

### Community 26 - "Community 26"
Cohesion: 0.23
Nodes (10): PDFSplitter, Path, Render PDF pages to images for OCR., Path, test_full_pipeline_without_ocr_api(), test_pdf_splitter_converts_alpha_bmp_to_jpeg(), test_pdf_splitter_converts_png_to_jpeg(), test_pdf_splitter_renders_real_pdf_as_jpeg() (+2 more)

### Community 27 - "Community 27"
Cohesion: 0.26
Nodes (13): Customer, 01/07/2024 — ngưỡng phân biệt CCCD cũ/mới., Bảng lưu thông tin người (sống hoặc đã chết)., create(), create_form(), detail(), edit(), edit_form() (+5 more)

### Community 28 - "Community 28"
Cohesion: 0.25
Nodes (8): APIConnectionError, APITimeoutError, OcrRequestError, Any, Exception, QwenCompatibleOcr, RateLimitError, RuntimeError

### Community 29 - "Community 29"
Cohesion: 0.13
Nodes (14): dependencies, zca-js, description, engines, node, name, private, scripts (+6 more)

### Community 30 - "Community 30"
Cohesion: 0.30
Nodes (13): _canonical_digest(), _error_dict(), _expected_mismatches(), _load_manifest(), main(), _package_versions(), Any, Path (+5 more)

### Community 31 - "Community 31"
Cohesion: 0.31
Nodes (6): OCRPage, PageInput, OCRRunner, Any, Call an OCR API with caching and bounded concurrency., test_ocr_runner_deduplicates_identical_page_hashes()

### Community 32 - "Community 32"
Cohesion: 0.29
Nodes (9): test_canonical_golden_manifest_hashes_and_routes(), test_golden_fixture_materialization_is_byte_repeatable(), materialize_golden_fixtures(), _normalize_office_zip(), _pdf(), Path, Create deterministic synthetic files for the GD-01..07 manifest., Normalize ZIP metadata so identical synthetic inputs have identical bytes. (+1 more)

### Community 33 - "Community 33"
Cohesion: 0.24
Nodes (9): test_malformed_pdf_is_unsupported_without_raising(), test_ocr_gate_allows_only_explicit_ocr_candidates(), test_ocr_gate_denies_without_explicit_permission(), classify_source(), decide_ocr(), OcrDecision, Path, Classify only the formats the POC is allowed to handle.      This intentionall (+1 more)

### Community 34 - "Community 34"
Cohesion: 0.42
Nodes (7): connect(), nextReconnectDelay(), reloadAfterRecovery(), sessionKey(), setStatus(), showTombstone(), websocketUrl()

### Community 35 - "Community 35"
Cohesion: 0.22
Nodes (8): casesRouter, casesRouterPath, detail, detailPath, exportModal, form, formPath, modalStart

### Community 36 - "Community 36"
Cohesion: 0.43
Nodes (3): _Hit, _normalize_token(), _normalized_exact_parts()

### Community 37 - "Community 37"
Cohesion: 0.43
Nodes (4): command_has_server_id(), is_brainstorm_server(), mark_stopped(), stop-server.sh script

### Community 39 - "Community 39"
Cohesion: 0.60
Nodes (5): combineGraphs(), extractDotBlocks(), extractGraphBody(), main(), renderToSvg()

### Community 40 - "Community 40"
Cohesion: 0.53
Nodes (4): createStore(), normalizeSnapshot(), { createStore, normalizeSnapshot }, require

### Community 42 - "Community 42"
Cohesion: 0.60
Nodes (4): configure_process_logging(), _ensure_handler(), _parse_log_level(), Logger

### Community 57 - "Community 57"
Cohesion: 0.40
Nodes (3): test_envelope_is_json_safe_and_has_experimental_version(), Path, Source

## Knowledge Gaps
- **53 isolated node(s):** `crypto`, `http`, `fs`, `path`, `OPCODES` (+48 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `WordParser` connect `Community 14` to `Community 26`, `Community 22`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Why does `parser()` connect `Community 14` to `Community 0`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `Customer` connect `Community 27` to `Community 3`, `Community 6`, `Community 10`, `Community 11`, `Community 13`, `Community 17`, `Community 25`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `Customer` (e.g. with `stats()` and `create()`) actually correct?**
  _`Customer` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 43 inferred relationships involving `ZaloConnectorAccount` (e.g. with `BatchCreate` and `Confirmation`) actually correct?**
  _`ZaloConnectorAccount` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `ZaloBatch` (e.g. with `batch_snapshot()` and `BatchCreate`) actually correct?**
  _`ZaloBatch` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `crypto`, `http`, `fs` to the rest of the system?**
  _53 weakly-connected nodes found - possible documentation gaps or missing edges._