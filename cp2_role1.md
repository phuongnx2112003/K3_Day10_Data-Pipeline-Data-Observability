# CP2 - Role 1: Integrator & Release Owner

> Tài liệu checkpoint 2 cho vai trò 1 của nhóm 6 người.
> Mục tiêu của mốc này là khóa clean schema, bảo đảm test set và vector index khớp với nhau, và kiểm tra smoke test cho retrieval/agent trước khi sang baseline end-to-end.

## 1. Mục tiêu của checkpoint 2

Checkpoint 2 là mốc chuyển từ "schema đã rõ" sang "có thể test được đường đi end-to-end ngắn" với các thành phần:

1. Clean dataset đã ổn định.
2. Evaluation test set đã được tạo và ID trong test set khớp với clean data.
3. Embedding manifest và Chroma collection baseline đã tồn tại.
4. Semantic search, exact lookup và agent smoke test đều trả về kết quả có thể truy vết.

Ở CP2, vai trò 1 vẫn là người điều phối contract và handoff, không phải người sở hữu toàn bộ retrieval stack.

## 2. Thành viên và phân vai

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Xuân Phượng | 2A202601874 | Vai trò 1 | `src/ingestion/crossref.py`, contract raw, artifact path, integration handoff |
| 2 | Phùng Hồng Phước | 2A202601215 | Vai trò 2 | `src/ingestion/cleaning.py`, clean schema, `text_for_embedding`, `age_days` |
| 3 | Lê Công Dũng | 2A202601649 | Vai trò 3 | `src/evaluation/testset.py`, evaluation set và ground truth |
| 4 | Nguyễn Đào Nam Hải | 2A202601037 | Vai trò 4 | `src/retrieval/embeddings.py`, `src/retrieval/index.py`, retrieval/index/agent check |
| 5 | Lê Nguyễn Minh Đức | 2A202601013 | Vai trò 5 | `src/observability/quality.py`, `src/observability/reporting.py`, report artifacts |
| 6 | Trần Đức Mạnh | 2A202601567 | Vai trò 6 | `src/pipelines/phase1.py`, `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` |

## 3. Kết luận về dependency ở CP3

Có. Ở **CP3**, role 1 **có phụ thuộc** vào output của các vai trò khác.

Cụ thể, nếu role 1 là người tích hợp baseline end-to-end thì cần:

- output của role 2 để có clean data và `text_for_embedding`,
- output của role 3 để có `test_set.json`,
- output của role 4 để có embeddings, Chroma collection và smoke test retrieval,
- output của role 5 để có quality/freshness report và baseline report,
- role 6 sẽ là người ghép orchestration cuối, nên role 1 cần phối hợp contract với role 6.

Nói ngắn gọn:

- **CP2:** role 1 chưa cần phụ thuộc nặng vào ai để chốt contract.
- **CP3:** role 1 **phải** dùng output của role 2, 3, 4, 5 để tích hợp baseline hoàn chỉnh.

## 4. Phạm vi của role 1 ở checkpoint 2

Ở checkpoint này, vai trò 1 nên tập trung vào:

- khóa contract giữa clean data, test set và index,
- xác nhận baseline collection/path riêng, không đè artifact,
- kiểm tra luồng handoff clean -> test set/index,
- ghi rõ blocker nếu smoke test thất bại,
- chuẩn bị nền cho `src/pipelines/phase1.py`.

## 5. Những gì repo hiện đã hỗ trợ cho CP2

### 5.1 Clean schema đã có để dùng làm đầu vào

`src/ingestion/cleaning.py` đã cung cấp:

- `paper_id`
- `title`
- `summary`
- `authors`
- `categories`
- `primary_category`
- `published`
- `updated`
- `age_days`
- `authors_joined`
- `categories_joined`
- `summary_chars`
- `text_for_embedding`
- `abs_url`
- `pdf_url`
- `comment`

Điều này đủ để người làm evaluation và retrieval không phải tự đoán cột nào dùng được.

### 5.2 Retrieval/index đã có contract rõ

`src/retrieval/index.py` đã cho thấy index cần:

- `paper_id`
- `title`
- `text_for_embedding`
- metadata gồm `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url`

Ngoài ra:

- embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- baseline collection: `papers-baseline`
- persistent store: `data/chroma/`
- manifest: `data/embeddings/papers_embeddings.json`

### 5.3 CP2 scripts đã phản ánh đúng mục tiêu checkpoint

Repo hiện có các script hỗ trợ CP2:

- `script/cp2_rag_build.py`
- `script/check_test_ids.py`

Hai script này cho thấy logic CP2 đã xoay quanh:

- đọc clean data,
- build embedding/index baseline,
- smoke test semantic search,
- smoke test exact lookup,
- kiểm tra `ground_truth_doc_ids` trong test set có tồn tại trong clean data.

## 6. Xác minh thực tế trên repo hiện tại

Mình đã kiểm tra trực tiếp môi trường và artifacts sau khi `git pull`:

- Python: `3.12.3`
- `data/clean/papers_clean.json`: 24 records
- `data/eval/test_set.json`: 72 questions
- `data/embeddings/papers_embeddings.json`: 24 documents, collection name `papers-baseline`
- `data/chroma/chroma.sqlite3`: tồn tại

Kết quả kiểm tra ID của test set:

- `script/check_test_ids.py` chạy thành công
- 72/72 `ground_truth_doc_ids` đều tồn tại trong clean corpus
- không có ID nào bị thiếu

Điều này xác nhận rằng CP2 đã có đủ input thực tế cho:

- test set owner,
- retrieval/index owner,
- và role 1 ở mốc tích hợp contract.

## 7. Pass criteria của checkpoint 2

Checkpoint 2 đạt yêu cầu khi các điều sau đúng:

### 6.1 Test set khớp clean data

- `data/eval/test_set.json` tồn tại
- mọi `ground_truth_doc_ids` đều khớp với `paper_id` trong clean data
- mỗi sample có:
  - `id`
  - `question_type`
  - `question`
  - `ground_truth`
  - `ground_truth_doc_ids`

### 6.2 Baseline index tồn tại

- `data/embeddings/papers_embeddings.json` tồn tại
- `data/chroma/` có collection baseline
- số document trong index khớp clean dataset đã nạp

### 6.3 Smoke test retrieval chạy được

- semantic search trả về kết quả hợp lý
- exact lookup theo `paper_id` hoặc title hoạt động
- agent có thể được khởi tạo và trả lời theo corpus

### 6.4 Handoff cho CP3 đã sẵn sàng

- role 1 biết rõ artifact nào sẽ được ghép vào baseline pipeline
- role 2, 3, 4, 5 đã có input/output rõ ràng
- role 6 có thể dùng contract này để bắt đầu tích hợp `phase1.py`

## 8. Checklist bàn giao của role 1 ở CP2

- [x] Chốt clean schema cuối cùng
- [x] Xác minh `paper_id` xuyên suốt raw -> clean -> index
- [x] Xác minh `test_set.json` dùng ID hợp lệ
- [x] Xác minh `papers_embeddings.json` và `data/chroma/` tồn tại
- [x] Chạy smoke test semantic search
- [x] Chạy smoke test exact lookup
- [x] Ghi blocker nếu agent chưa trả lời đúng
- [x] Chốt baseline collection name không đè artifact khác
- [x] Chuẩn bị đầu vào cho `src/pipelines/phase1.py`

## 9. Handoff cho các vai trò khác

### Cho người 2 - Cleaning / Data model owner

Đã đủ contract để tiếp tục giữ clean schema ổn định.
Người 2 cần đảm bảo `text_for_embedding`, `age_days` và deduplicate vẫn đúng khi baseline index được build.

### Cho người 3 - Evaluation set owner

Test set phải được khóa trên clean data.
Người 3 cần đảm bảo `ground_truth_doc_ids` đều hợp lệ và có thể kiểm tra bằng script riêng.

### Cho người 4 - Retrieval / Index owner

Người 4 cần build `papers-baseline` từ clean data, rồi chạy smoke test semantic search và lookup.
Nếu lookup hoặc retrieval sai, phải truy ngược lại contract clean/index trước.

### Cho người 5 - Observability / Reporting owner

Người 5 cần chốt khuôn report và sẵn sàng nhận metrics/quality signals từ baseline.

### Cho người 6 - Integration / Corruption owner

Người 6 chỉ nên ghép pipeline khi CP2 đã khóa được:

- clean schema,
- test set,
- index baseline,
- smoke test retrieval.

## 10. Kết luận

Checkpoint 2 của role 1 là mốc "khóa contract để chuẩn bị baseline".
Repo hiện tại đã đủ thông tin để bạn làm mốc này chỉnh chu:

- schema clean đã rõ,
- index contract đã rõ,
- test set contract đã rõ,
- smoke test CP2 đã có script hỗ trợ.

Và quan trọng hơn:

- **CP3 role 1 có phụ thuộc output của role 2, 3, 4, 5.**
- Vì vậy, CP2 là thời điểm hợp lý để chốt các contract này trước khi tích hợp baseline end-to-end.

## 11. Kết luận ngắn gọn để nộp

CP2 của vai trò 1 đã đủ input và đủ evidence để hoàn thành:

- clean data đã có và đúng schema,
- test set đã có và toàn bộ `ground_truth_doc_ids` hợp lệ,
- embedding manifest và Chroma collection baseline đã tồn tại,
- smoke test kiểm tra ID đã pass,
- role 1 có thể dùng CP2 này làm nền cho CP3 baseline integration.
