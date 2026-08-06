## CP0
**Thông tin bàn giao**:
   - **Path file raw snapshot**: `data/raw/crossref_records.json`
   - **Sample Record**:
   ```json
   {
     "paper_id": "10.47576/2949-1894.2026.7.7.023",
     "title": "Снижение рисков применения LLM (Large Language Model) в сфере экономической безопасности...",
     "summary": "В статье проведено исследование особенностей снижения рисков применения LLM...",
     "authors": [
       "И.В. Ермаков",
       "В.В. Филатов"
     ],
     "categories": [],
     "primary_category": "",
     "published": "2026-06-17",
     "updated": "2026-06-17",
     "abs_url": "https://doi.org/10.47576/2949-1894.2026.7.7.023",
     "pdf_url": "",
     "comment": "Publishing house Pegas"
   }
   ```


## CP1 Bàn giao cho Evaluation & Observability (Mốc: Data Lineage & Consistency)

1. **Kiểm tra một `paper_id` xuyên suốt raw → clean → index metadata**:
   - Lấy ngẫu nhiên `paper_id = "10.47576/2949-1894.2026.7.7.023"`. Em đã trace và xác minh được ID này đi qua toàn bộ pipeline không đổi:
     - `raw`: Xuất hiện dưới trường `DOI` trong `data/raw/crossref_response.json` và được lưu vào `paper_id` tại `data/raw/crossref_records.json`.
     - `clean`: Có mặt ở dạng khóa chính trong `data/clean/papers_clean.csv` và `papers_clean.json`.
     - `index`: Được đính kèm vào metadatas `paper_id` của từng chunk (ví dụ record_id `10.47576/2949-1894.2026.7.7.023::9`) trong `data/embeddings/papers_embeddings.json`.
     - `eval`: Nằm trong `source_doc_ids` của bộ câu hỏi ở `data/eval/test_set.json`.
   - Kết luận: Lineage chuẩn, không gãy vỡ ở bất cứ khâu nào.

2. **Cung cấp bằng chứng từ nguồn khi evaluator hoặc agent trả lời sai**:
   - Khi chạy RAG, bất kỳ chunk văn bản nào sinh ra câu trả lời đều giữ nguyên `paper_id` và `abs_url`. Nhờ sự xuyên suốt của ID này (đã được chứng minh ở mục 1), nếu RAG trả lời sai hoặc Evaluator chấm điểm thấp, ta luôn có thể truy xuất lại `data/raw/crossref_records.json` bằng đúng `paper_id` để biết lỗi do LLM hallucination hay do dữ liệu gốc chứa rác.
   
3. **Không refresh nguồn giữa chừng làm baseline thay đổi**:
   - File cấu hình `core/config.py` đã dùng cờ `refresh_source` thông qua biến môi trường.
   - Thống nhất nguyên tắc: **KHÔNG** bật `refresh_source=True` ở giữa quá trình chạy baseline và corrupted, vì việc gọi API tải dữ liệu mới sẽ làm xáo trộn evaluation set (làm invalid metrics so sánh). Source API chỉ được fetch lại 1 lần duy nhất lúc tạo baseline ban đầu.

## CP2 Xác minh & Thống kê dữ liệu (Mốc: Lineage & Count)

1. **Xác minh khả năng đọc dữ liệu**:
   - Đã chạy script kiểm tra: Các file `data/raw/crossref_response.json`, `data/raw/crossref_records.json` và `data/clean/papers_clean.csv` đều đọc/load thành công mà không gặp lỗi định dạng hay encoding (UTF-8).
   - Sample lineage của các file trên vẫn hoàn toàn khớp nối.

2. **So sánh số lượng raw / clean**:
   - Số lượng bản ghi raw (trước clean): **24** bản ghi.
   - Số lượng bản ghi clean (sau clean): **24** bản ghi.
   - **Độ chênh lệch**: 0 bản ghi. 
   - **Lý do**: Không có bản ghi nào bị drop trong lúc làm sạch do tất cả 24 bản ghi raw ban đầu (trích xuất từ Crossref) đều hợp lệ, không dính null ở các key bắt buộc (như DOI/title) nên tỷ lệ giữ lại là 100%.

3. **Đảm bảo Phase 1 không fetch lại nguồn ngoài ý muốn**:
   - Đã kiểm tra logic điều phối trong file `src/pipelines/phase1.py` (hàm `_load_raw_records`).
   - Luồng code đang áp dụng rule caching an toàn: chỉ gọi API bằng `fetch_source_records` nếu file json chưa tồn tại hoặc cờ `settings.refresh_source` đang bật.
   - Nhờ cơ chế này, quá trình chạy Phase 1 (Baseline) và các phase phía sau luôn khóa chặt (lock) nguồn dữ liệu, bảo đảm metrics baseline không tự nhiên bị thay đổi do dữ liệu trên Crossref cập nhật thêm bài viết mới.

## CP3 Xác minh & Thống kê dữ liệu (Mốc: Lineage & Count)

1. **Xác minh khả năng đọc dữ liệu**:
   - Đã chạy script kiểm tra: Các file `data/raw/crossref_response.json`, `data/raw/crossref_records.json` và `data/clean/papers_clean.csv` đều đọc/load thành công mà không gặp lỗi định dạng hay encoding (UTF-8).
   - Sample lineage của các file trên vẫn hoàn toàn khớp nối.

2. **So sánh số lượng raw / clean**:
   - Số lượng bản ghi raw (trước clean): **24** bản ghi.
   - Số lượng bản ghi clean (sau clean): **24** bản ghi.
   - **Độ chênh lệch**: 0 bản ghi. 
   - **Lý do**: Không có bản ghi nào bị drop trong lúc làm sạch do tất cả 24 bản ghi raw ban đầu (trích xuất từ Crossref) đều hợp lệ, không dính null ở các key bắt buộc (như DOI/title) nên tỷ lệ giữ lại là 100%.

3. **Đảm bảo Phase 1 không fetch lại nguồn ngoài ý muốn**:
   - Đã kiểm tra logic điều phối trong file `src/pipelines/phase1.py` (hàm `_load_raw_records`).
   - Luồng code đang áp dụng rule caching an toàn: chỉ gọi API bằng `fetch_source_records` nếu file json chưa tồn tại hoặc cờ `settings.refresh_source` đang bật.
   - Nhờ cơ chế này, quá trình chạy Phase 1 (Baseline) và các phase phía sau luôn khóa chặt (lock) nguồn dữ liệu, bảo đảm metrics baseline không tự nhiên bị thay đổi do dữ liệu trên Crossref cập nhật thêm bài viết mới.

## CP 5: Bàn giao cho Corrupted Flow (Mốc: Data Protection & Repairability)

1. **Xác nhận raw nguồn nguyên vẹn trước khi corrupt clean data**:
   - Trong quá trình gọi `corrupt_clean_dataframe()` (tại `src/pipelines/corruption_flow.py`), script chỉ thao tác trên bản sao bộ nhớ (dataframe) của file `data/clean/papers_clean.json`.
   - File gốc `data/raw/crossref_records.json` (chứa dữ liệu nguyên thủy) hoàn toàn không bị touch, read/write đè lên hay modify. Do đó, dù data downstream có bị nhiễu loạn hay xóa mất trường, dữ liệu thô ban đầu vẫn được bảo vệ 100%.

2. **Chọn record có lineage rõ để chứng minh có thể repair**:
   - Sử dụng lại record mẫu: `paper_id = "10.47576/2949-1894.2026.7.7.023"`.
   - Ngay cả khi bản ghi này bị mất `title`, abstract bị nhiễu ký tự lạ, hay ngày tháng biến thành NaN trong file `papers_clean_corrupted.csv`, thì hệ thống hoàn toàn có thể sửa chữa (Repair) bằng cách gọi lại: 
     `repaired_df = build_clean_dataframe(raw_records, now_utc())`
   - Nhờ sự tồn tại của `paper_id` chuẩn làm cầu nối, Pipeline map ngược được về bản ghi nguyên gốc trong Raw Snapshot để khôi phục (re-clean) mà không cần đoán mò.

3. **Kiểm tra corrupted flow không fetch nguồn mới làm comparison mất công bằng**:
   - Em đã review `src/pipelines/corruption_flow.py` và xác nhận script hoàn toàn **KHÔNG CÓ** hàm `fetch_source_records()`.
   - Hàm duy nhất được gọi để load lại dữ liệu phục hồi là `load_raw_records(settings.paths.raw_records_json)`. 
   - Điều này triệt tiêu rủi ro tải nhầm bản ghi mới từ Crossref. Data baseline và Data repaired sẽ có số lượng base records y hệt nhau, đảm bảo tính công bằng (apples-to-apples) tuyệt đối khi so sánh Metrics (Hit Rate, F1, Accuracy) trên biểu đồ/Report cuối cùng.