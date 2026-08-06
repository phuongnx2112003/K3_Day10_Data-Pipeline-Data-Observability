# Checkpoint 3 — Vai trò 6: Observability

## 1. Trạng thái hiện tại

Phần code Checkpoint 3 đã hoàn thiện. Sau khi tích hợp `main`, Role 6 đã nhận đủ
hai artifacts từ người phụ trách Evaluation:

- `data/results/baseline_metrics.json`
- `data/results/baseline_answers.json`

Runner đã sinh `phase1_report.md` từ số liệu thật và validation đã pass.

## 2. Những gì đã triển khai

### Baseline observability runner

File mới: `src/observability/baseline.py`.

Runner thực hiện theo thứ tự:

1. Đọc `data/clean/papers_clean.csv`.
2. Chạy lại data quality checks.
3. Chạy lại freshness report.
4. Audit embedding manifest.
5. Kiểm tra các input bắt buộc.
6. Ghi baseline observability snapshot.
7. Nếu thiếu metrics/answers: ghi trạng thái `pending` và không sinh report.
8. Nếu đủ input: sinh `phase1_report.md`.
9. Đối chiếu Markdown với payload JSON/CSV.
10. Kiểm tra `metrics.samples` bằng số phần tử trong `baseline_answers.json`.

### Report validator

Hàm `validate_phase1_report` trong `src/observability/reporting.py` tạo lại nội
dung mong đợi từ chính các payload nguồn và so sánh với Markdown đã ghi.

Validation chỉ pass khi:

- report tồn tại;
- toàn bộ nội dung khớp payload;
- đủ năm metrics bắt buộc;
- không có số liệu bị sửa tay hoặc thiếu.

Kết quả validation sẽ được lưu tại:

- `data/quality/baseline_report_validation.json`

File này chỉ xuất hiện sau khi report thật được tạo.

### Baseline snapshot có metrics

`build_observability_snapshot` đã được mở rộng để lưu:

- `samples`;
- `retrieval_hit_rate`;
- `mean_token_f1`;
- `judge_accuracy`;
- `mean_judge_score`;
- `answers_count`.

Các trường metric đã được điền từ `baseline_metrics.json`; `answers_count` được
lấy độc lập từ `baseline_answers.json` để đối chiếu sample count.

## 3. Artifacts đã cập nhật

- `data/quality/baseline_quality.json`
- `data/quality/baseline_freshness.json`
- `data/quality/baseline_embedding_audit.json`
- `data/quality/baseline_observability_snapshot.json`
- `data/quality/baseline_report_readiness.json`

Readiness hiện tại:

```json
{
  "status": "complete",
  "missing_inputs": [],
  "report_generated": true,
  "report_validated": true,
  "metrics_samples": 72,
  "answers_count": 72,
  "metrics_samples_match_answers": true
}
```

## 4. Baseline signals hiện tại

| Signal | Giá trị |
| --- | ---: |
| Row count | 24 |
| Null paper IDs | 0 |
| Duplicate paper ID rows | 0 |
| Missing title rows | 0 |
| Invalid summary rows | 0 |
| Invalid age rows | 0 |
| Stale rows | 1 |
| Stale ratio | 0.0417 |
| Indexed documents | 24 |
| Collection | `papers-baseline` |

Hai cảnh báo baseline vẫn còn:

1. Một record vượt freshness threshold 180 ngày.
2. Embedding manifest chứa `persist_path` của workspace cũ.

Không thay đổi hoặc che các cảnh báo này trong report.

## 5. Cách hoàn tất khi nhận hai file Evaluation

Đặt file đúng vị trí:

```text
data/results/baseline_metrics.json
data/results/baseline_answers.json
```

Sau đó chạy:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m observability.baseline
```

Kết quả mong đợi:

```text
Baseline observability status: complete
```

Artifacts được tạo/cập nhật:

- `data/reports/phase1_report.md`
- `data/quality/baseline_report_validation.json`
- `data/quality/baseline_report_readiness.json`
- `data/quality/baseline_observability_snapshot.json`

Nếu số dòng answers không khớp `metrics.samples`, trạng thái sẽ là `invalid`
thay vì `complete`.

## 6. Kiểm thử

Test bao phủ cả hai nhánh:

- thiếu metrics/answers: runner trả `pending`, không tạo report giả;
- đủ metrics/answers: runner tạo report, validation pass và sample count khớp.

Lệnh:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m pytest -q tests/test_observability_quality.py tests/test_observability_reporting.py tests/test_observability_baseline.py
```

Kết quả:

```text
......                                                                   [100%]
6 passed in 3.88s
```

Toàn bộ test suite sau khi tích hợp:

```text
...........                                                              [100%]
11 passed in 0.94s
```

## 7. Dependency cần bàn giao

Người phụ trách Evaluation cần cung cấp:

### `baseline_metrics.json`

Tối thiểu có:

```json
{
  "samples": 0,
  "retrieval_hit_rate": 0.0,
  "mean_token_f1": 0.0,
  "judge_accuracy": 0.0,
  "mean_judge_score": 0.0,
  "ragas": {}
}
```

Các số trên chỉ minh họa schema, không được dùng làm kết quả thật.

### `baseline_answers.json`

Phải là JSON list chứa answers thật. Số phần tử phải bằng `samples` trong
metrics.

## 8. Trạng thái Checkpoint 3 — Vai trò 6

- [x] Chạy data quality baseline.
- [x] Chạy freshness baseline.
- [x] Chạy embedding audit baseline.
- [x] Ghi baseline signals snapshot.
- [x] Hoàn thiện `generate_phase1_report`.
- [x] Hoàn thiện report validation với JSON/CSV thật.
- [x] Thêm runner tự hoàn tất khi evaluation artifacts xuất hiện.
- [x] Ghi readiness artifact trung thực.
- [x] Chạy 6 test CP3 thành công.
- [x] Chạy toàn bộ test suite sau merge: 11 test thành công.
- [x] Nhận `baseline_metrics.json`.
- [x] Nhận `baseline_answers.json`.
- [x] Sinh và validate `phase1_report.md` từ artifacts thật.
