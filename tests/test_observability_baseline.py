from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_json
from observability.baseline import run_baseline_observability


def _prepare_inputs(settings) -> None:
    df = pd.DataFrame(
        [
            {
                "paper_id": "paper-1",
                "title": "A valid title",
                "summary": "A complete and meaningful summary for observability testing. " * 2,
                "published": "2026-08-01",
                "age_days": 5,
            }
        ]
    )
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.paths.clean_csv, index=False)
    write_json(settings.paths.raw_records_json, [{"paper_id": "paper-1"}])
    settings.paths.chroma_dir.mkdir(parents=True)
    write_json(
        settings.paths.embeddings_json,
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
                        "title": "A valid title",
                        "published": "2026-08-01",
                        "summary": "A complete and meaningful summary for observability testing.",
                    },
                }
            ],
        },
    )


def test_baseline_observability_waits_for_evaluation_artifacts(tmp_path):
    settings = load_settings(tmp_path)
    _prepare_inputs(settings)

    result = run_baseline_observability(settings)

    assert result["status"] == "pending"
    assert result["missing_inputs"] == ["baseline_metrics", "baseline_answers"]
    assert not settings.paths.baseline_report.exists()


def test_baseline_observability_generates_and_validates_report(tmp_path):
    settings = load_settings(tmp_path)
    _prepare_inputs(settings)
    write_json(
        settings.paths.baseline_metrics,
        {
            "samples": 1,
            "retrieval_hit_rate": 1.0,
            "mean_token_f1": 1.0,
            "judge_accuracy": 1.0,
            "mean_judge_score": 5.0,
            "ragas": {"skipped": "fast test"},
        },
    )
    write_json(settings.paths.baseline_answers, [{"id": "sample-1"}])

    result = run_baseline_observability(settings)

    assert result["status"] == "complete"
    assert settings.paths.baseline_report.exists()
    validation = read_json(settings.paths.quality_dir / "baseline_report_validation.json")
    assert validation["success"] is True
