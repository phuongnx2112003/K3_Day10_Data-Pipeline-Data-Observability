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


   ## Bàn giao cho Evaluation & Observability (Mốc: Data Lineage & Consistency)

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