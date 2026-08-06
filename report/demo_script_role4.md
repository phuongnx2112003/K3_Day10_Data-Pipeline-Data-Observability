# Kịch Bản Demo: Đánh giá tác động của Data Quality lên hệ thống Agentic RAG
*(Dành cho Role 4 - RAG & Agent Owner)*

## 🎯 Mục tiêu Demo
Khán giả (Thầy giáo/Lead) sẽ thấy trực quan hệ thống AI Assistant (RAG) bị "mù" như thế nào khi Data Pipeline bị hỏng (Garbage In -> Garbage Out), và cách nó phục hồi sự thông minh sau khi Data được Repair.

---

## 🎬 Các bước thực hiện trên Giao diện Web (UI)

### Bước 1: Giới thiệu giao diện 3-State Compare
- **Hành động:** Mở tab `3-State Compare` trên giao diện web.
- **Thuyết minh:** 
  > *"Chào mọi người, đây là bảng theo dõi chất lượng RAG dựa trên 3 trạng thái dữ liệu của Data Pipeline. 
  > Như mọi người thấy, ở trạng thái **Baseline (Gốc)**, F1 Score và Hit Rate của chúng ta rất cao (91.6%).
  > Tuy nhiên, khi xảy ra lỗi dữ liệu ở trạng thái **Corrupted** (Bị mất text, nhiễu dữ liệu), các chỉ số này tụt thê thảm xuống chỉ còn ~45%. 
  > Và cuối cùng, sau khi Role 2 và Role 3 kích hoạt Data Observability và **Repaired (Phục hồi)** dữ liệu, RAG của chúng ta đã lấy lại phong độ."*

### Bước 2: Demo trực tiếp sức mạnh RAG ở trạng thái Baseline (Gốc)
- **Hành động:** 
  1. Chuyển sang tab `AI Assistant`.
  2. Ở thanh Dropdown **Database State**, chọn **Baseline**.
  3. Nhập câu hỏi: *"What does the paper SafeRAG talk about?"* hoặc *"Large language models and AI safety"*
  4. Nhấn Gửi.
- **Thuyết minh:** 
  > *"Bây giờ em sẽ thử truy vấn trực tiếp trên Database Baseline. 
  > Hệ thống ngay lập tức tìm thấy đúng bài báo **SafeRAG**, chứng tỏ Vector DB đang chứa thông tin chuẩn xác và Agent hoạt động tốt."*

### Bước 3: Đổi sang trạng thái Corrupted (Mô phỏng thảm họa dữ liệu)
- **Hành động:**
  1. Đổi thanh Dropdown **Database State** sang **Corrupted**.
  2. Nhập lại chính xác câu hỏi vừa rồi: *"What does the paper SafeRAG talk about?"*
  3. Nhấn Gửi.
- **Thuyết minh:**
  > *"Giả sử Data Pipeline bị lỗi ngầm, file JSON bị mất trường Title và Summary mà không ai biết. Hệ thống tự động đẩy dữ liệu rác này vào ChromaDB Corrupted.
  > Khi em hỏi lại cùng một câu hỏi, AI Assistant trả về kết quả hoàn toàn sai lệch (Ví dụ: Trả về bài báo về Insurance hoặc báo lỗi không tìm thấy). 
  > Đây chính là hiệu ứng Garbage In - Garbage Out. Dù LLM có xịn đến mấy, nếu Data hỏng thì Agent cũng bị mù."*

### Bước 4: Đổi sang trạng thái Repaired (Phục hồi thành công)
- **Hành động:**
  1. Đổi thanh Dropdown **Database State** sang **Repaired**.
  2. Nhập lại câu hỏi đó lần thứ 3.
  3. Nhấn Gửi.
- **Thuyết minh:**
  > *"Nhờ hệ thống Great Expectations chặn lại và cảnh báo ở Data Observability Tab, team Data Engineer đã phát hiện và chạy lệnh Repair.
  > Bây giờ với collection Repaired, hệ thống RAG đã thông minh trở lại và lập tức truy xuất trúng bài báo SafeRAG như lúc ban đầu."*

---

## 🏆 Thông điệp chốt (Takeaway)
> *"Qua buổi Lab này, team em đã chứng minh được: Việc xây dựng ứng dụng AI/Agent không chỉ nằm ở việc Prompt Engineering hay chọn LLM giỏi, mà **Cốt lõi nằm ở Data Pipeline và Data Observability**. Chỉ khi kiểm soát được luồng dữ liệu (Data Contract, Quality Checks), chúng ta mới đảm bảo được AI hoạt động ổn định và chính xác trên production."*
