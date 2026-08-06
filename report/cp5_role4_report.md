# Báo cáo Checkpoint 5 - Vai trò 4 (RAG & Agent Owner)

**Người thực hiện**: Nguyễn Đào Nam Hải (Vai trò 4)
**Mục tiêu**: Build Vector DB (Chroma) từ dữ liệu Corrupted (`papers_clean_corrupted.json`) do Vai trò 3 bàn giao, quan sát sự lệch lạc của kết quả truy xuất và bảo vệ dữ liệu Baseline.

## 1. Trạng thái hoàn thành
- [x] Đã sử dụng `papers_clean_corrupted.json` do Role 3 (Phụ trách Cleaning & Corruption) chuẩn bị.
- [x] Đã nhúng (embed) thành công 24 bản ghi bị làm hỏng vào một Collection hoàn toàn mới: `papers-corrupted`.
- [x] Đã chạy lại Smoke test Semantic Search với query *"Large language models and AI safety"*.
- [x] Đã chứng minh Baseline (`papers-baseline`) không bị ảnh hưởng (Collection `papers-baseline` vẫn được bảo toàn nguyên vẹn trong tệp `chroma.sqlite3`).

## 2. Kết quả Smoke Test (Corrupted vs Baseline)
Cùng một câu hỏi truy vấn: *"Large language models and AI safety"*

- **Ở Baseline (Dữ liệu Sạch)**:
  - Top 1 trả về bài báo đúng nhất: `SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework...` (ID: 10.2118/234689-pa)
  
- **Ở Checkpoint 5 (Dữ liệu Hỏng)**:
  - Top 1 bị thay đổi thành: `Adapting Large Language Models for Low-Resource Regulated Domains...` (ID: 10.21203/rs.3.rs-9770645/v1) với score `0.3887`
  - Top 2 bị thay đổi thành: `Hybrid Graph` (ID: 10.22214/ijraset.2026.82233) với score `0.3696`
  - **Kết luận**: Bài báo `SafeRAG` kỳ vọng đã bị văng khỏi Top kết quả tìm kiếm do dữ liệu `text_for_embedding` của bài báo này đã bị Role 3 làm hỏng (có thể là xóa title, summary hoặc thêm nhiễu). Điều này chứng minh **Dữ liệu rác (Garbage In) -> Truy xuất sai lệch hoàn toàn (Garbage Out)**.

## 3. Xác nhận bàn giao cho Checkpoint 6
- Collection `papers-corrupted` đã sẵn sàng trong `data/chroma`.
- Đã bàn giao lại cho **Thành viên 5 (Evaluator)** để chạy evaluation chấm điểm sụt giảm F1/Hit Rate.
- Đã thông báo cho **Thành viên 1 (Lead)** để tích hợp RAG vào pipeline `corruption_flow.py`.

Sẵn sàng sang giai đoạn Repair ở Checkpoint 6!
