from __future__ import annotations

from observability.reporting import generate_phase1_report, validate_phase1_report


def test_generate_phase1_report_renders_values_from_payloads(tmp_path):
    report_path = tmp_path / "phase1_report.md"
    generate_phase1_report(
        report_path,
        source_summary={"source": "Crossref", "clean_rows": 24},
        metrics={
            "samples": 8,
            "retrieval_hit_rate": 0.75,
            "mean_token_f1": 0.5,
            "judge_accuracy": 0.625,
            "mean_judge_score": 3.5,
            "ragas": {"skipped": "disabled for fast run"},
        },
        quality={
            "success": False,
            "check_results": [
                {
                    "name": "paper_id_unique",
                    "observed": 0,
                    "expected": "0 duplicate rows",
                    "success": True,
                }
            ],
        },
        freshness={
            "is_fresh": False,
            "source_timestamp_column": "published",
            "threshold_days": 180,
            "latest_published": "2026-08-05",
            "oldest_published": "2026-01-25",
            "stale_rows": 1,
            "stale_ratio": 1 / 24,
            "invalid_timestamp_rows": 0,
            "invalid_age_days_rows": 0,
        },
    )

    report = report_path.read_text(encoding="utf-8")
    assert "# Phase 1 — Baseline Observability Report" in report
    assert "`retrieval_hit_rate` | 0.7500" in report
    assert "`paper_id_unique` | 0 | 0 duplicate rows | PASS" in report
    assert "| Stale rows | 1 |" in report
    assert "Skipped: disabled for fast run" in report

    validation = validate_phase1_report(
        report_path,
        tmp_path / "validation.json",
        source_summary={"source": "Crossref", "clean_rows": 24},
        metrics={
            "samples": 8,
            "retrieval_hit_rate": 0.75,
            "mean_token_f1": 0.5,
            "judge_accuracy": 0.625,
            "mean_judge_score": 3.5,
            "ragas": {"skipped": "disabled for fast run"},
        },
        quality={
            "success": False,
            "check_results": [
                {
                    "name": "paper_id_unique",
                    "observed": 0,
                    "expected": "0 duplicate rows",
                    "success": True,
                }
            ],
        },
        freshness={
            "is_fresh": False,
            "source_timestamp_column": "published",
            "threshold_days": 180,
            "latest_published": "2026-08-05",
            "oldest_published": "2026-01-25",
            "stale_rows": 1,
            "stale_ratio": 1 / 24,
            "invalid_timestamp_rows": 0,
            "invalid_age_days_rows": 0,
        },
    )
    assert validation["success"] is True
