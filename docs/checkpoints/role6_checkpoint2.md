# Checkpoint 2 — Vai trò 6: Observability

## 1. Kết quả checkpoint

Checkpoint 2 đã hoàn thành ba yêu cầu của Vai trò 6:

1. Audit embedding manifest, collection name và document count.
2. Đóng băng baseline quality/freshness signals để đối chiếu sau corruption.
3. Chuẩn bị khuôn Phase 1 report chỉ nhận và hiển thị số liệu thật.

Không sửa embedding manifest hoặc Chroma collection vì chúng thuộc người phụ
trách RAG/index.

## 2. Embedding manifest audit

### Code đã thêm

Hàm `audit_embedding_manifest` trong `src/observability/quality.py` kiểm tra:

- manifest file tồn tại;
- backend là Chroma;
- embedding model khớp Settings;
- collection name khớp baseline config;
- số documents bằng số clean rows;
- `record_id` và `paper_id` không trùng;
- tập `paper_id` trong manifest khớp clean dataset;
- metadata có `paper_id`, `title`, `published`, `summary`;
- `persist_path` trong manifest khớp config hiện tại;
- thư mục Chroma theo config tồn tại.

Artifact đã tạo:

- `data/quality/baseline_embedding_audit.json`

### Kết quả thực tế

| Signal | Kết quả |
| --- | --- |
| Backend | `chroma` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Collection | `papers-baseline` |
| Manifest documents | 24 |
| Clean rows | 24 |
| Document count match | PASS |
| Paper IDs match | PASS |
| Required metadata | PASS |
| Configured Chroma path exists | PASS |
| Manifest persist path matches config | **FAIL** |

Manifest hiện ghi absolute path của máy/workspace khác:

```text
D:\AI Thực chiến\Thực hành\Day10\K3_Day10_Data-Pipeline-Data-Observability\data\chroma
```

Workspace hiện tại dùng:

```text
D:\K3_Day10_Data-Pipeline-Data-Observability\data\chroma
```

Vì vậy audit tổng là `false` với đúng một failed check:
`persist_path_matches_config`.

Role 6 chỉ báo lỗi. Người phụ trách RAG/index cần rebuild manifest tại workspace
hiện tại hoặc lưu persist path theo cách portable.

## 3. Baseline observability snapshot

### Code đã thêm

Hàm `build_observability_snapshot` đóng băng cùng một schema signals cho ba
trạng thái hợp lệ:

- `baseline`;
- `corrupted`;
- `repaired`.

Artifact baseline đã tạo:

- `data/quality/baseline_observability_snapshot.json`

### Baseline signals hiện tại

| Signal | Baseline |
| --- | ---: |
| Row count | 24 |
| Null paper IDs | 0 |
| Duplicate paper ID rows | 0 |
| Missing title rows | 0 |
| Invalid summary rows | 0 |
| Invalid age rows | 0 |
| Stale rows | 1 |
| Stale ratio | 0.0417 |
| Latest published | 2026-08-05 |
| Oldest published | 2026-01-25 |
| Embedding document count | 24 |
| Collection | `papers-baseline` |

Status tổng hợp:

- Quality success: `false` vì một stale record vượt 180 ngày.
- Freshness is fresh: `false` vì một stale record.
- Embedding audit success: `false` vì persist path cũ.

Snapshot này là mốc bất biến để tạo cùng payload cho corrupted/repaired và tính
delta về sau. Không chỉnh tay snapshot để làm baseline pass.

## 4. Khuôn Phase 1 report

### Code renderer

`generate_phase1_report` trong `src/observability/reporting.py` đã được triển
khai để nhận bốn payload:

- `source_summary`;
- `metrics`;
- `quality`;
- `freshness`.

Hàm tạo Markdown với:

- source summary;
- RAG metrics;
- trạng thái Ragas (kể cả skipped/error);
- từng quality check và observed/expected;
- freshness signals;
- guardrail không kết luận quá mức.

Mọi giá trị lấy từ payload truyền vào, không hard-code điểm số.

### Template cho người đọc

Đã tạo:

- `data/reports/phase1_report_template.md`

Template giữ placeholder vì CP2 chưa có `baseline_metrics.json`. File
`phase1_report.md` thật chỉ được sinh ở CP3 sau khi evaluator bàn giao metrics.

## 5. Kiểm thử

Đã bổ sung test cho:

- embedding audit hợp lệ;
- snapshot ghi đúng collection/document count;
- Phase 1 report lấy đúng metrics, quality và freshness payload;
- trạng thái Ragas skipped được ghi trung thực.

Lệnh:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m pytest -q tests/test_observability_quality.py tests/test_observability_reporting.py
```

Kết quả:

```text
....                                                                     [100%]
4 passed in 0.66s
```

Sau đó chạy toàn bộ test suite của repo:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m pytest -q
```

```text
........                                                                 [100%]
8 passed in 0.78s
```

## 6. Dependency cần từ các vai trò khác

### Cần người phụ trách RAG/index

- Rebuild `data/embeddings/papers_embeddings.json` để `persist_path` khớp
  workspace hiện tại.
- Không đổi collection baseline khỏi `papers-baseline` nếu chưa thống nhất lại
  Settings.
- Sau khi rebuild, báo Role 6 chạy lại embedding audit.

### Cần người phụ trách Evaluation

- Bàn giao `data/results/baseline_metrics.json`.
- Bàn giao `data/results/baseline_answers.json` để giải thích hit/miss.
- Cho biết Ragas chạy, skipped hay error.

### Cần người phụ trách Pipeline

- Gọi `generate_phase1_report` sau khi đủ source summary, metrics, quality và
  freshness payload.
- Không dùng placeholder template làm báo cáo kết quả thật.

## 7. Trạng thái Checkpoint 2 — Vai trò 6

- [x] Audit embedding manifest.
- [x] Kiểm tra collection name.
- [x] Đối chiếu 24 indexed documents với 24 clean rows.
- [x] Phát hiện stale absolute persist path.
- [x] Ghi baseline observability snapshot.
- [x] Chuẩn bị Phase 1 report renderer.
- [x] Chuẩn bị Markdown report template.
- [x] Chạy 4 test Role 6 thành công.
- [x] Chạy toàn bộ test suite: 8 test thành công.
- [ ] Chờ RAG owner rebuild manifest để audit pass.
- [ ] Chờ Evaluation owner bàn giao baseline metrics để sinh report CP3.
