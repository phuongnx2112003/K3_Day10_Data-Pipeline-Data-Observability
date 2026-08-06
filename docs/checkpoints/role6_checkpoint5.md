# Checkpoint 5 — Vai trò 6: Observability

## 1. Mục tiêu checkpoint

Vai trò 6 chạy quality/freshness trên corrupted dataset, lưu report riêng và chỉ nối
corruption với thay đổi signal/metric khi artifact thật cung cấp đủ bằng chứng.

Các đầu vào đã dùng:

- `data/clean/papers_clean_corrupted.csv`;
- `data/results/corruption_log.json`;
- `data/results/corrupted_metrics.json`;
- `data/results/corrupted_answers.json`;
- `data/embeddings/papers_embeddings_corrupted.json`;
- baseline snapshot và baseline metrics của CP3.

Readiness status là `complete`: có đủ đầu vào, metrics có 72 samples và answers có
72 phần tử.

## 2. Artifact của Role 6 tại CP5

| Artifact | Chức năng |
| --- | --- |
| `data/quality/corrupted_quality.json` | Kết quả kiểm tra cấu trúc/chất lượng corrupted data |
| `data/quality/corrupted_freshness.json` | Kết quả freshness dùng cột `published` |
| `data/quality/corrupted_embedding_audit.json` | Audit manifest/index corrupted |
| `data/quality/corrupted_observability_snapshot.json` | Snapshot signal và metric của trạng thái corrupted |
| `data/quality/corrupted_impact_evidence.json` | So sánh baseline–corrupted và liên kết corruption log với bằng chứng |
| `data/quality/corrupted_observability_readiness.json` | Xác nhận đủ input và số metrics/answers khớp nhau |

Runner có thể chạy lại bằng:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m observability.corrupted
```

## 3. Quality và freshness quan sát được

| Signal | Baseline | Corrupted | Delta | Kết luận |
| --- | ---: | ---: | ---: | --- |
| Row count | 24 | 24 | 0 | Không đổi |
| Null paper ID rows | 0 | 0 | 0 | Không đổi |
| Duplicate paper ID rows | 0 | 4 | +4 | Xấu đi |
| Missing title rows | 0 | 0 | 0 | Không đổi |
| Invalid summary rows | 0 | 2 | +2 | Xấu đi |
| Invalid age rows | 0 | 0 | 0 | Không đổi |
| Stale rows | 1 | 3 | +2 | Xấu đi |
| Stale ratio | 0.0417 | 0.1250 | +0.0833 | Xấu đi |

Corrupted quality thất bại ở ba check: `paper_id_unique`, `summary_min_length` và
`age_days_within_freshness_threshold`. Freshness có ngày mới nhất `2026-07-13`,
ngày cũ nhất `2016-02-26`, ba stale rows và stale ratio `12.5%`.

Row count giữ nguyên không có nghĩa dữ liệu vẫn tốt: flow xóa hai records mới nhất
rồi thêm hai duplicate records, nên tổng số dòng vẫn là 24.

## 4. Metric baseline so với corrupted

| Metric | Baseline | Corrupted | Delta | Quan sát |
| --- | ---: | ---: | ---: | --- |
| Retrieval hit rate | 1.0000 | 0.9167 | -0.0833 | Giảm |
| Mean token F1 | 0.4236 | 0.6603 | +0.2367 | Tăng |
| Judge accuracy | 0.3333 | 0.6250 | +0.2917 | Tăng |
| Mean judge score | 2.6250 | 3.7778 | +1.1528 | Tăng |

Kết luận có kiểm soát: structural quality, freshness và retrieval hit rate xấu đi.
Token F1 cùng judge metrics lại tăng trên lần chạy này, vì vậy không được kết luận
rằng mọi RAG metric đều giảm. Metric tăng cũng không phủ định các lỗi dữ liệu đã được
quality/freshness report đo trực tiếp.

## 5. Nối corruption log với bằng chứng

| Corruption event | Bằng chứng quan sát | Trạng thái |
| --- | --- | --- |
| `latest_drop` | 2 records ảnh hưởng 6 test questions; retrieval hit rate giảm 0.0833 | Có bằng chứng |
| `missing` | Invalid summary rows tăng 2 | Có bằng chứng |
| `old_date` | Stale rows tăng 2 | Có bằng chứng |
| `duplicate` | Duplicate paper ID rows tăng 4 | Có bằng chứng |
| `noise` | Chưa có check trực tiếp cho noise marker | Không quy kết |
| `truncate_title` | Title vẫn không rỗng; missing title rows không đổi | Không quy kết |

Không gán riêng mức tăng/giảm của Token F1 hoặc judge metric cho `noise` hay
`truncate_title`, vì nhiều corruption cùng xảy ra và artifact hiện tại không tách được
ảnh hưởng nhân quả của từng event.

## 6. Các signal không đổi

Các signal sau được ghi rõ để tránh kết luận quá mức:

- `row_count`;
- `null_paper_id_rows`;
- `missing_title_rows`;
- `invalid_age_days_rows`.

## 7. Đối chiếu dự báo CP4

- Dự báo đúng: row count 24, duplicate rows 4, stale rows 3 và stale ratio 0.125.
- Invalid summaries thực tế là 2, không phải 4 như forecast. Corruption flow thực tế
  chọn duplicate records tách biệt với records bị blank summary.
- Oldest published thực tế là `2016-02-26`; forecast CP4 là giả thuyết trước khi có
  corruption log thật nên không được sửa hồi tố.

## 8. Trạng thái Checkpoint 5 — Vai trò 6

- [x] Chạy quality report riêng cho corrupted dataset.
- [x] Chạy freshness report riêng từ `published`.
- [x] Audit corrupted embedding manifest.
- [x] Lưu snapshot baseline–corrupted và metric deltas.
- [x] Nối corruption log với signal/metric khi có bằng chứng.
- [x] Ghi các signal không đổi và các event chưa thể quy kết.
- [x] Xác nhận 72 metric samples khớp 72 corrupted answers.
- [x] Viết tài liệu CP5 ghi rõ Vai trò 6.
