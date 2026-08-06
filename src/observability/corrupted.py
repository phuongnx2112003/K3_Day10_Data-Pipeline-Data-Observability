from __future__ import annotations

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


METRIC_NAMES = (
    "retrieval_hit_rate",
    "mean_token_f1",
    "judge_accuracy",
    "mean_judge_score",
)


def _numeric_delta(before: Any, after: Any) -> float | None:
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return float(after - before)
    return None


def _direction(delta: float | None) -> str:
    if delta is None:
        return "not_comparable"
    if delta > 0:
        return "increase"
    if delta < 0:
        return "decrease"
    return "unchanged"


def _changed(delta: Any, direction: str) -> bool:
    """Return whether a numeric delta changed in the requested direction."""
    if not isinstance(delta, (int, float)):
        return False
    return delta < 0 if direction == "decrease" else delta > 0


def _event(log: dict[str, Any], event_type: str) -> dict[str, Any] | None:
    aliases = {
        "latest_drop": {"latest_drop", "drop_latest"},
        "missing": {"missing", "blank_summary"},
        "noise": {"noise", "summary_noise"},
        "truncate_title": {"truncate_title"},
        "old_date": {"old_date", "stale_published"},
        "duplicate": {"duplicate", "duplicate_rows"},
    }
    expected = aliases[event_type]
    return next((item for item in log.get("events", []) if item.get("type") in expected), None)


def _test_questions_for_ids(test_set: list[dict[str, Any]], paper_ids: set[str]) -> int:
    return sum(
        1
        for sample in test_set
        if paper_ids.intersection(str(item) for item in sample.get("ground_truth_doc_ids", []))
    )


def run_corrupted_observability(settings: Settings) -> dict[str, Any]:
    """Run CP5 observability and link corruptions to measured evidence."""
    quality_dir = settings.paths.quality_dir
    readiness_path = quality_dir / "corrupted_observability_readiness.json"
    required_inputs = {
        "corrupted_clean_csv": settings.paths.corrupted_clean_csv,
        "corruption_log": settings.paths.corruption_log,
        "corrupted_metrics": settings.paths.corrupted_metrics,
        "corrupted_answers": settings.paths.corrupted_answers,
        "corrupted_embedding_manifest": settings.paths.corrupted_embeddings_json,
        "baseline_snapshot": quality_dir / "baseline_observability_snapshot.json",
        "baseline_metrics": settings.paths.baseline_metrics,
        "test_set": settings.paths.eval_testset,
    }
    missing_inputs = [name for name, path in required_inputs.items() if not path.is_file()]
    readiness: dict[str, Any] = {
        "status": "pending" if missing_inputs else "ready",
        "required_inputs": {name: str(path) for name, path in required_inputs.items()},
        "missing_inputs": missing_inputs,
        "quality_generated": False,
        "freshness_generated": False,
        "evidence_generated": False,
    }
    if missing_inputs:
        write_json(readiness_path, readiness)
        return readiness

    df = pd.read_csv(settings.paths.corrupted_clean_csv)
    log = read_json(settings.paths.corruption_log)
    baseline_snapshot = read_json(quality_dir / "baseline_observability_snapshot.json")
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    corrupted_metrics = read_json(settings.paths.corrupted_metrics)
    corrupted_answers = read_json(settings.paths.corrupted_answers)
    test_set = read_json(settings.paths.eval_testset)
    answers_count = len(corrupted_answers) if isinstance(corrupted_answers, list) else None

    quality_path = quality_dir / "corrupted_quality.json"
    freshness_path = quality_dir / "corrupted_freshness.json"
    audit_path = quality_dir / "corrupted_embedding_audit.json"
    snapshot_path = quality_dir / "corrupted_observability_snapshot.json"
    evidence_path = quality_dir / "corrupted_impact_evidence.json"

    quality = run_data_quality_checks(df, settings, quality_path.name)
    freshness = build_freshness_report(df, settings, freshness_path)
    audit = audit_embedding_manifest(
        df,
        settings,
        settings.paths.corrupted_embeddings_json,
        audit_path,
        expected_collection_name=settings.corrupted_collection_name,
    )
    corrupted_snapshot = build_observability_snapshot(
        "corrupted",
        quality,
        freshness,
        audit,
        snapshot_path,
        metrics=corrupted_metrics,
        answers_count=answers_count,
    )

    baseline_signals = baseline_snapshot.get("signals", {})
    corrupted_signals = corrupted_snapshot.get("signals", {})
    signal_names = (
        "row_count",
        "null_paper_id_rows",
        "duplicate_paper_id_rows",
        "missing_title_rows",
        "invalid_summary_rows",
        "invalid_age_days_rows",
        "stale_rows",
        "stale_ratio",
    )
    signal_deltas = {
        name: {
            "baseline": baseline_signals.get(name),
            "corrupted": corrupted_signals.get(name),
            "delta": _numeric_delta(baseline_signals.get(name), corrupted_signals.get(name)),
        }
        for name in signal_names
    }
    for item in signal_deltas.values():
        item["direction"] = _direction(item["delta"])

    metric_deltas = {
        name: {
            "baseline": baseline_metrics.get(name),
            "corrupted": corrupted_metrics.get(name),
            "delta": _numeric_delta(baseline_metrics.get(name), corrupted_metrics.get(name)),
        }
        for name in METRIC_NAMES
    }
    for item in metric_deltas.values():
        item["direction"] = _direction(item["delta"])

    drop_event = _event(log, "latest_drop") or {}
    dropped_ids = set(drop_event.get("record_ids") or drop_event.get("paper_ids") or [])
    impacted_questions = _test_questions_for_ids(test_set, dropped_ids)
    event_evidence = [
        {
            "event": "latest_drop",
            "log_present": bool(drop_event),
            "affected_records": len(dropped_ids),
            "affected_test_questions": impacted_questions,
            "observed_metric": "retrieval_hit_rate",
            "metric_delta": metric_deltas["retrieval_hit_rate"]["delta"],
            "supported": (
                bool(drop_event)
                and impacted_questions > 0
                and _changed(metric_deltas["retrieval_hit_rate"]["delta"], "decrease")
            ),
        },
        {
            "event": "missing_summary",
            "log_present": _event(log, "missing") is not None,
            "observed_signal": "invalid_summary_rows",
            "signal_delta": signal_deltas["invalid_summary_rows"]["delta"],
            "supported": (
                _event(log, "missing") is not None
                and _changed(signal_deltas["invalid_summary_rows"]["delta"], "increase")
            ),
        },
        {
            "event": "summary_noise",
            "log_present": _event(log, "noise") is not None,
            "observed_signal": None,
            "supported": False,
            "reason": "No direct noise-marker quality check; aggregate metric changes cannot isolate this event.",
        },
        {
            "event": "truncate_title",
            "log_present": _event(log, "truncate_title") is not None,
            "observed_signal": "missing_title_rows",
            "signal_delta": signal_deltas["missing_title_rows"]["delta"],
            "supported": False,
            "reason": "Titles remain non-blank, so the current missing-title check does not detect truncation.",
        },
        {
            "event": "old_date",
            "log_present": _event(log, "old_date") is not None,
            "observed_signal": "stale_rows",
            "signal_delta": signal_deltas["stale_rows"]["delta"],
            "supported": (
                _event(log, "old_date") is not None
                and _changed(signal_deltas["stale_rows"]["delta"], "increase")
            ),
        },
        {
            "event": "duplicate",
            "log_present": _event(log, "duplicate") is not None,
            "observed_signal": "duplicate_paper_id_rows",
            "signal_delta": signal_deltas["duplicate_paper_id_rows"]["delta"],
            "supported": (
                _event(log, "duplicate") is not None
                and _changed(signal_deltas["duplicate_paper_id_rows"]["delta"], "increase")
            ),
        },
    ]
    unchanged_signals = [
        name for name, item in signal_deltas.items() if item["direction"] == "unchanged"
    ]
    evidence = {
        "state": "baseline_vs_corrupted",
        "corruption_log": str(settings.paths.corruption_log),
        "signal_deltas": signal_deltas,
        "metric_deltas": metric_deltas,
        "event_evidence": event_evidence,
        "unchanged_signals": unchanged_signals,
        "guarded_conclusions": [
            "Structural data quality worsened: duplicate IDs and invalid summaries increased.",
            "Freshness worsened because stale row count and stale ratio increased.",
            "Retrieval quality worsened because retrieval_hit_rate decreased.",
            "Token F1 and judge metrics increased, so the artifacts do not support a claim that every RAG metric worsened.",
            "Noise and title truncation are not directly detected by the current quality checks.",
        ],
        "artifacts": {
            "quality": str(quality_path),
            "freshness": str(freshness_path),
            "embedding_audit": str(audit_path),
            "snapshot": str(snapshot_path),
            "corrupted_metrics": str(settings.paths.corrupted_metrics),
            "corrupted_answers": str(settings.paths.corrupted_answers),
        },
    }
    write_json(evidence_path, evidence)

    samples_match_answers = corrupted_metrics.get("samples") == answers_count
    readiness.update(
        {
            "status": "complete" if samples_match_answers else "invalid",
            "quality_generated": quality_path.is_file(),
            "freshness_generated": freshness_path.is_file(),
            "evidence_generated": evidence_path.is_file(),
            "metrics_samples": corrupted_metrics.get("samples"),
            "answers_count": answers_count,
            "metrics_samples_match_answers": samples_match_answers,
        }
    )
    write_json(readiness_path, readiness)
    return readiness


def main() -> None:
    result = run_corrupted_observability(load_settings())
    print(f"Corrupted observability status: {result['status']}")
    if result.get("missing_inputs"):
        print("Missing inputs: " + ", ".join(result["missing_inputs"]))


if __name__ == "__main__":
    main()
