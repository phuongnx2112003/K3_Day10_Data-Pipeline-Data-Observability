# Checkpoint 0 — Vai trò 6: Observability

## 1. Vai trò và phạm vi phụ trách

Vai trò 6 chịu trách nhiệm quan sát chất lượng dữ liệu của hệ thống RAG, gồm:

- `quality`: phát hiện dữ liệu thiếu, trùng, rỗng hoặc không hợp lệ;
- `freshness`: phát hiện dữ liệu quá cũ;
- `reports`: tổng hợp quality, freshness và RAG metrics thành báo cáo kiểm chứng được.

Phạm vi phụ trách:

- `src/observability/quality.py`
- `src/observability/reporting.py`
- `data/quality/`
- báo cáo Markdown do observability tạo trong `data/reports/`.

Vai trò 6 không sở hữu test set, evaluator, ingestion, cleaning, embedding,
agent, corruption hoặc pipeline orchestration. Vai trò 6 nhận output của các
phần đó để đo, cảnh báo và báo cáo.

## 2. Mục tiêu Checkpoint 0

Checkpoint 0 chốt thiết kế trước khi có clean dataset:

1. Liệt kê artifacts phải có sau baseline và corruption flow.
2. Định nghĩa quality/freshness signals.
3. Chốt timestamp nguồn và ngưỡng stale.
4. Phác thảo report chứng minh dữ liệu xấu ảnh hưởng đến RAG.
5. Xác định dependency cần nhận từ các vai trò khác.

## 3. Artifact cần có sau baseline

| Artifact | Công dụng |
| --- | --- |
| `data/clean/papers_clean.csv` | Chạy quality và freshness checks |
| `data/results/baseline_metrics.json` | Mốc chất lượng RAG ban đầu |
| `data/results/baseline_answers.json` | Evidence giải thích hit/miss |
| `data/quality/baseline_quality.json` | Kết quả từng quality check |
| `data/quality/baseline_freshness.json` | Freshness signals baseline |
| `data/reports/phase1_report.md` | Báo cáo tổng hợp baseline |

Tên quality/freshness file là contract đề xuất. Pipeline owner cần thống nhất
trước khi tích hợp để không ghi đè các trạng thái khác.

## 4. Artifact cần có sau corruption flow

### Corrupted

- `data/clean/papers_clean_corrupted.csv`
- `data/results/corruption_log.json`
- `data/results/corrupted_metrics.json`
- `data/results/corrupted_answers.json`
- `data/quality/corrupted_quality.json`
- `data/quality/corrupted_freshness.json`

### Repaired

- `data/clean/papers_clean_repaired.csv`
- `data/results/repaired_metrics.json`
- `data/results/repaired_answers.json`
- `data/quality/repaired_quality.json`
- `data/quality/repaired_freshness.json`
- `data/reports/corruption_report.md`

Mỗi trạng thái phải có file riêng. Không ghi corrupted/repaired lên baseline.

## 5. Định nghĩa quality signals

### Row count

- Tổng số dòng của DataFrame.
- Baseline tối thiểu: `row_count > 0`.
- Dùng để phát hiện dataset rỗng hoặc bị mất record.
- Khi so sánh phải báo cả số lượng và delta với baseline.

### Null `paper_id`

- Đếm `null`, chuỗi rỗng và chuỗi chỉ có khoảng trắng.
- Kỳ vọng: `0`.
- Record thiếu ID không thể truy vết hoặc khớp ground-truth document ID.

### Duplicate `paper_id`

- Đếm số dòng có ID lặp, không chỉ đếm số giá trị ID bị lặp.
- Kỳ vọng: `0`.
- Duplicate có thể làm lệch row count, index và retrieval.

### Null/blank `title`

- Đếm `null`, chuỗi rỗng và chuỗi chỉ có khoảng trắng.
- Kỳ vọng: `0`.
- Title được dùng cho exact lookup và metadata.

### Summary không đạt chất lượng

- Đếm summary null, rỗng hoặc quá ngắn.
- Ngưỡng đề xuất: ít nhất 50 ký tự sau khi chuẩn hóa khoảng trắng.
- Ngưỡng thực tế phải được ghi trong JSON để audit được.

### `age_days` không hợp lệ

Một dòng lỗi khi `age_days` bị thiếu, không phải số, là số âm hoặc không nhất
quán rõ ràng với `published` tại ngày chạy. Kỳ vọng: `0` dòng lỗi.

## 6. Định nghĩa freshness signals

### Timestamp nguồn

Cột `published` là timestamp nguồn. Không dùng thời gian tạo file hoặc thời
gian chạy pipeline thay thế.

`age_days` là trường dẫn xuất:

```text
age_days = ngày chạy UTC - ngày published
```

### Ngưỡng stale

Dùng `settings.freshness_threshold_days`, hiện mặc định là 180 ngày:

```text
age_days <= 180  -> fresh
age_days > 180   -> stale
```

### Payload freshness dự kiến

```json
{
  "source_timestamp_column": "published",
  "threshold_days": 180,
  "latest_published": "2026-07-20",
  "oldest_published": "2025-01-10",
  "stale_rows": 3,
  "total_rows": 24,
  "stale_ratio": 0.125,
  "invalid_timestamp_rows": 0,
  "is_fresh": false
}
```

Quy tắc đề xuất: `is_fresh=true` khi dataset không rỗng, không có timestamp lỗi
và không có dòng stale. Nếu nhóm cho phép một tỷ lệ stale, pipeline owner phải
thống nhất ngưỡng trước khi chạy baseline.

## 7. Cấu trúc quality report dự kiến

```json
{
  "report_name": "baseline_quality",
  "total_rows": 24,
  "success": true,
  "checks": [
    {
      "name": "paper_id_not_null",
      "success": true,
      "observed": 0,
      "expected": 0
    }
  ]
}
```

Không hard-code `success=true`. Report tổng chỉ pass khi mọi check bắt buộc pass.

## 8. Phác thảo báo cáo baseline

`phase1_report.md` cần có:

1. Thông tin nguồn và row count.
2. Bảng quality check: tên, observed, expected, pass/fail.
3. Latest/oldest timestamp, stale rows, stale ratio và freshness status.
4. RAG metrics nhận từ evaluator.
5. Fallback hoặc giới hạn đã xảy ra khi đánh giá.
6. Đường dẫn JSON/CSV làm evidence.

Report phải lấy số từ payload thật, không tự viết số hoặc tự kết luận.

## 9. Phác thảo report chứng minh dữ liệu xấu làm RAG kém

`corruption_report.md` cần bảng:

| Signal/metric | Baseline | Corrupted | Repaired | Delta corrupted | Mức phục hồi |
| --- | ---: | ---: | ---: | ---: | ---: |
| Row count | B | C | R | C - B | R - B |
| Duplicate rows | B | C | R | C - B | R - B |
| Stale rows | B | C | R | C - B | R - B |
| Retrieval hit rate | B | C | R | C - B | R - B |
| Mean token F1 | B | C | R | C - B | R - B |
| Judge accuracy | B | C | R | C - B | R - B |

Chuỗi evidence:

```text
corruption_log
    -> quality/freshness signal xấu đi
    -> answer hoặc RAG metric xấu đi
    -> repair từ raw source
    -> signal và metric được đo lại
```

Ví dụ sau khi có số thật:

```text
Corruption làm 5 summary rỗng. invalid_summary_rows tăng từ 0 lên 5 và
mean_token_f1 giảm từ X xuống Y. Sau repair, vi phạm trở về 0 và metric đạt Z.
```

Nếu quality xấu đi nhưng RAG metric không đổi, report phải ghi chưa quan sát
được tác động lên metric, không được khẳng định RAG đã kém đi.

## 10. Dependency cần từ các vai trò khác

### Người phụ trách ingestion/cleaning

- DataFrame có `paper_id`, `title`, `summary`, `published`, `age_days`.
- Quy tắc tính `age_days` và ngày tham chiếu.
- Baseline, corrupted, repaired datasets ở path riêng.
- Corruption log có loại lỗi, record bị tác động và before/after count.

### Người phụ trách evaluation

- Metrics JSON baseline, corrupted, repaired có cùng schema.
- Answers JSON để giải thích case metric giảm hoặc không phục hồi.
- Ba trạng thái dùng cùng test set.

### Người phụ trách pipeline/integration

- Gọi quality/freshness checks cho từng trạng thái.
- Truyền report name và output path riêng.
- Chỉ tạo comparison report khi đủ metrics, quality và freshness payload.

## 11. Trạng thái Checkpoint 0 — Vai trò 6

- [x] Đã xác định đúng phạm vi quality, freshness và reports.
- [x] Đã liệt kê artifacts baseline, corrupted và repaired.
- [x] Đã định nghĩa row count, null, duplicate và `age_days` signals.
- [x] Đã chốt `published` là timestamp nguồn.
- [x] Đã phác thảo report nối data quality với RAG metrics.
- [x] Đã ghi dependency cần từ các vai trò khác.
- [ ] Chờ cleaned dataset/schema thật để triển khai checkpoint tiếp theo.

