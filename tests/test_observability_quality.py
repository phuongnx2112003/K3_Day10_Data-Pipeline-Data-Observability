from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_json
from observability.quality import (
    audit_embedding_manifest,
    build_freshness_report,
    build_observability_snapshot,
    run_data_quality_checks,
)


def _date_ago(days: int) -> str:
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


def test_quality_and_freshness_pass_for_valid_data(tmp_path):
    settings = load_settings(tmp_path)
    df = pd.DataFrame(
        [
            {
                "paper_id": "10.1/alpha",
                "title": "A valid paper",
                "summary": "A sufficiently detailed summary " * 3,
                "published": _date_ago(10),
                "age_days": 10,
            },
            {
                "paper_id": "10.1/beta",
                "title": "Another valid paper",
                "summary": "Another sufficiently detailed summary " * 3,
                "published": _date_ago(20),
                "age_days": 20,
            },
        ]
    )

    quality = run_data_quality_checks(df, settings, "baseline_quality")
    freshness_path = settings.paths.quality_dir / "baseline_freshness.json"
    freshness = build_freshness_report(df, settings, freshness_path)

    assert quality["success"] is True
    assert quality["failed_checks"] == []
    assert freshness["is_fresh"] is True
    assert freshness["stale_rows"] == 0
    assert read_json(settings.paths.quality_dir / "baseline_quality.json") == quality
    assert read_json(freshness_path) == freshness


def test_quality_reports_corruption_instead_of_crashing(tmp_path):
    settings = load_settings(tmp_path)
    df = pd.DataFrame(
        [
            {
                "paper_id": "duplicate-id",
                "title": "",
                "summary": "short",
                "published": "not-a-date",
                "age_days": -1,
            },
            {
                "paper_id": "duplicate-id",
                "title": "Title",
                "summary": None,
                "published": _date_ago(settings.freshness_threshold_days + 10),
                "age_days": settings.freshness_threshold_days + 10,
            },
        ]
    )

    quality = run_data_quality_checks(df, settings, "corrupted_quality.json")
    freshness = build_freshness_report(
        df, settings, settings.paths.quality_dir / "corrupted_freshness.json"
    )
    checks = {item["name"]: item for item in quality["checks"]}

    assert quality["success"] is False
    assert checks["paper_id_unique"]["observed"] == 2
    assert checks["title_not_null"]["observed"] == 1
    assert checks["summary_min_length"]["observed"] == 2
    assert checks["published_parseable"]["observed"] == 1
    assert checks["age_days_valid"]["observed"] == 1
    assert checks["age_days_within_freshness_threshold"]["observed"] == 1
    assert freshness["is_fresh"] is False
    assert freshness["invalid_timestamp_rows"] == 1
    assert freshness["invalid_age_days_rows"] == 1
    assert freshness["stale_rows"] == 1


def test_embedding_audit_and_snapshot_are_reproducible(tmp_path):
    settings = load_settings(tmp_path)
    settings.paths.chroma_dir.mkdir(parents=True)
    df = pd.DataFrame(
        [{"paper_id": "paper-1", "title": "Title", "summary": "S" * 60, "published": _date_ago(1), "age_days": 1}]
    )
    manifest_path = settings.paths.embeddings_json
    write_json(
        manifest_path,
        {
            "backend": "chroma",
            "embedding_model": settings.embedding_model,
            "persist_path": str(settings.paths.chroma_dir),
            "collection_name": settings.baseline_collection_name,
            "documents": [
                {
                    "record_id": "paper-1::0",
                    "paper_id": "paper-1",
                    "metadata": {
                        "paper_id": "paper-1",
                        "title": "Title",
                        "published": _date_ago(1),
                        "summary": "S" * 60,
                    },
                }
            ],
        },
    )
    audit_path = settings.paths.quality_dir / "baseline_embedding_audit.json"
    audit = audit_embedding_manifest(df, settings, manifest_path, audit_path)
    quality = run_data_quality_checks(df, settings, "baseline_quality")
    freshness = build_freshness_report(
        df, settings, settings.paths.quality_dir / "baseline_freshness.json"
    )
    snapshot_path = settings.paths.quality_dir / "baseline_observability_snapshot.json"
    snapshot = build_observability_snapshot(
        "baseline", quality, freshness, audit, snapshot_path
    )

    assert audit["success"] is True
    assert audit["document_count"] == 1
    assert snapshot["signals"]["embedding_collection_name"] == "papers-baseline"
    assert read_json(snapshot_path) == snapshot
