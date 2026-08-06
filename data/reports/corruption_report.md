# Phase 2 — Recovery Comparison Report

> Generated from baseline, corrupted, and repaired metrics/quality/freshness artifacts.

Overall recovery status: **PARTIAL**

## Quality and freshness signals

| Signal | Baseline | Corrupted | Repaired | Recovery outcome |
| --- | ---: | ---: | ---: | --- |
| `row_count` | 24 | 24 | 24 | unchanged_across_states |
| `null_paper_id_rows` | 0 | 0 | 0 | unchanged_from_baseline |
| `duplicate_paper_id_rows` | 0 | 4 | 0 | restored_to_baseline |
| `missing_title_rows` | 0 | 0 | 0 | unchanged_from_baseline |
| `invalid_summary_rows` | 0 | 2 | 0 | restored_to_baseline |
| `invalid_age_days_rows` | 0 | 0 | 0 | unchanged_from_baseline |
| `stale_rows` | 1 | 3 | 1 | restored_to_baseline |
| `stale_ratio` | 0.0417 | 0.1250 | 0.0417 | restored_to_baseline |

## Evaluation metrics

| Metric | Baseline | Corrupted | Repaired | Repaired − baseline | Recovery outcome |
| --- | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.9167 | 1.0000 | 0.0000 | restored_to_baseline |
| `mean_token_f1` | 0.7569 | 0.6603 | 0.7569 | 0.0000 | restored_to_baseline |
| `judge_accuracy` | 0.6806 | 0.6250 | 0.6667 | -0.0139 | below_baseline |
| `mean_judge_score` | 3.9583 | 3.7778 | 3.9583 | 0.0000 | restored_to_baseline |

## Status comparison

| Status | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| structural_quality | PASS | FAIL | PASS |
| freshness | FAIL | FAIL | FAIL |
| embedding_audit | FAIL | FAIL | FAIL |

## Evidence-based conclusions

- Structural quality and measured freshness signals returned to their baseline values.
- Metrics restored exactly to baseline: retrieval_hit_rate, mean_token_f1, mean_judge_score.
- Metrics still below baseline: judge_accuracy.
- Overall recovery is partial because at least one metric or audit signal remains unresolved.

## Limits of the conclusion

- Metrics still below baseline: judge_accuracy.
- Repaired freshness is still FAIL because one source record is older than the 180-day threshold; this matches the baseline condition.
- Repaired embedding audit is not PASS: persist_path_matches_config.
- Ragas was skipped, so no Ragas-based recovery claim is made.

## Evidence artifacts

- `baseline_metrics`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\results\baseline_metrics.json`
- `corrupted_metrics`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\results\corrupted_metrics.json`
- `repaired_metrics`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\results\repaired_metrics.json`
- `baseline_quality`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\baseline_quality.json`
- `corrupted_quality`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\corrupted_quality.json`
- `repaired_quality`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\repaired_quality.json`
- `baseline_freshness`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\baseline_freshness.json`
- `corrupted_freshness`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\corrupted_freshness.json`
- `repaired_freshness`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\repaired_freshness.json`
- `repaired_embedding_audit`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\repaired_embedding_audit.json`
- `repaired_snapshot`: `D:\K3_Day10_Data-Pipeline-Data-Observability\data\quality\repaired_observability_snapshot.json`
