# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Đào Nam Hải             |
| MSSV               | 2A202601037                     |
| Khóa/Lớp         | K3              |
| Tên nhóm         | 2k345     |
| Vai trò chính    | Vai trò 4 (RAG & Agent Owner)                 |
| Repository         | https://github.com/phuongnx2112003/K3_Day10_Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Xây dựng Vector DB (ChromaDB)      | `src/retrieval/index.py`           | `papers_clean.json` (3 trạng thái: Baseline, Corrupted, Repaired)          | `data/chroma/`, `papers_embeddings.json` | Hoàn thành |
| Tích hợp LangChain Agent & RAG Tools      | `src/retrieval/agent.py`           | User Query từ giao diện          | LLM Response kèm Context truy xuất | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Phát triển Web UI Dashboard (React + Vite) tích hợp toàn diện | Toàn bộ Team (Role 1, 5, 6) | Xây dựng 6 Tabs giao diện cực đẹp (Dark Cyber) kèm State Switcher, giúp demo trực quan sự thay đổi qua 3 giai đoạn của data pipeline. |
| Xử lý Parsing API Backend | File `web_server.py` | Sửa lỗi 404 cho API `/api/papers` và hỗ trợ param `?state=...` cho các components khác. |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Khởi tạo Embeddings & Index 3 mức dữ liệu | `src/retrieval/index.py` | Tạo ra 3 bộ dữ liệu vector tương ứng (Baseline, Corrupted, Repaired) | Kiểm tra `data/chroma` và `data/embeddings/` |
| Xây dựng RAG Agent | `src/retrieval/agent.py` | Agent xử lý ngôn ngữ tự nhiên sử dụng Semantic Search tool để truy vấn bài báo | Mở UI (localhost:5173), chat với Bot. |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Thư mục `data/chroma/` chứa 3 collection độc lập (`papers-baseline`, `papers-corrupted`, `papers-repaired`), mỗi collection nhúng (embed) chuẩn xác 24 records thông qua mô hình `all-MiniLM-L6-v2`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Hệ thống RAG cần một "bộ não" lưu trữ thông tin (Vector DB) để trích xuất ngữ cảnh. Nhiệm vụ của tôi là biến những bài báo thô (văn bản) từ Role 3 thành dạng số (vector), lưu trữ tối ưu, và cung cấp các "công cụ" (Tools) để LangChain Agent (LLM) có thể tự động gọi hàm tìm kiếm khi người dùng đặt câu hỏi.

### Cách triển khai

- **Embeddings:** Sử dụng model Sentence Transformer `all-MiniLM-L6-v2` để mã hóa trường `text_for_embedding` (đã được nối từ Title, Authors, Categories, Summary) thành không gian vector 384 chiều.
- **Index:** Lưu vào ChromaDB qua `PersistentClient`, mỗi trạng thái data pipeline tương ứng với một collection riêng biệt để dễ dàng đối chiếu.
- **Agent Tools:** Tạo 2 tools cho LangChain:
  1. `semantic_search_papers`: Tính Cosine Similarity giữa Vector câu hỏi và Vector bài báo để lấy top K.
  2. `lookup_paper`: Tìm kiếm trực tiếp bài báo dựa trên tên/ID (sau đó update thành Partial Match để tăng tỷ lệ hit).

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | JSON records (`papers_clean.json`), Câu hỏi từ UI           |
| Output                         | Danh sách bài báo (Search Results), Câu trả lời từ LLM |
| Module phụ thuộc             | `cleaning.py` (Nhận data sạch từ Role 3)                    |
| Module sử dụng output        | `web_server.py` (API trả kết quả ra Frontend), Role 5 (Evaluation) |
| Điều kiện lỗi cần xử lý | Lỗi LangChain Agent trả về dạng `List[dict]` thay vì string khi sinh text. |

### Cách xác minh

```bash
python -m pytest tests/test_retrieval_agent.py
# Hoặc chạy thử truy vấn thông qua Web UI Chat
```

- **Kết quả mong đợi:** Agent nhận câu hỏi, tự động trigger Tool search ChromaDB, lấy context và sinh ra câu trả lời văn bản sạch.
- **Kết quả thực tế:** 100% khớp quy trình ở mức Baseline và Repaired. Ở mức Corrupted, Agent không tìm thấy context (phản ánh đúng bản chất dữ liệu bị hỏng).
- **Artifact/log:** `data/chroma/`, `data/results/baseline_answers.json`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi người dùng hỏi cụ thể *"What does the paper SafeRAG talk about?"*, hàm tìm kiếm `lookup_paper` cũ dùng Exact Match (Khớp 100%).
- **Các phương án đã cân nhắc:**
  1. Yêu cầu LLM tạo lệnh Semantic Search vector thông thường.
  2. Bắt LLM truyền vào chính xác 100% title bài báo.
  3. Sửa hàm `lookup_paper` thành Partial Match (Tìm kiếm chuỗi con).
- **Phương án đã chọn:** Phương án 3 (Sửa hàm `lookup_paper` trong `index.py`).
- **Lý do:** LLM hiếm khi trích xuất được tiêu đề dài chính xác 100% (ví dụ: *SafeRAG: A Large-Language-Model-Based Multistage...*). Nếu dùng Exact Match, tool sẽ luôn trả về lỗi "không tìm thấy", làm luồng RAG bị crash logic. Dùng Substring match (chỉ cần chứa chữ "SafeRAG") giúp tăng độ linh hoạt, giảm thiểu False Negative mà không tốn kém tài nguyên tính vector.
- **Bằng chứng quyết định phù hợp:** Thử nghiệm trên UI sau khi sửa logic, Agent đã lập tức gọi đúng bài báo SafeRAG.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Trên giao diện Chatbot, thay vì hiển thị chữ bình thường, hệ thống văng ra chuỗi JSON thô: `[{'type': 'text', 'text': 'I couldn\'t find an exact match...'}]`.
- **Lệnh hoặc bước tái hiện:** Chat câu hỏi trên UI (tab AI Assistant) khi data đang ở mức Corrupted.
- **Nguyên nhân gốc:** Class LangChain (cụ thể là các BaseChatModel) thi thoảng trả về list of dicts thay vì một string nguyên bản, đặc biệt khi model trả về cấu trúc nội bộ hoặc đang bối rối vì không tìm thấy dữ liệu (ở mức Corrupted). Code backend Python bắt kết quả này đem ép kiểu `str(answer)` khiến dấu ngoặc bị biến thành chuỗi luôn (string literal).
- **Cách xử lý:** Cập nhật hàm `run_agent_question` trong `src/retrieval/agent.py`. Viết logic check: nếu `isinstance(content, list)`, duyệt qua list, kiểm tra type dict, và extract key `"text"`. Sau đó `"\n".join(texts)`.
- **Cách xác minh sau khi sửa:** Chat lại câu hỏi trên UI, kết quả hiển thị lại thành đoạn văn bản thuần tự nhiên.
- **Điều học được:** Không được tin tưởng LLM/LangChain luôn trả về String. Phải luôn xây dựng Parsing layer chặt chẽ trước khi đẩy data ra API.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
   Crossref trả về Raw JSON qua API (Role 2). Role 3 chạy clean, loại bỏ null/html, ghép nối các trường Title, Authors, Summary thành một trường duy nhất `text_for_embedding`. Dữ liệu này được Role 4 dùng Sentence Transformers (MiniLM) để biến thành ma trận Vector, lưu vào database ChromaDB (Vector Index).
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
   Evaluation set cung cấp bộ câu hỏi chuẩn và ID bài báo (ground-truth). Khi RAG hoạt động, nếu ID bài báo mà ChromaDB trả về nằm trong danh sách ground-truth thì Hit Rate tăng. LLM Answer sinh ra được đối chiếu với Reference Answer bằng Ragas để đo F1 và Accuracy.
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
   Quality Checks bằng Great Expectations thiên về hình thái và độ đầy đủ (Null values, độ dài, schema regex). Freshness thiên về tính thời gian (bài báo có bị quá đát so với threshold 180 ngày hay không).
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
   Để đảm bảo tính đối chứng khoa học (A/B Testing). Nếu đổi câu hỏi, ta không thể biết sự sụt giảm metric (F1/Hit Rate) là do chất lượng dữ liệu hỏng hay do câu hỏi mới khó hơn.
5. Repair được xem là thành công dựa trên artifact và metric nào?
   Dựa trên file `papers_clean_repaired.json` được sinh ra, các Quality report trả về 100% Passed, và quan trọng nhất là sự phục hồi của các metric RAG (hit_rate trở về 1.0, F1 phục hồi lại mức baseline).

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      1.0 |       0.916 |      1.0 | Việc dữ liệu hỏng (mất title/summary) làm vector nhiễu, RAG tìm sai bài báo. |
| `mean_token_f1`      |      0.756 |       0.660 |      0.756 | Context sai dẫn đến câu trả lời sinh ra bị lệch chuẩn. |
| `judge_accuracy`     |      0.680 |       0.625 |      0.666 | LLM Judge đánh giá thấp đi rõ rệt. |
| `mean_judge_score`   |      3.958 |       3.777 |      3.958 | Điểm số tuyệt đối bị hạ từ ~4 xuống 3.7 do thiếu dữ kiện. |
| Quality checks         |      100% Pass |       Failed |      100% Pass | Cảnh báo đỏ chính xác ở bước Corrupted (Role 6 làm tốt). |
| Freshness status       |      Valid |       Valid/Invalid |      Valid | Trạng thái date được phục hồi. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. **[Data corruption (mất Title/Summary)]** → **[quality signal fail, nhiều Nulls]** → **[agent metric `retrieval_hit_rate` sụt giảm (0.91)]**.
2. **[Repair action (fill back dữ liệu)]** → **[quality signal 100% Passed]** → **[agent metric `hit_rate` phục hồi về 1.0]**.

Corruption nào ảnh hưởng rõ nhất và vì sao?
Việc làm mất (Null) `title` và `summary` là chí mạng nhất đối với Role 4 (RAG). Vì trường `text_for_embedding` hoàn toàn phụ thuộc vào 2 nội dung này. Khi chúng bị Null, Vector sinh ra là vô nghĩa, dẫn đến `retrieval_hit_rate` giảm, và LLM không có thông tin để trả lời câu hỏi.

Kết quả nào khác với kỳ vọng ban đầu?
LLM `judge_accuracy` ở mức Repaired (0.666) không phục hồi tuyệt đối 100% về mức Baseline (0.680), dù `retrieval_hit_rate` và `token_f1` đã y hệt. Lý do có thể là do bản chất tính ngẫu nhiên (temperature) của LLM-as-a-Judge khi đánh giá lại, hoặc cấu trúc dữ liệu Repaired có format khoảng trắng/xuống dòng hơi khác một chút so với dữ liệu gốc.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Garbage In, Garbage Out**: Data Pipeline không chỉ là vận chuyển dữ liệu, nó là huyết mạch. Data kỹ thuật (ETL) rác sẽ kéo theo toàn bộ AI Downstream (RAG, LLM) biến thành "đứa trẻ mù".
2. **LangChain & LLM Tools**: Việc thiết kế Tool (Ví dụ Exact Lookup) cho LLM cần sự linh hoạt (như Partial matching). LLM không phải một cỗ máy code chính xác tuyệt đối.
3. **Giá trị của Data Observability**: Không có Data Observability (Quality/Freshness Checks), ta sẽ lầm tưởng RAG hoạt động kém do model AI kém, trong khi thực chất nguyên nhân cốt lõi là do Data hỏng ngay từ đầu nguồn.

### Nếu có thêm thời gian

Nếu có thêm thời gian, tôi sẽ triển khai Hybrid Search (kết hợp BM25 Keyword Search + Vector Semantic Search) cho Retrieval, và tích hợp Reranker. Cách đo lường là tính lại `retrieval_hit_rate` và `MRR` trên tập Test, tôi tin hit rate của hệ thống sẽ chống chịu tốt hơn nữa ngay cả khi data bị Corrupt một phần.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Đào Nam Hải

**Ngày xác nhận:** 2026-08-06
