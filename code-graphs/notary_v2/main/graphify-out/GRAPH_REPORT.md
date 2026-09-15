# Graph Report - D:\systemdocs\code-graphs\notary_v2\main  (2026-09-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 843 nodes · 2119 edges · 41 communities (34 shown, 7 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 195 edges (avg confidence: 0.75)
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
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38

## God Nodes (most connected - your core abstractions)
1. `_clean_text()` - 55 edges
2. `Customer` - 48 edges
3. `AnalyzeImagesTests` - 45 edges
4. `CompareEngine` - 30 edges
5. `InheritanceCase` - 26 edges
6. `_local_ocr_batch_from_inputs_triage_v2()` - 25 edges
7. `_normalize_property_ocr_doc()` - 24 edges
8. `_analyze_image_prepare()` - 24 edges
9. `Property` - 23 edges
10. `_process_single_property_image()` - 23 edges

## Surprising Connections (you probably didn't know these)
- `lifespan()` --calls--> `warmup_local_ocr()`  [INFERRED]
  ../../../.scan-src/notary_v2-main/main.py → ../../../.scan-src/notary_v2-main/routers/ocr_local.py
- `stats()` --indirect_call--> `InheritanceCase`  [INFERRED]
  ../../../.scan-src/notary_v2-main/main.py → ../../../.scan-src/notary_v2-main/models.py
- `DiagramPayloadValidationError` --uses--> `Customer`  [INFERRED]
  ../../../.scan-src/notary_v2-main/routers/cases.py → ../../../.scan-src/notary_v2-main/models.py
- `delete()` --indirect_call--> `Customer`  [INFERRED]
  ../../../.scan-src/notary_v2-main/routers/customers.py → ../../../.scan-src/notary_v2-main/models.py
- `detail()` --indirect_call--> `Customer`  [INFERRED]
  ../../../.scan-src/notary_v2-main/routers/customers.py → ../../../.scan-src/notary_v2-main/models.py

## Import Cycles
- None detected.

## Communities (41 total, 7 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (120): AsyncClient, analyze_images(), analyze_property_images(), analyze_property_pair(), _append_ai_doc(), _ascii_text(), _call_qwen_native_ocr_single(), _classify_property_book_type() (+112 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (55): CompareEngine, _Hit, _normalize_token(), _normalized_exact_parts(), Compare Word fields against OCR text corpus and emit audit issues., Return list of (page_id, text, span_doc_type)., DocumentGrouper, Group sequential OCR pages into document spans using lightweight rules. (+47 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (32): as_input_value(), consonant_skeleton(), create(), create_form(), delete(), detail(), edit(), edit_form() (+24 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (49): applyEngineResult(), assignPersonToNode(), BASE_NODE_DEFS, bootstrapId(), BrickCard, bridgeWorkflowUpdates(), buildAssignedNode(), buildCommittedSnapshot() (+41 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (20): ScanSource, PDFSplitter, Path, Render PDF pages to images for OCR., Path, Collect supported scan/image/word files from a folder, ignoring temps and cache., ScanLoader, Path (+12 more)

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (25): stats(), Customer, Property, 01/07/2024 — ngưỡng phân biệt CCCD cũ/mới., Căn cước công dân (trước 01/10/2024) hoặc Căn cước (từ 01/10/2024)., Bộ Công an (từ 01/10/2024) hoặc Cục CSQLHC về TTXH (trước đó)., Cư trú tại' (từ 01/10/2024) hoặc 'Thường trú tại' (trước đó)., Bảng lưu thông tin Giấy chứng nhận quyền sử dụng đất (sổ đỏ). (+17 more)

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (13): absBigInt(), addSet(), buildGraph(), compareDeath(), Fraction, gcdBigInt(), idOf(), makeLedger() (+5 more)

### Community 8 - "Community 8"
Cohesion: 0.13
Nodes (22): InheritanceCase, Bảng lưu Hồ sơ thừa kế — trung tâm của hệ thống., _build_normalized_mapping(), _build_template_mapping(), export_preview(), export_word(), _fmt_birth_or_year(), _fmt_date() (+14 more)

### Community 9 - "Community 9"
Cohesion: 0.16
Nodes (19): classify_doc_type(), detect_word_template_type(), extract_dates(), extract_id_numbers(), has_placeholders(), is_notary_page(), normalize_for_rules(), Path (+11 more)

### Community 10 - "Community 10"
Cohesion: 0.17
Nodes (9): DiagramPayloadValidationError, _normalize_case_state_json(), _parse_case_diagram_payload(), CaseStatePayloadTests, CaseStateSchemaTests, _customer(), DiagramPayloadParserTests, _payload() (+1 more)

### Community 11 - "Community 11"
Cohesion: 0.13
Nodes (22): _address_expected(), _append_person_raw_text(), _apply_delta_merge(), _build_summary(), _clean_doc_number(), _collect_warnings(), _count_vietnamese_diacritics(), _finalize_image_rows() (+14 more)

### Community 12 - "Community 12"
Cohesion: 0.14
Nodes (19): OCRJob, Tram kiem soat tien do OCR., analyze_images_local(), _ensure_local_ocr_dependencies(), get_local_job_status(), _get_rapidocr_engine(), _get_rapidocr_recognizer(), _get_vietocr_engine() (+11 more)

### Community 13 - "Community 13"
Cohesion: 0.19
Nodes (17): _ascii_fold(), _clean_name_candidate(), _empty_person_data(), _ensure_person_record(), _extract_anchor_block(), _extract_date_after_label(), _extract_dates(), _extract_gender_from_text() (+9 more)

### Community 14 - "Community 14"
Cohesion: 0.21
Nodes (19): Luu cac file mau Word do nguoi dung tai len de xuat van ban., WordTemplate, activate_word_template(), api_activate_template(), api_delete_template(), api_upload_template(), delete(), delete_word_template() (+11 more)

### Community 15 - "Community 15"
Cohesion: 0.26
Nodes (13): addKinship(), buildDiagramEdges(), buildFlowEdges(), buildKinshipEdges(), createIndex(), getKinshipFamilyKey(), hasNode(), hasSourcePerson() (+5 more)

### Community 16 - "Community 16"
Cohesion: 0.38
Nodes (15): cmd_approve(), cmd_draft(), cmd_execute(), cmd_review(), cmd_status(), _format_task(), _load_status(), main() (+7 more)

### Community 17 - "Community 17"
Cohesion: 0.24
Nodes (12): configure_process_logging(), _ensure_handler(), _parse_log_level(), _delete_file(), _delete_path(), _ensure_worker_logging(), _ms(), _parse_json_array() (+4 more)

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (15): _analyze_image_prepare(), _build_qr_person_data(), _coarse_doc_type_from_profile(), _detect_documents(), DocCrop, _is_valid_qr_data(), _numeric_stats(), _opencv_smart_crop() (+7 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (15): _cv_to_pil_gray_local(), _detect_face_proxy(), _detect_qr_proxy(), _get_face_cascade(), _get_qr_detector(), _make_proxy_image(), _mrz_likelihood_score(), _qr_variants_local() (+7 more)

### Community 20 - "Community 20"
Cohesion: 0.21
Nodes (12): Base, ExtractedDocument, InheritanceCaseProperty, InheritanceParticipant, Lien ket nhieu tai san cho mot ho so., Bảng lưu những người tham gia hồ sơ thừa kế., Kho luu tru du lieu da boc tach sau khi user xac nhan., confirm_save() (+4 more)

### Community 21 - "Community 21"
Cohesion: 0.29
Nodes (13): _box_area_ratio(), _box_bounds(), _box_center_ratio(), _box_height_ratio(), _crop_box_image(), _ensure_detection(), filter_target_boxes(), _normalize_box_points() (+5 more)

### Community 22 - "Community 22"
Cohesion: 0.22
Nodes (4): CacheStore, Path, Filesystem cache for page images and OCR text., CacheEntry

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (5): DetectorAndCropTests, FilterTargetBoxesTests, make_box(), MergeFlowTests, ParseFullTextTests

### Community 25 - "Community 25"
Cohesion: 0.20
Nodes (11): _ensure_table_columns(), get_db(), migrate_customers_nullable(), migrate_inheritance_case_properties_schema(), migrate_inheritance_cases_schema(), migrate_properties_schema(), Cung cấp kết nối DB cho mỗi request, tự đóng sau khi xong., Chuyển các cột customers (trừ ho_ten) sang nullable nếu chưa có. (+3 more)

### Community 26 - "Community 26"
Cohesion: 0.38
Nodes (11): create(), create_form(), delete(), detail(), edit(), edit_form(), inline_create(), list_properties() (+3 more)

### Community 27 - "Community 27"
Cohesion: 0.44
Nodes (9): _build_raw_text(), _extract_primary_id(), _group_lines(), _infer_doc_profile(), _log_debug(), _preview_text(), _print_rapidocr_raw_text(), _recognize_target_boxes() (+1 more)

### Community 28 - "Community 28"
Cohesion: 0.42
Nodes (8): decode_cp1252_mojibake_once(), fix_file(), main(), mojibake_score(), parse_args(), Namespace, Path, should_scan()

### Community 29 - "Community 29"
Cohesion: 0.38
Nodes (5): home(), http_timing_log(), lifespan(), Request, FastAPI

### Community 30 - "Community 30"
Cohesion: 0.67
Nodes (7): _clean_nullable_text(), _clean_text(), _coerce_bool(), _extract_diagram_participants(), _normalize_diagram_payload(), _normalize_role(), Any

### Community 31 - "Community 31"
Cohesion: 0.53
Nodes (4): createStore(), normalizeSnapshot(), { createStore, normalizeSnapshot }, require

## Knowledge Gaps
- **10 isolated node(s):** `rootElement`, `BASE_NODE_DEFS`, `S`, `BrickCard`, `TIER_DEFS` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AnalyzeImagesTests` connect `Community 4` to `Community 29`, `Community 23`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `Customer` connect `Community 6` to `Community 10`, `Community 2`, `Community 20`, `Community 30`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `DiagramPayloadValidationError` connect `Community 10` to `Community 2`, `Community 6`, `Community 8`, `Community 14`, `Community 20`, `Community 30`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 29 inferred relationships involving `Customer` (e.g. with `stats()` and `create()`) actually correct?**
  _`Customer` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `CompareEngine` (e.g. with `test_address_does_not_match_only_by_shared_digit()` and `test_case_insensitive_and_punctuation_normalized()`) actually correct?**
  _`CompareEngine` has 19 INFERRED edges - model-reasoned connections that need verification._
- **What connects `rootElement`, `BASE_NODE_DEFS`, `S` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.06129476584022039 - nodes in this community are weakly interconnected._