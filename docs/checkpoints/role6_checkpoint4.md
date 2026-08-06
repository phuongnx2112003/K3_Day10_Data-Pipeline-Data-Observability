# Checkpoint 4 — Vai trò 6: Observability

## 1. Mục tiêu checkpoint

Checkpoint 4 là mốc nghỉ và chuẩn bị cho corruption flow. Vai trò 6 chưa chạy
corruption tại mốc này; nhiệm vụ là dự báo trước quality/freshness signals để
sau CP5 có thể so sánh dự báo với quan sát thật.

Artifact dự báo:

- `data/quality/cp4_corruption_signal_forecast.json`

## 2. Baseline dùng làm mốc

Nguồn: `data/quality/baseline_observability_snapshot.json`.

| Signal/metric | Baseline |
| --- | ---: |
| Row count | 24 |
| Duplicate paper ID rows | 0 |
| Invalid summary rows | 0 |
| Invalid age rows | 0 |
| Stale rows | 1 |
| Stale ratio | 0.0417 |
| Latest published | 2026-08-05 |
| Oldest published | 2026-01-25 |
| Retrieval hit rate | 1.0000 |
| Mean token F1 | 0.4236 |
| Judge accuracy | 0.3333 |
| Mean judge score | 2.6250 |

## 3. Corruption contract đã đọc

Nguồn: `src/ingestion/corruption.py`.

Với 24 baseline rows, hàm deterministic dự kiến:

1. Xóa 2 paper mới nhất.
2. Dataset còn 22 rows.
3. Chọn 2 rows cho mỗi scenario.
4. Blank 2 summaries.
5. Thêm noise vào 2 summaries.
6. Cắt ngắn 2 titles.
7. Làm 2 publication dates cũ đi 10 năm.
8. Thêm 2 duplicate rows.
9. Row count cuối trở lại 24.

Hai paper dự kiến bị xóa:

- `10.2118/234689-pa`, published `2026-08-05`.
- `10.63646/kpqm1958`, published `2026-07-17`.

Chúng tương ứng với 6/72 evaluation questions.

## 4. Dự báo quality/freshness signals

| Signal | Baseline | Dự báo corrupted | Thay đổi |
| --- | ---: | ---: | --- |
| Row count | 24 | 24 | Không đổi |
| Null paper IDs | 0 | 0 | Không đổi |
| Duplicate paper ID rows | 0 | 4 | Tăng |
| Missing titles | 0 | 0 | Không đổi |
| Invalid summaries | 0 | 4 | Tăng |
| Invalid age values | 0 | 0 | Không đổi |
| Stale rows | 1 | 3 | Tăng |
| Stale ratio | 0.0417 | 0.1250 | Tăng |
| Latest published | 2026-08-05 | 2026-07-13 | Cũ hơn |
| Oldest published | 2026-01-25 | 2016-06-17 | Cũ hơn khoảng 10 năm |
| Structural quality | PASS | FAIL | Xấu đi |
| Freshness status | FAIL | FAIL | Status không đổi, count xấu hơn |

### Vì sao duplicate rows dự báo là 4?

Corruption thêm hai bản sao của hai rows đầu. Với cách đếm
`duplicated(keep=False)`, cả hai bản gốc và hai bản sao đều được đánh dấu, nên
số duplicate rows là 4.

### Vì sao invalid summaries dự báo là 4?

Hai rows đầu bị blank summary. Cuối flow chính hai rows này được duplicate, nên
corrupted dataset dự kiến có bốn rows summary dưới ngưỡng.

## 5. Dự báo RAG metrics

Đây chỉ là giả thuyết trước CP5, không phải kết quả đo:

- `retrieval_hit_rate` có upper bound khoảng `66/72 = 0.9167` vì sáu câu hỏi
  tham chiếu hai documents bị xóa. Các corruption khác có thể làm thấp hơn.
- `mean_token_f1` dự kiến giảm do blank summaries và metadata bị đổi.
- `judge_accuracy` và `mean_judge_score` dự kiến không tăng, nhưng phải chờ
  answers/metrics thật mới được kết luận.

Không ghi các giá trị dự báo vào corrupted metrics artifact.

## 6. Observability gaps phát hiện trước CP5

### Row count có thể không phát hiện lỗi

Hai rows bị xóa và hai rows được thêm lại dưới dạng duplicate nên tổng row count
vẫn là 24. Vì vậy phải xem đồng thời duplicate count và corruption log.

### Summary noise chưa có direct check

Noise marker không làm summary rỗng hoặc ngắn. Quality check hiện tại không
phát hiện trực tiếp `CORRUPTED_NOISE`.

### Truncated title chưa có direct check

Title bị cắt còn 12 ký tự nhưng không blank, nên `title_not_blank` vẫn pass.
Tác động chỉ có thể xuất hiện qua retrieval/answer metrics hoặc check độ dài bổ
sung ở checkpoint sau nếu nhóm thống nhất.

### Freshness status một mình không đủ

Baseline đã có `is_fresh=false` vì một stale row. Corrupted cũng dự kiến false,
vì vậy phải so sánh `stale_rows`, `stale_ratio`, latest và oldest timestamp để
thấy mức độ xấu đi.

## 7. Cách xác minh ở CP5

Sau khi corruption flow chạy, đối chiếu forecast với:

- `data/results/corruption_log.json`;
- corrupted quality JSON;
- corrupted freshness JSON;
- `data/results/corrupted_answers.json`;
- `data/results/corrupted_metrics.json`.

Chỉ thay chữ “dự báo” bằng “quan sát” khi các artifact trên tồn tại và khớp
nhau.

## 8. Trạng thái Checkpoint 4 — Vai trò 6

- [x] Đã nghỉ/chuyển mốc sau baseline.
- [x] Đã khóa baseline signals/metrics làm mốc.
- [x] Đã đọc corruption contract hiện tại.
- [x] Đã dự báo từng quality/freshness signal.
- [x] Đã chỉ ra row count có thể không đổi dù dữ liệu bị lỗi.
- [x] Đã chỉ ra gaps cho summary noise và truncated title.
- [x] Đã ghi forecast artifact để đối chiếu tại CP5.
- [ ] Chưa chạy corruption flow tại CP4.

