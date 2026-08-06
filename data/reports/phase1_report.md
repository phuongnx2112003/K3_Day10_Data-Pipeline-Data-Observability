# Phase 1 — Baseline Observability Report

> Generated from source, metrics, quality, and freshness payloads. No values are hard-coded.

## Source summary

| Field | Value |
| --- | --- |
| `source` | Crossref REST API |
| `query` | agentic retrieval augmented generation large language model |
| `filter` | from-pub-date:2026-02-07,has-abstract:true |
| `raw_rows` | 24 |
| `clean_rows` | 24 |
| `embedding_collection` | papers-baseline |
| `indexed_documents` | 24 |

## RAG evaluation metrics

| Metric | Value |
| --- | ---: |
| `samples` | 72 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 0.4236 |
| `judge_accuracy` | 0.3333 |
| `mean_judge_score` | 2.6250 |

Ragas: Skipped: Set RUN_RAGAS=1 to enable the slower Ragas pass.

## Data quality

Overall status: **FAIL**

| Check | Observed | Expected | Status |
| --- | ---: | --- | --- |
| `row_count_positive` | 24 | > 0 | PASS |
| `required_columns_present` | 0 | 0 missing columns | PASS |
| `paper_id_not_null` | 0 | 0 invalid rows | PASS |
| `paper_id_unique` | 0 | 0 duplicate rows | PASS |
| `title_not_null` | 0 | 0 invalid rows | PASS |
| `summary_min_length` | 0 | 0 rows shorter than 50 characters | PASS |
| `published_parseable` | 0 | 0 invalid rows | PASS |
| `age_days_valid` | 0 | 0 null, non-numeric, or negative rows | PASS |
| `age_days_within_freshness_threshold` | 1 | 0 rows older than 180 days | FAIL |

## Freshness

Overall status: **FAIL**

| Signal | Value |
| --- | ---: |
| Source timestamp | `published` |
| Threshold days | 180 |
| Latest published | 2026-08-05 |
| Oldest published | 2026-01-25 |
| Stale rows | 1 |
| Stale ratio | 0.0417 |
| Invalid timestamps | 0 |
| Invalid age values | 0 |

## Embedding audit

| Signal | Value |
| --- | --- |
| Backend | chroma |
| Model | sentence-transformers/all-MiniLM-L6-v2 |
| Collection | `papers-baseline` |
| Indexed documents | 24 |
| Clean rows | 24 |
| Audit status | FAIL |

## Evidence artifacts

- `clean_csv`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\clean\papers_clean.csv`
- `baseline_metrics`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\results\baseline_metrics.json`
- `baseline_answers`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\results\baseline_answers.json`
- `quality`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\baseline_quality.json`
- `freshness`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\baseline_freshness.json`
- `embedding_audit`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\baseline_embedding_audit.json`
- `observability_snapshot`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\baseline_observability_snapshot.json`

## Interpretation guardrail

This baseline is the comparison point for corrupted and repaired data. A later report must use the same test set and must not claim degradation or recovery unless the corresponding artifacts show it.
