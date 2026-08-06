# BÁO CÁO TIẾN ĐỘ THEO CHECKPOINT — VAI TRÒ 5 (EVALUATION OWNER)

**Người thực hiện:** Minh Đức  
**Vai trò:** Vai trò 5 — Evaluation Owner (Nhóm 6 người)  
**Phạm vi phụ trách:** `src/evaluation/testset.py`, `src/evaluation/metrics.py`, `data/eval/`, `data/results/`

---

## 📌 CHECKPOINT 0 (00:00 – 00:30): Khởi động & Thống nhất Contract
- **Công việc thực hiện:**
  - Đọc và phân tích cấu trúc các file `src/evaluation/testset.py`, `qa.py`, `metrics.py`.
  - Thống nhất Schema dữ liệu đầu vào với Cleaning Owner (`paper_id`, `title`, `summary`, `authors_joined`, `published`, `categories_joined`).
- **Kết quả:**
  - Thống nhất contract JSON Schema cho `test_set.json` gồm 5 trường chuẩn: `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids`.

---

## 📌 CHECKPOINT 1 (00:30 – 01:05): Triển khai Code & Tạo Test Set
- **Công việc thực hiện:**
  - Hoàn thiện hàm `build_test_set(df, output_path)` trong `src/evaluation/testset.py`.
  - Đọc 24 bài báo khoa học thật từ `data/clean/papers_clean.csv`.
  - Thiết kế bộ câu hỏi tự động theo 4 nhóm: `summary`, `authors`, `date`, `categories`.
  - Lọc sạch các giá trị rỗng/`nan` để đảm bảo chất lượng ground truth.
- **Kết quả:**
  - Sinh thành công **72 câu hỏi kiểm thử chuẩn** gán đúng DOI thật (`ground_truth_doc_ids`).
  - Đã commit và push nhánh `minh_duc` lên GitHub repository.

---

## 📌 CHECKPOINT 2 (01:05 – 01:35): Khóa Test Set & Kiểm tra Đồng bộ
- **Công việc thực hiện:**
  - Khóa file `data/eval/test_set.json` (72 câu hỏi).
  - Kiểm tra đối chiếu 100% `paper_id` trong test set tồn tại trong file clean để chuẩn bị cho Vector Store.
- **Kết quả:**
  - File `data/eval/test_set.json` đạt độ chính xác 100%, không bị rác dữ liệu.

---

## 📌 CHECKPOINT 3 (01:35 – 02:00): Đánh giá Baseline (Phase 1)
- **Công việc thực hiện:**
  - Thực thi luồng đánh giá RAG Agent trên bộ dữ liệu sạch 24 bài báo.
  - Tạo ra 2 file kết quả: `data/results/baseline_answers.json` và `data/results/baseline_metrics.json`.
  - Đọc và phân tích các chỉ số đánh giá.
- **Kết quả Baseline Metrics:**
  - `samples`: **72 / 72 câu hỏi**
  - `retrieval_hit_rate`: **1.0 (100%)** — ChromaDB Vector Store tìm thấy chính xác 100% tài liệu gốc.
  - `mean_token_f1`: **0.4236 (42.36%)** — Độ trùng khớp từ ngữ tự nhiên giữa Agent và ground truth.
  - `judge_accuracy`: **33.33% / 34.72%** — Sử dụng Heuristic Fallback Judge minh bạch.

---

## 📌 CHECKPOINT 4 (02:00 – 02:15): Nghỉ giải lao & Chuẩn bị Kịch bản Corruption
- **Công việc thực hiện:**
  - Nghỉ giải lao 15 phút.
  - Chuẩn bị kế hoạch re-evaluate bộ câu hỏi cũ trên dữ liệu hỏng.

---

## 📌 CHECKPOINT 5 (02:15 – 03:15): Đánh giá Dữ liệu Hỏng (Corrupted Evaluation & Impact)
- **Công việc thực hiện:**
  - Re-evaluate bộ 72 câu hỏi `test_set.json` trên tập dữ liệu bị cấy 5 dạng lỗi (`papers_clean_corrupted.csv`).
  - Xuất kết quả ra `data/results/corrupted_metrics.json` và `corrupted_answers.json`.
- **Kết quả Corrupted Metrics:**
  - `retrieval_hit_rate`: **0.9167 (91.67%)** — **Sụt giảm 8.33%** so với Baseline.
- **Bằng chứng Kỹ thuật (Impact Analysis):**
  - Sự sụt giảm 8.33% xảy ra do sự kiện `drop_latest` đã xóa mất 2 bài báo mới nhất (`10.2118/234689-pa` và `10.63646/kpqm1958`), khiến RAG Agent bị Retrieval Miss ở 6 câu hỏi liên quan.

---

## 📌 CHECKPOINT 6 (03:15 – 04:00): Đánh giá Khôi phục (Repaired Evaluation) & Báo cáo So sánh
- **Công việc thực hiện:**
  - Re-evaluate trên dữ liệu đã phục hồi (`papers_clean_repaired.csv`).
  - So sánh bộ chỉ số qua 3 giai đoạn: **Baseline $\rightarrow$ Corrupted $\rightarrow$ Repaired**.
- **Kết quả Tổng hợp So sánh:**
  - **Hit Rate:** Baseline (100%) $\rightarrow$ Corrupted (91.67%) $\rightarrow$ Repaired (100%).
  - Chứng minh thành công: Dữ liệu xấu làm suy giảm hiệu năng của AI Agent, và quy trình Data Repair đã giúp khôi phục 100% độ chính xác.
