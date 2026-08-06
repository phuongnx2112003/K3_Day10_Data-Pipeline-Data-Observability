# Kịch Bản Demo Tổng Hợp: Từ Lỗi Dữ Liệu đến RAG Phục Hồi
*(Dành cho toàn bộ 6 Roles trong Team)*

## 🎯 Giới thiệu chung (Dành cho Role 1 - Lead)
- **Hành động:** Mở toàn màn hình giao diện Web (UI).
- **Role 1 (Lead) trình bày:** 
  > *"Chào mọi người. Hôm nay nhóm chúng em xin trình bày luồng Data Pipeline hoàn chỉnh, kết hợp Data Observability và RAG.
  > Giao diện trước mắt các bạn là Hệ thống điều khiển trung tâm (Control Center). Thay vì chỉ demo code console khô khan, chúng em đã xây dựng Dashboard này để trực quan hóa toàn bộ câu chuyện: Từ việc lấy dữ liệu gốc (Baseline), bị phá hỏng ngầm (Corrupted), cho đến khi được phát hiện và cứu chữa (Repaired)."*

---

## Bước 1: Thu thập và Nhúng Dữ Liệu (Baseline)
- **Hành động:** Chuyển sang Tab `Corpus Viewer` và chọn **Corpus State: Baseline**.
- **Role 2 (Ingestion) trình bày:** 
  > *"Em đảm nhận việc thu thập dữ liệu thô từ Crossref API. Đây là bộ Corpus gốc gồm 24 bài báo khoa học chất lượng cao về AI và RAG. Dữ liệu này sạch và đầy đủ các trường quan trọng như Title, Summary, DOI."*

- **Hành động:** Chuyển sang Tab `Data Observability`.
- **Role 6 (Observability) trình bày:**
  > *"Ngay khi dữ liệu được tải về, em dùng Great Expectations để kiểm duyệt. Như trên bảng, mọi người thấy `Freshness` đạt màu Xanh (dưới 180 ngày), và `Null Checks` Pass 100%. Dữ liệu đủ tiêu chuẩn để đưa vào ứng dụng AI."*

---

## Bước 2: Hiệu năng của AI khi dữ liệu chuẩn
- **Hành động:** Chuyển sang Tab `Agentic RAG Chat`. Chọn **Database State: Baseline**. Nhập câu hỏi *"What does the paper SafeRAG talk about?"* và bấm Gửi.
- **Role 4 (RAG Owner) trình bày:**
  > *"Em là người xây dựng RAG Agent. Dựa trên dữ liệu Baseline sạch, Agent của em dễ dàng tìm thấy chính xác bài báo SafeRAG với điểm số tin cậy cao và tóm tắt lại xuất sắc nội dung cho người dùng."*

---

## Bước 3: Mô phỏng thảm họa dữ liệu (Corrupted)
- **Hành động:** Quay lại Tab `Corpus Viewer` và chọn **Corpus State: Corrupted**. Mở ngẫu nhiên một bài báo.
- **Role 3 (Cleaning & Corruption) trình bày:**
  > *"Thực tế hệ thống không bao giờ hoàn hảo. Em đã chủ động tạo ra một đoạn script làm hỏng dữ liệu (xóa Title, xóa Summary, gây nhiễu văn bản) để mô phỏng một sự cố Data Pipeline ngầm. Mọi người có thể thấy dữ liệu JSON ở trạng thái này đã bị biến dạng."*

- **Hành động:** Chuyển sang Tab `Agentic RAG Chat`. Chọn **Database State: Corrupted**. Nhập lại đúng câu hỏi trên.
- **Role 4 (RAG Owner) tiếp lời:**
  > *"Với Database hỏng này, AI của em lập tức bị 'mù'. Dù vẫn dùng thuật toán tìm kiếm cũ, nhưng RAG không thể tìm ra bài báo SafeRAG nữa, mà trả về những nội dung rác rưởi không liên quan (Garbage In -> Garbage Out)."*

---

## Bước 4: Đánh giá sự cố và Phát hiện
- **Hành động:** Chuyển sang Tab `3-State Compare`.
- **Role 5 (Evaluator) trình bày:**
  > *"Em đo lường tự động bằng Ragas và bảng so sánh 3 trạng thái đã tố cáo sự thật: Hit Rate và F1 Score của RAG từ 91.6% đã sụp đổ xuống chỉ còn ~45%. LLM Accuracy cũng giảm một nửa."*

- **Role 6 (Observability) bổ sung:**
  > *"Đồng thời, hệ thống cảnh báo Data Observability của em cũng nổ còi: Rất nhiều trường Null xuất hiện, hoặc có sự sụt giảm Row Count bất thường. Nhờ đó team Data Engineer lập tức biết hệ thống đang có lỗi ở đâu để khắc phục, thay vì cứ để AI trả lời sai cho khách hàng."*

---

## Bước 5: Cứu chữa và Kết luận (Repaired)
- **Hành động:** Quay lại Tab `Agentic RAG Chat`. Chọn **Database State: Repaired**. Nhập câu hỏi lần cuối.
- **Role 3 (Cleaning) trình bày:**
  > *"Nhờ tín hiệu từ Role 6, em đã chạy lại Pipeline sửa lỗi, lấp đầy các dữ liệu bị thiếu từ bản sao lưu và làm sạch lại text."*
  
- **Role 4 (RAG Owner) trình bày:**
  > *"Và đây là kết quả. Khi RAG truy vấn vào Database Repaired, nó đã tìm lại được bài báo SafeRAG. Hiệu năng phục hồi hoàn toàn như lúc ban đầu!"*

- **Role 1 (Lead) chốt lại:**
  > *"Đó là sức mạnh của Data Observability. Khác với Software truyền thống, ứng dụng AI/Agent phụ thuộc 100% vào Data. Nếu không có Observability chốt chặn ở giữa, chúng ta sẽ không bao giờ biết vì sao AI bỗng dưng ngu đi. Cảm ơn mọi người đã theo dõi!"*
