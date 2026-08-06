from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def _load_clean_dataframe(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing baseline clean dataset at {path}. Run phase 1 before corruption flow."
        )
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"Expected JSON list at {path}, got {type(payload).__name__}.")
    df = pd.DataFrame(payload)
    if df.empty:
        raise ValueError("Baseline clean dataframe is empty; cannot continue corruption flow.")
    return df


def _write_clean_artifacts(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    write_json(json_path, df.to_dict(orient="records"))


def _require_existing(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required {label}: {path}")


def _load_json_report(path: Path) -> dict[str, Any]:
    if path.exists():
        payload = read_json(path)
        if isinstance(payload, dict):
            return payload
    raise FileNotFoundError(f"Missing required report artifact: {path}")


def _load_or_build_report(path: Path, builder) -> dict[str, Any]:
    if path.exists():
        return _load_json_report(path)
    return builder()


def _evaluate_state(
    *,
    df: pd.DataFrame,
    settings,
    embeddings_path: Path,
    metrics_path: Path,
    answers_path: Path,
) -> tuple[LocalEmbeddingIndex, dict[str, Any]]:
    index = LocalEmbeddingIndex.build(
        df=df,
        settings=settings,
        embeddings_output_path=embeddings_path,
    )
    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=metrics_path,
        answers_output_path=answers_path,
    )
    return index, evaluation.summary


def main() -> None:
    """Run the controlled corruption -> repair -> comparison flow."""
    settings = load_settings()

    _require_existing(settings.paths.clean_json, "baseline clean dataset")
    _require_existing(settings.paths.eval_testset, "evaluation test set")
    _require_existing(settings.paths.baseline_metrics, "baseline metrics")
    _require_existing(settings.paths.raw_records_json, "raw records snapshot")

    baseline_df = _load_clean_dataframe(settings.paths.clean_json)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_quality = _load_or_build_report(
        settings.paths.quality_dir / "baseline_quality.json",
        lambda: run_data_quality_checks(baseline_df, settings, "baseline_quality"),
    )
    baseline_freshness = _load_or_build_report(
        settings.paths.freshness_report,
        lambda: build_freshness_report(baseline_df, settings, settings.paths.freshness_report),
    )

    corrupted_df = corrupt_clean_dataframe(
        baseline_df,
        settings.paths.corruption_log,
    )
    _write_clean_artifacts(
        corrupted_df,
        settings.paths.corrupted_clean_csv,
        settings.paths.corrupted_clean_json,
    )
    corrupted_index, corrupted_metrics = _evaluate_state(
        df=corrupted_df,
        settings=settings,
        embeddings_path=settings.paths.corrupted_embeddings_json,
        metrics_path=settings.paths.corrupted_metrics,
        answers_path=settings.paths.corrupted_answers,
    )
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted_quality")
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings,
        settings.paths.quality_dir / "corrupted_freshness.json",
    )

    raw_records = load_raw_records(settings.paths.raw_records_json)
    if not raw_records:
        raise RuntimeError("Raw snapshot is empty; cannot repair corrupted data from source.")
    repaired_df = build_clean_dataframe(raw_records, now_utc())
    if repaired_df.empty:
        raise RuntimeError("Repair from raw source produced an empty dataframe.")
    _write_clean_artifacts(
        repaired_df,
        settings.paths.repaired_clean_csv,
        settings.paths.repaired_clean_json,
    )
    repaired_index, repaired_metrics = _evaluate_state(
        df=repaired_df,
        settings=settings,
        embeddings_path=settings.paths.repaired_embeddings_json,
        metrics_path=settings.paths.repaired_metrics,
        answers_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired_quality")
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings,
        settings.paths.quality_dir / "repaired_freshness.json",
    )

    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        baseline_quality=baseline_quality,
        baseline_freshness=baseline_freshness,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    print("=== CORRUPTION FLOW COMPLETED ===")
    print(f"Baseline rows: {len(baseline_df)}")
    print(f"Corrupted rows: {len(corrupted_df)}")
    print(f"Repaired rows: {len(repaired_df)}")
    print(f"Corruption log saved to: {settings.paths.corruption_log}")
    print(f"Corrupted metrics saved to: {settings.paths.corrupted_metrics}")
    print(f"Repaired metrics saved to: {settings.paths.repaired_metrics}")
    print(f"Comparison report saved to: {settings.paths.comparison_report}")
    print(
        "Retrieval hit rate:",
        baseline_metrics.get("retrieval_hit_rate"),
        "->",
        corrupted_metrics.get("retrieval_hit_rate"),
        "->",
        repaired_metrics.get("retrieval_hit_rate"),
    )
    print(
        "Mean token F1:",
        baseline_metrics.get("mean_token_f1"),
        "->",
        corrupted_metrics.get("mean_token_f1"),
        "->",
        repaired_metrics.get("mean_token_f1"),
    )
    print(
        "Judge accuracy:",
        baseline_metrics.get("judge_accuracy"),
        "->",
        corrupted_metrics.get("judge_accuracy"),
        "->",
        repaired_metrics.get("judge_accuracy"),
    )
    print(f"Corrupted collection: {corrupted_index.collection_name}")
    print(f"Repaired collection: {repaired_index.collection_name}")


if __name__ == "__main__":
    main()
