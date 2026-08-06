# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Nguyễn Xuân Phượng |
| MSSV | 2A202601874 |
| Khóa/Lớp | K3 |
| Tên nhóm | 2k345 |
| Vai trò chính | Vai trò 1 - Integrator & Release Owner |
| Repository | `git@github.com:phuongnx2112003/K3_Day10_Data-Pipeline-Data-Observability.git` |
| Ngày hoàn thành | 2026-08-06 |

### Danh sách thành viên nhóm

| Họ và tên | MSSV | Vai trò |
| --- | --- | --- |
| Nguyễn Xuân Phượng | 2A202601874 | Vai trò 1 |
| Nguyễn Đào Nam Hải | 2A202601037 | Vai trò 4 |
| Phùng Hồng Phước | 2A202601215 | Vai trò 2 |
| Lê Công Dũng | 2A202601649 | Vai trò 3 |
| Trần Đức Mạnh | 2A202601567 | Vai trò 6 |
| Lê Nguyễn Minh Đức | 2A202601013 | Vai trò 5 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Baseline orchestration | `src/pipelines/phase1.py::main` | Raw Crossref records, clean schema, test set, settings | `data/results/baseline_metrics.json`, `data/results/baseline_answers.json`, `data/reports/phase1_report.md`, `data/quality/baseline_quality.json`, `data/quality/freshness_report.json` | Hoàn thành |
| Corruption, repair, comparison orchestration | `src/pipelines/corruption_flow.py::main` | Baseline clean dataset, raw snapshot, test set, corruption contract, settings | `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` | Hoàn thành |
| Integration report cho cá nhân role 1 | `cp0_role1.md` đến `cp6_role1.md` | Artifact thật từ pipeline và report | Báo cáo checkpoint theo từng mốc của role 1 | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Đồng bộ contract clean, eval, index, quality | Role 2, 3, 4, 5 | Chốt được artifact path riêng cho baseline, corrupted, repaired và test set dùng chung |
| Kiểm tra report và evidence | `src/observability/reporting.py`, `data/reports/` | Sinh báo cáo baseline và comparison khớp với JSON/CSV thật |
| Chạy smoke test pipeline | `script/run_phase1.py`, `script/run_corruption_flow.py` | Xác nhận baseline và corruption flow chạy end-to-end bằng artifact thật |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Ghép baseline end-to-end | `src/pipelines/phase1.py` | Baseline chạy từ raw -> clean -> index -> evaluate -> quality/freshness -> report | `PYTHONPATH=src ./venv/bin/python script/run_phase1.py` |
| Ghép corruption flow có kiểm soát | `src/pipelines/corruption_flow.py` | Corrupted/repaired artifacts, comparison report, corruption log | `PYTHONPATH=src ./venv/bin/python script/run_corruption_flow.py` |
| Chuẩn hóa report baseline và comparison | `src/observability/reporting.py` | `phase1_report.md`, `corruption_report.md` | Đối chiếu report với `data/results/*.json` và `data/quality/*.json` |
| Viết bàn giao checkpoint cho role 1 | `cp0_role1.md`, `cp1_role1.md`, `cp2_role1.md`, `cp3_role1.md`, `cp5_role1.md`, `cp6_role1.md` | Tài liệu checkpoint rõ input/output/dependency | Đọc nội dung file và artifact thật trong `data/` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

`data/reports/corruption_report.md` chứng minh rõ baseline tốt hơn corrupted ở retrieval hit rate, token F1 và judge metrics, sau đó repaired quay lại gần baseline.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Vai trò 1 phải đảm bảo toàn bộ pipeline của lab có thể chạy end-to-end mà không ghi đè baseline, đồng thời phải ghép được corruption, repair và comparison trên cùng một test set để chứng minh data quality ảnh hưởng trực tiếp tới kết quả RAG.

### Cách triển khai

Mình triển khai theo hướng orchestration rõ ràng:

- `phase1.py` lấy raw Crossref snapshot, clean dữ liệu, build embedding/index, sinh test set và evaluate baseline.
- `corruption_flow.py` đọc baseline clean data, tạo corrupted copy có log, build lại collection riêng, evaluate lại trên test set cũ, chạy quality/freshness, rồi repair từ raw snapshot và so sánh ba trạng thái.
- `reporting.py` sinh markdown report từ các JSON artifact thật thay vì hard-code số liệu.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `data/raw/crossref_records.json`, `data/clean/papers_clean.json`, `data/eval/test_set.json`, `data/results/baseline_metrics.json`, `data/quality/*.json` |
| Output | `data/results/baseline_metrics.json`, `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md` |
| Module phụ thuộc | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/ingestion/corruption.py`, `src/evaluation/testset.py`, `src/evaluation/metrics.py`, `src/observability/quality.py`, `src/observability/reporting.py`, `src/retrieval/index.py`, `src/retrieval/qa.py` |
| Module sử dụng output | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Không có raw snapshot, test set thiếu, baseline chưa chạy xong, corrupted collection ghi đè baseline, report không khớp artifact thật |

### Cách xác minh

```bash
PYTHONPATH=src ./venv/bin/python script/run_phase1.py
PYTHONPATH=src ./venv/bin/python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** baseline và corruption flow đều tạo artifact thật, report khớp JSON/CSV, corrupted giảm chất lượng và repaired phục hồi.
- **Kết quả thực tế:** cả hai flow đều chạy thành công, corrupted giảm hit rate/F1/judge metrics, repaired quay lại mức baseline.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi làm CP5 và CP6, baseline không được phép bị ghi đè trong lúc tạo corrupted/repaired artifacts.
- **Các phương án đã cân nhắc:** 
  - Dùng chung một collection và ghi đè theo từng trạng thái.
  - Tách riêng paths và collection cho baseline, corrupted, repaired.
- **Phương án đã chọn:** Tách riêng artifact path và collection name cho từng trạng thái.
- **Lý do:** Cách này giữ reproducibility, dễ audit, tránh lẫn dữ liệu giữa baseline và corruption flow, và giúp comparison report tin cậy hơn.
- **Bằng chứng quyết định phù hợp:** `data/reports/corruption_report.md` có baseline/corrupted/repaired metrics riêng; `data/embeddings/papers_embeddings_corrupted.json` và `data/embeddings/papers_embeddings_repaired.json` tồn tại riêng.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `NotImplementedError: Student task: implement corruption flow pipeline.` ở `src/pipelines/corruption_flow.py`
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_corruption_flow.py` trước khi implement flow.
- **Nguyên nhân gốc:** File orchestration cho corruption flow vẫn là starter stub, chưa ghép các bước corruption, evaluate, repair và compare.
- **Cách xử lý:** Viết lại `src/pipelines/corruption_flow.py` để đọc baseline, tạo corrupted copy, build collection riêng, evaluate lại, repair từ raw snapshot và sinh comparison report; đồng thời cập nhật `src/observability/reporting.py`.
- **Cách xác minh sau khi sửa:** Chạy lại `PYTHONPATH=src ./venv/bin/python script/run_corruption_flow.py` và kiểm tra `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md`.
- **Điều học được:** Orchestration phải ưu tiên artifact contract và tách trạng thái rõ ràng; nếu không, report và metrics rất dễ lệch nhau dù script vẫn chạy xong.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Crossref trả về raw response, sau đó `src/ingestion/crossref.py` parse thành raw records. `src/ingestion/cleaning.py` chuyển raw records sang clean schema, `src/retrieval/index.py` build embeddings và lưu vào Chroma collection riêng.
2. Test set chứa câu hỏi, ground truth và `ground_truth_doc_ids`. Khi evaluator chạy, nó so document mà agent retrieve được với `ground_truth_doc_ids` để tính retrieval hit rate, token F1 và judge metrics.
3. Quality checks kiểm tra tính đúng đắn của dữ liệu tại thời điểm chạy, ví dụ duplicate `paper_id`, blank summary, blank text, valid date. Freshness monitoring tập trung vào độ mới của bản ghi dựa trên `published` và `age_days`.
4. Vì giữ nguyên test set giúp so sánh công bằng. Nếu đổi test set giữa baseline, corrupted và repaired thì không thể kết luận sự khác biệt là do dữ liệu hay do bộ câu hỏi.
5. Repair thành công khi repaired artifacts tách riêng, quality/freshness quay về mức tốt hơn corrupted, và các metric như retrieval hit rate, token F1, judge accuracy phục hồi về gần baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0 | 0.9166666666666666 | 1.0 | Corruption làm giảm khả năng truy hồi đúng tài liệu; repair khôi phục hoàn toàn. |
| `mean_token_f1` | 0.7569240806733034 | 0.660252909856381 | 0.7569240806733034 | Dữ liệu xấu làm câu trả lời lệch hơn so với ground truth. |
| `judge_accuracy` | 0.6666666666666666 | 0.625 | 0.6666666666666666 | Judge minh bạch cho thấy corrupted kém hơn baseline, repaired trở lại như cũ. |
| `mean_judge_score` | 3.9583333333333335 | 3.7777777777777777 | 3.9583333333333335 | Điểm trung bình giảm khi dữ liệu bị hỏng và phục hồi sau repair. |
| Quality checks | True | False | True | Corrupted fail vì duplicate và blank summary; repaired pass. |
| Freshness status | False | False | False | Dataset gốc đã có 1 stale row, corruption làm tệ hơn nhưng repair không làm mới được lịch sử xuất bản. |

### Kết luận từ số liệu

1. `drop_latest`, `blank_summary`, `summary_noise`, `truncate_title`, `stale_published`, `duplicate_rows` → quality/freshness signal xấu đi → retrieval và answer quality giảm.
2. Repair từ raw/source → quality/freshness phục hồi so với corrupted → metric retrieval, F1 và judge phục hồi về baseline.

Corruption ảnh hưởng rõ nhất là sự kết hợp giữa `drop_latest` và `duplicate_rows`, vì nó vừa làm mất tài liệu gốc vừa làm dataset vi phạm tính duy nhất của `paper_id`.

Kết quả khác với kỳ vọng ban đầu là freshness của repaired vẫn `False`. Lý do là repair được làm lại từ raw snapshot cùng nguồn, nên nó phục hồi dữ liệu đúng chứ không “làm mới” thời gian xuất bản gốc.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Pipeline dữ liệu phải được thiết kế theo contract artifact rõ ràng, nếu không rất dễ ghi đè baseline hoặc lẫn trạng thái.
2. Quality checks và freshness monitoring cần được tách riêng vì chúng kiểm tra những khía cạnh khác nhau của data health.
3. RAG agent phụ thuộc rất mạnh vào dữ liệu đầu vào; corruption nhỏ vẫn có thể làm retrieval và answer quality giảm rõ ràng.

### Nếu có thêm thời gian

Mình sẽ bổ sung một report so sánh delta tự động hơn nữa, ví dụ highlight top case xấu nhất giữa baseline/corrupted/repaired để demo trực quan hơn và dễ giải thích hơn trong buổi nộp.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Xuân Phượng
**Ngày xác nhận:** 2026-08-06
