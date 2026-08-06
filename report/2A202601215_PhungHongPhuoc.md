# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Phùng Hồng Phước |
| MSSV | 2A202601215 |
| Khóa/Lớp | K3 |
| Tên nhóm | 2k345 |
| Vai trò chính | Vai trò 2 - Cleaning / Data Model Owner |
| Repository | `https://github.com/phuongnx2112003/K3_Day10_Data-Pipeline-Data-Observability-2k345-E403` |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Cleaning pipeline | `src/ingestion/cleaning.py` - `build_clean_dataframe` | Raw Crossref records | Clean DataFrame, CSV/JSON clean artifacts, `text_for_embedding`, `age_days` | Hoàn thành |
| Data model contract | `src/ingestion/cleaning.py` - schema chuẩn | Raw records và rule chuẩn hóa | Schema sạch để index/eval/observability dùng chung | Hoàn thành |
| Corruption support | `src/ingestion/corruption.py` | Clean baseline dataframe | Corrupted dataframe và corruption log | Hoàn thành |
| Repair support | `src/ingestion/cleaning.py` | Raw snapshot | Repaired dataframe từ nguồn thật | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Đồng bộ contract raw/clean | Role 1, 3, 4, 5, 6 | Chốt `paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `published`, `age_days`, `text_for_embedding` |
| Hỗ trợ corruption flow | Role 1 và Role 6 | Xác nhận corruption chỉ tác động trên bản sao dataframe clean, không đụng raw snapshot |
| Hỗ trợ repair | Role 1 và Role 6 | Xác nhận repaired dataframe được dựng lại từ raw snapshot, không vá tay JSON lỗi |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Làm sạch dữ liệu Crossref | `src/ingestion/cleaning.py` | `data/clean/papers_clean.csv` và `data/clean/papers_clean.json` | `python script/run_phase1.py` |
| Tạo `text_for_embedding` và `age_days` | `src/ingestion/cleaning.py` | Cột chuẩn cho retrieval/index và freshness | Kiểm tra schema clean và vector manifest |
| Tạo dữ liệu corrupted có kiểm soát | `src/ingestion/corruption.py` | `data/clean/papers_clean_corrupted.json`, `data/results/corruption_log.json` | `python script/run_corruption_flow.py` |
| Dựng lại repaired dataframe từ raw | `src/ingestion/cleaning.py` | `data/clean/papers_clean_repaired.csv/json` | Đối chiếu với raw snapshot và comparison report |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

`data/clean/papers_clean.json` là đầu vào sạch ổn định cho toàn bộ pipeline baseline, còn `data/clean/papers_clean_corrupted.json` và `data/clean/papers_clean_repaired.json` chứng minh được corruption/repair đều tách bạch khỏi raw snapshot.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Raw Crossref records có thể chứa text rác, ngày tháng không đồng nhất và bản ghi trùng DOI. Nếu không chuẩn hóa sớm, embedding/index sẽ nhận input không ổn định và các module phía sau không thể so sánh baseline, corrupted và repaired một cách công bằng.

### Cách triển khai

Mình chuẩn hóa dữ liệu theo một schema thống nhất:

- giữ `paper_id`, `title`, `summary`, `authors_joined`, `categories_joined`, `published`, `updated`, `age_days`
- tạo `text_for_embedding` từ title, summary, authors và categories
- loại duplicate theo `paper_id`
- tính `age_days` để hỗ trợ freshness
- đảm bảo corrupted/repaired data đều có cùng cấu trúc để Role 1 và Role 6 so sánh được

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Raw JSON records từ `data/raw/crossref_records.json` |
| Output | Clean DataFrame, CSV/JSON clean artifacts, cột `text_for_embedding`, `age_days` |
| Module phụ thuộc | `src/ingestion/crossref.py` |
| Module sử dụng output | `src/retrieval/index.py`, `src/evaluation/testset.py`, `src/observability/quality.py`, `src/pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | `summary` rỗng, DOI trùng, record thiếu title/published, dữ liệu corrupted phải vẫn rebuild được |

### Cách xác minh

```bash
PYTHONPATH=src ./venv/bin/python script/run_phase1.py
PYTHONPATH=src ./venv/bin/python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** clean data đủ schema, corrupted/repaired có thể build lại index và evaluate.
- **Kết quả thực tế:** baseline, corrupted và repaired đều chạy được, clean/corrupted/repaired artifacts tách riêng.
- **Artifact/log:** `data/clean/papers_clean.csv`, `data/clean/papers_clean_corrupted.json`, `data/clean/papers_clean_repaired.csv`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi gặp record thiếu `summary`, có thể либо xóa luôn record đó hoặc giữ lại và để summary rỗng.
- **Các phương án đã cân nhắc:**
  - Xóa record thiếu summary để dữ liệu “sạch tuyệt đối”.
  - Giữ record lại, chuẩn hóa summary rỗng và để title/metadata vẫn đi vào `text_for_embedding`.
- **Phương án đã chọn:** Giữ record nếu còn đủ khóa chính và trường bắt buộc để không mất tri thức.
- **Lý do:** Giữ record giúp tránh mất dữ liệu hữu ích cho retrieval, đặc biệt khi title và metadata vẫn đủ để tạo ngữ cảnh.
- **Bằng chứng quyết định phù hợp:** Baseline giữ đủ 24 records; corruption/repaired vẫn so sánh được trên cùng 72 câu hỏi và corruption report cho thấy quality/freshness thay đổi đúng hướng.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ValueError: Expected IDs to be unique. Found duplicates...`
- **Lệnh hoặc bước tái hiện:** Chạy pipeline index trên tập dữ liệu raw/clean chưa lọc duplicate.
- **Nguyên nhân gốc:** Crossref trả về bản ghi trùng DOI, nếu không deduplicate trước khi build vector index sẽ làm ChromaDB báo lỗi.
- **Cách xử lý:** Chuẩn hóa theo `paper_id` và loại duplicate trước khi export clean artifact.
- **Cách xác minh sau khi sửa:** `python script/run_phase1.py` chạy qua bước build index thành công.
- **Điều học được:** Cleaning không chỉ để “đẹp dữ liệu”, mà còn là bước bảo vệ toàn bộ pipeline phía sau.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu đi từ Crossref đến vector index như thế nào? Raw response được parse thành records, clean hóa thành dataframe chuẩn, rồi index dùng `text_for_embedding` để build embeddings và lưu vào ChromaDB.
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao? Test set giữ câu hỏi và `ground_truth_doc_ids`, giúp đo xem index và agent có lấy đúng tài liệu nguồn hay không.
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab? Quality checks kiểm tra schema, blank, duplicate, validity; freshness kiểm tra dữ liệu có bị cũ quá ngưỡng hay không.
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired? Để so sánh công bằng, tránh thay đổi metric do thay đổi bộ câu hỏi.
5. Repair được xem là thành công dựa trên artifact và metric nào? Repair thành công khi repaired clean artifacts được tạo từ raw snapshot, quality/freshness phục hồi và metrics quay lại gần baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0 | 0.9166666666666666 | 1.0 | Corruption làm giảm hit rate, repair phục hồi hoàn toàn |
| `mean_token_f1` | 0.7569240806733034 | 0.660252909856381 | 0.7569240806733034 | Dữ liệu hỏng làm answer lệch hơn so với ground truth |
| `judge_accuracy` | 0.6666666666666666 | 0.625 | 0.6666666666666666 | Judge phản ánh rõ tác động của corruption |
| `mean_judge_score` | 3.9583333333333335 | 3.7777777777777777 | 3.9583333333333335 | Repaired trở lại baseline |
| Quality checks | True | False | True | Duplicate và blank summary được phát hiện đúng |
| Freshness status | False | False | False | Repaired không thể làm mới timestamp nguồn gốc |

### Kết luận từ số liệu

1. `duplicate_rows` và `blank_summary` → quality signal fail → retrieval/answer metrics giảm.
2. Re-run cleaning từ raw snapshot → quality signal phục hồi → metrics phục hồi về baseline.

Corruption ảnh hưởng rõ nhất là các thay đổi trực tiếp vào summary và duplicate row, vì chúng tác động thẳng vào nội dung để embed và vào tính duy nhất của `paper_id`.

Kết quả khác với kỳ vọng ban đầu là freshness của repaired vẫn `False`. Lý do là repair khôi phục dữ liệu đúng từ nguồn gốc chứ không làm thay đổi tuổi thật của bài báo.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Cleaning phải giữ contract ổn định cho downstream modules.
2. Chỉ cần một số corruption nhỏ nhưng đúng chỗ cũng có thể ảnh hưởng rõ đến retrieval.
3. Repair tốt không có nghĩa là dữ liệu sẽ fresh; freshness và correctness là hai tín hiệu khác nhau.

### Nếu có thêm thời gian

Mình sẽ bổ sung validation chặt hơn cho summary/title length và date parsing, đồng thời viết thêm test tự động cho cleaning rules để tránh regressions khi update source.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo của thành viên khác.

**Họ và tên:** Phùng Hồng Phước
**Ngày xác nhận:** 2026-08-06
