from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def _safe_int(value: object) -> int:
    try:
        if pd.isna(value):
            return 0
    except Exception:
        pass
    try:
        return int(value)
    except Exception:
        return 0


def _quality_path(settings: Settings, report_name: str) -> Path:
    report_path = Path(report_name)
    if report_path.suffix.lower() != ".json":
        report_path = report_path.with_suffix(".json")
    if not report_path.is_absolute():
        report_path = settings.paths.quality_dir / report_path.name
    return report_path


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run baseline data-quality checks and persist a JSON evidence file."""
    required_columns = [
        "paper_id",
        "title",
        "summary",
        "published",
        "age_days",
        "text_for_embedding",
        "authors_joined",
        "categories_joined",
    ]
    missing_columns = [column for column in required_columns if column not in df.columns]

    paper_ids = (
        df["paper_id"].fillna("").astype(str).str.strip()
        if "paper_id" in df.columns
        else pd.Series([], dtype="string")
    )
    titles = df["title"].astype(str).str.strip() if "title" in df.columns else pd.Series([], dtype="string")
    summaries = df["summary"].fillna("").astype(str).str.strip() if "summary" in df.columns else pd.Series([], dtype="string")
    texts = (
        df["text_for_embedding"].fillna("").astype(str).str.strip()
        if "text_for_embedding" in df.columns
        else pd.Series([], dtype="string")
    )
    published = (
        pd.to_datetime(df["published"], errors="coerce", utc=True, format="mixed")
        if "published" in df.columns
        else pd.Series([], dtype="datetime64[ns, UTC]")
    )
    age_days_numeric = (
        pd.to_numeric(df["age_days"], errors="coerce")
        if "age_days" in df.columns
        else pd.Series([], dtype="float64")
    )

    total_rows = int(len(df))
    blank_paper_id = int((paper_ids == "").sum()) if not paper_ids.empty else total_rows
    duplicate_paper_id = int(paper_ids.str.casefold().duplicated().sum()) if not paper_ids.empty else 0
    blank_title = int((titles == "").sum()) if not titles.empty else total_rows
    blank_summary = int((summaries == "").sum()) if not summaries.empty else total_rows
    blank_text = int((texts == "").sum()) if not texts.empty else total_rows
    invalid_published = int(published.isna().sum()) if len(published) else total_rows
    invalid_age_days = (
        int((age_days_numeric.isna() | (age_days_numeric < 0)).sum())
        if len(age_days_numeric)
        else total_rows
    )
    stale_rows = (
        int((age_days_numeric > settings.freshness_threshold_days).sum())
        if len(age_days_numeric)
        else total_rows
    )
    summary_chars = (
        pd.to_numeric(df["summary_chars"], errors="coerce").fillna(0).astype(int)
        if "summary_chars" in df.columns
        else pd.Series([_safe_int(len(value)) for value in summaries], dtype="int64")
    )

    checks = {
        "required_columns_present": not missing_columns,
        "row_count_positive": total_rows > 0,
        "paper_id_not_blank": blank_paper_id == 0,
        "paper_id_unique": duplicate_paper_id == 0,
        "title_not_blank": blank_title == 0,
        "published_valid": invalid_published == 0,
        "age_days_valid": invalid_age_days == 0,
        "text_for_embedding_not_blank": blank_text == 0,
    }
    payload: dict[str, Any] = {
        "report_name": report_name,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "total_rows": total_rows,
        "required_columns": required_columns,
        "missing_columns": missing_columns,
        "overall_pass": all(checks.values()),
        "checks": {
            **checks,
            "summary_present_ratio": round(1.0 - (blank_summary / total_rows), 4) if total_rows else 0.0,
            "text_for_embedding_present_ratio": round(1.0 - (blank_text / total_rows), 4) if total_rows else 0.0,
            "fresh_rows_ratio": round(1.0 - (stale_rows / total_rows), 4) if total_rows else 0.0,
        },
        "counts": {
            "blank_paper_id": blank_paper_id,
            "duplicate_paper_id": duplicate_paper_id,
            "blank_title": blank_title,
            "blank_summary": blank_summary,
            "blank_text_for_embedding": blank_text,
            "invalid_published": invalid_published,
            "invalid_age_days": invalid_age_days,
            "stale_rows": stale_rows,
            "min_summary_chars": int(summary_chars.min()) if len(summary_chars) else 0,
            "max_summary_chars": int(summary_chars.max()) if len(summary_chars) else 0,
            "mean_summary_chars": round(float(summary_chars.mean()), 2) if len(summary_chars) else 0.0,
        },
        "thresholds": {
            "freshness_threshold_days": settings.freshness_threshold_days,
        },
    }

    output_path = _quality_path(settings, report_name)
    write_json(output_path, payload)
    payload["output_path"] = str(output_path)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Create a JSON freshness summary for the current clean corpus."""
    output_path = Path(report_path)
    if output_path.suffix.lower() != ".json":
        output_path = output_path.with_suffix(".json")
    if not output_path.is_absolute():
        output_path = settings.paths.quality_dir / output_path.name

    if df.empty or "published" not in df.columns:
        payload: dict[str, Any] = {
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "total_rows": int(len(df)),
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": int(len(df)),
            "fresh_rows": 0,
            "freshness_threshold_days": settings.freshness_threshold_days,
            "is_fresh": False,
        }
        write_json(output_path, payload)
        payload["output_path"] = str(output_path)
        return payload

    published = pd.to_datetime(df["published"], errors="coerce", utc=True, format="mixed")
    age_days = pd.to_numeric(df["age_days"], errors="coerce").fillna(0).astype(int) if "age_days" in df.columns else pd.Series([0] * len(df))
    valid = published.dropna()

    latest = valid.max() if not valid.empty else None
    oldest = valid.min() if not valid.empty else None
    stale_rows = int((age_days > settings.freshness_threshold_days).sum())
    total_rows = int(len(df))

    payload = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "total_rows": total_rows,
        "latest_published": latest.date().isoformat() if latest is not None else None,
        "oldest_published": oldest.date().isoformat() if oldest is not None else None,
        "stale_rows": stale_rows,
        "fresh_rows": total_rows - stale_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "stale_ratio": round(stale_rows / total_rows, 4) if total_rows else 0.0,
        "is_fresh": stale_rows == 0,
    }
    write_json(output_path, payload)
    payload["output_path"] = str(output_path)
    return payload
