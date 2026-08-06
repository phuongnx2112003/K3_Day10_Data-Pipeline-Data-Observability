# Nhật ký công việc của Tác tử (Agent work log)

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

## Bổ sung luồng đọc và xuất dữ liệu CP0

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

## Kết quả chạy trên raw artifact thực tế (2026-08-06)

Đã phát hiện và đọc thành công `data/raw/crossref_records.json`:

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
