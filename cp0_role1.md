# CP0 - Role 1: Integrator & Release Owner

> Vai trò này ở checkpoint 0 không phải là implement pipeline đầy đủ.
> Mục tiêu là chốt contract ban đầu để cả nhóm làm song song mà không vỡ schema, vỡ path, hoặc đè artifact của nhau.

## 1. Mục tiêu của CP0

- Chốt ownership rõ ràng cho team.
- Chốt branch làm việc và tiêu chí hoàn thành.
- Kiểm tra môi trường chạy được trên máy cục bộ.
- Lập sơ đồ handoff tổng thể cho pipeline.
- Đảm bảo mọi người biết artifact nào sẽ sinh ra và nằm ở đâu.

## 2. Việc cần làm trong CP0

### 2.1 Chốt ownership và phạm vi

- Ghi rõ ai phụ trách ingestion, cleaning, evaluation, observability, retrieval, integration.
- Xác định một người chịu trách nhiệm release/integration cuối cùng.
- Chốt ranh giới: ai sửa module nào, ai chỉ review, ai chỉ tích hợp.

### 2.2 Chốt branch và định nghĩa hoàn thành

- Tạo hoặc chọn branch làm việc chung cho lab.
- Quy định naming cho branch, commit, artifact nếu team cần.
- Định nghĩa xong là khi:
  - raw, clean, eval, embeddings, quality, reports đều có artifact thật,
  - report khớp với artifact,
  - baseline và corruption flow không ghi đè nhau.

### 2.3 Kiểm tra môi trường

- Kiểm tra Python version có nằm trong khoảng `3.11` đến `3.13`.
- Cài dependency theo project lockfile hoặc `pip install -e .`.
- Tạo `.env` cục bộ từ `.env.example`.
- Kiểm tra provider LLM sẽ dùng.

### 2.4 Lập sơ đồ handoff

```text
Crossref raw
    -> cleaned data
    -> embedding/index
    -> evaluation
    -> quality/freshness
    -> corruption
    -> repair
    -> comparison report
```

## 3. Artifact path cần thống nhất ngay từ CP0

| Giai đoạn | Artifact path | Mục đích |
| --- | --- | --- |
| Raw | `data/raw/` | Lưu response gốc và raw records |
| Clean | `data/clean/` | Lưu dữ liệu đã làm sạch |
| Embedding | `data/embeddings/` | Lưu manifest/index metadata |
| Eval | `data/eval/` | Lưu test set cố định |
| Results | `data/results/` | Lưu metrics, answers, logs |
| Quality | `data/quality/` | Lưu quality/freshness checks |
| Reports | `data/reports/` | Lưu report markdown |

## 4. Contract cần chốt ở CP0

### 4.1 Raw contract

- Source dữ liệu là Crossref.
- Raw response phải được lưu trước khi parse.
- Raw records phải có `paper_id` ổn định.

### 4.2 Clean contract

- Clean data phải giữ được schema đủ cho embedding và retrieval.
- `text_for_embedding` phải tồn tại sau cleaning.
- Trường ngày tháng phải đủ để tính freshness.

### 4.3 Evaluation contract

- Test set phải cố định để dùng cho baseline, corrupted, repaired.
- Mỗi sample phải có:
  - `question`
  - `ground_truth`
  - `ground_truth_doc_ids`
  - `question_type`

### 4.4 Comparison contract

- Không ghi đè baseline khi chạy corruption.
- Repair phải chạy lại từ nguồn đáng tin, không sửa tay metric hoặc answer.
- So sánh phải dùng cùng test set và cùng tiêu chí.

## 5. Checklist CP0 cho vai trò 1

- [ ] Chốt branch làm việc.
- [ ] Chốt owner cho từng module.
- [ ] Chốt artifact path theo `data/`.
- [ ] Kiểm tra Python version.
- [ ] Kiểm tra dependency install được.
- [ ] Kiểm tra `.env` và LLM provider.
- [ ] Vẽ sơ đồ handoff cho toàn pipeline.
- [ ] Ghi rõ điều kiện done cho cả nhóm.

## 6. Output của vai trò 1 ở CP0

Kết quả cần bàn giao ở mốc này là:

- một bản phân công và contract rõ ràng,
- một sơ đồ handoff từ raw tới report,
- một danh sách artifact path thống nhất,
- một checklist để các người còn lại làm song song mà không đụng nhau.

## 7. Ghi chú quan trọng

- CP0 chưa phải lúc implement full pipeline.
- Nếu môi trường chưa đúng, ưu tiên sửa môi trường trước khi code sâu.
- Nếu schema chưa thống nhất, chưa nên để các người khác build tiếp vì sẽ dễ phải sửa dây chuyền.

