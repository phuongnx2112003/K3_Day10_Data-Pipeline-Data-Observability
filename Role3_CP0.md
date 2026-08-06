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
