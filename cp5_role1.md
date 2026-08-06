# CP5 - Role 1: Integrator & Release Owner

> Báo cáo checkpoint 5 cho vai trò 1 của nhóm 6 người.
> Mốc này hoàn thiện corruption flow có kiểm soát, đo impact lên retrieval/evaluation, rồi repair lại từ raw source để so sánh ba trạng thái: baseline, corrupted và repaired.

## 1. Mục tiêu của CP5

Checkpoint 5 yêu cầu role 1 không chỉ chạy được pipeline, mà phải:

- tạo corruption có chủ đích trên clean baseline,
- rebuild index và evaluate lại trên cùng test set,
- chạy quality/freshness cho corrupted dataset,
- repair lại từ raw source thay vì sửa tay output,
- so sánh baseline / corrupted / repaired bằng artifact thật.

## 2. Trả lời ngắn gọn: CP5 có cần output của role nào không?

Có.

Role 1 ở CP5 cần dùng output đã ổn định từ các role khác:

- Role 2: clean dataset và `text_for_embedding`
- Role 3: `test_set.json`
- Role 4: embedding/index contract và retrieval smoke-test
- Role 5: quality/freshness report format

Ngoài ra, để repair đúng chuẩn, role 1 còn cần raw snapshot đã lưu từ phase trước.

Nói cách khác:

- **Corruption** dựa trên clean output của role 2
- **Evaluation** dựa trên test set của role 3
- **Index/retrieval** dựa trên contract của role 4
- **Quality/report** dựa trên output/report format của role 5
- **Repair** quay về raw/source snapshot, không chỉnh tay corrupted JSON

## 3. Vai trò của role 1 trong CP5

Role 1 chịu trách nhiệm integrator và release owner, nên phần mình làm là:

- ghép `corrupt -> rebuild -> evaluate -> quality/freshness -> repair -> compare`,
- giữ baseline không bị ghi đè,
- tách riêng corrupted và repaired collection/path,
- ghi corruption log có thể audit,
- xuất comparison report có số liệu thật.

## 4. Các file đã hoàn thiện

- `src/pipelines/corruption_flow.py`
- `src/observability/reporting.py`
- `cp5_role1.md`

## 5. Cách flow chạy

Flow hiện tại làm theo đúng thứ tự:

1. Đọc baseline clean dataset.
2. Tạo corrupted dataframe bằng `corrupt_clean_dataframe`.
3. Ghi corrupted clean CSV/JSON và corruption log.
4. Build lại index corrupted riêng.
5. Evaluate corrupted trên test set cũ.
6. Chạy quality checks và freshness report cho corrupted.
7. Load raw snapshot và repair lại từ raw.
8. Build repaired index riêng.
9. Evaluate repaired trên cùng test set.
10. Chạy quality/freshness cho repaired.
11. Sinh report so sánh baseline / corrupted / repaired.

## 6. Evidence thực tế sau khi chạy

Lệnh đã chạy:

```bash
PYTHONPATH=src ./venv/bin/python script/run_corruption_flow.py
```

Kết quả chính:

- Baseline rows: `24`
- Corrupted rows: `24`
- Repaired rows: `24`

### 6.1 Metrics

| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| Retrieval hit rate | `1.0` | `0.9166666666666666` | `1.0` |
| Mean token F1 | `0.4235907473399701` | `0.35469735430082544` | `0.4235907473399701` |
| Judge accuracy | `0.3333333333333333` | `0.2916666666666667` | `0.3472222222222222` |
| Mean judge score | `2.625` | `2.138888888888889` | `2.361111111111111` |

### 6.2 Quality / freshness

| Signal | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| Overall pass | `True` | `False` | `True` |
| Duplicate `paper_id` | `0` | `2` | `0` |
| Blank summary | `0` | `2` | `0` |
| Blank `text_for_embedding` | `0` | `0` | `0` |
| Stale rows | `1` | `3` | `1` |

Freshness:

- Baseline `is_fresh`: `False`
- Corrupted `is_fresh`: `False`
- Repaired `is_fresh`: `False`

## 7. Corruption log

Corruption log được ghi tại:

- `data/results/corruption_log.json`

Các thao tác corruption có chủ đích:

- drop latest records
- blank summary
- add noise vào summary
- truncate title
- làm stale published date
- duplicate rows

## 8. Artifact bàn giao

- `data/clean/papers_clean_corrupted.csv`
- `data/clean/papers_clean_corrupted.json`
- `data/embeddings/papers_embeddings_corrupted.json`
- `data/results/corrupted_metrics.json`
- `data/results/corrupted_answers.json`
- `data/quality/corrupted_quality.json`
- `data/quality/corrupted_freshness.json`
- `data/clean/papers_clean_repaired.csv`
- `data/clean/papers_clean_repaired.json`
- `data/embeddings/papers_embeddings_repaired.json`
- `data/results/repaired_metrics.json`
- `data/results/repaired_answers.json`
- `data/quality/repaired_quality.json`
- `data/quality/repaired_freshness.json`
- `data/reports/corruption_report.md`

## 9. Kết luận

CP5 role 1 đã hoàn thiện đúng tinh thần checkpoint:

- corruption có log và có thể audit,
- corrupted/repaired artifacts tách riêng,
- baseline không bị ghi đè,
- repaired flow quay về raw/source,
- comparison report phản ánh đúng chênh lệch số liệu.

Kết luận ngắn:

- **Có**, CP5 cần output của role 2, 3, 4, 5 để chạy trọn vẹn.
- **Không**, phần repair không phụ thuộc vào corrupted JSON để sửa tay, mà phụ thuộc vào raw snapshot đáng tin cậy.
