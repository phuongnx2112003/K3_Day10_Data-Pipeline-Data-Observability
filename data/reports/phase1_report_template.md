# Phase 1 — Baseline Observability Report

> Vai trò 6 chuẩn bị tại Checkpoint 2. Chỉ thay placeholder bằng số lấy từ
> artifacts thật khi baseline evaluation hoàn tất ở Checkpoint 3.

## Source summary

| Field | Value |
| --- | --- |
| Source | `[source]` |
| Raw rows | `[raw_rows]` |
| Clean rows | `[clean_rows]` |
| Embedding collection | `[collection_name]` |
| Indexed documents | `[document_count]` |

## RAG evaluation metrics

| Metric | Value |
| --- | ---: |
| `samples` | `[samples]` |
| `retrieval_hit_rate` | `[retrieval_hit_rate]` |
| `mean_token_f1` | `[mean_token_f1]` |
| `judge_accuracy` | `[judge_accuracy]` |
| `mean_judge_score` | `[mean_judge_score]` |

Ragas status: `[ragas status/skipped/error]`

## Data quality

Overall status: **[PASS/FAIL]**

| Check | Observed | Expected | Status |
| --- | ---: | --- | --- |
| Row count | `[value]` | `> 0` | `[PASS/FAIL]` |
| Null paper IDs | `[value]` | `0` | `[PASS/FAIL]` |
| Duplicate paper IDs | `[value]` | `0` | `[PASS/FAIL]` |
| Missing titles | `[value]` | `0` | `[PASS/FAIL]` |
| Invalid summaries | `[value]` | `0` | `[PASS/FAIL]` |
| Invalid age values | `[value]` | `0` | `[PASS/FAIL]` |

## Freshness

Overall status: **[PASS/FAIL]**

| Signal | Value |
| --- | ---: |
| Source timestamp | `published` |
| Threshold days | `[threshold_days]` |
| Latest published | `[date]` |
| Oldest published | `[date]` |
| Stale rows | `[value]` |
| Stale ratio | `[value]` |

## Embedding audit

| Signal | Value |
| --- | --- |
| Manifest path | `[path]` |
| Backend | `[backend]` |
| Model | `[embedding_model]` |
| Collection | `[collection_name]` |
| Indexed documents | `[document_count]` |
| Clean rows | `[clean_row_count]` |
| Persist path matches config | `[PASS/FAIL]` |

## Evidence

- `[path to baseline_metrics.json]`
- `[path to baseline_quality.json]`
- `[path to baseline_freshness.json]`
- `[path to baseline_embedding_audit.json]`
- `[path to baseline_observability_snapshot.json]`

## Interpretation

`[Chỉ kết luận từ artifacts thật. Nếu quality/freshness fail nhưng RAG metric
không giảm, ghi rõ chưa quan sát thấy ảnh hưởng thay vì khẳng định quá mức.]`

