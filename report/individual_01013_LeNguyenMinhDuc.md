# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | Lê Nguyễn Minh Đức |
| **MSSV** | 01013 |
| **Khóa/Lớp** | K3 |
| **Tên nhóm** | Nhóm 6 người (Data Pipeline & Data Observability) |
| **Vai trò chính** | **Vai trò 5: Evaluation Owner** (Evaluation Set & Metrics Owner) |
| **Repository** | `https://github.com/phuongnx2112003/K3_Day10_Data-Pipeline-Data-Observability` |
| **Ngày hoàn thành** | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Test Set Generator** | `src/evaluation/testset.py` (`build_test_set`) | `papers_clean.csv` (24 bài báo) | `data/eval/test_set.json` (72 câu hỏi) | Hoàn thành |
| **Metrics Calculation** | `src/evaluation/metrics.py` (`evaluate_pipeline`) | `test_set.json` & RAG Agent | `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json` | Hoàn thành |
| **QA Extraction Logic** | `src/retrieval/qa.py` (`_extract_answer`) | Question string & Top SearchResult | `AnswerResult` với câu trả lời trích xuất chuẩn | Hoàn thành |
| **Evaluation Reports** | `report/role5_evaluation_report.md` | Kết quả chạy 3 mốc evaluation | Báo cáo tiến độ & đo lường tác động qua 7 CP | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| **Fix KeyError in QA** | Module Retrieval (`src/retrieval/qa.py`) | Thêm xử lý `metadata.get()` chống sập ứng dụng khi gặp dữ liệu bị rác/thiếu thông tin trong phase Corrupted. |
| **Git Resolve Conflict** | Toàn nhóm (Main branch) | Xử lý xung đột nhị phân ChromaDB và file JSON kết quả, đẩy sạch sẽ toàn bộ code & metrics lên branch `main`. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Sinh bộ câu hỏi kiểm thử chuẩn | `src/evaluation/testset.py` | 72 Q&A pairs thuộc 4 nhóm (`summary`, `authors`, `date`, `categories`) | View file `data/eval/test_set.json` |
| Đánh giá Baseline Phase 1 | `src/evaluation/metrics.py` | `baseline_metrics.json` (Hit Rate: 1.0, Token F1: 0.7569) | `uv run python script/run_phase1.py` |
| Đánh giá Corrupted Phase 2 | `src/evaluation/metrics.py` | `corrupted_metrics.json` (Hit Rate: 0.9167, Token F1: 0.6603) | `uv run python script/run_corruption_flow.py` |
| Đánh giá Repaired Phase 3 | `src/evaluation/metrics.py` | `repaired_metrics.json` (Hit Rate: 1.0, Token F1: 0.7569) | View file `data/reports/corruption_report.md` |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng một bộ đánh giá tự động (Automated Evaluation Suite) có khả năng định lượng chính xác chất lượng truy xuất (Retrieval Accuracy) và chất lượng sinh câu trả lời (Answer Quality) của RAG Agent khi làm việc với 3 trạng thái dữ liệu: Sạch (Baseline) $\rightarrow$ Hỏng (Corrupted) $\rightarrow$ Khôi phục (Repaired).

### Cách triển khai
1. **Thiết kế Test Set đa dạng 4 nhóm (`testset.py`):**
   - Đọc 24 bài báo từ `papers_clean.csv`, lọc bỏ các giá trị `nan`/rỗng.
   - Tự động sinh 72 câu hỏi (3 câu/bài báo) với 4 dạng: `summary` (tóm tắt nội dung), `authors` (tác giả), `date` (ngày xuất bản), `categories` (chuyên mục).
   - Gán cứng `ground_truth_doc_ids` bằng DOI duy nhất để đánh giá Hit Rate khách quan.

2. **Thuật toán đánh giá Metrics (`metrics.py` & `qa.py`):**
   - **Retrieval Hit Rate:** Kiểm tra DOI của tài liệu gốc (`ground_truth_doc_ids`) có nằm trong Top-$K$ tài liệu RAG Agent tìm thấy hay không.
   - **Token F1 Score:** Tính độ trùng khớp từ vựng (Unigram Token F1) giữa câu trả lời trích xuất của Agent và `ground_truth`.
   - **Heuristic LLM Judge Fallback:** Khi không có API Key, sử dụng Heuristic Judge tự động dựa trên Token F1 ($\ge 0.50 \rightarrow 3/5$ điểm, $\ge 0.70 \rightarrow 5/5$ điểm) để tránh gián đoạn pipeline.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | `data/clean/papers_clean.csv` (24 bài báo) & Vector Index (`ChromaDB`) |
| **Output** | `data/eval/test_set.json` (72 Q&A) & `data/results/*_metrics.json` |
| **Module phụ thuộc** | `src/ingestion/cleaning.py` (Cleaning Owner) & `src/retrieval/index.py` (RAG Owner) |
| **Module sử dụng output** | `src/observability/reporting.py` (Observability Owner) |
| **Điều kiện lỗi cần xử lý** | Trường metadata trong Vector Store bị `None`/rỗng khi dữ liệu bị Corrupt. Xử lý bằng `metadata.get(key, "")`. |

### Cách xác minh

```bash
.\.venv\Scripts\python.exe script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Tự động sinh ra 3 bộ kết quả metrics cho Baseline, Corrupted, Repaired và file so sánh `corruption_report.md`.
- **Kết quả thực tế:** Hit Rate chạy thành công: Baseline (100%) $\rightarrow$ Corrupted (91.67%) $\rightarrow$ Repaired (100%).
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi đánh giá câu trả lời dạng tác giả, ngày xuất bản hoặc chuyên mục, hàm `_extract_answer()` mặc định chỉ lấy câu đầu tiên của đoạn summary, làm cho Token F1 ở các câu hỏi thông tin ngắn bị thấp bất hợp lý (~0.42).
- **Các phương án đã cân nhắc:**
  1. *Phương án A:* Giữ nguyên logic cũ chỉ lấy `first_sentence(summary)` cho mọi dạng câu hỏi.
  2. *Phương án B (Đã chọn):* Mở rộng điều kiện khớp ngữ nghĩa trong `_extract_answer()` để trích xuất trực tiếp các trường metadata tương ứng (`authors_joined`, `published`, `categories_joined`).
- **Lý do chọn:** Phương án B phản ánh đúng khả năng trích xuất thông tin thực tế của RAG Agent, đưa Token F1 của Baseline từ 0.4236 lên mức 0.7569 (75.69%), giúp phát hiện sự sụt giảm F1 khi dữ liệu bị rác rõ ràng hơn.
- **Bằng chứng:** Token F1 baseline tăng từ 42.36% lên 75.69%, và khi bị cấy rác F1 giảm xuống 66.03% (đo được mức sụt giảm 9.66%).

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  File "D:\...\src\retrieval\qa.py", line 29, in _extract_answer
      return first_sentence(metadata["summary"])
                            ~~~~~~~~^^^^^^^^^^^
  KeyError: 'summary'
  ```
- **Lệnh hoặc bước tái hiện:** `.\.venv\Scripts\python.exe script/run_corruption_flow.py` (ở bước đánh giá Corrupted Data).
- **Nguyên nhân gốc:** Bước Data Corruption đã chủ đích xóa trắng trường `summary` (hoặc đặt giá trị rỗng) của một số bài báo. Hàm `_extract_answer` truy cập trực tiếp `metadata["summary"]` theo kiểu dictionary key nên bị ném ngoại lệ `KeyError`.
- **Cách xử lý:** Thay đổi truy cập key trực tiếp thành `str((metadata or {}).get("summary", ""))` có fallback an toàn.
- **Cách xác minh sau khi sửa:** Chạy lại `run_corruption_flow.py`, pipeline thực thi mượt mà qua 72 câu hỏi dữ liệu hỏng mà không gặp crash.
- **Bài học kỹ thuật:** Luôn thiết kế code xử lý dữ liệu với tư tưởng "Defensive Programming" khi làm việc với hệ thống RAG và Data Observability.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến Vector Index:**
   Crossref API trả về JSON thô $\rightarrow$ `cleaning.py` bóc tách HTML, làm sạch text và tính `age_days` $\rightarrow$ `index.py` tạo vector embeddings (`MiniLM`) và nạp vào ChromaDB persistent storage (`chroma.sqlite3`).
2. **Role của Evaluation set & Ground-truth document IDs:**
   Test set chứa 72 câu hỏi đi kèm `ground_truth_doc_ids` (DOI chuẩn). RAG Agent thực hiện Semantic Search lấy Top-$K$ tài liệu; nếu DOI chuẩn xuất hiện trong Top-$K$, `retrieval_hit` = True.
3. **Quality checks vs Freshness monitoring:**
   - *Quality checks:* Kiểm tra tính toàn vẹn cấu trúc dữ liệu tại chỗ (dữ liệu rỗng, trùng lặp ID, thiếu trường).
   - *Freshness monitoring:* Theo dõi thời gian biến động của dữ liệu theo chu kỳ thời gian (ví dụ: phát hiện bài báo quá 180 ngày chưa cập nhật).
4. **Vì sao dùng chung 1 test set cho cả 3 mốc?**
   Đảm bảo nguyên tắc "Cố định biến phụ thuộc" (Controlled Experiment). Việc giữ nguyên 72 câu hỏi giúp các chỉ số so sánh (Hit Rate, F1) giữa Baseline, Corrupted và Repaired mang tính khoa học và minh bạch 100%.
5. **Dấu hiệu chứng minh Repair thành công:**
   Khi `retrieval_hit_rate` phục hồi từ 91.67% quay lại 100%, `mean_token_f1` quay lại 75.69%, và `Quality Pass` chuyển từ `False` về `True`.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | ---: | ---: | ---: | :--- |
| **`retrieval_hit_rate`** | **1.0 (100%)** | **0.9167 (91.67%)** | **1.0 (100%)** | Dữ liệu lỗi xóa bài mới nhất làm Hit Rate giảm 8.33%. Sửa xong phục hồi 100%. |
| **`mean_token_f1`** | **0.7569 (75.69%)** | **0.6603 (66.03%)** | **0.7569 (75.69%)** | Dữ liệu rác/bị xóa làm suy giảm 9.66% độ trùng khớp ngữ nghĩa. Sửa xong phục hồi 100%. |
| **`judge_accuracy`** | **0.6667 (66.67%)** | **0.6250 (62.50%)** | **0.6806 (68.06%)** | Độ chính xác của Heuristic Judge sụt giảm khi dữ liệu hỏng. |
| **`mean_judge_score`** | **3.958 / 5.0** | **3.778 / 5.0** | **3.958 / 5.0** | Điểm đánh giá trung bình giảm 0.18 điểm khi bị cấy rác. |
| **Quality checks** | **Pass (True)** | **Fail (False)** | **Pass (True)** | Nhận diện chính xác 2 dòng trùng lặp và 2 summary rỗng ở phase Corrupted. |
| **Freshness status** | **False (1 stale)** | **False (3 stale)** | **False (1 stale)** | Phát hiện thêm 2 bài báo bị đẩy lùi ngày xuất bản 10 năm ở phase Corrupted. |

### Kết luận từ số liệu

1. **[Data corruption] $\rightarrow$ [Quality check Fail & 3 Stale Rows] $\rightarrow$ [Retrieval Hit Rate giảm 8.33%, Token F1 giảm 9.66%].**
2. **[Repair action từ Raw Source] $\rightarrow$ [Quality check Pass & Stale Rows giảm về 1] $\rightarrow$ [Retrieval Hit Rate phục hồi 100%, Token F1 phục hồi 75.69%].**

- **Corruption ảnh hưởng rõ nhất:** Kịch bản `latest_drop` (xóa bài báo mới) vì trực tiếp khiến Vector Store không thể tìm thấy tài liệu gốc, dẫn đến thất bại truy xuất hoàn toàn (Hit Rate = 0 cho các câu hỏi đó).
- **Kết quả ngoài kỳ vọng:** Việc tối ưu hàm trích xuất câu trả lời trong `qa.py` giúp tăng vọt độ nhạy của chỉ số Token F1, phản ánh sự biến động chất lượng dữ liệu rõ nét hơn nhiều so với việc chỉ lấy câu tóm tắt mặc định.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Về Data Pipeline:** Thấy rõ tầm quan trọng của việc duy trì Snapshot Nguồn Thô (Single Source of Truth) để phục vụ cho việc khôi phục dữ liệu (Data Recovery) khi gặp sự cố.
2. **Về Data Quality & Observability:** Data Observability không chỉ dừng ở việc "báo lỗi" mà phải là kim chỉ nam để giải thích lý do vì sao mô hình AI/RAG lại hoạt động kém.
3. **Về ảnh hưởng của Data đến RAG Agent:** "Garbage in, Garbage out" — Dữ liệu chỉ cần rác 10% đã làm suy giảm đáng kể độ tin cậy và chính xác của AI Agent.

### Nếu có thêm thời gian
Tích hợp LLM Judge thực sự (sử dụng GPT-4o hoặc Claude 3.5 API) thay cho Heuristic Fallback Judge để đánh giá thêm độ tiệm cận về mặt lập luận (Faithfulness & Answer Relevance).

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lê Nguyễn Minh Đức  
**Ngày xác nhận:** 2026-08-06
