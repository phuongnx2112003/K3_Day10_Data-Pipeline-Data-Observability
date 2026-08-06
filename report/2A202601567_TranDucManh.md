# Individual Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Trần Đức Mạnh |
| MSSV | 2A202601567 |
| Khóa/Lớp | K3 |
| Tên nhóm | Nhóm 6 thành viên |
| Vai trò chính | Vai trò 6 — Observability owner |
| Phạm vi | Data quality, freshness, embedding audit và reporting |
| Repository | `https://github.com/phuongnx2112003/K3_Day10_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

Tôi phụ trách đo và báo cáo mức độ đáng tin cậy của dữ liệu ở ba trạng thái
`baseline`, `corrupted` và `repaired`. Tôi nhận dữ liệu, embedding manifest, answers và
metrics do các module khác tạo ra; tôi không nhận ownership cho ingestion, cleaning,
test-set generation, corruption logic, RAG retrieval hoặc LLM evaluation.

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Data quality | `src/observability/quality.py` — `run_data_quality_checks` | Clean DataFrame của từng trạng thái | Quality JSON, check results và failed checks | Hoàn thành |
| Freshness | `src/observability/quality.py` — `build_freshness_report` | `published`, `age_days`, ngưỡng 180 ngày | Freshness JSON | Hoàn thành |
| Embedding audit | `audit_embedding_manifest` | Clean data, embedding manifest và config | Audit document count, ID, metadata, collection, persist path | Hoàn thành |
| Observability snapshot | `build_observability_snapshot` | Quality, freshness, audit và metrics | Snapshot so sánh được giữa ba trạng thái | Hoàn thành |
| Baseline observability | `src/observability/baseline.py` | Baseline artifacts | Baseline quality/freshness/snapshot và Phase 1 report | Hoàn thành |
| Corrupted observability | `src/observability/corrupted.py` | Corrupted artifacts và corruption log | Corrupted snapshot và impact evidence | Hoàn thành |
| Repaired observability | `src/observability/repaired.py` | Repaired artifacts và hai trạng thái trước | Recovery comparison JSON và trạng thái recovery | Hoàn thành |
| Reporting | `src/observability/reporting.py` | Metrics, quality và freshness thật | `phase1_report.md`, `corruption_report.md` | Hoàn thành |
| Kiểm thử | `tests/test_observability_*.py` | Fixtures baseline/corrupted/repaired | Regression tests cho checks, evidence và report | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Kiểm tra contract artifact | Evaluation và RAG/index | Xác nhận metrics samples khớp answers và manifest có đúng collection/count |
| Giải quyết merge conflict | Các JSON/report sinh tự động | Tái sinh theo thứ tự baseline → corrupted → repaired; không còn conflict marker |
| Tài liệu checkpoint | Nhóm và người thuyết trình | Viết `docs/checkpoints/role6_checkpoint0.md` đến `role6_checkpoint6.md` |

## 3. Kết quả theo vai trò

| Nhiệm vụ | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Định nghĩa quality signals | `quality.py`, `data/quality/*_quality.json` | Row count, null ID, duplicate ID, missing title, invalid summary và invalid age | Mở `check_results` và `counts` trong JSON |
| Đo freshness | `*_freshness.json` | Dùng timestamp nguồn `published`, ngưỡng 180 ngày, stale count/ratio | Chạy `observability.baseline`, `corrupted`, `repaired` |
| Audit embedding manifest | `*_embedding_audit.json` | Kiểm collection, 24 documents, metadata, ID và persist path | Xem `success` và `failed_checks` |
| Khóa baseline | `baseline_observability_snapshot.json` | Mốc quality/freshness/metrics để so sánh | Đối chiếu `baseline_metrics.json` |
| Nối corruption với evidence | `corrupted_impact_evidence.json` | Chỉ ghi quan hệ có log và signal/metric đo được | Kiểm `event_evidence` và `guarded_conclusions` |
| Đánh giá recovery | `recovery_comparison.json` | Recovery `partial`; ghi rõ metric chưa hồi phục | Kiểm `unresolved_metrics` |
| Sinh báo cáo | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Report lấy số từ artifact, không hard-code kết quả | Chạy lại runner và so sánh report |

Output tiêu biểu của tôi là
`data/quality/recovery_comparison.json`. Artifact này gom quality, freshness và metrics
của cả ba trạng thái, đồng thời chỉ ra `judge_accuracy` repaired vẫn dưới baseline nên
recovery chỉ được ghi là `partial`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline chạy xong không đồng nghĩa dữ liệu đang đáng tin cậy. Một corruption flow có
thể xóa records rồi thêm duplicate làm tổng số dòng không đổi. Nếu chỉ nhìn row count
hoặc trạng thái thực thi, nhóm có thể bỏ sót dữ liệu lỗi và kết luận sai về chất lượng
RAG. Phần observability phải tạo tín hiệu đo được, giữ riêng artifact từng trạng thái và
chỉ kết luận khi report khớp JSON/CSV thật.

### Cách triển khai

Quality runner chuẩn hóa null/blank, đếm duplicate bằng `duplicated(keep=False)` để cả
bản gốc và bản sao đều được đánh dấu, kiểm summary tối thiểu 50 ký tự, parse
`published` và xác thực `age_days`. Freshness sử dụng `published` làm timestamp nguồn,
`age_days` làm giá trị dẫn xuất và đánh dấu stale khi lớn hơn 180 ngày.

Embedding audit đối chiếu manifest với clean dataset: backend, model, collection name,
document count, uniqueness, metadata, paper IDs và persist path. Snapshot chuyển các
report khác schema thành một bộ signal chung để baseline, corrupted và repaired có thể
so sánh trực tiếp.

Ở CP5, corruption log chỉ được nối với signal khi cả event và delta phù hợp cùng tồn
tại. Ví dụ `old_date` đi cùng stale rows tăng 2; noise và truncated title không được
quy kết vì hiện chưa có direct check. Ở CP6, recovery được phân loại theo từng signal và
metric. Một metric còn dưới baseline hoặc embedding audit còn fail sẽ ngăn trạng thái
`complete`.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | Clean CSV; embedding manifest; answers/metrics JSON; corruption log; test set |
| Output | Quality, freshness, embedding audit, snapshot, evidence và Markdown report |
| Module phụ thuộc | `core.config`, `core.utils`, pandas và artifact từ ingestion/RAG/evaluation |
| Module sử dụng output | UI/demo, comparison report và phần đánh giá kết quả cuối |
| Điều kiện lỗi | Thiếu file, thiếu cột, samples không khớp answers, manifest sai collection/path, metric không so sánh được |

### Cách xác minh

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m observability.baseline
.\.venv\Scripts\python.exe -m observability.corrupted
.\.venv\Scripts\python.exe -m observability.repaired
.\.venv\Scripts\python.exe -m pytest -q
```

- Kết quả mong đợi: ba runner có status `complete`; comparison được sinh; test pass.
- Kết quả thực tế: baseline, corrupted và repaired runner đều `complete`; recovery
  `partial`; `13 passed`.
- Artifact chính: `data/quality/recovery_comparison.json` và
  `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn timestamp phản ánh độ mới của dữ liệu nguồn.
- **Phương án 1:** Dùng thời điểm pipeline tải hoặc ghi file. Cách này dễ lấy nhưng chỉ
  đo độ mới của lần chạy, không đo tuổi của paper.
- **Phương án 2:** Dùng `published` làm source timestamp và tính/đối chiếu `age_days`.
- **Phương án đã chọn:** `published` là timestamp nguồn; stale khi `age_days > 180`.
- **Lý do:** Freshness phải phản ánh nội dung nguồn. Nếu chạy lại hôm nay với một paper
  đã cũ, thời gian tải file mới không được làm paper đó trở thành fresh.
- **Bằng chứng:** Baseline có 1 stale row; corruption `old_date` làm stale rows tăng lên
  3; repaired trở về 1. Signal phản ánh đúng corruption và recovery trong khi row count
  vẫn giữ nguyên 24.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** Khi merge `main`, bảy file quality/report phát sinh conflict, gồm
  `baseline_quality.json`, corrupted/repaired quality/freshness và hai Markdown report.
- **Nguyên nhân gốc:** Đây là generated artifacts được thay đổi ở cả branch cá nhân và
  `main`; chọn toàn bộ `ours` hoặc `theirs` có thể làm report lệch metrics mới nhất.
- **Cách xử lý:** Không sửa marker thủ công theo một phía. Tôi dùng code đã merge để tái
  sinh artifact theo thứ tự baseline → corrupted → repaired, sau đó cập nhật kết luận
  động theo metrics mới và stage đúng các file đã resolve.
- **Cách xác minh:** Không còn file `UU`, không còn marker conflict; ba runner
  `complete`; `13 passed`.
- **Điều học được:** Với generated artifacts, nguồn sự thật là input và generator.
  Regenerate có kiểm soát an toàn hơn ghép từng dòng JSON/Markdown.

Blocker còn lại: embedding manifests lưu `persist_path` của workspace cũ nên baseline
và repaired embedding audit vẫn fail `persist_path_matches_config`. Người phụ trách
RAG/index cần rebuild manifest tại workspace hiện tại; Vai trò 6 chỉ audit và báo lỗi,
không tự sửa index thuộc ownership của vai trò khác.

## 7. Hiểu biết về luồng end-to-end

Crossref trả về raw response và raw paper records. Cleaning chuẩn hóa schema, giữ
`paper_id`, title, summary, authors, categories, `published`, tạo `age_days` và
`text_for_embedding`. Embedding module dùng MiniLM 384 chiều và lưu documents vào các
Chroma collections tách riêng cho baseline, corrupted và repaired.

Evaluation set tạo câu hỏi, ground truth answer và `ground_truth_doc_ids`. Retrieval hit
rate kiểm tra retrieved IDs có chạm ground-truth IDs; Token F1 đo mức trùng token giữa
answer và ground truth; judge metrics đánh giá câu trả lời bằng cùng protocol. Ba trạng
thái phải dùng cùng 72 câu hỏi để delta phản ánh thay đổi dữ liệu/index thay vì thay đổi
bộ kiểm thử.

Quality checks đo tính đầy đủ, hợp lệ và duy nhất của dữ liệu. Freshness monitoring chỉ
tập trung vào độ mới theo `published`/`age_days`; vì vậy structural quality có thể PASS
trong khi freshness FAIL. Corruption tạo dataset/index/metrics riêng và giữ baseline
không đổi. Repair dựng lại dữ liệu từ nguồn, rebuild index và evaluation lại. Recovery
chỉ hoàn toàn khi quality/freshness signals, metrics, answers count và audit artifacts
đều cung cấp bằng chứng phù hợp.

## 8. Phân tích kết quả

### Metrics và signals chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.9167 | 1.0000 | Giảm sau corruption, repaired về baseline |
| `mean_token_f1` | 0.7569 | 0.6603 | 0.7569 | Giảm 0.0967, repaired về baseline |
| `judge_accuracy` | 0.6806 | 0.6250 | 0.6667 | Hồi phục một phần, còn thấp hơn baseline 0.0139 |
| `mean_judge_score` | 3.9583 | 3.7778 | 3.9583 | Repaired về baseline |
| Structural quality | PASS | FAIL | PASS | Duplicate và summary errors đã được sửa |
| Duplicate paper ID rows | 0 | 4 | 0 | Row count 24 không phát hiện được lỗi này |
| Invalid summary rows | 0 | 2 | 0 | Corruption được phát hiện và repair |
| Stale rows | 1 | 3 | 1 | Repaired về baseline nhưng baseline chưa hoàn toàn fresh |
| Freshness status | FAIL | FAIL | FAIL | Cần đọc stale count/ratio, không chỉ đọc boolean status |

### Chuỗi nguyên nhân–bằng chứng

1. Corruption xóa 2 papers mới nhất, tạo 4 duplicate rows, 2 invalid summaries và làm
   stale rows tăng `1 → 3`; 2 papers bị xóa liên quan đến 6/72 evaluation questions;
   retrieval hit rate giảm `1.0000 → 0.9167` và các answer metrics cũng giảm. Vì nhiều
   corruption xảy ra đồng thời, tôi không quy toàn bộ mức giảm answer metrics cho riêng
   một event.
2. Repair dựng lại dữ liệu từ nguồn làm duplicate `4 → 0`, invalid summary `2 → 0`,
   stale rows `3 → 1`; retrieval, Token F1 và mean judge score về baseline. Judge
   accuracy chỉ lên `0.6667`, còn dưới baseline `0.6806`, nên recovery là `partial`.

Corruption có bằng chứng ảnh hưởng agent rõ nhất là `latest_drop`: hai document bị xóa
được 6 test questions tham chiếu và retrieval hit rate giảm đúng 6/72, tương đương
0.0833. Với quality, duplicate là ví dụ rõ nhất cho việc row count có thể che giấu lỗi:
tổng số rows không đổi nhưng duplicate rows tăng từ 0 lên 4.

Kết quả khác kỳ vọng ban đầu là repaired data đã khôi phục toàn bộ structural signals
nhưng recovery vẫn chưa `complete`. Điều này cho thấy khôi phục dữ liệu không bảo đảm
mọi judge metric giống tuyệt đối trong một lần chạy, đồng thời audit portability của
embedding manifest vẫn phải được xử lý riêng.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Một pipeline cần artifact tách riêng và contract ổn định để so sánh được giữa các
   trạng thái; không được ghi đè baseline.
2. Observability phải dùng nhiều signal. Row count hoặc một boolean PASS/FAIL không đủ
   để phát hiện duplicate, mức độ stale hay kết luận recovery.
3. Chất lượng dữ liệu có thể ảnh hưởng cả retrieval và answer metrics, nhưng tương quan
   từ một flow tổng hợp chưa đủ để kết luận quan hệ nhân quả cho từng corruption event.

### Nếu có thêm thời gian

Tôi sẽ bổ sung direct checks cho noise marker và title length, chuyển manifest sang
persist path tương đối hoặc rebuild trên workspace hiện tại, bật Ragas và chạy judge
evaluation nhiều lần với cấu hình/randomness được kiểm soát. Cải thiện được đo bằng:
embedding audit PASS, Ragas artifacts tồn tại, từng corruption scenario có test cô lập
và độ lệch judge metrics giữa các lần chạy được báo cáo.

## 10. Cam kết của thành viên

- [x] Nội dung phản ánh đúng phạm vi Observability của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận đều có JSON, Markdown report hoặc metric để đối chiếu.
- [x] Tôi không ghi hoàn thành cho blocker persist path và Ragas chưa chạy.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo không sao chép nguyên văn báo cáo nhóm hoặc báo cáo của thành viên khác.

**Họ và tên:** Trần Đức Mạnh

**Ngày xác nhận:** 2026-08-06
