from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_json
from observability.quality import (
    audit_embedding_manifest,
    build_freshness_report,
    build_observability_snapshot,
    run_data_quality_checks,
)
from observability.repaired import run_repaired_observability


def _row(paper_id: str) -> dict:
    return {
        "paper_id": paper_id,
        "title": "A complete title",
        "summary": "A sufficiently long summary " * 4,
        "published": "2026-08-01",
        "age_days": 5,
        "text_for_embedding": "Embedding content",
        "authors_joined": "Author",
        "categories_joined": "AI",
    }


def _manifest(settings, path, collection: str, rows: list[dict]) -> None:
    write_json(
        path,
        {
            "backend": "chroma",
            "embedding_model": settings.embedding_model,
            "persist_path": str(settings.paths.chroma_dir),
            "collection_name": collection,
            "documents": [
                {
                    "record_id": f"{row['paper_id']}::0",
                    "paper_id": row["paper_id"],
                    "metadata": {
                        "paper_id": row["paper_id"],
                        "title": row["title"],
                        "published": row["published"],
                        "summary": row["summary"],
                    },
                }
                for row in rows
            ],
        },
    )


def test_repaired_observability_marks_remaining_metric_gap_as_partial(tmp_path):
    settings = load_settings(tmp_path)
    settings.paths.chroma_dir.mkdir(parents=True)
    quality_dir = settings.paths.quality_dir
    baseline_rows = [_row("p1"), _row("p2")]
    corrupted_rows = [_row("p1"), _row("p1")]

    baseline_df = pd.DataFrame(baseline_rows)
    corrupted_df = pd.DataFrame(corrupted_rows)
    baseline_quality = run_data_quality_checks(baseline_df, settings, "baseline_quality")
    baseline_freshness = build_freshness_report(
        baseline_df, settings, quality_dir / "baseline_freshness.json"
    )
    _manifest(settings, settings.paths.embeddings_json, settings.baseline_collection_name, baseline_rows)
    baseline_audit = audit_embedding_manifest(
        baseline_df,
        settings,
        settings.paths.embeddings_json,
        quality_dir / "baseline_embedding_audit.json",
    )
    build_observability_snapshot(
        "baseline",
        baseline_quality,
        baseline_freshness,
        baseline_audit,
        quality_dir / "baseline_observability_snapshot.json",
    )

    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted_quality")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, quality_dir / "corrupted_freshness.json"
    )
    build_observability_snapshot(
        "corrupted",
        corrupted_quality,
        corrupted_freshness,
        {},
        quality_dir / "corrupted_observability_snapshot.json",
    )

    settings.paths.repaired_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    baseline_df.to_csv(settings.paths.repaired_clean_csv, index=False)
    _manifest(settings, settings.paths.repaired_embeddings_json, settings.repaired_collection_name, baseline_rows)
    write_json(settings.paths.baseline_metrics, {"retrieval_hit_rate": 1.0, "mean_token_f1": 0.5, "judge_accuracy": 0.5, "mean_judge_score": 3.0})
    write_json(settings.paths.corrupted_metrics, {"retrieval_hit_rate": 0.5, "mean_token_f1": 0.4, "judge_accuracy": 0.4, "mean_judge_score": 2.0})
    write_json(settings.paths.repaired_metrics, {"samples": 1, "retrieval_hit_rate": 1.0, "mean_token_f1": 0.5, "judge_accuracy": 0.6, "mean_judge_score": 2.5})
    write_json(settings.paths.repaired_answers, [{"id": "q1"}])

    result = run_repaired_observability(settings)
    comparison = read_json(quality_dir / "recovery_comparison.json")

    assert result["status"] == "complete"
    assert result["recovery_status"] == "partial"
    assert comparison["quality_freshness_recovered_to_baseline"] is True
    assert comparison["metric_comparison"]["retrieval_hit_rate"]["outcome"] == "restored_to_baseline"
    assert comparison["metric_comparison"]["judge_accuracy"]["outcome"] == "above_baseline"
    assert comparison["unresolved_metrics"] == ["mean_judge_score"]
    assert settings.paths.comparison_report.is_file()
