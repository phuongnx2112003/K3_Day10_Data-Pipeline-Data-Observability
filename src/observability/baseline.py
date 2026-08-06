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
from observability.reporting import generate_phase1_report, validate_phase1_report


def _count_json_records(path: Path) -> int | None:
    if not path.is_file():
        return None
    payload = read_json(path)
    return len(payload) if isinstance(payload, list) else None


def run_baseline_observability(settings: Settings) -> dict[str, Any]:
    """Run Role 6 baseline checks and finalize the report when metrics exist."""
    if not settings.paths.clean_csv.is_file():
        raise FileNotFoundError(f"Clean dataset not found: {settings.paths.clean_csv}")

    df = pd.read_csv(settings.paths.clean_csv)
    quality_path = settings.paths.quality_dir / "baseline_quality.json"
    freshness_path = settings.paths.quality_dir / "baseline_freshness.json"
    audit_path = settings.paths.quality_dir / "baseline_embedding_audit.json"
    snapshot_path = settings.paths.quality_dir / "baseline_observability_snapshot.json"
    readiness_path = settings.paths.quality_dir / "baseline_report_readiness.json"
    validation_path = settings.paths.quality_dir / "baseline_report_validation.json"

    quality = run_data_quality_checks(df, settings, quality_path.name)
    freshness = build_freshness_report(df, settings, freshness_path)
    embedding_audit = audit_embedding_manifest(
        df, settings, settings.paths.embeddings_json, audit_path
    )

    required_inputs = {
        "clean_csv": settings.paths.clean_csv,
        "raw_records_json": settings.paths.raw_records_json,
        "embedding_manifest": settings.paths.embeddings_json,
        "baseline_metrics": settings.paths.baseline_metrics,
        "baseline_answers": settings.paths.baseline_answers,
    }
    missing_inputs = [name for name, path in required_inputs.items() if not path.is_file()]
    readiness = {
        "status": "ready" if not missing_inputs else "pending",
        "required_inputs": {name: str(path) for name, path in required_inputs.items()},
        "missing_inputs": missing_inputs,
        "report_generated": False,
        "report_validated": False,
    }

    metrics = read_json(settings.paths.baseline_metrics) if settings.paths.baseline_metrics.is_file() else None
    answers = read_json(settings.paths.baseline_answers) if settings.paths.baseline_answers.is_file() else None
    answers_count = len(answers) if isinstance(answers, list) else None
    build_observability_snapshot(
        "baseline",
        quality,
        freshness,
        embedding_audit,
        snapshot_path,
        metrics=metrics,
        answers_count=answers_count,
    )

    if missing_inputs:
        write_json(readiness_path, readiness)
        return readiness

    source_summary = {
        "source": settings.source_api,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "raw_rows": _count_json_records(settings.paths.raw_records_json),
        "clean_rows": len(df),
        "embedding_collection": embedding_audit.get("collection_name"),
        "indexed_documents": embedding_audit.get("document_count"),
    }
    artifact_paths = {
        "clean_csv": settings.paths.clean_csv,
        "baseline_metrics": settings.paths.baseline_metrics,
        "baseline_answers": settings.paths.baseline_answers,
        "quality": quality_path,
        "freshness": freshness_path,
        "embedding_audit": audit_path,
        "observability_snapshot": snapshot_path,
    }
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary,
        metrics,
        quality,
        freshness,
        embedding_audit=embedding_audit,
        artifact_paths=artifact_paths,
    )
    validation = validate_phase1_report(
        settings.paths.baseline_report,
        validation_path,
        source_summary,
        metrics,
        quality,
        freshness,
        embedding_audit=embedding_audit,
        artifact_paths=artifact_paths,
    )
    samples_match_answers = metrics.get("samples") == answers_count
    readiness.update(
        {
            "status": "complete" if validation["success"] and samples_match_answers else "invalid",
            "report_generated": settings.paths.baseline_report.is_file(),
            "report_validated": validation["success"],
            "metrics_samples": metrics.get("samples"),
            "answers_count": answers_count,
            "metrics_samples_match_answers": samples_match_answers,
        }
    )
    write_json(readiness_path, readiness)
    return readiness


def main() -> None:
    result = run_baseline_observability(load_settings())
    print(f"Baseline observability status: {result['status']}")
    if result.get("missing_inputs"):
        print("Missing inputs: " + ", ".join(result["missing_inputs"]))


if __name__ == "__main__":
    main()
