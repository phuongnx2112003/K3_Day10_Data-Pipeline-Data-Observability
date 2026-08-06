from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def _load_raw_records(settings) -> tuple[list[Any], dict[str, Any]]:
    raw_records_path = settings.paths.raw_records_json
    if settings.refresh_source or not raw_records_path.exists():
        records = fetch_source_records(settings)
        source_mode = "fetched"
    else:
        records = load_raw_records(raw_records_path)
        source_mode = "loaded"
        if not records:
            records = fetch_source_records(settings)
            source_mode = "refetched-empty-cache"

    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "source_mode": source_mode,
        "raw_response_path": str(settings.paths.raw_api_response),
        "raw_records_path": str(settings.paths.raw_records_json),
        "raw_records": len(records),
    }
    return records, source_summary


def _write_clean_artifacts(df: pd.DataFrame, settings) -> None:
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.clean_json.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.paths.clean_csv, index=False, encoding="utf-8-sig")
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))


def _load_or_build_test_set(df: pd.DataFrame, settings) -> list[dict[str, Any]]:
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        return build_test_set(df, settings.paths.eval_testset)
    test_set = read_json(settings.paths.eval_testset)
    if not isinstance(test_set, list):
        raise ValueError("test_set.json must contain a JSON list of samples.")
    return test_set


def _build_demo_answers(
    settings,
    index: LocalEmbeddingIndex,
    test_set: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    demo_items = test_set[: min(3, len(test_set))]
    demo_answers: list[dict[str, Any]] = []

    agent = None
    agent_status = "skipped"
    try:
        agent = build_agent(settings, index)
        agent_status = "ready"
    except Exception as exc:
        agent_status = f"unavailable: {type(exc).__name__}"

    for item in demo_items:
        qa_result = answer_question(item["question"], settings=settings, index=index)
        payload: dict[str, Any] = {
            "id": item["id"],
            "question": item["question"],
            "ground_truth": item["ground_truth"],
            "deterministic_answer": qa_result.answer,
            "retrieved_doc_ids": qa_result.retrieved_doc_ids,
            "retrieved_titles": qa_result.retrieved_titles,
            "retrieved_contexts": qa_result.retrieved_contexts,
            "agent_status": agent_status,
        }
        if agent is not None:
            try:
                payload["agent_answer"] = run_agent_question(agent, item["question"])
                payload["agent_status"] = "ready"
            except Exception as exc:
                payload["agent_status"] = f"failed: {type(exc).__name__}"
        demo_answers.append(payload)

    return demo_answers


def main() -> None:
    """Build the Phase 1 baseline pipeline end-to-end."""
    settings = load_settings()

    records, source_summary = _load_raw_records(settings)
    if not records:
        raise RuntimeError("No raw Crossref records available for the baseline pipeline.")

    clean_df = build_clean_dataframe(records, now_utc())
    if clean_df.empty:
        raise RuntimeError("Cleaning produced an empty dataframe; cannot continue.")
    _write_clean_artifacts(clean_df, settings)

    test_set = _load_or_build_test_set(clean_df, settings)
    index = LocalEmbeddingIndex.build(
        df=clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )

    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    quality = run_data_quality_checks(clean_df, settings, "baseline_quality")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
    demo_answers = _build_demo_answers(settings, index, test_set)
    write_json(settings.paths.demo_answers, demo_answers)

    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary={
            **source_summary,
            "clean_records": int(len(clean_df)),
            "test_set_samples": len(test_set),
            "embedding_documents": len(index.documents),
            "evaluation_samples": evaluation.summary.get("samples", len(test_set)),
        },
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )

    print("=== PHASE 1 COMPLETED ===")
    print(f"Raw records: {len(records)}")
    print(f"Clean records: {len(clean_df)}")
    print(f"Test set samples: {len(test_set)}")
    print(f"Baseline collection: {index.collection_name}")
    print(f"Baseline metrics saved to: {settings.paths.baseline_metrics}")
    print(f"Baseline answers saved to: {settings.paths.baseline_answers}")
    print(f"Baseline report saved to: {settings.paths.baseline_report}")


if __name__ == "__main__":
    main()
