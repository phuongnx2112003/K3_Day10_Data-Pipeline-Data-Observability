from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a concise markdown baseline report."""
    path = Path(report_path)
    lines: list[str] = [
        "# Phase 1 Baseline Report",
        "",
        "## Source Summary",
        f"- Source API: {source_summary.get('source_api', 'N/A')}",
        f"- Query: {source_summary.get('source_query', 'N/A')}",
        f"- Filter: {source_summary.get('source_filter', 'N/A')}",
        f"- Raw records: {source_summary.get('raw_records', 'N/A')}",
        f"- Clean records: {source_summary.get('clean_records', 'N/A')}",
        f"- Test set samples: {source_summary.get('test_set_samples', 'N/A')}",
        f"- Embedding documents: {source_summary.get('embedding_documents', 'N/A')}",
        "",
        "## Metrics",
        f"- Retrieval hit rate: {metrics.get('retrieval_hit_rate', 'N/A')}",
        f"- Mean token F1: {metrics.get('mean_token_f1', 'N/A')}",
        f"- Judge accuracy: {metrics.get('judge_accuracy', 'N/A')}",
        f"- Mean judge score: {metrics.get('mean_judge_score', 'N/A')}",
        f"- Ragas: {metrics.get('ragas', 'N/A')}",
        "",
        "## Data Quality",
        f"- Total rows: {quality.get('total_rows', 'N/A')}",
        f"- Missing columns: {quality.get('missing_columns', [])}",
        f"- Duplicate paper_id: {quality.get('counts', {}).get('duplicate_paper_id', 'N/A')}",
        f"- Blank summary: {quality.get('counts', {}).get('blank_summary', 'N/A')}",
        f"- Blank text_for_embedding: {quality.get('counts', {}).get('blank_text_for_embedding', 'N/A')}",
        f"- Fresh rows ratio: {quality.get('checks', {}).get('fresh_rows_ratio', 'N/A')}",
        "",
        "## Freshness",
        f"- Latest published: {freshness.get('latest_published', 'N/A')}",
        f"- Oldest published: {freshness.get('oldest_published', 'N/A')}",
        f"- Stale rows: {freshness.get('stale_rows', 'N/A')}",
        f"- Freshness threshold days: {freshness.get('freshness_threshold_days', 'N/A')}",
        f"- Is fresh: {freshness.get('is_fresh', 'N/A')}",
        "",
        "## Conclusion",
        "- Baseline artifacts are ready for downstream corruption and comparison stages.",
    ]
    write_text(path, "\n".join(lines).rstrip() + "\n")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write a markdown comparison report for baseline/corrupted/repaired."""
    path = Path(report_path)
    lines: list[str] = [
        "# Corruption Comparison Report",
        "",
        "## Metrics Comparison",
        f"- Baseline retrieval hit rate: {baseline_metrics.get('retrieval_hit_rate', 'N/A')}",
        f"- Corrupted retrieval hit rate: {corrupted_metrics.get('retrieval_hit_rate', 'N/A')}",
        f"- Repaired retrieval hit rate: {repaired_metrics.get('retrieval_hit_rate', 'N/A')}",
        f"- Baseline mean token F1: {baseline_metrics.get('mean_token_f1', 'N/A')}",
        f"- Corrupted mean token F1: {corrupted_metrics.get('mean_token_f1', 'N/A')}",
        f"- Repaired mean token F1: {repaired_metrics.get('mean_token_f1', 'N/A')}",
        f"- Baseline judge accuracy: {baseline_metrics.get('judge_accuracy', 'N/A')}",
        f"- Corrupted judge accuracy: {corrupted_metrics.get('judge_accuracy', 'N/A')}",
        f"- Repaired judge accuracy: {repaired_metrics.get('judge_accuracy', 'N/A')}",
        f"- Baseline mean judge score: {baseline_metrics.get('mean_judge_score', 'N/A')}",
        f"- Corrupted mean judge score: {corrupted_metrics.get('mean_judge_score', 'N/A')}",
        f"- Repaired mean judge score: {repaired_metrics.get('mean_judge_score', 'N/A')}",
        "",
        "## Quality Comparison",
        f"- Corrupted duplicate paper_id: {corrupted_quality.get('counts', {}).get('duplicate_paper_id', 'N/A')}",
        f"- Repaired duplicate paper_id: {repaired_quality.get('counts', {}).get('duplicate_paper_id', 'N/A')}",
        f"- Corrupted blank summary: {corrupted_quality.get('counts', {}).get('blank_summary', 'N/A')}",
        f"- Repaired blank summary: {repaired_quality.get('counts', {}).get('blank_summary', 'N/A')}",
        f"- Corrupted blank text_for_embedding: {corrupted_quality.get('counts', {}).get('blank_text_for_embedding', 'N/A')}",
        f"- Repaired blank text_for_embedding: {repaired_quality.get('counts', {}).get('blank_text_for_embedding', 'N/A')}",
        "",
        "## Freshness Comparison",
        f"- Corrupted stale rows: {corrupted_freshness.get('stale_rows', 'N/A')}",
        f"- Repaired stale rows: {repaired_freshness.get('stale_rows', 'N/A')}",
        f"- Corrupted is fresh: {corrupted_freshness.get('is_fresh', 'N/A')}",
        f"- Repaired is fresh: {repaired_freshness.get('is_fresh', 'N/A')}",
        "",
        "## Notes",
        "- Baseline should remain untouched while corrupted and repaired artifacts are rebuilt separately.",
    ]
    write_text(path, "\n".join(lines).rstrip() + "\n")
