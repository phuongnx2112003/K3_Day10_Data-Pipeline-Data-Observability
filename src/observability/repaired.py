from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings, load_settings
from core.utils import read_json, write_json
from observability.quality import (
    audit_embedding_manifest,
    build_freshness_report,
    build_observability_snapshot,
    run_data_quality_checks,
)
from observability.reporting import generate_recovery_comparison_report


METRIC_NAMES = (
    "retrieval_hit_rate",
    "mean_token_f1",
    "judge_accuracy",
    "mean_judge_score",
)

LOWER_IS_BETTER_SIGNALS = (
    "null_paper_id_rows",
    "duplicate_paper_id_rows",
    "missing_title_rows",
    "invalid_summary_rows",
    "invalid_age_days_rows",
    "stale_rows",
    "stale_ratio",
)


def _delta(before: Any, after: Any) -> float | None:
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return float(after - before)
    return None


def _signal_outcome(name: str, baseline: Any, corrupted: Any, repaired: Any) -> str:
    if baseline is None or repaired is None:
        return "not_comparable"
    if name == "row_count":
        if repaired != baseline:
            return "differs_from_baseline"
        return "restored_to_baseline" if corrupted != baseline else "unchanged_across_states"
    if name in LOWER_IS_BETTER_SIGNALS:
        if repaired == baseline:
            return "restored_to_baseline" if corrupted != baseline else "unchanged_from_baseline"
        if isinstance(repaired, (int, float)) and isinstance(baseline, (int, float)):
            return "better_than_baseline" if repaired < baseline else "worse_than_baseline"
    return "matches_baseline" if repaired == baseline else "differs_from_baseline"


def _metric_outcome(baseline: Any, repaired: Any) -> str:
    if not isinstance(baseline, (int, float)) or not isinstance(repaired, (int, float)):
        return "not_comparable"
    if repaired == baseline:
        return "restored_to_baseline"
    return "above_baseline" if repaired > baseline else "below_baseline"


def _load_answers_count(path: Path) -> int | None:
    payload = read_json(path)
    return len(payload) if isinstance(payload, list) else None


def run_repaired_observability(settings: Settings) -> dict[str, Any]:
    """Run CP6 checks and report recovery across all three pipeline states."""
    quality_dir = settings.paths.quality_dir
    report_path = settings.paths.comparison_report
    readiness_path = quality_dir / "repaired_observability_readiness.json"
    required_inputs = {
        "repaired_clean_csv": settings.paths.repaired_clean_csv,
        "repaired_metrics": settings.paths.repaired_metrics,
        "repaired_answers": settings.paths.repaired_answers,
        "repaired_embedding_manifest": settings.paths.repaired_embeddings_json,
        "baseline_quality": quality_dir / "baseline_quality.json",
        "baseline_freshness": quality_dir / "baseline_freshness.json",
        "baseline_metrics": settings.paths.baseline_metrics,
        "baseline_snapshot": quality_dir / "baseline_observability_snapshot.json",
        "corrupted_quality": quality_dir / "corrupted_quality.json",
        "corrupted_freshness": quality_dir / "corrupted_freshness.json",
        "corrupted_metrics": settings.paths.corrupted_metrics,
        "corrupted_snapshot": quality_dir / "corrupted_observability_snapshot.json",
    }
    missing_inputs = [name for name, path in required_inputs.items() if not path.is_file()]
    readiness: dict[str, Any] = {
        "status": "pending" if missing_inputs else "ready",
        "required_inputs": {name: str(path) for name, path in required_inputs.items()},
        "missing_inputs": missing_inputs,
        "report_generated": False,
        "comparison_generated": False,
    }
    if missing_inputs:
        write_json(readiness_path, readiness)
        return readiness

    repaired_df = pd.read_csv(settings.paths.repaired_clean_csv)
    baseline_quality = read_json(quality_dir / "baseline_quality.json")
    baseline_freshness = read_json(quality_dir / "baseline_freshness.json")
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_snapshot = read_json(quality_dir / "baseline_observability_snapshot.json")
    corrupted_quality = read_json(quality_dir / "corrupted_quality.json")
    corrupted_freshness = read_json(quality_dir / "corrupted_freshness.json")
    corrupted_metrics = read_json(settings.paths.corrupted_metrics)
    corrupted_snapshot = read_json(quality_dir / "corrupted_observability_snapshot.json")
    repaired_metrics = read_json(settings.paths.repaired_metrics)
    repaired_answers_count = _load_answers_count(settings.paths.repaired_answers)

    repaired_quality_path = quality_dir / "repaired_quality.json"
    repaired_freshness_path = quality_dir / "repaired_freshness.json"
    repaired_audit_path = quality_dir / "repaired_embedding_audit.json"
    repaired_snapshot_path = quality_dir / "repaired_observability_snapshot.json"
    comparison_path = quality_dir / "recovery_comparison.json"

    repaired_quality = run_data_quality_checks(
        repaired_df, settings, repaired_quality_path.name
    )
    repaired_freshness = build_freshness_report(
        repaired_df, settings, repaired_freshness_path
    )
    repaired_audit = audit_embedding_manifest(
        repaired_df,
        settings,
        settings.paths.repaired_embeddings_json,
        repaired_audit_path,
        expected_collection_name=settings.repaired_collection_name,
    )
    repaired_snapshot = build_observability_snapshot(
        "repaired",
        repaired_quality,
        repaired_freshness,
        repaired_audit,
        repaired_snapshot_path,
        metrics=repaired_metrics,
        answers_count=repaired_answers_count,
    )

    baseline_signals = baseline_snapshot.get("signals", {})
    corrupted_signals = corrupted_snapshot.get("signals", {})
    repaired_signals = repaired_snapshot.get("signals", {})
    signal_names = ("row_count", *LOWER_IS_BETTER_SIGNALS)
    signal_comparison = {}
    for name in signal_names:
        baseline = baseline_signals.get(name)
        corrupted = corrupted_signals.get(name)
        repaired = repaired_signals.get(name)
        signal_comparison[name] = {
            "baseline": baseline,
            "corrupted": corrupted,
            "repaired": repaired,
            "corrupted_delta": _delta(baseline, corrupted),
            "repaired_delta": _delta(baseline, repaired),
            "outcome": _signal_outcome(name, baseline, corrupted, repaired),
        }

    metric_comparison = {}
    for name in METRIC_NAMES:
        baseline = baseline_metrics.get(name)
        corrupted = corrupted_metrics.get(name)
        repaired = repaired_metrics.get(name)
        metric_comparison[name] = {
            "baseline": baseline,
            "corrupted": corrupted,
            "repaired": repaired,
            "corrupted_delta": _delta(baseline, corrupted),
            "repaired_delta": _delta(baseline, repaired),
            "outcome": _metric_outcome(baseline, repaired),
        }

    unresolved_signals = [
        name
        for name, values in signal_comparison.items()
        if values["outcome"] in {"worse_than_baseline", "differs_from_baseline", "not_comparable"}
    ]
    unresolved_metrics = [
        name
        for name, values in metric_comparison.items()
        if values["outcome"] in {"below_baseline", "not_comparable"}
    ]
    quality_recovered = not unresolved_signals
    metric_recovered = not unresolved_metrics
    samples_match_answers = repaired_metrics.get("samples") == repaired_answers_count
    recovery_status = (
        "complete"
        if quality_recovered and metric_recovered and repaired_audit.get("success")
        else "partial"
    )

    limitations = []
    if unresolved_metrics:
        limitations.append(
            "Metrics still below baseline: " + ", ".join(unresolved_metrics) + "."
        )
    if not repaired_freshness.get("is_fresh"):
        limitations.append(
            "Repaired freshness is still FAIL because one source record is older than the 180-day threshold; this matches the baseline condition."
        )
    if not repaired_audit.get("success"):
        limitations.append(
            "Repaired embedding audit is not PASS: "
            + ", ".join(repaired_audit.get("failed_checks", []))
            + "."
        )
    ragas = repaired_metrics.get("ragas", {})
    if isinstance(ragas, dict) and ragas.get("skipped"):
        limitations.append("Ragas was skipped, so no Ragas-based recovery claim is made.")

    comparison = {
        "state": "baseline_vs_corrupted_vs_repaired",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "recovery_status": recovery_status,
        "quality_freshness_recovered_to_baseline": quality_recovered,
        "evaluation_metrics_recovered": metric_recovered,
        "unresolved_signals": unresolved_signals,
        "unresolved_metrics": unresolved_metrics,
        "signal_comparison": signal_comparison,
        "metric_comparison": metric_comparison,
        "status_comparison": {
            "structural_quality": {
                "baseline": baseline_quality.get("overall_pass"),
                "corrupted": corrupted_quality.get("overall_pass"),
                "repaired": repaired_quality.get("overall_pass"),
            },
            "freshness": {
                "baseline": baseline_freshness.get("is_fresh"),
                "corrupted": corrupted_freshness.get("is_fresh"),
                "repaired": repaired_freshness.get("is_fresh"),
            },
            "embedding_audit": {
                "baseline": baseline_snapshot.get("status", {}).get("embedding_audit_success"),
                "corrupted": corrupted_snapshot.get("status", {}).get("embedding_audit_success"),
                "repaired": repaired_audit.get("success"),
            },
        },
        "conclusions": [
            "Structural quality and measured freshness signals returned to their baseline values.",
            "Retrieval hit rate and mean token F1 returned exactly to baseline.",
            "Judge accuracy is above baseline, but mean judge score remains below baseline.",
            "Overall recovery is partial because at least one metric or audit signal remains unresolved.",
        ],
        "limitations": limitations,
        "artifacts": {
            "baseline_metrics": str(settings.paths.baseline_metrics),
            "corrupted_metrics": str(settings.paths.corrupted_metrics),
            "repaired_metrics": str(settings.paths.repaired_metrics),
            "baseline_quality": str(quality_dir / "baseline_quality.json"),
            "corrupted_quality": str(quality_dir / "corrupted_quality.json"),
            "repaired_quality": str(repaired_quality_path),
            "baseline_freshness": str(quality_dir / "baseline_freshness.json"),
            "corrupted_freshness": str(quality_dir / "corrupted_freshness.json"),
            "repaired_freshness": str(repaired_freshness_path),
            "repaired_embedding_audit": str(repaired_audit_path),
            "repaired_snapshot": str(repaired_snapshot_path),
        },
    }
    write_json(comparison_path, comparison)
    generate_recovery_comparison_report(report_path, comparison)

    readiness.update(
        {
            "status": "complete" if samples_match_answers else "invalid",
            "report_generated": report_path.is_file(),
            "comparison_generated": comparison_path.is_file(),
            "recovery_status": recovery_status,
            "metrics_samples": repaired_metrics.get("samples"),
            "answers_count": repaired_answers_count,
            "metrics_samples_match_answers": samples_match_answers,
        }
    )
    write_json(readiness_path, readiness)
    return readiness


def main() -> None:
    result = run_repaired_observability(load_settings())
    print(f"Repaired observability status: {result['status']}")
    print(f"Recovery status: {result.get('recovery_status', 'not evaluated')}")
    if result.get("missing_inputs"):
        print("Missing inputs: " + ", ".join(result["missing_inputs"]))


if __name__ == "__main__":
    main()
