from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import read_json, write_json


MIN_SUMMARY_CHARS = 50


def _blank_mask(series: pd.Series) -> pd.Series:
    """Return a boolean mask for null, empty, or whitespace-only values."""
    normalized = series.astype("string").str.strip()
    return series.isna() | normalized.isna() | normalized.eq("")


def _check(name: str, observed: int, expected: str, success: bool) -> dict[str, Any]:
    return {
        "name": name,
        "success": bool(success),
        "observed": int(observed),
        "expected": expected,
    }


def _quality_report_path(settings: Settings, report_name: str) -> Path:
    """Resolve a report name inside data/quality without allowing traversal."""
    name = str(report_name).strip()
    if not name or Path(name).name != name:
        raise ValueError("report_name must be a non-empty file name, not a path.")
    return settings.paths.quality_dir / (name if name.endswith(".json") else f"{name}.json")


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run auditable checks for the canonical clean-paper schema.

    Every check records its observed value and expectation. Missing columns are
    reported as failed checks instead of raising a ``KeyError`` so the artifact
    still explains why a pipeline state is invalid.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    total_rows = len(df)
    required_columns = (
        "paper_id",
        "title",
        "summary",
        "published",
        "age_days",
        "text_for_embedding",
        "authors_joined",
        "categories_joined",
    )
    missing_columns = [column for column in required_columns if column not in df.columns]

    def missing_count(column: str) -> int:
        return total_rows if column not in df.columns else int(_blank_mask(df[column]).sum())

    null_paper_ids = missing_count("paper_id")
    null_titles = missing_count("title")

    if "paper_id" in df.columns:
        valid_ids = (
            df.loc[~_blank_mask(df["paper_id"]), "paper_id"]
            .astype("string")
            .str.strip()
            .str.casefold()
        )
        duplicate_paper_id_rows = int(valid_ids.duplicated(keep=False).sum())
    else:
        duplicate_paper_id_rows = total_rows

    if "summary" in df.columns:
        summary_lengths = (
            df["summary"]
            .fillna("")
            .astype(str)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .str.len()
        )
        invalid_summary_rows = int((summary_lengths < MIN_SUMMARY_CHARS).sum())
    else:
        summary_lengths = pd.Series([0] * total_rows, dtype="int64")
        invalid_summary_rows = total_rows

    blank_summary_rows = missing_count("summary")
    blank_text_rows = missing_count("text_for_embedding")

    if "published" in df.columns:
        published = pd.to_datetime(df["published"], errors="coerce", utc=True, format="mixed")
        invalid_published_rows = int(published.isna().sum())
    else:
        invalid_published_rows = total_rows

    if "age_days" in df.columns:
        age_days = pd.to_numeric(df["age_days"], errors="coerce")
        invalid_age_days_rows = int((age_days.isna() | age_days.lt(0)).sum())
        stale_rows = int(age_days.gt(settings.freshness_threshold_days).fillna(False).sum())
    else:
        invalid_age_days_rows = total_rows
        stale_rows = total_rows

    check_results = [
        _check("row_count_positive", total_rows, "> 0", total_rows > 0),
        _check("required_columns_present", len(missing_columns), "0 missing columns", not missing_columns),
        _check("paper_id_not_null", null_paper_ids, "0 invalid rows", null_paper_ids == 0),
        _check(
            "paper_id_unique",
            duplicate_paper_id_rows,
            "0 duplicate rows",
            duplicate_paper_id_rows == 0,
        ),
        _check("title_not_null", null_titles, "0 invalid rows", null_titles == 0),
        _check(
            "summary_min_length",
            invalid_summary_rows,
            f"0 rows shorter than {MIN_SUMMARY_CHARS} characters",
            invalid_summary_rows == 0,
        ),
        _check(
            "published_parseable",
            invalid_published_rows,
            "0 invalid rows",
            invalid_published_rows == 0,
        ),
        _check(
            "age_days_valid",
            invalid_age_days_rows,
            "0 null, non-numeric, or negative rows",
            invalid_age_days_rows == 0,
        ),
        _check(
            "age_days_within_freshness_threshold",
            stale_rows,
            f"0 rows older than {settings.freshness_threshold_days} days",
            stale_rows == 0,
        ),
    ]
    structural_checks = {
        "required_columns_present": not missing_columns,
        "row_count_positive": total_rows > 0,
        "paper_id_not_blank": null_paper_ids == 0,
        "paper_id_unique": duplicate_paper_id_rows == 0,
        "title_not_blank": null_titles == 0,
        "published_valid": invalid_published_rows == 0,
        "age_days_valid": invalid_age_days_rows == 0,
        "text_for_embedding_not_blank": blank_text_rows == 0,
        "summary_min_length": invalid_summary_rows == 0,
    }
    summary_present_ratio = 1.0 - (blank_summary_rows / total_rows) if total_rows else 0.0
    text_present_ratio = 1.0 - (blank_text_rows / total_rows) if total_rows else 0.0
    fresh_rows_ratio = 1.0 - (stale_rows / total_rows) if total_rows else 0.0
    checks = {
        **structural_checks,
        "summary_present_ratio": round(summary_present_ratio, 4),
        "text_for_embedding_present_ratio": round(text_present_ratio, 4),
        "fresh_rows_ratio": round(fresh_rows_ratio, 4),
    }
    failed_checks = [check["name"] for check in check_results if not check["success"]]
    generated_at = datetime.now(UTC).isoformat()
    payload = {
        "report_name": Path(str(report_name)).stem,
        "generated_at": generated_at.replace("+00:00", "Z"),
        "generated_at_utc": generated_at,
        "total_rows": total_rows,
        "required_columns": list(required_columns),
        "missing_columns": missing_columns,
        "summary_min_chars": MIN_SUMMARY_CHARS,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "overall_pass": all(structural_checks.values()),
        "success": not failed_checks,
        "passed_checks": len(check_results) - len(failed_checks),
        "failed_checks": failed_checks,
        "checks": checks,
        "check_results": check_results,
        "counts": {
            "blank_paper_id": null_paper_ids,
            "duplicate_paper_id": duplicate_paper_id_rows,
            "blank_title": null_titles,
            "blank_summary": blank_summary_rows,
            "blank_text_for_embedding": blank_text_rows,
            "invalid_published": invalid_published_rows,
            "invalid_age_days": invalid_age_days_rows,
            "stale_rows": stale_rows,
            "min_summary_chars": int(summary_lengths.min()) if total_rows else 0,
            "max_summary_chars": int(summary_lengths.max()) if total_rows else 0,
            "mean_summary_chars": round(float(summary_lengths.mean()), 2) if total_rows else 0.0,
        },
        "thresholds": {"freshness_threshold_days": settings.freshness_threshold_days},
    }
    write_json(_quality_report_path(settings, report_name), payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Build freshness signals from source ``published`` and derived ``age_days``."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")

    total_rows = len(df)
    published = (
        pd.to_datetime(df["published"], errors="coerce", utc=True, format="mixed")
        if "published" in df.columns
        else pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns, UTC]")
    )
    age_days = (
        pd.to_numeric(df["age_days"], errors="coerce")
        if "age_days" in df.columns
        else pd.Series(float("nan"), index=df.index, dtype="float64")
    )

    invalid_timestamp_rows = int(published.isna().sum())
    invalid_age_days_rows = int((age_days.isna() | age_days.lt(0)).sum())
    stale_mask = age_days.gt(settings.freshness_threshold_days).fillna(False)
    stale_rows = int(stale_mask.sum())
    valid_published = published.dropna()

    latest = valid_published.max().date().isoformat() if not valid_published.empty else None
    oldest = valid_published.min().date().isoformat() if not valid_published.empty else None
    stale_ratio = stale_rows / total_rows if total_rows else 0.0
    is_fresh = (
        total_rows > 0
        and invalid_timestamp_rows == 0
        and invalid_age_days_rows == 0
        and stale_rows == 0
    )
    generated_at = datetime.now(UTC).isoformat()
    payload = {
        "generated_at": generated_at.replace("+00:00", "Z"),
        "generated_at_utc": generated_at,
        "source_timestamp_column": "published",
        "age_column": "age_days",
        "threshold_days": settings.freshness_threshold_days,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "latest_published": latest,
        "oldest_published": oldest,
        "stale_rows": stale_rows,
        "fresh_rows": total_rows - stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "invalid_timestamp_rows": invalid_timestamp_rows,
        "invalid_age_days_rows": invalid_age_days_rows,
        "is_fresh": is_fresh,
    }
    write_json(Path(report_path), payload)
    return payload


def audit_embedding_manifest(
    df: pd.DataFrame,
    settings: Settings,
    manifest_path,
    report_path,
) -> dict[str, Any]:
    """Audit the embedding manifest against clean data and configured index paths."""
    manifest_file = Path(manifest_path)
    if not manifest_file.is_file():
        payload = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "success": False,
            "manifest_path": str(manifest_file),
            "failed_checks": ["manifest_file_exists"],
            "checks": [_check("manifest_file_exists", 0, "1 existing file", False)],
        }
        write_json(Path(report_path), payload)
        return payload

    manifest = read_json(manifest_file)
    documents = manifest.get("documents")
    documents = documents if isinstance(documents, list) else []
    document_count = len(documents)
    clean_count = len(df)

    record_ids = [str(item.get("record_id", "")).strip() for item in documents]
    manifest_paper_ids = [str(item.get("paper_id", "")).strip() for item in documents]
    clean_paper_ids = (
        set(df["paper_id"].dropna().astype(str).str.strip()) if "paper_id" in df.columns else set()
    )
    nonblank_manifest_paper_ids = {paper_id for paper_id in manifest_paper_ids if paper_id}
    duplicate_record_rows = sum(
        1 for value in record_ids if value and record_ids.count(value) > 1
    )
    duplicate_paper_rows = sum(
        1 for value in manifest_paper_ids if value and manifest_paper_ids.count(value) > 1
    )
    missing_metadata_rows = sum(
        1
        for document in documents
        if not isinstance(document.get("metadata"), dict)
        or any(
            not str(document["metadata"].get(field, "")).strip()
            for field in ("paper_id", "title", "published", "summary")
        )
    )

    configured_persist_path = settings.paths.chroma_dir.resolve()
    manifest_persist_raw = str(manifest.get("persist_path", "")).strip()
    manifest_persist_path = Path(manifest_persist_raw).resolve() if manifest_persist_raw else None
    manifest_path_matches_config = manifest_persist_path == configured_persist_path

    checks = [
        _check("manifest_file_exists", 1, "1 existing file", True),
        _check("backend_is_chroma", int(manifest.get("backend") == "chroma"), "1", manifest.get("backend") == "chroma"),
        _check(
            "embedding_model_matches_config",
            int(manifest.get("embedding_model") == settings.embedding_model),
            "1",
            manifest.get("embedding_model") == settings.embedding_model,
        ),
        _check(
            "collection_name_matches_baseline_config",
            int(manifest.get("collection_name") == settings.baseline_collection_name),
            "1",
            manifest.get("collection_name") == settings.baseline_collection_name,
        ),
        _check(
            "document_count_matches_clean_rows",
            document_count,
            f"{clean_count} documents",
            document_count == clean_count,
        ),
        _check("record_id_unique", duplicate_record_rows, "0 duplicate rows", duplicate_record_rows == 0),
        _check("paper_id_unique", duplicate_paper_rows, "0 duplicate rows", duplicate_paper_rows == 0),
        _check(
            "paper_ids_match_clean_data",
            len(nonblank_manifest_paper_ids.symmetric_difference(clean_paper_ids)),
            "0 differing IDs",
            nonblank_manifest_paper_ids == clean_paper_ids,
        ),
        _check(
            "required_metadata_present",
            missing_metadata_rows,
            "0 invalid documents",
            missing_metadata_rows == 0,
        ),
        _check(
            "persist_path_matches_config",
            int(manifest_path_matches_config),
            "1",
            manifest_path_matches_config,
        ),
        _check(
            "configured_persist_path_exists",
            int(configured_persist_path.exists()),
            "1",
            configured_persist_path.exists(),
        ),
    ]
    failed_checks = [check["name"] for check in checks if not check["success"]]
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "manifest_path": str(manifest_file),
        "backend": manifest.get("backend"),
        "embedding_model": manifest.get("embedding_model"),
        "collection_name": manifest.get("collection_name"),
        "document_count": document_count,
        "clean_row_count": clean_count,
        "manifest_persist_path": manifest_persist_raw or None,
        "configured_persist_path": str(configured_persist_path),
        "success": not failed_checks,
        "passed_checks": len(checks) - len(failed_checks),
        "failed_checks": failed_checks,
        "checks": checks,
    }
    write_json(Path(report_path), payload)
    return payload


def build_observability_snapshot(
    state: str,
    quality: dict[str, Any],
    freshness: dict[str, Any],
    embedding_audit: dict[str, Any],
    output_path,
    metrics: dict[str, Any] | None = None,
    answers_count: int | None = None,
) -> dict[str, Any]:
    """Freeze comparable observability signals for one pipeline state."""
    normalized_state = str(state).strip().lower()
    if normalized_state not in {"baseline", "corrupted", "repaired"}:
        raise ValueError("state must be baseline, corrupted, or repaired.")

    quality_checks = {
        item.get("name"): item.get("observed")
        for item in quality.get("check_results", [])
    }
    payload = {
        "state": normalized_state,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "signals": {
            "row_count": quality.get("total_rows", 0),
            "null_paper_id_rows": quality_checks.get("paper_id_not_null"),
            "duplicate_paper_id_rows": quality_checks.get("paper_id_unique"),
            "missing_title_rows": quality_checks.get("title_not_null"),
            "invalid_summary_rows": quality_checks.get("summary_min_length"),
            "invalid_age_days_rows": freshness.get("invalid_age_days_rows"),
            "stale_rows": freshness.get("stale_rows"),
            "stale_ratio": freshness.get("stale_ratio"),
            "latest_published": freshness.get("latest_published"),
            "oldest_published": freshness.get("oldest_published"),
            "embedding_document_count": embedding_audit.get("document_count"),
            "embedding_collection_name": embedding_audit.get("collection_name"),
        },
        "status": {
            "quality_success": quality.get("success", False),
            "freshness_is_fresh": freshness.get("is_fresh", False),
            "embedding_audit_success": embedding_audit.get("success", False),
        },
        "failed_checks": {
            "quality": quality.get("failed_checks", []),
            "embedding": embedding_audit.get("failed_checks", []),
        },
        "metrics": {
            name: (metrics or {}).get(name)
            for name in (
                "samples",
                "retrieval_hit_rate",
                "mean_token_f1",
                "judge_accuracy",
                "mean_judge_score",
            )
        },
        "answers_count": answers_count,
    }
    write_json(Path(output_path), payload)
    return payload
