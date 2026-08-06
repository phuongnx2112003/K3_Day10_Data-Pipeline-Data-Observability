from __future__ import annotations

from pathlib import Path
from typing import Any

from core.utils import write_json, write_text


def _text(value: Any) -> str:
    if value is None:
        return "N/A"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _number(value: Any, digits: int = 4) -> str:
    if isinstance(value, bool) or value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}" if isinstance(value, float) else str(value)
    return _text(value)


def _status(value: Any) -> str:
    return "PASS" if value is True else "FAIL" if value is False else "N/A"


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
    embedding_audit: dict[str, Any] | None = None,
    artifact_paths: dict[str, Any] | None = None,
) -> None:
    """Render a baseline Markdown report exclusively from provided artifacts."""
    content = _build_phase1_report_content(
        source_summary,
        metrics,
        quality,
        freshness,
        embedding_audit=embedding_audit,
        artifact_paths=artifact_paths,
    )
    write_text(Path(report_path), content)


def _build_phase1_report_content(
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
    embedding_audit: dict[str, Any] | None = None,
    artifact_paths: dict[str, Any] | None = None,
) -> str:
    source_rows = [
        f"| `{_text(key)}` | {_text(value)} |" for key, value in source_summary.items()
    ] or ["| `status` | No source summary provided |"]

    metric_names = (
        "samples",
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    )
    metric_rows = [
        f"| `{name}` | {_number(metrics.get(name))} |" for name in metric_names
    ]

    quality_rows = []
    for check in quality.get("check_results", []):
        quality_rows.append(
            "| `{}` | {} | {} | {} |".format(
                _text(check.get("name")),
                _text(check.get("observed")),
                _text(check.get("expected")),
                _status(check.get("success")),
            )
        )
    if not quality_rows:
        quality_rows.append("| `N/A` | N/A | N/A | N/A |")

    ragas = metrics.get("ragas", {})
    if isinstance(ragas, dict) and "skipped" in ragas:
        ragas_note = f"Skipped: {_text(ragas['skipped'])}"
    elif isinstance(ragas, dict) and "error" in ragas:
        ragas_note = f"Error: {_text(ragas['error'])}"
    else:
        ragas_note = _text(ragas)

    embedding_audit = embedding_audit or {}
    embedding_rows = [
        f"| Backend | {_text(embedding_audit.get('backend'))} |",
        f"| Model | {_text(embedding_audit.get('embedding_model'))} |",
        f"| Collection | `{_text(embedding_audit.get('collection_name'))}` |",
        f"| Indexed documents | {_number(embedding_audit.get('document_count'))} |",
        f"| Clean rows | {_number(embedding_audit.get('clean_row_count'))} |",
        f"| Audit status | {_status(embedding_audit.get('success'))} |",
    ]
    evidence_rows = [
        f"- `{_text(name)}`: `{_text(path)}`" for name, path in (artifact_paths or {}).items()
    ] or ["- No artifact paths provided."]

    return "\n".join(
        [
            "# Phase 1 — Baseline Observability Report",
            "",
            "> Generated from source, metrics, quality, and freshness payloads. No values are hard-coded.",
            "",
            "## Source summary",
            "",
            "| Field | Value |",
            "| --- | --- |",
            *source_rows,
            "",
            "## RAG evaluation metrics",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            *metric_rows,
            "",
            f"Ragas: {ragas_note}",
            "",
            "## Data quality",
            "",
            f"Overall status: **{_status(quality.get('success'))}**",
            "",
            "| Check | Observed | Expected | Status |",
            "| --- | ---: | --- | --- |",
            *quality_rows,
            "",
            "## Freshness",
            "",
            f"Overall status: **{_status(freshness.get('is_fresh'))}**",
            "",
            "| Signal | Value |",
            "| --- | ---: |",
            f"| Source timestamp | `{_text(freshness.get('source_timestamp_column'))}` |",
            f"| Threshold days | {_number(freshness.get('threshold_days'))} |",
            f"| Latest published | {_text(freshness.get('latest_published'))} |",
            f"| Oldest published | {_text(freshness.get('oldest_published'))} |",
            f"| Stale rows | {_number(freshness.get('stale_rows'))} |",
            f"| Stale ratio | {_number(freshness.get('stale_ratio'))} |",
            f"| Invalid timestamps | {_number(freshness.get('invalid_timestamp_rows'))} |",
            f"| Invalid age values | {_number(freshness.get('invalid_age_days_rows'))} |",
            "",
            "## Embedding audit",
            "",
            "| Signal | Value |",
            "| --- | --- |",
            *embedding_rows,
            "",
            "## Evidence artifacts",
            "",
            *evidence_rows,
            "",
            "## Interpretation guardrail",
            "",
            "This baseline is the comparison point for corrupted and repaired data. "
            "A later report must use the same test set and must not claim degradation or recovery "
            "unless the corresponding artifacts show it.",
            "",
        ]
    )


def validate_phase1_report(
    report_path,
    validation_output_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
    embedding_audit: dict[str, Any] | None = None,
    artifact_paths: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify that the Markdown report exactly matches its source payloads."""
    path = Path(report_path)
    expected = _build_phase1_report_content(
        source_summary,
        metrics,
        quality,
        freshness,
        embedding_audit=embedding_audit,
        artifact_paths=artifact_paths,
    )
    actual = path.read_text(encoding="utf-8") if path.is_file() else None
    required_metrics = (
        "samples",
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    )
    missing_metrics = [name for name in required_metrics if metrics.get(name) is None]
    payload = {
        "report_path": str(path),
        "report_exists": path.is_file(),
        "content_matches_payloads": actual == expected,
        "missing_metrics": missing_metrics,
        "success": path.is_file() and actual == expected and not missing_metrics,
    }
    write_json(Path(validation_output_path), payload)
    return payload


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
