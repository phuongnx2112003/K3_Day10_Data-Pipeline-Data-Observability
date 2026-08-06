# Checkpoint 1 — Vai trò 6: Observability

## 1. Kết quả checkpoint

Checkpoint 1 đã triển khai phần quality gate và freshness monitoring trong
`src/observability/quality.py`, đồng thời tạo evidence đầu tiên từ cleaned
dataset hiện có.

Phạm vi thực hiện đúng Vai trò 6:

- kiểm tra row count;
- kiểm tra `paper_id` null và duplicate;
- kiểm tra `title` null/blank;
- kiểm tra `summary` thiếu hoặc quá ngắn;
- kiểm tra `published` và `age_days`;
- xác định stale records;
- ghi quality/freshness JSON vào `data/quality/`.

Không sửa ingestion, cleaning, retrieval, evaluation hoặc pipeline.

## 2. Những gì đã triển khai

### `run_data_quality_checks`

Hàm nhận cleaned DataFrame, `Settings` và tên report, sau đó:

1. Kiểm tra DataFrame không rỗng.
2. Kiểm tra đủ năm cột bắt buộc: `paper_id`, `title`, `summary`, `published`,
   `age_days`.
3. Đếm `paper_id` null/blank.
4. Đếm toàn bộ dòng có `paper_id` lặp bằng `duplicated(keep=False)`.
5. Đếm `title` null/blank.
6. Đếm summary ngắn hơn 50 ký tự sau khi chuẩn hóa khoảng trắng.
7. Đếm `published` không parse được.
8. Đếm `age_days` null, không phải số hoặc âm.
9. Đếm record có `age_days` vượt ngưỡng freshness.
10. Ghi từng check với `observed`, `expected`, `success` và kết quả tổng.

Nếu thiếu cột, hàm ghi failed check vào artifact thay vì dừng bằng `KeyError`.
Điều này giúp quan sát được nguyên nhân pipeline fail.

Tên report được giới hạn là tên file, không chấp nhận path traversal như
`../outside.json`.

### `build_freshness_report`

Hàm dùng đồng thời:

- `published`: timestamp nguồn để lấy ngày mới nhất/cũ nhất và kiểm tra parse;
- `age_days`: giá trị dẫn xuất để xác định record stale;
- `settings.freshness_threshold_days`: ngưỡng hiện tại là 180 ngày.

Payload gồm:

- `source_timestamp_column`;
- `age_column`;
- `threshold_days`;
- `latest_published`, `oldest_published`;
- `stale_rows`, `stale_ratio`, `total_rows`;
- `invalid_timestamp_rows`, `invalid_age_days_rows`;
- `is_fresh`.

`is_fresh=true` chỉ khi dataset không rỗng, timestamp/age hợp lệ và không có
record vượt ngưỡng.

## 3. Cấu trúc quality check

Ví dụ một check:

```json
{
  "name": "paper_id_unique",
  "success": true,
  "observed": 0,
  "expected": "0 duplicate rows"
}
```

Kết quả tổng không hard-code. `success=true` chỉ khi toàn bộ check pass;
`failed_checks` chứa tên các check không đạt.

## 4. Evidence baseline đã tạo

Artifacts:

- `data/quality/baseline_quality.json`
- `data/quality/baseline_freshness.json`

Clean input:

- `data/clean/papers_clean.csv`
- 24 records.

Kết quả thực tế:

| Signal | Kết quả |
| --- | ---: |
| Row count | 24 |
| Missing required columns | 0 |
| Null `paper_id` | 0 |
| Duplicate `paper_id` rows | 0 |
| Null/blank title | 0 |
| Summary dưới 50 ký tự | 0 |
| Invalid `published` | 0 |
| Invalid `age_days` | 0 |
| Stale rows (`age_days > 180`) | 1 |
| Stale ratio | 4.17% |
| Latest published | 2026-08-05 |
| Oldest published | 2026-01-25 |
| Quality success | `false` |
| Freshness is fresh | `false` |

Baseline không pass hoàn toàn vì có một record 193 ngày tuổi, vượt ngưỡng 180
ngày. Đây là kết quả từ dữ liệu thật, vì vậy report giữ trạng thái fail thay vì
ép pass. Record cần thành viên data kiểm tra:

```text
paper_id: 10.35314/3y9hy151
published: 2026-01-25
age_days: 193
```

## 5. Kiểm thử đã bổ sung

File: `tests/test_observability_quality.py`

Hai tình huống được định nghĩa:

1. Dataset hợp lệ: quality pass, freshness pass và JSON được ghi đúng.
2. Dataset lỗi: duplicate ID, title rỗng, summary ngắn, ngày sai, age âm và
   record stale đều được phát hiện mà hàm không crash.

Xác minh thực tế trong môi trường hiện tại:

- Python 3.11 `compileall`: **PASS**.
- Smoke assertions trên dataset hợp lệ/lỗi: **PASS**.
- Sinh baseline quality/freshness artifacts: **PASS**.
- `pytest`: **PASS — 2 passed in 0.53s**.
- Toàn bộ test suite của repo: **PASS — 4 passed in 0.78s**.

Lệnh xác minh cuối cùng:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m pytest -q tests/test_observability_quality.py
```

Output:

```text
..                                                                       [100%]
2 passed in 0.53s
```

Chạy toàn bộ test suite:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m pytest -q
```

```text
....                                                                     [100%]
4 passed in 0.78s
```

## 6. Vấn đề môi trường đã xử lý

`.venv` cũ trỏ đến Python Windows Store đã mất nên không khởi động được. Đã:

1. Giữ bản cũ tại `.venv-broken` để có thể khôi phục.
2. Cài runtime Python 3.11.14 bằng uv.
3. Tạo `.venv` mới với Python 3.11.14.
4. Bootstrap pip trong `.venv`.
5. Cài `pandas`, `python-dotenv` và `pytest` để kiểm thử Role 6.

`uv sync --extra dev` bị treo trong quá trình truy cập package/cache nên đã
được dừng. Kiểm thử cuối cùng chạy trực tiếp bằng Python 3.11 trong `.venv`,
không còn dùng compatibility shim Python 3.10.

## 7. Dependency cần từ thành viên khác

### Cần thành viên Data foundation xác nhận

- Record `10.35314/3y9hy151` có đúng thuộc baseline mong muốn không.
- Baseline có bắt buộc mọi record không quá 180 ngày hay nhóm chấp nhận một tỷ
  lệ stale nhất định.
- `age_days` được tính tại ngày/run timestamp nào và có cần tái tính mỗi lần
  pipeline chạy không.

### Cần thành viên Pipeline thống nhất

- Gọi `run_data_quality_checks(df, settings, "baseline_quality")`.
- Gọi `build_freshness_report` với path riêng cho baseline, corrupted, repaired.
- Không ghi mọi trạng thái vào `settings.paths.freshness_report` duy nhất.

## 8. Cách chạy lại

Sau khi dependency được cài đầy đủ:

```powershell
uv sync --extra dev
uv run pytest -q tests/test_observability_quality.py
```

Quality và freshness sẽ được pipeline gọi ở checkpoint tích hợp. Không nên sửa
tay JSON artifact vì report phải phản ánh DataFrame thật.

## 9. Trạng thái Checkpoint 1 — Vai trò 6

- [x] Hoàn thiện row count check.
- [x] Hoàn thiện `paper_id` null/unique/duplicate check.
- [x] Hoàn thiện title/summary missing check.
- [x] Tạo freshness từ `published` và `age_days`.
- [x] Ghi baseline quality report đầu tiên.
- [x] Ghi baseline freshness report đầu tiên.
- [x] Thêm unit test cho dữ liệu pass và corrupted.
- [x] Chạy pytest: 2 test passed.
- [ ] Nhận quyết định của nhóm về một baseline record vượt ngưỡng 180 ngày.
