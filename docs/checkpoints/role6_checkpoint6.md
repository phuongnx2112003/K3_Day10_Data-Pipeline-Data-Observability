# Checkpoint 6 — Vai trò 6: Observability

## 1. Mục tiêu checkpoint

Vai trò 6 tạo comparison report từ các artifact metrics, quality và freshness thật
của ba trạng thái:

1. `baseline`: dữ liệu sạch ban đầu;
2. `corrupted`: dữ liệu sau khi cố ý làm hỏng;
3. `repaired`: dữ liệu được dựng lại từ nguồn.

Checkpoint này không thực hiện repair hoặc chạy lại RAG. Vai trò 6 chỉ đo, đối chiếu
artifact đã được các flow trước bàn giao và kết luận trong giới hạn bằng chứng.

## 2. Phần đã triển khai

Runner CP6:

- `src/observability/repaired.py`.

Runner thực hiện:

- kiểm tra đủ repaired dataset, metrics, answers và embedding manifest;
- chạy lại quality/freshness trên repaired dataset;
- audit repaired embedding manifest với collection `papers-repaired`;
- đóng băng repaired observability snapshot;
- so sánh signal và metric giữa baseline–corrupted–repaired;
- xác định signal/metric nào đã hồi phục hoặc còn dưới baseline;
- sinh JSON evidence và Markdown comparison report.

Cách chạy lại:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m observability.repaired
```

Kết quả chạy hiện tại:

- observability status: `complete`;
- recovery status: `partial`;
- repaired metrics samples: 72;
- repaired answers: 72;
- samples và answers khớp nhau.

## 3. Artifact CP6

| Artifact | Chức năng |
| --- | --- |
| `data/quality/repaired_quality.json` | Quality report của repaired dataset |
| `data/quality/repaired_freshness.json` | Freshness report dùng timestamp nguồn `published` |
| `data/quality/repaired_embedding_audit.json` | Audit collection, document count, metadata và persist path |
| `data/quality/repaired_observability_snapshot.json` | Snapshot signal/metric repaired |
| `data/quality/recovery_comparison.json` | Bằng chứng so sánh có cấu trúc cho ba trạng thái |
| `data/quality/repaired_observability_readiness.json` | Kiểm tra input và tính nhất quán metrics/answers |
| `data/reports/corruption_report.md` | Báo cáo comparison để đọc và trình bày |

## 4. So sánh quality và freshness

| Signal | Baseline | Corrupted | Repaired | Kết luận |
| --- | ---: | ---: | ---: | --- |
| Row count | 24 | 24 | 24 | Không đổi cả ba trạng thái |
| Null paper ID rows | 0 | 0 | 0 | Không đổi |
| Duplicate paper ID rows | 0 | 4 | 0 | Đã về baseline |
| Missing title rows | 0 | 0 | 0 | Không đổi |
| Invalid summary rows | 0 | 2 | 0 | Đã về baseline |
| Invalid age rows | 0 | 0 | 0 | Không đổi |
| Stale rows | 1 | 3 | 1 | Đã về baseline |
| Stale ratio | 0.0417 | 0.1250 | 0.0417 | Đã về baseline |

Structural quality chuyển `PASS → FAIL → PASS`. Quality/freshness signals do
corruption gây ra đã được sửa về đúng baseline.

Freshness status vẫn là `FAIL` ở repaired vì baseline vốn đã có một record lớn hơn
ngưỡng 180 ngày. Đây không phải lỗi còn sót lại do corruption: stale rows đã giảm từ
3 về 1, đúng bằng baseline. Tuy nhiên cũng không được nói repaired dataset “hoàn toàn
fresh”.

## 5. So sánh evaluation metrics

| Metric | Baseline | Corrupted | Repaired | Repaired − baseline | Kết luận |
| --- | ---: | ---: | ---: | ---: | --- |
| Retrieval hit rate | 1.0000 | 0.9167 | 1.0000 | 0.0000 | Đã về baseline |
| Mean token F1 | 0.4236 | 0.6603 | 0.4236 | 0.0000 | Đã về baseline |
| Judge accuracy | 0.3333 | 0.6250 | 0.3472 | +0.0139 | Cao hơn baseline |
| Mean judge score | 2.6250 | 3.7778 | 2.3611 | -0.2639 | Còn dưới baseline |

Không được nói mọi metric xấu đi khi corruption xảy ra: Token F1 và judge metrics
của corrupted run thực tế cao hơn baseline. Sau repair, retrieval và Token F1 khớp
baseline, judge accuracy cao hơn baseline, nhưng mean judge score vẫn thấp hơn
baseline khoảng 0.264 điểm.

## 6. Vì sao recovery là `partial`?

Quality và freshness signals đã hồi phục về baseline, nhưng toàn bộ hệ thống chưa đủ
bằng chứng để ghi `complete` vì:

- `mean_judge_score` repaired còn thấp hơn baseline;
- repaired embedding audit còn fail `persist_path_matches_config` do manifest đang
  lưu đường dẫn workspace cũ;
- Ragas đang được skip, nên không có Ragas evidence để kết luận;
- freshness repaired vẫn fail theo ngưỡng 180 ngày, dù đây cũng là trạng thái baseline.

`judge_accuracy` cao hơn baseline là tín hiệu tốt, nhưng không thể dùng một metric này
để che đi metric/audit còn chưa đạt.

## 7. Giới hạn của kết luận

- Report chỉ phản ánh artifact hiện có, không chứng minh quan hệ nhân quả riêng cho
  từng corruption event.
- Judge metrics có thể biến động theo lần chạy model; muốn kết luận ổn định cần chạy
  lặp lại với cùng cấu hình và kiểm soát randomness.
- Ragas chưa chạy nên report không đưa ra kết luận Ragas.
- Persist path sai là vấn đề portability của embedding manifest; cần người phụ trách
  RAG/index rebuild manifest trên workspace hiện tại để audit chuyển PASS.

## 8. Trạng thái Checkpoint 6 — Vai trò 6

- [x] Chạy quality/freshness cho repaired dataset.
- [x] Audit repaired embedding manifest.
- [x] Tạo repaired observability snapshot.
- [x] So sánh baseline–corrupted–repaired bằng dữ liệu thật.
- [x] Sinh structured comparison JSON và Markdown report.
- [x] Ghi rõ recovery chưa hoàn toàn.
- [x] Nêu các signal hồi phục, signal chưa đạt và giới hạn kết luận.
- [x] Kiểm tra 72 metric samples khớp 72 repaired answers.
- [x] Viết tài liệu CP6 ghi rõ Vai trò 6.
