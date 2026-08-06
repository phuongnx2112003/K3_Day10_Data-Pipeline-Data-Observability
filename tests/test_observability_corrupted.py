from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import read_json, write_json
from observability.corrupted import run_corrupted_observability


def _document(paper_id: str, published: str, summary: str) -> dict:
    return {
        "record_id": f"{paper_id}::0",
        "paper_id": paper_id,
        "metadata": {
            "paper_id": paper_id,
            "title": "Title",
            "published": published,
            "summary": summary,
        },
    }


def test_corrupted_observability_links_events_to_measured_changes(tmp_path):
    settings = load_settings(tmp_path)
    settings.paths.chroma_dir.mkdir(parents=True)
    quality_dir = settings.paths.quality_dir
    corrupted = pd.DataFrame(
        [
            {
                "paper_id": "duplicate",
                "title": "Title",
                "summary": "",
                "published": "2016-01-01",
                "age_days": 3652,
                "text_for_embedding": "Title",
                "authors_joined": "Author",
                "categories_joined": "AI",
            },
            {
                "paper_id": "duplicate",
                "title": "Title",
                "summary": "",
                "published": "2016-01-01",
                "age_days": 3652,
                "text_for_embedding": "Title",
                "authors_joined": "Author",
                "categories_joined": "AI",
            },
        ]
    )
    settings.paths.corrupted_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    corrupted.to_csv(settings.paths.corrupted_clean_csv, index=False)
    write_json(settings.paths.baseline_metrics, {"retrieval_hit_rate": 1.0, "mean_token_f1": 0.5, "judge_accuracy": 0.5, "mean_judge_score": 3.0})
    write_json(settings.paths.corrupted_metrics, {"samples": 1, "retrieval_hit_rate": 0.0, "mean_token_f1": 0.6, "judge_accuracy": 0.6, "mean_judge_score": 3.5})
    write_json(settings.paths.corrupted_answers, [{"id": "q1"}])
    write_json(settings.paths.eval_testset, [{"id": "q1", "ground_truth_doc_ids": ["dropped"]}])
    write_json(
        settings.paths.corruption_log,
        {
            "events": [
                {"type": "latest_drop", "record_ids": ["dropped"]},
                {"type": "missing", "record_ids": ["duplicate"]},
                {"type": "old_date", "record_ids": ["duplicate"]},
                {"type": "duplicate", "record_ids": ["duplicate"]},
            ]
        },
    )
    write_json(
        quality_dir / "baseline_observability_snapshot.json",
        {
            "signals": {
                "row_count": 2,
                "null_paper_id_rows": 0,
                "duplicate_paper_id_rows": 0,
                "missing_title_rows": 0,
                "invalid_summary_rows": 0,
                "invalid_age_days_rows": 0,
                "stale_rows": 0,
                "stale_ratio": 0.0,
            }
        },
    )
    write_json(
        settings.paths.corrupted_embeddings_json,
        {
            "backend": "chroma",
            "embedding_model": settings.embedding_model,
            "persist_path": str(settings.paths.chroma_dir),
            "collection_name": settings.corrupted_collection_name,
            "documents": [
                _document("duplicate", "2016-01-01", "Summary"),
                {**_document("duplicate", "2016-01-01", "Summary"), "record_id": "duplicate::1"},
            ],
        },
    )

    result = run_corrupted_observability(settings)
    evidence = read_json(quality_dir / "corrupted_impact_evidence.json")

    assert result["status"] == "complete"
    assert evidence["signal_deltas"]["duplicate_paper_id_rows"]["delta"] == 2
    assert evidence["signal_deltas"]["stale_rows"]["delta"] == 2
    assert evidence["metric_deltas"]["retrieval_hit_rate"]["delta"] == -1.0
    assert "row_count" in evidence["unchanged_signals"]
