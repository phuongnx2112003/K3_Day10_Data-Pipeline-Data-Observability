# CP1 - Role 1: Integrator & Release Owner

> Tài liệu checkpoint 1 cho vai trò 1 của nhóm 6 người.
> Mục tiêu của mốc này là chốt contract kỹ thuật giữa raw -> clean, xác nhận artifact path, và bảo đảm các nhóm khác có thể làm song song mà không vỡ schema.

## 1. Mục tiêu của checkpoint 1

Checkpoint 1 tập trung vào 3 việc chính:

1. Xác nhận source code đã đủ thông tin để chốt contract cho ingestion và cleaning.
2. Chốt ranh giới trách nhiệm giữa người làm ingestion, cleaning, evaluation, observability và integration.
3. Xác nhận các quality gates tối thiểu để pipeline có thể đi tiếp sang evaluation và index.

Ở mốc này, vai trò 1 chưa cần hoàn thiện toàn bộ pipeline end-to-end. Điều cần làm là bảo đảm cả nhóm không bị lệch schema, lệch path, hoặc đè artifact của nhau.

## 1.1 Thành viên và phân vai

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Xuân Phượng | 2A202601874 | Vai trò 1 | `src/ingestion/crossref.py`, raw contract, artifact path, handoff |
| 2 | Phùng Hồng Phước | 2A202601215 | Vai trò 2 | `src/ingestion/cleaning.py`, clean schema, `text_for_embedding`, `age_days` |
| 3 | Lê Công Dũng | 2A202601649 | Vai trò 3 | `src/evaluation/testset.py`, evaluation set và ground truth |
| 4 | Nguyễn Đào Nam Hải | 2A202601037 | Vai trò 4 | `src/retrieval/embeddings.py`, `src/retrieval/index.py`, retrieval/index/agent check |
| 5 | Lê Nguyễn Minh Đức | 2A202601013 | Vai trò 5 | `src/observability/quality.py`, `src/observability/reporting.py`, report artifacts |
| 6 | Trần Đức Mạnh | 2A202601567 | Vai trò 6 | `src/pipelines/phase1.py`, `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` |

### Ghi chú phối hợp

- Vai trò 1 là người chốt contract đầu vào và artifact path để các vai trò sau không bị vỡ schema.
- Vai trò 2 phụ thuộc trực tiếp vào raw records do vai trò 1 bàn giao.
- Vai trò 3 chỉ nên tạo test set sau khi clean schema đã ổn định.
- Vai trò 4 cần clean dataset với `text_for_embedding` và metadata đủ dùng cho retrieval.
- Vai trò 5 cần dữ liệu sạch và metrics từ các vai trò sau để viết report.
- Vai trò 6 là người tích hợp cuối cùng, nên chỉ ghép pipeline khi contract giữa các vai trò đã rõ.

## 2. Kết luận nhanh

Source code hiện tại đã **đủ để làm checkpoint 1** nếu checkpoint này yêu cầu:

- chốt ownership và handoff,
- mô tả rõ raw/clean contract,
- xác minh artifact path,
- nêu trạng thái hiện tại của module ingestion và cleaning,
- chỉ ra việc nào đã sẵn sàng, việc nào còn chờ implement.

Source code **chưa đủ** nếu yêu cầu của checkpoint 1 là chạy xong toàn bộ pipeline, vì các module sau vẫn còn `NotImplementedError`:

- `src/evaluation/testset.py`
- `src/observability/quality.py`
- `src/observability/reporting.py`
- `src/pipelines/phase1.py`
- `src/pipelines/corruption_flow.py`

## 3. Phạm vi của role 1 ở checkpoint 1

Theo phân công của nhóm 6 người, role 1 là **Source / Ingestion owner**.
Nghĩa là checkpoint 1 của bạn nên tập trung vào:

- nguồn dữ liệu Crossref,
- schema raw record,
- cách lưu raw response và raw records,
- input contract cho cleaning,
- các artifact path cần thống nhất,
- các điều kiện bàn giao cho các vai trò sau.

## 4. Những gì source code hiện đã có

### 4.1 Artifact path và settings đã được chốt

Trong `src/core/config.py`, repo đã định nghĩa sẵn các đường dẫn chính:

- `data/raw/`
- `data/clean/`
- `data/embeddings/`
- `data/eval/`
- `data/results/`
- `data/quality/`
- `data/reports/`

Ngoài ra, `Settings` cũng đã có:

- `source_api`
- `source_query`
- `source_filter`
- `max_results`
- `top_k`
- `freshness_threshold_days`
- cờ `refresh_source` và `refresh_test_set`

Điều này đủ để team không phải đoán đường dẫn hay cấu hình đầu vào.

### 4.2 Ingestion đã có khung rõ ràng

Trong `src/ingestion/crossref.py`, repo đã có:

- `PaperRecord` với các field chính:
  - `paper_id`
  - `title`
  - `summary`
  - `authors`
  - `categories`
  - `primary_category`
  - `published`
  - `updated`
  - `abs_url`
  - `pdf_url`
  - `comment`
- `parse_crossref_payload()` để parse payload Crossref thành `PaperRecord`
- `fetch_source_records()` để:
  - gọi Crossref API,
  - retry khi gặp `429` hoặc `503`,
  - lưu raw API response vào `data/raw/crossref_response.json`,
  - lưu raw records đã parse vào `data/raw/crossref_records.json`

### 4.3 Cleaning contract đã được code hóa

Trong `src/ingestion/cleaning.py`, repo đã định nghĩa rõ clean schema và quy tắc chính:

- `paper_id` được chuẩn hóa về lowercase
- record thiếu `paper_id`, `title` hoặc `published` hợp lệ sẽ bị loại
- `updated` fallback về `published` nếu không parse được
- `authors` và `categories` được normalize và deduplicate
- `age_days` được tính từ ngày chạy
- `text_for_embedding` được tạo từ:
  - title
  - summary
  - authors
  - categories

Điều quan trọng là cleaning không còn phải tự đoán schema đầu vào, vì raw schema đã tương thích với các field cần thiết.

## 5. Pass criteria của checkpoint 1

Checkpoint 1 này đạt yêu cầu khi tài liệu và source code chứng minh được các điều sau:

### 5.1 Raw to clean contract rõ ràng

- Raw records phải có `paper_id` ổn định.
- Raw response phải được lưu trước khi parse.
- Cleaned data phải giữ được schema đủ để build embedding và retrieval.

### 5.2 Clean schema đủ để nhóm khác tiếp tục

- Có `text_for_embedding`
- Có `published` và `age_days`
- Có `authors_joined` và `categories_joined`
- Có `paper_id` không trùng sau deduplicate

### 5.3 Artifact path không bị mơ hồ

- Raw nằm trong `data/raw/`
- Clean nằm trong `data/clean/`
- Embedding nằm trong `data/embeddings/`
- Eval nằm trong `data/eval/`
- Quality nằm trong `data/quality/`
- Reports nằm trong `data/reports/`

### 5.4 Contract cho các nhóm sau đã đủ để họ làm song song

- Người làm evaluation biết document ID nào là stable ID.
- Người làm observability biết field nào dùng cho freshness.
- Người làm integration biết đâu là baseline artifact, đâu là corruption artifact.

## 6. Checklist bàn giao của role 1

- [ ] Chốt nguồn dữ liệu: Crossref REST API
- [ ] Chốt query/filter mặc định trong settings
- [ ] Chốt raw schema và stable `paper_id`
- [ ] Chốt raw artifact path
- [ ] Chốt clean artifact path
- [ ] Chốt rule deduplicate và filter record lỗi
- [ ] Chốt field dùng cho `text_for_embedding`
- [ ] Chốt field dùng cho freshness
- [ ] Chốt ownership giữa 6 thành viên
- [ ] Chốt điều kiện done cho nhóm

## 7. Handoff cho các vai trò khác

### Cho người 2 - Cleaning / Data model owner

Bạn nhận đầu vào là raw records từ `src/ingestion/crossref.py`.
Bạn cần dựa trên các field hiện có để:

- chuẩn hóa text,
- xử lý danh sách authors/categories,
- tạo `text_for_embedding`,
- tính `age_days`,
- lưu cleaned dataset vào `data/clean/`.

### Cho người 3 - Evaluation set owner

Bạn sẽ dùng cleaned dataset, không dùng raw data chưa chuẩn hóa.
Điểm cần nhớ:

- `paper_id` phải ổn định,
- `ground_truth_doc_ids` phải map từ document thật,
- test set phải dùng chung cho baseline, corrupted, repaired.

### Cho người 4 - Retrieval / Index owner

Bạn cần cleaned data có `text_for_embedding` và metadata đủ để build vector store.
Vì vậy, checkpoint 1 của role 1 phải chốt được schema mà người 4 có thể tiêu thụ ngay.

### Cho người 5 - Observability / Reporting owner

Người 5 cần biết:

- field nào là freshness source,
- dữ liệu nào là baseline sạch,
- artifact nào sẽ dùng cho report.

### Cho người 6 - Integration / Corruption owner

Người 6 cần contract ổn định từ raw đến clean để ghép pipeline và về sau so sánh baseline/corrupted/repaired mà không bị đổi schema giữa chừng.

## 8. Trạng thái hiện tại của source code

### Đã sẵn sàng

- Crossref ingestion contract
- Raw record schema
- Clean dataframe contract
- Artifact path trong `data/`
- Embedding-friendly text construction

### Chưa hoàn tất

- Evaluation set builder
- Quality checks
- Freshness report generator
- Baseline pipeline orchestration
- Corruption flow orchestration

Điều này phù hợp với checkpoint 1: phần của bạn là chốt nền tảng để các module sau đi tiếp.

## 9. Ghi chú xác minh

Từ test trong repo, có thể thấy các yêu cầu CP1 được kỳ vọng như sau:

- raw-to-clean phải giữ được `paper_id` ổn định,
- cleaning phải deduplicate, normalize text và tạo `text_for_embedding`,
- corruption sau này phải rebuild được `text_for_embedding` và có log đầy đủ.

Đây là dấu hiệu rằng schema hiện tại đã đủ chắc để nhóm tiến sang các module kế tiếp.

## 10. Kết luận

Checkpoint 1 của vai trò 1 đã có đủ nền tảng để làm chỉnh chu:

- contract đã rõ,
- artifact path đã có,
- raw/clean schema đã chốt,
- các nhóm phụ thuộc đã biết input/output của mình.

Việc còn lại không phải là đoán schema nữa, mà là triển khai tiếp các module sau trên contract đã thống nhất.

**Kết luận cuối:** source code hiện tại **đủ để bạn làm checkpoint 1 của vai trò 1** theo hướng bàn giao contract và chuẩn bị phối hợp nhóm.
