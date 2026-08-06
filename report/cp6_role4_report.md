# Báo cáo Checkpoint 6 - Vai trò 4 (RAG & Agent Owner)

**Người thực hiện**: Nguyễn Đào Nam Hải (Vai trò 4)
**Mục tiêu**: Build Vector DB (Chroma) từ dữ liệu Repaired (`papers_clean_repaired.json`) do Vai trò 2 và Vai trò 3 bàn giao, kiểm chứng khả năng phục hồi của RAG và xác nhận sự tồn tại độc lập của cả 3 trạng thái Pipeline.

## 1. Trạng thái hoàn thành
- [x] Nhận `papers_clean_repaired.json` từ nhánh `main`.
- [x] Đã nhúng (embed) thành công 24 bản ghi phục hồi vào Collection cuối cùng: `papers-repaired`.
- [x] Đã chạy Smoke test Semantic Search và Exact Lookup.
- [x] Đã kiểm tra và xác nhận 3 collection (`papers-baseline`, `papers-corrupted`, `papers-repaired`) tồn tại độc lập, không ghi đè lẫn nhau, mỗi collection chứa chuẩn 24 records.

## 2. Kết quả Phục hồi (Smoke Test)
Với câu hỏi truy vấn: *"Large language models and AI safety"*

- **Corrupted (Checkpoint 5)**: Bài báo *SafeRAG* bị biến mất hoàn toàn do lỗi dữ liệu.
- **Repaired (Checkpoint 6)**: Hệ thống RAG đã tìm lại được bài báo này.
  - Top 1: `The Age of Autonomous Agents...` (Score: 0.4706)
  - Top 2: `SafeRAG: A Large-Language-Model-Based Multistage Retrieval-Augmented Framework...` (Score: 0.4170)
  
**Kết luận**: Chức năng RAG đã được phục hồi hoàn toàn sau khi quá trình Data Observability phát hiện lỗi và Data Engineering (Role 2 & 3) thực hiện Repair pipeline. Exact Lookup hoạt động tốt và trả về đúng nội dung toàn vẹn của paper.

## 3. Bàn giao cuối cùng
- Artifact `data/embeddings/papers_embeddings_repaired.json` và Vector DB `papers-repaired` đã được push lên GitHub.
- **Hoàn thành 100% nhiệm vụ của Role 4 trong Lab!** Mọi thứ đã sẵn sàng cho buổi Demo trình diễn cuối giờ.
