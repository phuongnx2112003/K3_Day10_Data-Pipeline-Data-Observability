# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K3 |
| Tên nhóm | 2k345 |
| Repository | `https://github.com/phuongnx2112003/K3_Day10_Data-Pipeline-Data-Observability-2k345-E403` |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Xuân Phượng | 2A202601874 | Vai trò 1 | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`, orchestration, release |
| 2 | Phùng Hồng Phước | 2A202601215 | Vai trò 2 | `src/ingestion/cleaning.py`, data model, `text_for_embedding`, `age_days` |
| 3 | Lê Công Dũng | 2A202601649 | Vai trò 3 | `src/evaluation/testset.py`, evaluation set, ground truth IDs |
| 4 | Nguyễn Đào Nam Hải | 2A202601037 | Vai trò 4 | `src/retrieval/index.py`, `src/retrieval/agent.py`, embeddings/index/agent |
| 5 | Lê Nguyễn Minh Đức | 2A202601013 | Vai trò 5 | `src/evaluation/metrics.py`, `src/retrieval/qa.py`, evaluation metrics |
| 6 | Trần Đức Mạnh | 2A202601567 | Vai trò 6 | `src/observability/quality.py`, `src/observability/reporting.py`, observability/reporting |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành pipeline end-to-end từ Crossref raw records đến baseline evaluation, quality/freshness monitoring, corruption flow, repair và comparison report. Baseline tạo đủ artifact ở `data/raw/`, `data/clean/`, `data/eval/`, `data/embeddings/`, `data/results/`, `data/quality/` và `data/reports/`. Bộ test set có 72 câu hỏi trên 24 bài báo, cùng một tập câu hỏi được giữ nguyên cho baseline, corrupted và repaired để so sánh công bằng. Corruption có tác động rõ nhất đến retrieval/answer quality là `latest_drop` kết hợp với các lỗi `missing summary`, `noise`, `truncate_title`, `old_date` và `duplicate`. Khi corruption chạy, retrieval hit rate giảm từ `1.0` xuống `0.9167`, mean token F1 giảm từ `0.7569` xuống `0.6603`, judge accuracy giảm từ `0.6667` xuống `0.6250`. Repair từ raw snapshot đã phục hồi các metric về baseline. Giới hạn còn lại là freshness của repaired vẫn `False` vì dữ liệu nguồn vốn đã có một bài báo stale; repair khôi phục đúng dữ liệu gốc chứ không thay đổi lịch sử xuất bản.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref REST API | Fetch, retry, parse, lưu raw response/raw records | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Nguyễn Xuân Phượng |
| Cleaning | Raw records | Làm sạch text, chuẩn hóa schema, deduplicate, tính `age_days`, `text_for_embedding` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Phùng Hồng Phước |
| Embedding/index | Clean dataframe | Build MiniLM embeddings, Chroma collection, manifest | `data/embeddings/`, `data/chroma/` | Nguyễn Đào Nam Hải |
| Evaluation | Clean dataframe + test set | Sinh test set, chạy evaluator, tính metrics | `data/eval/test_set.json`, `data/results/*_metrics.json`, `data/results/*_answers.json` | Lê Công Dũng / Lê Nguyễn Minh Đức |
| Observability | Clean/corrupted/repaired artifacts | Quality checks, freshness, embedding audit, Markdown report | `data/quality/`, `data/reports/` | Trần Đức Mạnh |
| Corruption/repair | Clean baseline + raw snapshot | Corrupt có kiểm soát, repair từ raw, so sánh 3 trạng thái | `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` | Nguyễn Xuân Phượng + Phùng Hồng Phước |
| Orchestration | Tất cả artifact trên | Freeze scope, chạy baseline/corruption flow, review final evidence | Báo cáo cuối và artifact bàn giao | Nguyễn Xuân Phượng |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | `gemini` |
| `LLM_MODEL` | `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | `24` |
| Retrieval `top_k` | `4` |
| Freshness threshold | `180` ngày |
| Random seed, nếu có | `42` |

### Lệnh cài đặt

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| --- | --- | --- | --- |
| Baseline pipeline | Thành công | 2026-08-06 | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow | Thành công | 2026-08-06 | `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | Crossref REST API |
| Query/filter | `agentic retrieval augmented generation large language model` / `from-pub-date:2026-02-07,has-abstract:true` |
| Thời điểm lấy dữ liệu | Snapshot đã lưu trong `data/raw/` |
| Số record nhận được | `24` |
| Cơ chế retry/backoff | Có retry cho lỗi HTTP tạm thời và lưu raw snapshot trước parse |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | string | Có | Định danh bài báo / DOI | Loại nếu thiếu, deduplicate theo `paper_id` |
| `title` | string | Có | Tiêu đề bài báo | Loại nếu thiếu, normalize whitespace |
| `summary` | string | Không | Abstract / tóm tắt | Điền chuỗi rỗng nếu thiếu |
| `authors_joined` | string | Không | Tác giả đã join | Chuẩn hóa list thành chuỗi |
| `categories_joined` | string | Không | Chủ đề đã join | Chuẩn hóa list thành chuỗi |
| `published` | string | Có | Ngày xuất bản | Parse chuẩn YYYY-MM-DD |
| `age_days` | int | Có | Độ cũ của bản ghi | Tính từ `published` |
| `text_for_embedding` | string | Có | Nội dung đưa vào embedding | Ghép title + summary + authors + categories |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
| --- | --- | ---: | --- |
| Chuẩn hóa whitespace và text | Validity | 24 | `data/clean/papers_clean.json` |
| Deduplicate theo `paper_id` | Uniqueness | 0 ở baseline, 2 ở corrupted | `data/quality/*_quality.json` |
| Tạo `text_for_embedding` | Completeness | 24 | `data/embeddings/*.json` |
| Tính `age_days` | Freshness | 24 | `data/quality/*_freshness.json` |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

`text_for_embedding` được ghép từ title, summary, authors_joined và categories_joined để vector hóa tốt hơn. `paper_id` giữ vai trò document ID ổn định xuyên suốt raw → clean → index → eval. `age_days` được tính từ `published` để dùng cho freshness monitoring.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | `72` |
| Các `question_type` | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID | Lấy từ `paper_id` của clean data, lưu trong `ground_truth_doc_ids` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection | `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Retrieval `top_k` | `4` |
| LLM provider/model | `gemini` / `gemini-2.5-flash` |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Để so sánh công bằng. Chỉ khi giữ nguyên test set thì sự thay đổi metric mới phản ánh đúng tác động của dữ liệu và repair, không bị nhiễu bởi bộ câu hỏi khác nhau.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| Raw response/records | `data/raw/` | Có | Snapshot đã lưu |
| Cleaned dataset | `data/clean/` | Có | `papers_clean.csv/json` |
| Embedding manifest/index | `data/embeddings/`, `data/chroma/` | Có | Collection baseline riêng |
| Evaluation set | `data/eval/` | Có | 72 câu hỏi |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Metrics thật |
| Quality/freshness | `data/quality/` | Có | Baseline quality/freshness |
| Baseline report | `data/reports/phase1_report.md` | Có | Markdown report |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | `1.0` | Tất cả câu hỏi đều có ground-truth doc trong top-k |
| `mean_token_f1` | `0.7569` | Câu trả lời khớp tốt với ground truth |
| `judge_accuracy` | `0.6806` | Judge chấm đúng phần lớn câu trả lời |
| `mean_judge_score` | `3.9583` | Điểm judge trung bình khá cao |
| Ragas | Skipped | Chưa bật `RUN_RAGAS=1` |

## 8. Data quality và freshness

### Quality checks

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| `paper_id_unique` | Uniqueness | 0 duplicate | Pass | `data/quality/baseline_quality.json` |
| `title_not_blank` | Completeness | 0 blank | Pass | `data/quality/baseline_quality.json` |
| `summary_present_ratio` | Completeness | Gần 1.0 | Pass | `data/quality/baseline_quality.json` |
| `age_days_valid` | Validity/Freshness | 0 invalid | Pass | `data/quality/baseline_quality.json` |

### Freshness

| Thuộc tính | Giá trị |
| --- | --- |
| Freshness được đo tại | `data/quality/baseline_freshness.json` |
| Timestamp mới nhất | `2026-08-05` |
| Ngưỡng freshness | `180` ngày |
| Trạng thái baseline | `False` |
| Lý do | Có `1` stale row trong nguồn gốc |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| --- | --- | ---: | --- | --- | --- |
| `latest_drop` | Xóa 2 record mới nhất | 2 | Giảm retrieval hit rate | Hit rate giảm `1.0 -> 0.9167` | Rebuild từ raw snapshot |
| `missing` / `noise` summary | Blank và thêm noise vào summary | 4 | Giảm completeness | `blank_summary = 2` | Re-run cleaning từ raw |
| `truncate_title` | Cắt ngắn title | 2 | Giảm signal ngữ nghĩa | Title length giảm rõ rệt | Rebuild clean data |
| `old_date` | Lùi `published` 10 năm | 2 | Tăng stale rows | `stale_rows = 3` | Rebuild từ raw snapshot |
| `duplicate` | Nhân bản 2 record | 2 | Vi phạm uniqueness | `duplicate_paper_id = 2` | Deduplicate khi clean lại |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log có đủ event, record IDs, tham số và trước/sau số lượng

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Repair không chỉnh sửa trực tiếp file corrupted. Pipeline load lại raw snapshot từ `data/raw/crossref_records.json`, rồi chạy cleaning từ đầu để tạo repaired clean artifacts. Nhờ vậy, lineage giữ nguyên và comparison giữa baseline/corrupted/repaired là công bằng.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | `1.0` | `0.9167` | `1.0` | `-0.0833` | `100%` | Hit rate phục hồi hoàn toàn |
| `mean_token_f1` | `0.7569` | `0.6603` | `0.7569` | `-0.0967` | `100%` | Answer quality phục hồi hoàn toàn |
| `judge_accuracy` | `0.6806` | `0.6250` | `0.6667` | `-0.0556` | `97.9%` | Phục hồi gần baseline nhưng chưa hoàn toàn |
| `mean_judge_score` | `3.9583` | `3.7778` | `3.9583` | `-0.1806` | `100%` | Điểm judge phục hồi hoàn toàn |
| Quality checks pass/fail | Pass | Fail | Pass | Rõ ràng | Rõ ràng | Corrupted fail vì duplicate/blank summary |
| Freshness status | False | False | False | Không đổi | Không đổi | Repair không đổi lịch sử xuất bản |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. `latest_drop` + `missing summary` + `duplicate` → quality/freshness signal xấu đi → retrieval/answer metric giảm.
2. Re-run cleaning từ raw snapshot → quality/freshness phục hồi → retrieval hit rate, token F1 và mean judge score phục hồi về baseline.

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Corruption flow ban đầu là starter stub, baseline và corrupted artifacts dễ bị ghi đè nếu dùng chung path/collection.
- **Nguyên nhân:** Thiếu orchestration chính thức cho `corruption -> rebuild -> evaluate -> repair -> compare`.
- **Cách xử lý:** Vai trò 1 ghép riêng `src/pipelines/corruption_flow.py`, tách collection/path cho baseline/corrupted/repaired và dùng comparison report sinh từ JSON thật.
- **Cách xác minh:** `python script/run_corruption_flow.py` tạo ra `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md`.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| Freshness của repaired vẫn `False` | Repair không làm thay đổi lịch sử xuất bản | Chỉ có thể cải thiện bằng nguồn dữ liệu mới hoặc threshold khác |
| `RUN_RAGAS` chưa bật | Chưa có Ragas score đầy đủ | Bật `RUN_RAGAS=1` và chạy lại evaluation |
| Judge có fallback heuristic | Có thể làm metric hơi dao động | Dùng LLM judge thật khi có key hợp lệ |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
