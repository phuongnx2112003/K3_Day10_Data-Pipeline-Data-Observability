# CP3 - Role 1: Integrator & Release Owner

> Báo cáo checkpoint 3 cho vai trò 1 của nhóm 6 người.
> Đây là mốc chốt baseline end-to-end: raw -> clean -> index -> test set -> evaluate -> quality/freshness -> report.

## 1. Mục tiêu của CP3

Checkpoint 3 là mốc mà role 1 phải chứng minh được pipeline baseline chạy được từ đầu đến cuối trên dữ liệu sạch, đồng thời mọi artifact quan trọng đều được ghi ra đúng chỗ:

- raw data
- clean data
- embedding/index
- evaluation set
- baseline metrics và answers
- quality/freshness report
- markdown report baseline

Ở mốc này, role 1 không chỉ giữ contract nữa mà phải thực sự tích hợp và xác minh baseline.

## 2. Kết quả hoàn thành

CP3 role 1 đã hoàn thành theo đúng tinh thần checkpoint.

### 2.1 Pipeline baseline đã chạy end-to-end

Đã hoàn thiện `src/pipelines/phase1.py` để:

- load settings
- load hoặc fetch raw Crossref records
- clean dữ liệu
- ghi clean CSV/JSON
- build Chroma index
- tạo hoặc load evaluation set
- evaluate baseline
- chạy quality checks
- tạo freshness report
- ghi baseline markdown report
- sinh demo answers cho smoke test

### 2.2 Entry point chạy được

Đã chỉnh các script entrypoint để chạy trực tiếp trong repo:

- `script/run_phase1.py`
- `script/run_corruption_flow.py`

### 2.3 Observability/reporting đã có output thật

Đã implement:

- `src/observability/quality.py`
- `src/observability/reporting.py`

Nhờ đó baseline có đủ:

- quality JSON
- freshness JSON
- phase1 markdown report

## 3. Thành viên và phân vai

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Xuân Phượng | 2A202601874 | Vai trò 1 | `src/ingestion/crossref.py`, `src/pipelines/phase1.py`, contract raw/clean, artifact path, integration handoff |
| 2 | Phùng Hồng Phước | 2A202601215 | Vai trò 2 | `src/ingestion/cleaning.py`, clean schema, `text_for_embedding`, `age_days` |
| 3 | Lê Công Dũng | 2A202601649 | Vai trò 3 | `src/evaluation/testset.py`, evaluation set và ground truth |
| 4 | Nguyễn Đào Nam Hải | 2A202601037 | Vai trò 4 | `src/retrieval/embeddings.py`, `src/retrieval/index.py`, retrieval/index/agent check |
| 5 | Lê Nguyễn Minh Đức | 2A202601013 | Vai trò 5 | `src/observability/quality.py`, `src/observability/reporting.py`, report artifacts |
| 6 | Trần Đức Mạnh | 2A202601567 | Vai trò 6 | `src/pipelines/phase1.py`, `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` |

## 4. Evidence thực tế

### 4.1 Chạy pipeline

Lệnh đã chạy thành công:

```bash
PYTHONPATH=src ./venv/bin/python script/run_phase1.py
```

### 4.2 Kết quả sinh ra

- Raw records: `24`
- Clean records: `24`
- Test set samples: `72`
- Baseline collection: `papers-baseline`

### 4.3 Metrics baseline

| Metric | Giá trị |
| --- | ---: |
| `retrieval_hit_rate` | `1.0` |
| `mean_token_f1` | `0.4235907473399701` |
| `judge_accuracy` | `0.3472222222222222` |
| `mean_judge_score` | `2.361111111111111` |
| `ragas` | skipped vì chưa bật `RUN_RAGAS=1` |

### 4.4 Quality và freshness

| Signal | Giá trị |
| --- | ---: |
| Tổng số clean rows | `24` |
| `paper_id` null | `0` |
| `paper_id` duplicate | `0` |
| `title` trống | `0` |
| `summary` trống | `0` |
| `text_for_embedding` trống | `0` |
| `stale_rows` | `1` |
| `fresh_rows_ratio` | `0.9583` |

Freshness summary:

- latest published: `2026-08-05`
- oldest published: `2026-01-25`
- stale rows: `1`
- freshness threshold: `180` days
- `is_fresh`: `False`

## 5. Artifact bàn giao

### 5.1 Baseline artifacts

- `data/raw/crossref_response.json`
- `data/raw/crossref_records.json`
- `data/clean/papers_clean.csv`
- `data/clean/papers_clean.json`
- `data/embeddings/papers_embeddings.json`
- `data/chroma/chroma.sqlite3`
- `data/eval/test_set.json`
- `data/results/baseline_metrics.json`
- `data/results/baseline_answers.json`
- `data/results/agent_demo_answers.json`
- `data/quality/baseline_quality.json`
- `data/quality/freshness_report.json`
- `data/reports/phase1_report.md`

### 5.2 Source files đã hoàn thiện cho CP3

- `src/pipelines/phase1.py`
- `src/observability/quality.py`
- `src/observability/reporting.py`
- `script/run_phase1.py`
- `script/run_corruption_flow.py`

## 6. Giải thích kỹ thuật

### 6.1 Tại sao dùng `papers_clean.json`

CP3 cần dữ liệu sạch đầy đủ để phục vụ index, evaluation và observability. Vì vậy pipeline dùng `papers_clean.json` làm nguồn chính cho stage baseline, thay vì chỉ dùng schema 9 cột exchange cũ.

### 6.2 Vì sao có demo answers

Demo answers được sinh ra để smoke test nhanh:

- xác minh retrieval trả về document thật
- xem thử agent có thể trả lời trên corpus không
- lưu lại một artifact dễ đọc cho team

### 6.3 Vì sao freshness không hoàn toàn fresh

Pipeline baseline có `1` record vượt ngưỡng freshness 180 ngày, nên `is_fresh = False`. Đây không phải lỗi pipeline, mà là tín hiệu thực tế từ dữ liệu đầu vào.

## 7. Điều còn lại sau CP3

CP3 role 1 đã hoàn tất baseline. Phần còn lại thuộc mốc corruption/comparison:

- corruption flow
- repair flow
- comparison report giữa baseline / corrupted / repaired

Những phần đó tương ứng với checkpoint sau, không còn là nhiệm vụ cốt lõi của CP3.

## 8. Kết luận

Role 1 ở CP3 đã hoàn thành mục tiêu:

- pipeline baseline chạy end-to-end
- artifacts được ghi đầy đủ
- metrics baseline có số liệu thật
- quality/freshness report đã sinh
- report baseline đã tạo

**Kết luận cuối:** CP3 role 1 đạt yêu cầu và có đủ evidence để bàn giao sang giai đoạn corruption / repair / comparison.

