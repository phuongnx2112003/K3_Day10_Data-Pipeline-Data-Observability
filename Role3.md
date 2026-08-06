# Nhật ký công việc của Tác tử (Agent work log)

## Thông tin học viên
Họ và tên: Lê Công Dũng
Mã HV: 2202601649
Lớp: E403
Ngày hoàn thiện: 06/08/2026


## CP0 - Giao kèo dữ liệu thô sang dữ liệu sạch (Raw to clean data contract)

Được triển khai trong `src/ingestion/cleaning.py`:

* Khai báo một lược đồ (schema) DataFrame sạch ổn định. Các trường RAG bắt buộc bao gồm `paper_id`, `title`, `text_for_embedding`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, và `pdf_url`.
* Loại bỏ các hàng thô khi thiếu `paper_id`, `title`, hoặc ngày `published` có thể phân tích được. Các giá trị văn bản tùy chọn được chuẩn hóa thành một chuỗi trống.
* Chuẩn hóa ngày tháng về định dạng UTC `YYYY-MM-DD`; giá trị `updated` không hợp lệ sẽ quay lại sử dụng `published`.
* Tính toán `age_days` (số ngày tuổi) từ ngày xuất bản đã chuẩn hóa đến `run_date`.
* Chuẩn hóa khoảng trắng, làm phẳng tác giả/thể loại bằng `", "`, và loại bỏ các giá trị danh sách lặp lại không phân biệt chữ hoa chữ thường.
* Chuẩn hóa ID DOI/tài liệu thành chữ thường và loại bỏ các giá trị `paper_id` bị trùng lặp, giữ lại lần xuất hiện thô đầu tiên.
* Xây dựng `text_for_embedding` từ tiêu đề, tóm tắt, danh sách tác giả đã làm phẳng và danh sách thể loại đã làm phẳng.

Được triển khai trong `src/ingestion/corruption.py`:

* Xác thực giao kèo DataFrame sạch trước khi thực hiện làm nhiễu/làm hỏng (corruption).
* Mô phỏng một cách tất định việc thiếu các bản ghi mới nhất, tóm tắt trống/nhiễu, tiêu đề bị cắt cụt, ngày cũ kỹ và các hàng bị trùng lặp.
* Tính toán lại `summary_chars`, `age_days` cho các hàng cũ, và `text_for_embedding` sau khi làm nhiễu.
* Ghi lại một nhật ký làm nhiễu dạng JSON có khả năng tái tạo mà không làm thay đổi đầu vào cơ sở (baseline).

Việc xác thực CP0 nằm trong `tests/test_ingestion_cleaning.py`. Chạy kiểm thử bằng lệnh:

```powershell
$env:PYTHONPATH="src"
python -m pytest -q tests/test_ingestion_cleaning.py

```

## CP1 - Bổ sung luồng đọc và xuất dữ liệu 

Đã bổ sung vào `src/ingestion/cleaning.py`:

- `load_raw_records_json`: đọc `data/raw/crossref_records.json`, hỗ trợ JSON là
  một danh sách trực tiếp hoặc object có khóa `records`.
- Chuyển dictionary nullable sang `PaperRecord`; mọi trường text tùy chọn bị
  null được đổi thành chuỗi rỗng, còn authors/categories không phải list được
  đổi thành list rỗng.
- `authors_joined` và `categories_joined` được nối bằng `", "`. List rỗng cho
  kết quả `""`, không sinh `None`, `{}` hoặc chuỗi `"nan"`.
- `published` được parse bằng Pandas ở UTC, xuất dưới dạng `YYYY-MM-DD`, và
  `age_days` là số nguyên tính từ ngày chạy pipeline.
- `text_for_embedding` được ghép từ Title, Summary, Authors và Categories.
- Dedupe theo `paper_id` đã chuẩn hóa, dùng đúng `keep="first"`.
- Counter gồm `input_records`, `dropped_missing_core`, `dropped_duplicates`,
  và `clean_records`; kết quả được log và in ra console.
- `save_target_clean_data` chỉ xuất đúng 9 cột trong Target Clean Schema.
- `run_raw_to_clean` điều phối toàn bộ quá trình và mặc định ghi:
  `data/clean/cleaned_records.csv` và `data/clean/cleaned_records.json`.
- `src/ingestion/corruption.py` đã được đồng bộ để nhận trực tiếp artifact chỉ
  có 9 cột target; `age_days` được cập nhật khi có nhưng không còn là điều kiện
  bắt buộc của file giao tiếp CP0.

Tại thời điểm kiểm tra, `data/raw/crossref_records.json` chưa tồn tại nên chưa
sinh artifact thật. Validation tự động dùng fixture Cyrillic tương ứng bản ghi
mẫu và nằm trong `tests/test_ingestion_cleaning.py`.

Lệnh chạy khi raw artifact sẵn sàng:

```powershell
$env:PYTHONPATH="src"
python -c "from ingestion.cleaning import run_raw_to_clean; run_raw_to_clean()"
```

## Kết quả chạy trên raw artifact thực tế

- Kích thước file: 58,291 bytes.
- Số bản ghi đầu vào: 24.
- Bản ghi bị loại do thiếu `paper_id`, `title` hoặc ngày hợp lệ: 0.
- Bản ghi bị loại do trùng `paper_id`: 0.
- Số bản ghi sạch: 24.

Đã sinh hai artifact:
- `data/clean/cleaned_records.csv`
- `data/clean/cleaned_records.json`

Đối chiếu bản ghi `10.47576/2949-1894.2026.7.7.023` thành công:
- `authors_joined` là `И.В. Ермаков, В.В. Филатов`.
- `categories_joined` là chuỗi rỗng.
- `pdf_url` là chuỗi rỗng.
- `published` là `2026-06-17`; tại ngày chạy `2026-08-06`, `age_days = 50`
  trong DataFrame vận hành.
- `text_for_embedding` chứa đúng Title, Authors và Summary từ raw record.

Kiểm tra artifact xác nhận đủ 24 dòng, `paper_id` duy nhất, ba trường cốt lõi
không rỗng, Unicode được giữ nguyên, và output chỉ có đúng 9 cột target. Bộ test
tự động tiếp tục đạt `3 passed`.

## CP2 - Xác minh toàn vẹn, test set và schema contract

Đã kiểm tra cả `data/clean/cleaned_records.json` và
`data/clean/papers_clean.csv`:

- Mỗi artifact có 24 records.
- `text_for_embedding` rỗng/null: 0.
- `paper_id` trùng lặp sau khi trim và so sánh không phân biệt hoa thường: 0.
- `paper_id`, `title`, `published` rỗng: 0.
- Đủ toàn bộ 9 field mà `LocalEmbeddingIndex` sử dụng.
- Dry-run chuyển đổi sang document/metadata của index thành công cho 24/24 rows.

Đã rà soát toàn bộ `data/eval/test_set.json`, không chỉ một sample:

- Tổng số câu hỏi: 72; test ID duy nhất: 72.
- Số paper được tham chiếu: 24/24.
- Phân bố: 24 summary, 24 authors, 24 date. Không có câu categories vì nguồn
  Crossref hiện có `categories_joined` rỗng; builder đã đúng khi không tạo
  ground truth giả.
- Mọi `ground_truth_doc_ids` đều tồn tại trong clean corpus.
- Mọi ground truth đều khớp chính xác field nguồn tương ứng.
- Không có question/ground truth rỗng, `nan`, `none`, `null` hoặc ký tự null.
- Title trong từng question khớp với title của row được tham chiếu.

Script `script/test_rag_config.py` xác nhận clean dataframe đủ field và toàn bộ
embedding text hợp lệ. Vì không có lỗi thiếu field ở index hoặc test set nên
schema contract 9 cột được giữ nguyên, không thêm field giả hay thay đổi giao
tiếp giữa các vai trò.

Việc import full package `retrieval` trong môi trường hiện tại báo thiếu thư viện
`langchain`. Đây là dependency môi trường, không phải lỗi thiếu field trong dữ
liệu. Contract index đã được kiểm tra bằng đúng phép dựng document/metadata mà
`LocalEmbeddingIndex` sử dụng, không gọi model hoặc tải embedding.

## CP3 - Artifact, quality checks và sửa contract

### Kiểm tra clean artifacts

Đã mở và kiểm tra trực tiếp bốn artifact trong `data/clean/`:

- `cleaned_records.csv`: 24 rows.
- `cleaned_records.json`: 24 rows.
- `papers_clean.csv`: 24 rows.
- `papers_clean.json`: 24 rows.

Tất cả đều có `age_days` dạng số nguyên, nhỏ nhất 1 và lớn nhất 193 tại ngày
chạy. Cả bốn artifact có 0 giá trị `text_for_embedding` rỗng. Nội dung embedding
được tạo động từ title, summary, authors và categories của từng row.

Phát hiện contract thực tế: hai artifact `cleaned_records.*` trước CP3 chỉ chứa
9 cột và thiếu `age_days`, trong khi artifact baseline `papers_clean.*` đã có
cột này. Đã sửa `TARGET_CLEAN_COLUMNS` thành contract 10 cột có `age_days`, sau
đó chạy lại raw-to-clean. Kết quả: input 24, invalid 0, duplicate 0, clean 24.

### Xác minh quality check không hardcode Pass

Đã tăng cường `run_data_quality_checks` để tính trực tiếp từ DataFrame:

- Kiểm tra required columns và row count.
- Bắt paper ID null/blank và duplicate không phân biệt hoa thường.
- Bắt title và embedding text rỗng.
- Parse và bắt `published` không hợp lệ.
- Bắt `age_days` null, không phải số hoặc âm.
- Tính `overall_pass` bằng `all()` trên các check bắt buộc thay vì gán cố định.
- Các tỷ lệ summary, embedding và freshness vẫn được báo cáo như metric.

Chạy trên `papers_clean.json` thật cho kết quả `overall_pass: true`: thiếu cột
0, ID blank 0, ID duplicate 0, title blank 0, embedding blank 0, ngày lỗi 0,
age lỗi 0. Có 1 row stale trên ngưỡng 180 ngày; freshness ratio là 0.9583. Đây
là tín hiệu dữ liệu thật và freshness report vẫn trả `is_fresh: false`, không
bị che thành Pass.

Để chứng minh negative path, test tạo bản copy và cố ý tiêm ID blank, duplicate
khác kiểu hoa/thường, title blank, embedding blank, ngày lỗi và age âm. Quality
check trả `overall_pass: false` và từng check tương ứng đều False. Test nằm tại
`tests/test_quality_checks.py`.

### Chạy lại

Đã sinh lại `cleaned_records.csv/json` và cập nhật
`data/quality/baseline_quality.json` từ 24 rows thật. Không cần rebuild toàn bộ
vector index vì traceback contract chỉ tác động artifact giao tiếp
`cleaned_records.*`; baseline dùng `papers_clean.*`, vốn đã có `age_days` và đủ
field index. Kiểm thử CP3 đạt 4 tests.

## CP4 - Corruption có chủ đích trên clean data

Đã thao tác trực tiếp trên `src/ingestion/corruption.py` và dùng
`data/clean/papers_clean.json` làm dữ liệu nạn nhân. Hàm luôn deep-copy đầu vào;
assertion sau khi chạy xác nhận baseline không bị thay đổi.

Các kịch bản được triển khai và chạy thật với rate 10%:

- Drop 2 records mới nhất để mô phỏng thiếu dữ liệu.
- Xóa trắng summary của 2 records; log lưu độ dài trước và sau corruption.
- Sinh chuỗi noise ngẫu nhiên dài 24 ký tự và chèn vào summary của 2 records.
- Cắt title của 2 records xuống tối đa 12 ký tự; log lưu độ dài ban đầu.
- Dịch `published` của 2 records lùi 10 năm và tăng `age_days` tương ứng.
- Thêm 2 duplicate rows để tạo lỗi khóa `paper_id`.

Việc chọn row và tạo noise dùng local random generator với seed mặc định 42.
Do đó các row/noise có tính ngẫu nhiên nhưng kết quả vẫn tái lập được khi chạy
baseline/corrupted/repaired trên cùng dữ liệu. Có thể truyền seed khác qua tham
số keyword nếu muốn tạo một lần thử khác.

Sau khi thay đổi title/summary, code tính lại `summary_chars` và
`text_for_embedding`, bảo đảm vector index nhận đúng nội dung đã bị corruption
thay vì embedding text cũ. Log có seed, corruption rate, paper IDs, noise tokens
và các độ dài trước/sau để audit.

Artifact đã sinh:

- `data/clean/papers_clean_corrupted.csv`
- `data/clean/papers_clean_corrupted.json`
- `data/results/corruption_log.json`

Kết quả thực tế: baseline 24 rows; sau drop 2 và add duplicate 2, corrupted có
24 rows. Kiểm tra artifact thấy đúng 2 summary rỗng, 2 summary có marker noise,
2 title ngắn tối đa 12 ký tự và baseline input không đổi. Cùng seed tạo lại
DataFrame giống hệt. Bộ kiểm thử hiện đạt 4 tests.

Quality check trên corrupted artifact trả `overall_pass: false`, bắt được 2
duplicate IDs, 2 summary rỗng, tổng stale rows tăng từ 1 lên 3 và
`min_summary_chars` giảm xuống 0. Kết quả được lưu tại
`data/quality/corrupted_quality.json`, chứng minh anomalies đã đi vào artifact
thật và được hệ thống quan sát phát hiện.

## CP5 - Corruption audit log và nghiệm thu corrupted dataset

Đã hoàn thiện `corrupt_clean_dataframe` với năm nhóm lỗi bắt buộc: `missing`,
`latest_drop`, `noise`, `old_date`, `duplicate`. Kịch bản truncate title từ CP4
được giữ lại như một corruption bổ sung. Hàm làm việc trên deep copy và log ghi
giá trị kiểm tra thực tế `baseline_unchanged`.

Mỗi event trong `data/results/corruption_log.json` hiện có cùng audit contract:

- `type`: loại corruption.
- `record_ids`: toàn bộ paper ID bị tác động.
- `parameters`: field, rate/mức độ và giá trị đặc thù của action.
- `before_count`: row count ngay trước action.
- `after_count`: row count ngay sau action.

Parameters chi tiết gồm độ dài summary trước khi blank; từng noise token và độ
dài token; độ dài title trước/sau truncate; ngày trước/sau và số năm dịch lùi;
selection/rate của latest drop; khóa dedupe và số copies của duplicate.

Đã sinh lại corrupted CSV/JSON và đối chiếu tự động từng event với dữ liệu:

- `latest_drop`: 2 IDs trong log không còn trong corrupted dataset; count 24 → 22.
- `missing`: đúng 2 IDs có summary rỗng; count giữ nguyên 22 → 22.
- `noise`: đúng token đã log xuất hiện ở summary của từng ID; count 22 → 22.
- `old_date`: ngày của đúng 2 IDs khớp `after_dates` trong log; count 22 → 22.
- `duplicate`: đúng 2 IDs có ít nhất hai occurrences; count 22 → 24.
- `truncate_title`: đúng 2 IDs bị giới hạn title còn tối đa 12 ký tự.
- `text_for_embedding` của mọi row khớp title/summary sau corruption.
- Baseline DataFrame không bị mutate.

Hai dataset khác nhau cả về nội dung lẫn checksum:

- Baseline SHA-256:
  `4c6d40677d8542bceb2561d5ff4465f49334efded35c399fb68db590a67914e2`.
- Corrupted SHA-256:
  `0793aad67ec8dd6ac83faf84f079a3e76cb7f0366a7fd6fb5249f6d3bc01ca00`.

Tất cả 11 điều kiện nghiệm thu (counts, log fields, năm loại lỗi, rebuilt text,
baseline bất biến và checksum khác nhau) đều trả True. Bộ test đạt 4 tests.

## CP6 - Repair từ raw và đối chiếu clean/corrupted/repaired

### Quy trình repair và provenance

Repair được thực thi lại từ `data/raw/crossref_records.json` bằng đúng
`load_raw_records` và `build_clean_dataframe` trong ingestion pipeline. Kết quả
được ghi mới vào `data/clean/papers_clean_repaired.csv` và
`data/clean/papers_clean_repaired.json` bằng utilities xuất dữ liệu. Không có
thao tác copy baseline, không đọc baseline để tạo repaired và không sửa tay row.

Counter của lần chạy repair:

- Raw input: 24 records.
- Drop do thiếu core field/ngày lỗi: 0.
- Drop duplicate raw ID: 0.
- Repaired output: 24 records.

### Kiểm tra repaired dataset

Repaired có đúng 16 cột operational schema giống baseline, gồm `age_days`,
`summary_chars`, flattened authors/categories và `text_for_embedding`. Kết quả
quality trên dữ liệu repaired thật:

- 24 rows và 24 unique paper IDs.
- Duplicate ID: 0.
- Blank summary: 0.
- Noise marker: 0.
- Title dài tối đa 12 ký tự do corruption: 0.
- Empty `text_for_embedding`: 0.
- Stale rows: 1, trở về đúng mức tự nhiên của nguồn.
- `overall_pass: true`.

Freshness repaired được lưu tại `data/quality/repaired_freshness.json`; quality
được lưu tại `data/quality/repaired_quality.json`.

### So sánh ba trạng thái

| Signal | Clean | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| Rows | 24 | 24 | 24 |
| Unique paper IDs | 24 | 22 | 24 |
| Duplicate rows theo ID | 0 | 2 | 0 |
| Blank summary | 0 | 2 | 0 |
| Noise rows | 0 | 2 | 0 |
| Title ngắn ≤ 12 ký tự | 0 | 2 | 0 |
| Stale rows | 1 | 3 | 1 |
| Empty embedding text | 0 | 0 | 0 |
| Quality overall | Pass | Fail | Pass |

Số rows corrupted vẫn là 24 vì corruption xóa 2 latest rồi thêm 2 duplicate;
row count đơn lẻ vì thế không phát hiện được lỗi. Unique IDs và quality signals
cho thấy corpus thực sự đã mất hai papers và thay bằng hai bản sao. Repair đọc
lại raw phục hồi hai IDs đã mất, loại duplicate/noise/missing/old-date anomalies
và rebuild embedding text sạch.

Canonical SHA-256:

- Clean: `54241a54431fb172fef657057830227d12373633c17cda95c434d6b12109b571`.
- Corrupted: `887ddeabb350126b9ab6d8cb1e5e96e4a5bdaab7ee5dfe3f3031e8e7788899ea`.
- Repaired: `54241a54431fb172fef657057830227d12373633c17cda95c434d6b12109b571`.

DataFrame clean khác corrupted, còn repaired bằng clean ở toàn bộ schema và
giá trị. Checksum repaired trùng clean là kết quả của việc tái tạo xác định từ
cùng raw source và cleaning rules, không phải do sao chép artifact. Bộ test sau
repair đạt 4 tests.
