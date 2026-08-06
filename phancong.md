# Phân Công Công Việc - Day 10: Data Pipeline & Data Observability

> Mẫu phân công cho nhóm 6 người. Có thể thay `Người 1..6` bằng tên thật của từng thành viên.
> Mục tiêu: chia việc để làm song song, mỗi người có một đầu việc chính rõ ràng, và ghi rõ phụ thuộc giữa các task.

## 1. Mục tiêu chung của nhóm

Nhóm cần hoàn thành một pipeline end-to-end gồm:

1. Lấy dữ liệu từ Crossref.
2. Làm sạch và chuẩn hóa dữ liệu.
3. Tạo evaluation set.
4. Build embedding và vector index.
5. Chạy baseline pipeline và đánh giá.
6. Tạo quality/freshness report.
7. Tạo corruption flow, repair dữ liệu và so sánh kết quả.

## 2. Nguyên tắc phân việc

- Mỗi người có **một module chính** để chịu trách nhiệm.
- Mỗi task cần có **input, output, và người phụ thuộc** rõ ràng.
- Không để một người ôm cả ingestion, cleaning, evaluation và orchestration cùng lúc.
- Các phần có thể làm song song thì làm song song, nhưng phải thống nhất schema sớm.

## 3. Phân công chính

| Người | Vai trò chính | Module/deliverable sở hữu | Output cần bàn giao |
| --- | --- | --- | --- |
| Người 1 | Source / Ingestion owner | `src/ingestion/crossref.py` | Raw response, raw records, schema input, lưu vào `data/raw/` |
| Người 2 | Cleaning / Data model owner | `src/ingestion/cleaning.py` | Cleaned dataset, `text_for_embedding`, `published`, `age_days`, lưu vào `data/clean/` |
| Người 3 | Evaluation set owner | `src/evaluation/testset.py` | Test set trong `data/eval/` với `question`, `ground_truth`, `ground_truth_doc_ids`, `question_type` |
| Người 4 | Retrieval / Index / Agent owner | `src/retrieval/embeddings.py`, `src/retrieval/index.py`, kiểm tra `src/retrieval/agent.py` | Embedding manifest/index trong `data/embeddings/`, retrieval chạy được |
| Người 5 | Observability / Reporting owner | `src/observability/quality.py`, `src/observability/reporting.py` | Quality/freshness artifacts, `data/quality/`, `data/reports/phase1_report.md` |
| Người 6 | Integration / Corruption owner | `src/pipelines/phase1.py`, `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | Baseline run end-to-end, corruption log, repaired run, comparison report |

## 4. Chi tiết từng task và phụ thuộc

### 4.1 Người 1 - Source / Ingestion owner

**Việc làm**

- Gọi Crossref API.
- Parse response thành raw records.
- Lưu raw response và raw records vào `data/raw/`.
- Chốt schema đầu vào cho các module sau.

**Phụ thuộc**

- Không phụ thuộc vào ai để bắt đầu.

**Người khác phụ thuộc vào Người 1**

- Người 2 cần raw records để viết cleaning.
- Người 3 cần hiểu field nào có sẵn để tạo evaluation set.
- Người 6 cần raw data để repair dữ liệu sau corruption.

**Output bàn giao**

- `data/raw/` có raw response.
- `data/raw/` có raw records đã parse.
- Mô tả schema các field chính.

---

### 4.2 Người 2 - Cleaning / Data model owner

**Việc làm**

- Làm sạch record không hợp lệ.
- Chuẩn hóa title, summary, authors, categories.
- Tạo `text_for_embedding`.
- Tính `published` và `age_days`.
- Deduplicate nếu cần.

**Phụ thuộc**

- Phụ thuộc Người 1 để có raw records.

**Người khác phụ thuộc vào Người 2**

- Người 3 cần cleaned dataset để tạo evaluation set.
- Người 4 cần cleaned data để build embedding/index.
- Người 5 cần cleaned data để tính quality/freshness.
- Người 6 cần cleaned baseline để tạo corruption và để repair so sánh.

**Output bàn giao**

- `data/clean/` có cleaned CSV/JSON.
- Mô tả cleaning rules và schema cuối.

---

### 4.3 Người 3 - Evaluation set owner

**Việc làm**

- Tạo bộ câu hỏi từ cleaned dataset.
- Đảm bảo mỗi sample có:
  - `question`
  - `ground_truth`
  - `ground_truth_doc_ids`
  - `question_type`
- Kiểm tra test set dùng được cho cả baseline, corrupted và repaired.

**Phụ thuộc**

- Phụ thuộc Người 2 vì cần cleaned dataset.

**Người khác phụ thuộc vào Người 3**

- Người 6 cần evaluation set chung để chạy baseline và corruption flow.
- Người 4 có thể dùng test set để kiểm tra retrieval/agent.
- Người 5 có thể dùng test set để ghi nhận report kết quả đánh giá.

**Output bàn giao**

- `data/eval/` có test set.
- Mô tả cách chọn câu hỏi và ground truth.

---

### 4.4 Người 4 - Retrieval / Index / Agent owner

**Việc làm**

- Tạo embedding bằng model có sẵn.
- Tạo vector store / ChromaDB index.
- Kiểm tra semantic search, exact lookup theo `paper_id` hoặc title.
- Xác minh agent có thể trả lời trên corpus local.

**Phụ thuộc**

- Phụ thuộc Người 2 vì cần cleaned dataset để embed.
- Phụ thuộc Người 3 để test retrieval trên evaluation set.

**Người khác phụ thuộc vào Người 4**

- Người 6 cần index/retrieval chạy được để baseline pipeline hoàn chỉnh.
- Người 5 có thể cần thông tin retrieval output để ghi vào report.

**Output bàn giao**

- `data/embeddings/` có manifest/index.
- Ghi rõ embedding model, collection name, `top_k`.

---

### 4.5 Người 5 - Observability / Reporting owner

**Việc làm**

- Implement data quality checks.
- Implement freshness monitoring.
- Sinh báo cáo Markdown.
- Tổng hợp kết quả baseline vào `phase1_report.md`.

**Phụ thuộc**

- Phụ thuộc Người 2 vì quality/freshness cần cleaned data.
- Phụ thuộc Người 3 và Người 4 vì report cần metric và evaluation result.
- Phụ thuộc Người 6 để có kết quả chạy thực tế đưa vào report.

**Người khác phụ thuộc vào Người 5**

- Người 6 cần report format và quality check output để ghép vào baseline/corruption flow.

**Output bàn giao**

- `data/quality/` có quality checks và freshness artifacts.
- `data/reports/phase1_report.md`.

---

### 4.6 Người 6 - Integration / Corruption owner

**Việc làm**

- Ghép baseline pipeline trong `src/pipelines/phase1.py`.
- Tạo corruption trong `src/ingestion/corruption.py`.
- Ghép corruption flow trong `src/pipelines/corruption_flow.py`.
- Chạy baseline, corrupted, repaired và so sánh metrics.

**Phụ thuộc**

- Phụ thuộc Người 1, 2, 3, 4, 5 vì đây là người tích hợp toàn pipeline.

**Người khác phụ thuộc vào Người 6**

- Không ai bắt buộc phụ thuộc ngược, nhưng kết quả của Người 6 là output cuối để nhóm viết báo cáo chung.

**Output bàn giao**

- `data/results/baseline_metrics.json`
- `data/results/corruption_log.json`
- `data/reports/corruption_report.md`
- So sánh baseline / corrupted / repaired

## 5. Chuỗi phụ thuộc tổng thể

```text
Người 1 (Crossref ingestion)
    -> Người 2 (cleaning)
    -> Người 3 (evaluation set)
    -> Người 4 (embedding/index/agent)
    -> Người 5 (quality/freshness/report)
    -> Người 6 (phase1 + corruption flow + comparison)
```

### Phụ thuộc chi tiết

- Người 2 phụ thuộc Người 1.
- Người 3 phụ thuộc Người 2.
- Người 4 phụ thuộc Người 2, và test bằng Người 3.
- Người 5 phụ thuộc Người 2, 3, 4.
- Người 6 phụ thuộc toàn bộ các người còn lại.

## 6. Việc có thể làm song song

### Có thể bắt đầu ngay

- Người 1 bắt đầu ingestion.
- Người 5 có thể đọc rubric và dựng khung report.
- Người 6 có thể đọc flow, chuẩn bị orchestration và danh sách artifact cần có.

### Có thể làm sau khi có schema sơ bộ

- Người 2 bắt đầu cleaning khi Người 1 chốt raw schema.
- Người 3 bắt đầu thiết kế test set khi Người 2 chốt schema clean.
- Người 4 bắt đầu embedding/index khi Người 2 chốt `text_for_embedding`.

### Chỉ nên tích hợp sau cùng

- Người 6 chỉ ghép pipeline end-to-end sau khi Người 1, 2, 3, 4, 5 chốt contract.

## 7. Checklist bàn giao giữa các người

### Người 1 bàn giao cho Người 2 và 6

- Raw schema
- Sample raw records
- File lưu trong `data/raw/`

### Người 2 bàn giao cho Người 3, 4, 5, 6

- Cleaned dataset
- `text_for_embedding`
- `published`, `age_days`
- Quy tắc loại record lỗi

### Người 3 bàn giao cho Người 4, 5, 6

- Test set
- Mô tả cách chọn ground truth
- Cách dùng chung cho baseline/corrupted/repaired

### Người 4 bàn giao cho Người 5 và 6

- Embedding manifest
- Index configuration
- Retrieval config, `top_k`

### Người 5 bàn giao cho Người 6 và nhóm

- Quality/freshness artifacts
- Report template và report baseline

### Người 6 bàn giao cho cả nhóm

- Baseline metrics
- Corruption log
- Repaired metrics
- Comparison report

## 8. Gợi ý phân vai thực tế cho nhóm 6 người

Nếu bạn muốn chia theo năng lực và giảm tải đều, có thể dùng cách này:

1. Người 1: mạnh về API / data fetching.
2. Người 2: mạnh về pandas / data cleaning.
3. Người 3: mạnh về testing / evaluation.
4. Người 4: mạnh về retrieval / vector DB.
5. Người 5: mạnh về report / observability.
6. Người 6: mạnh về integration / pipeline / debugging.

## 9. Ghi chú khi làm việc nhóm

- Mọi người phải thống nhất schema trước khi code sâu.
- Không hard-code path hoặc secret.
- Dùng cùng evaluation set cho baseline, corrupted và repaired.
- Mỗi thay đổi ở cleaning hoặc schema phải báo cho Người 3, 4, 5, 6.
- Khi ghép pipeline, ưu tiên artifact thật hơn là chỉ nói “chạy được”.

## 10. Mẫu câu chốt giao việc

Bạn có thể copy câu này vào nhóm chat:

> Mỗi người phụ trách đúng module của mình, bám theo contract chung. Khi xong phần nào thì bàn giao luôn artifact, schema, và các phụ thuộc để người kế tiếp ghép tiếp. Không làm riêng lẻ rồi cuối cùng mới ghép.

