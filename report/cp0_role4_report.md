# Báo cáo hoàn thành Checkpoint 0 (Vai trò 4: RAG & Agent Owner)

## 1. Phân tích đầu vào & đầu ra hệ thống (`index.py`, `embeddings.py`, `agent.py`)

*   **`embeddings.py` (MiniLMEmbeddings):** 
    Sử dụng `SentenceTransformer` để load mô hình nhúng. Đầu vào là list các văn bản (`str`), đầu ra là list các vector biểu diễn (`list[float]`).
*   **`index.py` (LocalEmbeddingIndex):**
    *   **Đầu vào cần thiết từ bước Clean:** Một DataFrame chứa các cột bắt buộc: `paper_id`, `title`, `text_for_embedding`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url`.
    *   **Đầu ra:** Dữ liệu được lưu cục bộ dưới dạng Vector Database (ChromaDB) và một file manifest (`embeddings.json`). Đã định nghĩa sẵn hàm `search` (tìm kiếm theo ngữ nghĩa) và `lookup` (tìm kiếm chính xác).
*   **`agent.py` (build_agent):**
    *   Tạo Agent bằng Langchain.
    *   Được trang bị 2 tool mặc định: `semantic_search_papers` và `lookup_paper`.
    *   **Quy tắc:** Agent bị ép buộc qua system prompt là *phải dùng tool trước khi trả lời* các câu hỏi thực tế (factual questions).

## 2. Thống nhất các cấu hình cốt lõi (Contract)

*   **Embedding Model:** Sử dụng model `sentence-transformers/all-MiniLM-L6-v2`. (Tốc độ xử lý nhanh, phù hợp chạy local).
*   **Quy tắc đặt tên Collection:** Dùng 3 tên riêng biệt để quản lý 3 trạng thái của pipeline, tránh ghi đè:
    *   `papers-baseline` (Dữ liệu sạch, chuẩn)
    *   `papers-corrupted` (Dữ liệu cố tình làm hỏng để test)
    *   `papers-repaired` (Dữ liệu đã được phục hồi)
*   **Metadata bắt buộc khi index:** `paper_id`, `title`, `published`, `authors_joined`, `categories_joined`, `summary`, `abs_url`, `pdf_url`. Yêu cầu này sẽ được chốt với Vai trò 3 (phụ trách Clean).

## 3. Các kịch bản kiểm thử (Smoke Query) chuẩn bị sẵn cho Checkpoint 2

Sau khi build xong index, sẽ dùng các query sau để test ngay lập tức:

*   **Semantic Search (Tìm kiếm ngữ nghĩa):**
    *   *"What are the latest advancements mentioned in these papers?"*
    *   *"How does machine learning improve data observability?"*
*   **Exact Lookup (Tìm kiếm chính xác):**
    *   Chuẩn bị sẵn một mã DOI thực tế (ví dụ: `10.1234/abc.567`) hoặc tiêu đề chính xác của một bài báo lấy từ file `data/clean/` để kiểm tra khả năng tra cứu 1-1 của index.
